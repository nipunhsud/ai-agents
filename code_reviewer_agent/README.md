# Code Reviewer Agent

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [File Structure](#file-structure)
- [Inputs and Outputs](#inputs-and-outputs)
- [Workflows](#workflows)

---

## Overview

The Code Reviewer Agent is a Django application designed to automate code review processes for GitHub repositories. It acts as a webhook listener that responds to pull request events, analyzing commits and providing automated feedback by updating commit messages, PR descriptions, and titles using AI-powered suggestions.

The agent integrates with GitHub's API to process pull requests and commits, leveraging Claude LLM to generate meaningful code review feedback and documentation. It aims to improve code quality and maintain consistent commit message standards across projects.

---

## Features

### Automated Code Review
- Webhook integration with GitHub for real-time PR monitoring
- Automatic analysis of commit changes and diffs
- AI-powered generation of conventional commit messages
- Comprehensive PR description generation
- Smart PR title suggestions based on commit contents

### GitHub Integration
- Secure webhook verification using HMAC signatures
- Complete GitHub API integration for:
  - Fetching commit details and diffs
  - Updating commit messages
  - Modifying PR descriptions and titles
  - Managing repository branches

### Code Analysis
- Detailed diff parsing and analysis
- Support for file additions, modifications, and deletions
- Statistical tracking of code changes
- Patch content analysis for granular change tracking

---

## File Structure

```
code_reviewer_agent/
├── __init__.py           # Package initializer
├── admin.py             # Django admin configuration (currently empty)
├── apps.py              # Django app configuration
├── models.py            # Database models (currently empty)
├── planner.py           # Core logic for code review automation
├── tests.py             # Test cases (currently empty)
└── views.py             # HTTP endpoint handlers

- **`planner.py`**: Contains the core business logic for processing GitHub webhooks, analyzing code changes, and generating reviews
- **`views.py`**: Implements HTTP endpoints for webhook handling and testing
- **`apps.py`**: Defines the Django app configuration with name 'agents.code_reviewer_agent'
```

---

## Inputs and Outputs

### GitHub Webhook Handler

**Inputs:**
- GitHub webhook POST requests containing:
  - Event type header (X-GitHub-Event)
  - HMAC signature (X-Hub-Signature-256)
  - JSON payload with pull request or commit information
- Required environment variables:
  - GitHub API token
  - Webhook secret for verification

**Outputs:**
- HTTP response indicating webhook processing status
- Updated commit messages in GitHub repository
- Modified pull request descriptions and titles
- Created commit comments with suggestions

### Code Analysis

**Inputs:**
- Commit data including:
  - SHA identifiers
  - File changes and patches
  - Original commit messages
  - Statistical information

**Outputs:**
- Generated conventional commit messages
- Detailed commit descriptions
- Pull request summaries
- Change analysis reports

---

## Workflows

### Pull Request Processing

1. **Webhook Reception**
   - Application receives GitHub webhook POST request
   - Validates webhook signature using HMAC
   - Identifies event type from headers

2. **Event Processing**
   - For 'pull_request' events:
     - Handles 'opened' and 'synchronize' actions
     - Fetches complete commit details
     - Triggers analysis workflow

3. **Commit Analysis**
   - For each commit:
     - Retrieves diff information
     - Analyzes file changes
     - Categorizes modifications
     - Generates statistics

4. **Review Generation**
   - Analyzes all commits in the PR
   - Generates appropriate commit messages
   - Creates comprehensive PR description
   - Suggests meaningful PR title

5. **GitHub Updates**
   - Updates commit messages maintaining git history
   - Modifies PR description and title
   - Adds review comments when necessary

### Security Considerations

- Implements webhook signature verification
- Uses secure GitHub API token handling
- Validates all incoming webhook payloads
- Implements error handling and logging

### Performance Optimization

- Processes commits sequentially to maintain consistency
- Uses efficient diff parsing
- Implements proper error handling and recovery
- Maintains atomic operations for GitHub updates

The agent is designed to be reliable, secure, and maintainable while providing valuable automated code review assistance through AI-powered analysis and suggestions.