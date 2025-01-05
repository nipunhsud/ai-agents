from pathlib import Path
import yaml

def load_email_templates():
    """Load email templates from YAML file."""
    template_path = Path(__file__).parent / "templates" / "email_templates.yaml"
    try:
        with open(template_path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}

def save_email_template(template_name: str, template_content: dict):
    """Save email template to YAML file."""
    template_path = Path(__file__).parent / "templates" / "email_templates.yaml"
    templates = load_email_templates()
    templates[template_name] = template_content
    
    template_path.parent.mkdir(exist_ok=True)
    with open(template_path, 'w') as f:
        yaml.dump(templates, f)