import re

def is_valid_email_regex(email:str):
    """
    Validates an email address using a general-purpose regular expression.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
    
    if re.fullmatch(pattern, email):
        return True
    else:
        return False