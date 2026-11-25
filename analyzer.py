import re
from collections import Counter
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


COMPLAINT_THEMES = {
    "Updates & Changes": ["update", "updated", "version", "downgrade", "ruined", "changed"],
    "Bugs & Errors": ["bug", "bugs", "error", "glitch", "broken", "issue", "issues", "fix"],
    "Sync & Calendar": ["sync", "syncing", "calendar", "google", "backup", "cloud"],
    "Pricing & Paywall": ["pay", "paid", "subscription", "price", "premium", "money", "charge", "charged", "free"],
    "Crash & Freeze": ["crash", "crashes", "crashing", "freeze", "freezes", "freezing", "stuck", "hang"],
    "Notifications & Alerts": ["notification", "notifications", "reminder", "reminders", "alarm", "alert", "spam"],
    "Login & Account": ["login", "sign", "signin", "account", "password", "register", "access"],
    "Slow & Performance": ["slow", "lag", "laggy", "loading", "battery", "drain", "heavy"],
    "Data Loss & Delete": ["lost", "delete", "deleted", "disappeared", "missing", "gone", "wipe"],
    "Ads & Popups": ["ad", "ads", "advert", "popup", "popups", "annoying"],
}


def analyze_sentiment(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Runs VADER sentiment analysis on 'redacted_text'.
    Adds 'compound_score' and 'sentiment' columns to the DataFrame.
    Returns: (updated_df, sentiment_counts_dict)
    """
    sia = SentimentIntensityAnalyzer()
    df = df.copy()

    def classify(text: str) -> tuple[float, str]:
        score = sia.polarity_scores(str(text))["compound"]
        if score >= 0.05:
            return score, "Positive"
        elif score <= -0.05:
            return score, "Negative"
        else:
            return score, "Neutral"

    results = df["redacted_text"].apply(classify)
    df["compound_score"] = results.apply(lambda x: x[0])
    df["sentiment"] = results.apply(lambda x: x[1])

    counts = df["sentiment"].value_counts().to_dict()
    summary = {
        "Total": len(df),
        "Positive": counts.get("Positive", 0),
        "Neutral": counts.get("Neutral", 0),
        "Negative": counts.get("Negative", 0),
    }
    return df, summary


def extract_negative_themes(
    df: pd.DataFrame, top_n: int = 8, max_examples: int = 3
) -> tuple[list[tuple[str, int]], dict[str, list[str]]]:
    """
    Groups Negative reviews into actionable complaint themes and maps each
    theme to real redacted example reviews.
    Returns: ([(theme_name, count), ...], {theme_name: [example_reviews]})
    """
    neg_reviews = df[df["sentiment"] == "Negative"]["redacted_text"].tolist()

    # Pre-compile one regex pattern per theme for fast matching
    compiled_patterns = {
        theme: re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.IGNORECASE)
        for theme, words in COMPLAINT_THEMES.items()
    }

    theme_counts = Counter()
    examples = {theme: [] for theme in COMPLAINT_THEMES}

    for review in neg_reviews:
        for theme, pattern in compiled_patterns.items():
            if pattern.search(review):
                theme_counts[theme] += 1
                if len(examples[theme]) < max_examples:
                    examples[theme].append(review)

    top_themes = theme_counts.most_common(top_n)
    return top_themes, examples
