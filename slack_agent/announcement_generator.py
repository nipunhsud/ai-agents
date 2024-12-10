from datetime import datetime
import json
from typing import Dict, Optional, List
import requests
from atlassian import Jira
from trello import TrelloClient




class ExternalDataFetcher:
    def __init__(self):
        self.jira_client = None
        self.trello_client = None
    
    def connect_jira(self, url: str, username: str, api_token: str):
        """Connect to Jira instance"""
        self.jira_client = Jira(
            url=url,
            username=username,
            password=api_token
        )
    
    def connect_trello(self, api_key: str, token: str):
        """Connect to Trello"""
        self.trello_client = TrelloClient(
            api_key=api_key,
            token=token
        )
    
    def get_jira_team_milestones(self, project_key: str, sprint_name: Optional[str] = None) -> Dict:
        """Fetch team milestone information from Jira"""
        if not self.jira_client:
            raise ValueError("Jira client not connected")
        
        # Get active sprint if sprint_name not provided
        if not sprint_name:
            board_id = self.jira_client.get_board_by_project_key(project_key)['id']
            sprints = self.jira_client.get_all_sprints(board_id, state='active')
            sprint = sprints[0] if sprints else None
            sprint_name = sprint['name'] if sprint else None
        
        if sprint_name:
            jql = f'project = {project_key} AND sprint in ("{sprint_name}")'
        else:
            jql = f'project = {project_key}'
            
        issues = self.jira_client.jql(jql)
        
        completed_issues = [i for i in issues['issues'] if i['fields']['status']['name'] == 'Done']
        
        return {
            'sprint_name': sprint_name,
            'total_issues': len(issues['issues']),
            'completed_issues': len(completed_issues),
            'completion_rate': len(completed_issues) / len(issues['issues']) * 100 if issues['issues'] else 0
        }
    

    def get_upcoming_events(self, project_key: str, days_ahead: int = 30) -> Dict:
        """Fetch upcoming events and deadlines from Jira"""
        if not self.jira_client:
            raise ValueError("Jira client not connected")
        
        # Get issues with due dates in the next X days
        jql = f'''project = {project_key} 
                AND duedate >= now() 
                AND duedate <= startOfDay(+{days_ahead}d)
                ORDER BY duedate ASC'''
                
        issues = self.jira_client.jql(jql)
        
        return {
            'events': [{
                'title': issue['fields']['summary'],
                'due_date': issue['fields']['duedate'],
                'priority': issue['fields']['priority']['name'],
                'type': issue['fields']['issuetype']['name']
            } for issue in issues['issues']]
        }

    def get_trello_team_milestones(self, board_id: str) -> Dict:
        """Fetch team milestone information from Trello"""
        if not self.trello_client:
            raise ValueError("Trello client not connected")
            
        board = self.trello_client.get_board(board_id)
        lists = board.list_lists()
        
        milestones = []
        for lst in lists:
            cards = lst.list_cards()
            completed = len([c for c in cards if c.get_list().name == 'Done'])
            if cards:
                milestones.append({
                    'name': lst.name,
                    'total_cards': len(cards),
                    'completed_cards': completed,
                    'completion_rate': (completed / len(cards)) * 100
                })
        
        return {'milestones': milestones}



class SlackAnnouncementGenerator:
    def __init__(self):
        self.external_data = ExternalDataFetcher()
        self.templates = {
            'feature': {
                'emoji': '🎉',
                'title': 'New Feature Launch',
                'blocks': self._feature_launch_blocks
            },
            'company': {
                'emoji': '📢',
                'title': 'Company Update',
                'blocks': self._company_update_blocks
            },
            'milestone': {
                'emoji': '🏆',
                'title': 'Team Milestone',
                'blocks': self._milestone_blocks
            },
            'event': {
                'emoji': '📅',
                'title': 'Upcoming Event',
                'blocks': self._event_blocks
            }
        }

    def generate_team_milestone_announcement(self, source: str = 'jira', **kwargs) -> Dict:
        """Generate a team milestone announcement using data from Jira or Trello"""
        if source.lower() == 'jira':
            milestone_data = self.external_data.get_jira_team_milestones(
                project_key=kwargs.get('project_key'),
                sprint_name=kwargs.get('sprint_name')
            )
            
            description = (f"Sprint: {milestone_data['sprint_name']}\n"
                         f"Progress: {milestone_data['completion_rate']:.1f}% complete\n"
                         f"Completed Tasks: {milestone_data['completed_issues']}/{milestone_data['total_issues']}")
            
            return self.generate_announcement(
                type='milestone',
                title=f"Sprint Update: {milestone_data['sprint_name']}",
                description=description,
                impact=f"Team has completed {milestone_data['completed_issues']} tasks this sprint!",
                next_steps=[
                    "Review remaining sprint tasks",
                    "Join daily standup for updates",
                    "Update your task status in Jira"
                ]
            )
            
        elif source.lower() == 'trello':
            milestone_data = self.external_data.get_trello_team_milestones(
                board_id=kwargs.get('board_id')
            )
            
            # Find the milestone with the highest completion rate
            top_milestone = max(milestone_data['milestones'], 
                              key=lambda x: x['completion_rate'])
            
            description = (f"Board Progress Update:\n" + 
                         "\n".join([f"• {m['name']}: {m['completion_rate']:.1f}% complete" 
                                  for m in milestone_data['milestones']]))
            
            return self.generate_announcement(
                type='milestone',
                title="Team Progress Update",
                description=description,
                impact=f"Highest progress in '{top_milestone['name']}' at {top_milestone['completion_rate']:.1f}% completion!",
                next_steps=[
                    "Check Trello board for detailed status",
                    "Update your card status",
                    "Join team sync for updates"
                ]
            )
        else:
            raise ValueError("Invalid source. Use 'jira' or 'trello'")

    def generate_upcoming_events_announcement(self, project_key: str, days_ahead: int = 30) -> Dict:
        """Generate an announcement for upcoming events and deadlines"""
        events_data = self.external_data.get_upcoming_events(project_key, days_ahead)
        
        # Group events by week
        from datetime import datetime
        events_by_week = {}
        for event in events_data['events']:
            event_date = datetime.strptime(event['due_date'], '%Y-%m-%d')
            week_num = event_date.isocalendar()[1]
            if week_num not in events_by_week:
                events_by_week[week_num] = []
            events_by_week[week_num].append(event)
        
        # Create description with events grouped by week
        description = "📅 Upcoming Events & Deadlines:\n\n"
        for week_num in sorted(events_by_week.keys()):
            description += f"Week of {events_by_week[week_num][0]['due_date']}:\n"
            for event in events_by_week[week_num]:
                description += f"• {event['due_date']}: {event['title']} ({event['priority']} priority)\n"
        
        next_steps = [
            "Add these dates to your calendar",
            "Review and update your assigned tasks",
            f"Check Jira for more details on specific items"
        ]
        
        if len(events_data['events']) > 0:
            impact = f"We have {len(events_data['events'])} important dates coming up in the next {days_ahead} days!"
        else:
            impact = f"No major deadlines in the next {days_ahead} days."
        
        return self.generate_announcement(
            type='event',
            title=f"📅 Upcoming Events & Deadlines ({days_ahead} Day Outlook)",
            description=description,
            impact=impact,
            next_steps=next_steps
        )

    def generate_announcement(self, 
                            type: str,
                            title: str,
                            description: str,
                            date: Optional[str] = None,
                            impact: Optional[str] = None,
                            next_steps: Optional[List[str]] = None,
                            additional_info: Optional[Dict] = None) -> Dict:
        """
        Generate a Slack announcement message with proper formatting.
        
        Args:
            type: Type of announcement ('feature', 'company', 'milestone', 'event')
            title: Main announcement title
            description: Detailed description
            date: Relevant date (optional)
            impact: Impact description (optional)
            next_steps: List of next steps (optional)
            additional_info: Any additional fields specific to the announcement type
        
        Returns:
            Dict containing formatted Slack message blocks
        """
        if type not in self.templates:
            raise ValueError(f"Invalid announcement type. Must be one of: {', '.join(self.templates.keys())}")

        template = self.templates[type]
        return template['blocks'](
            title=title,
            description=description,
            date=date,
            impact=impact,
            next_steps=next_steps,
            additional_info=additional_info
        )

    def _feature_launch_blocks(self, **kwargs) -> Dict:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎉 New Feature Launch: {kwargs['title']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*What's New:*\n{kwargs['description']}"
                }
            }
        ]

        if kwargs.get('impact'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Impact:*\n{kwargs['impact']}"
                }
            })

        if kwargs.get('date'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Launch Date:* {kwargs['date']}"
                }
            })

        if kwargs.get('next_steps'):
            steps_text = "\n".join([f"• {step}" for step in kwargs['next_steps']])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Next Steps:*\n{steps_text}"
                }
            })

        return {"blocks": blocks}

    def _company_update_blocks(self, **kwargs) -> Dict:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📢 Company Update: {kwargs['title']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": kwargs['description']
                }
            }
        ]

        if kwargs.get('impact'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Key Impact:*\n{kwargs['impact']}"
                }
            })

        if kwargs.get('next_steps'):
            steps_text = "\n".join([f"• {step}" for step in kwargs['next_steps']])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Next Steps:*\n{steps_text}"
                }
            })

        return {"blocks": blocks}

    def _milestone_blocks(self, **kwargs) -> Dict:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🏆 Team Milestone: {kwargs['title']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": kwargs['description']
                }
            }
        ]

        if kwargs.get('impact'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Achievement Impact:*\n{kwargs['impact']}"
                }
            })

        return {"blocks": blocks}

    def _event_blocks(self, **kwargs) -> Dict:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📅 Upcoming Event: {kwargs['title']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": kwargs['description']
                }
            }
        ]

        if kwargs.get('date'):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Date:* {kwargs['date']}"
                }
            })

        if kwargs.get('next_steps'):
            steps_text = "\n".join([f"• {step}" for step in kwargs['next_steps']])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Items:*\n{steps_text}"
                }
            })

        return {"blocks": blocks}



"""
# Example usage:
if __name__ == "__main__":
    # Initialize the generator
    generator = SlackAnnouncementGenerator()
    
    # Example feature announcement
    feature_announcement = generator.generate_announcement(
        type='feature',
        title='Dark Mode',
        description='We're introducing Dark Mode across all our applications!',
        date='2024-12-15',
        impact='This update will improve user experience in low-light conditions and reduce eye strain.',
        next_steps=[
            'Update your app to the latest version',
            'Access settings to toggle Dark Mode',
            'Share feedback in #product-feedback channel'
        ]
    )
    
    # Example company update
    company_announcement = generator.generate_announcement(
        type='company',
        title='Q4 Results',
        description='We\'ve exceeded our Q4 targets across all key metrics!',
        impact='This positions us well for continued growth in the coming year.',
        next_steps=[
            'Join the all-hands meeting tomorrow at 10 AM',
            'Review the detailed report in the shared drive'
        ]
    )
    
    # Print examples
    print("Feature Announcement:")
    print(json.dumps(feature_announcement, indent=2))
    print("\nCompany Update:")
    print(json.dumps(company_announcement, indent=2))

"""