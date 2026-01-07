import re
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    # Allow simpler formats with common separators
    # Strip spaces, dashes, parens
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    # Remove leading + if present (country code)
    if clean_phone.startswith('+'):
        clean_phone = clean_phone[1:]
    # Check length (7-15 digits) and numeric
    return clean_phone.isdigit() and 7 <= len(clean_phone) <= 15

def validate_tech_stack(tech_stack):
    techs = [tech.strip() for tech in tech_stack.split(',') if tech.strip()]
    return len(techs) > 0

import re

def validate_groq_key(key: str) -> bool:
    """Validate a Groq API key roughly by pattern.

    Expected pattern: starts with 'gsk_' followed by 16-128 allowed chars (alnum, hyphen, underscore).
    This is a lightweight check — the key may still be invalid on the server side.
    """
    if not key or not isinstance(key, str):
        return False
    pattern = r'^gsk_[A-Za-z0-9\-_]{16,128}$'
    return bool(re.match(pattern, key.strip()))


def sanitize_groq_key(input_str: str):
    """Attempt to extract one or more Groq API keys from user input.

    Returns (key, warnings) where key is the first matched key (or None) and
    warnings is a list of strings describing issues (e.g., multiple keys found).
    """
    if not input_str or not isinstance(input_str, str):
        return None, ["No key provided"]
    # Find all matches
    matches = re.findall(r'(gsk_[A-Za-z0-9\-_]{16,128})', input_str)
    warnings = []
    if len(matches) == 0:
        # Maybe the user included spaces or extra text; attempt to strip common prefixes/suffixes
        candidate = input_str.strip()
        if validate_groq_key(candidate):
            return candidate, warnings
        return None, ["No Groq-style key found in input"]
    if len(matches) > 1:
        warnings.append(f"Found multiple keys; using the first one. ({len(matches)} keys detected)")
    return matches[0], warnings
