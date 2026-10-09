import re
import tiktoken


def clean_prompt(text: str) -> str:
    no_html = re.sub(r'<[^>]+>', '', text)
    
    no_unprintable = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', no_html)
    
    normalized_spaces = re.sub(r'[^\S\r\n]+', ' ', no_unprintable)
    
    cleaned_text = normalized_spaces.strip()
    
    compressed_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    return compressed_text


def estimate_token_count(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    return len(tokens)


def process_prompt(text: str) -> tuple[str, int]:
    cleaned = clean_prompt(text)
    token_count = estimate_token_count(cleaned)
    return cleaned, token_count