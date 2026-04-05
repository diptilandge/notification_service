import jinja2

# In-memory mock storage for templates
# In a real app, these would come from a database or a file system
MOCK_TEMPLATES = {
    "order_shipped": "Hello {{name}}, your order {{order_id}} has shipped!",
    "welcome_email": "Welcome {{name}}! Thank you for joining.",
    "otp_code": "Your OTP is {{code}}. Do not share it with anyone."
}

def render_template(template_name: str, payload: dict) -> str:
    template_str = MOCK_TEMPLATES.get(template_name)
    if not template_str:
        # Fallback to generating raw string from payload if template not found
        # Or raise an exception, let's keep it simple and just stringify
        return str(payload)
    
    template = jinja2.Template(template_str)
    return template.render(**payload)
