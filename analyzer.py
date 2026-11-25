import re
from collections import Counter
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Common English stopwords to ignore when extracting complaint keywords
STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "have", "from", "they", "will",
    "would", "there", "their", "what", "about", "which", "when", "make", "like",
    "time", "just", "know", "take", "into", "year", "your", "good", "some",
    "could", "them", "other", "than", "then", "look", "only", "come", "over",
    "think", "also", "back", "after", "work", "first", "well", "even", "want",
    "because", "these", "give", "most", "very", "been", "were", "was", "are",
    "not", "but", "all", "can", "had", "her", "one", "our", "out", "you", "his",
    "has", "its", "get", "app", "really", "still", "every", "much", "more",
    "email", "redacted", "url", "phone", "dont", "cant", "wont", "doesnt"
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
    df: pd.DataFrame, top_n: int = 5, max_examples: int = 3
) -> tuple[list[tuple[str, int]], dict[str, list[str]]]:
    """
    Finds the top frequent keywords in Negative reviews and maps each
    keyword to real redacted example reviews.
    Returns: ([(keyword, count), ...], {keyword: [example_reviews]})
    """
    neg_reviews = df[df["sentiment"] == "Negative"]["redacted_text"].tolist()
    word_counts = Counter()

    for review in neg_reviews:
        words = re.findall(r"\b[a-z]{3,}\b", review.lower())
        filtered = [w for w in words if w not in STOPWORDS]
        word_counts.update(filtered)

    top_keywords = word_counts.most_common(top_n)

    examples = {}
    for keyword, _ in top_keywords:
        pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
        matched = [rev for rev in neg_reviews if pattern.search(rev)]
        examples[keyword] = matched[:max_examples]

    return top_keywords, examples
