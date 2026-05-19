import re

def tokenize_and_squeeze(raw_text: str) -> str:
    """The TokenJuice equivalent. Strips out formatting, HTML, and bloat."""
    if not raw_text:
        return ""
    
    # 1. Strip HTML tags
    clean = re.sub(r'<[^>]+>', ' ', raw_text)
    # 2. Remove URLs (replace with [LINK])
    clean = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[LINK]', clean)
    # 3. Strip excessive whitespace and newlines
    clean = re.sub(r'\s+', ' ', clean)
    # 4. Remove non-ASCII noise
    clean = clean.encode('ascii', 'ignore').decode()
    
    return clean.strip()