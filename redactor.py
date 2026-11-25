import re
import pandas as pd

# Compiled regex patterns for PII detection
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
URL_PATTERN = re.compile(r'(https?://\S+|www\.\S+)', re.IGNORECASE)
PHONE_PATTERN = re.compile(r'(\+?\d{1,3}[\s.-]?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|\b\d{10}\b)')


def redact_text(text: str) -> tuple[str, int]:
    """
    Masks emails, URLs, and phone numbers in a single review string.
    Returns: (redacted_text, count_of_redactions)
    """
    if not isinstance(text, str):
        return "", 0

    redaction_count = 0

    text, email_hits = EMAIL_PATTERN.subn("[EMAIL REDACTED]", text)
    redaction_count += email_hits

    text, url_hits = URL_PATTERN.subn("[URL REDACTED]", text)
    redaction_count += url_hits

    text, phone_hits = PHONE_PATTERN.subn("[PHONE REDACTED]", text)
    redaction_count += phone_hits

    return text, redaction_count


def load_and_redact_csv(filepath: str, text_col: str = None) -> tuple[pd.DataFrame, int]:
    """
    Loads a CSV file, detects the review text column if not specified,
    removes empty reviews, and applies PII redaction to every review.
    Returns: (cleaned_dataframe, total_pii_redacted)
    """
    df = pd.read_csv(filepath, encoding="utf-8", on_bad_lines="skip")

    # Auto-detect common review text column names if not explicitly passed
    if text_col is None:
        possible_cols = ["review", "review_text", "text", "comment", "content", "feedback"]
        for col in df.columns:
            if col.strip().lower() in possible_cols:
                text_col = col
                break
        if text_col is None:
            raise ValueError(
                f"Could not find a review text column. Available columns: {list(df.columns)}"
            )

    # Drop rows with missing review text
    df = df.dropna(subset=[text_col]).copy()
    df[text_col] = df[text_col].astype(str).str.strip()
    df = df[df[text_col] != ""].reset_index(drop=True)

    # Apply PII redaction
    results = df[text_col].apply(redact_text)
    df["redacted_text"] = results.apply(lambda x: x[0])
    df["pii_count"] = results.apply(lambda x: x[1])

    total_pii_redacted = int(df["pii_count"].sum())
    return df, total_pii_redacted


# Independent test block for Member 1
if __name__ == "__main__":
    sample_reviews = [
        "App crashes every time! Mail me at user123@example.com for logs.",
        "Support link https://help.example.com is useless. Call 9876543210.",
        "Great app, works smoothly without any issues!"
    ]
    for rev in sample_reviews:
        clean, count = redact_text(rev)
        print(f"Redactions: {count} | {clean}")
