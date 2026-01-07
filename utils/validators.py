import re
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    # Allow simpler formats with common separators
    # Strip spaces, dashes, parens, plus
    clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    # Check length (10-15 digits) and numeric
    return clean_phone.isdigit() and 10 <= len(clean_phone) <= 15

def validate_tech_stack(tech_stack):
    techs = [tech.strip() for tech in tech_stack.split(',') if tech.strip()]
    return len(techs) > 0
