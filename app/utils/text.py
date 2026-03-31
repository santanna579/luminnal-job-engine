def normalize_text(text: str) -> str:
    if not text:
        return ""

    return " ".join(text.strip().split()).lower()