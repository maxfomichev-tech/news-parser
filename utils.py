
import re
import html
import html2text
from typing import List

html_converter = html2text.HTML2Text()
html_converter.ignore_links = False
html_converter.ignore_images = True
html_converter.body_width = 0

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    try:
        text = html_converter.handle(raw_html)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    except Exception:
        clean = re.sub(r'<[^>]+>', '', raw_html)
        return html.unescape(clean).strip()

def split_message(text: str, max_length: int = 4096) -> List[str]:
    if len(text) <= max_length:
        return [text]
    parts = []
    current = ""
    for paragraph in text.split('\n\n'):
        if len(current) + len(paragraph) + 2 > max_length:
            if current:
                parts.append(current.strip())
            current = paragraph
        else:
            current += "\n\n" + paragraph if current else paragraph
    if current:
        parts.append(current.strip())
    return parts

class RateLimiter:
    def __init__(self, cooldown):
        self.cooldown = cooldown
        self.last_request = {}

    def can_proceed(self, user_id: int) -> bool:
        from datetime import datetime
        now = datetime.now()
        if user_id not in self.last_request:
            self.last_request[user_id] = now
            return True
        elapsed = (now - self.last_request[user_id]).total_seconds()
        if elapsed >= self.cooldown:
            self.last_request[user_id] = now
            return True
        return False

    def get_remaining_time(self, user_id: int) -> int:
        from datetime import datetime
        if user_id not in self.last_request:
            return 0
        elapsed = (datetime.now() - self.last_request[user_id]).total_seconds()
        return max(0, int(self.cooldown - elapsed))
