import re
import tiktoken

def clean_promt(text: str)-> str:
    cleaned_text=text.strip()
    compressed_text=re.sub(r'\n{3,}','\n\n',cleaned_text)
    return compressed_text

def estimate_token_count(text: str)->int:
    encoding=tiktoken.get_encoding("cl100k_base")
    tokens=encoding.encode(text)
    return len(tokens)

def process_prompt(text: str)->tuple[str, int]:
    cleaned=clean_promt(text)
    token_count=estimate_token_count(cleaned)
    return cleaned, token_count
