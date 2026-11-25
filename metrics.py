import pandas as pd


def _normalize_label(val) -> str | None:
    """Maps common dataset labels (text, 1-5 stars, or Sentiment140 0/2/4) to Pos/Neu/Neg."""
    s = str(val).strip().lower()
    if s in {"positive", "pos", "4", "5"}:
        return "Positive"
    if s in {"neutral", "neu", "2", "3"}:
        return "Neutral"
    if s in {"negative", "neg", "0", "1"}:
        return "Negative"
    return None


def compute_validation(
    df: pd.DataFrame, label_col: str = None
) -> tuple[float | None, pd.DataFrame | None]:
    """
    Compares VADER 'sentiment' against a ground-truth label column (if present).
    Returns: (accuracy_percentage, confusion_matrix_df) or (None, None)
    """
    if label_col is None:
        possible = ["label", "actual", "actual_sentiment", "rating", "stars", "target", "polarity"]
        for col in df.columns:
            if col.strip().lower() in possible and col != "sentiment":
                label_col = col
                break

    if label_col is None or label_col not in df.columns:
        return None, None

    actual = df[label_col].apply(_normalize_label)
    valid_mask = actual.notna()
    if valid_mask.sum() == 0:
        return None, None

    y_true = actual[valid_mask]
    y_pred = df.loc[valid_mask, "sentiment"]

    accuracy = round((y_true == y_pred).mean() * 100, 2)

    classes = ["Positive", "Neutral", "Negative"]
    cm = pd.crosstab(
        pd.Categorical(y_true, categories=classes),
        pd.Categorical(y_pred, categories=classes),
        dropna=False,
    )
    cm.index = [f"Actual {c[:3]}" for c in classes]
    cm.columns = [f"Pred {c[:3]}" for c in classes]

    return accuracy, cm


def compute_monthly_drift(df: pd.DataFrame, date_col: str = None) -> pd.Series:
    """
    Groups reviews by month and computes the average VADER compound score.
    Returns a pandas Series indexed by 'YYYY-MM' (empty if no date column found).
    """
    if date_col is None:
        possible = ["date", "timestamp", "created_at", "review_date", "time", "month"]
        for col in df.columns:
            if col.strip().lower() in possible:
                date_col = col
                break

    if date_col is None or date_col not in df.columns:
        return pd.Series(dtype=float)

    temp = df[[date_col, "compound_score"]].copy()
    temp["parsed_date"] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=["parsed_date"])

    if temp.empty:
        return pd.Series(dtype=float)

    temp["year_month"] = temp["parsed_date"].dt.to_period("M").astype(str)
    monthly_avg = temp.groupby("year_month")["compound_score"].mean().round(3)
    return monthly_avg
