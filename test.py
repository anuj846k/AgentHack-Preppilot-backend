import re

def derive_name_from_email(email):
    if not email or "@" not in email:
        return email
    
    prefix = email.split("@")[0]
    parts = re.split(r'[0-9_]+', prefix)
    parts = [p for p in parts if p]

    if len(parts) == 1:
        word = parts[0]
        # try to split before last 5-7 characters (often surname length)
        split_at = len(word) - 6
        if split_at > 2:  
            parts = [word[:split_at], word[split_at:]]
    
    return " ".join(p.capitalize() for p in parts)



print(derive_name_from_email('kshitijakarsh@gmail.com'))