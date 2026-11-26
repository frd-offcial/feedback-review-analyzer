# ReviewPulse — Feedback & Review Analyzer

**Course:** Computational Thinking and Programming (`2026CSAE100`) — B.Tech CSE (Semester 1)  
**Institution:** Bennett University, Greater Noida  

**ReviewPulse** is a modular desktop NLP and Data Analytics application built in Python that processes 10,000+ unstructured app-store and product reviews into actionable insights—featuring automated PII redaction, domain-tuned VADER sentiment classification, complaint theme extraction with real user evidence, ground-truth accuracy validation, and monthly sentiment drift monitoring.

---

## Key Features

- **Automated PII Redaction (`redactor.py`):** Scans incoming CSV reviews using regular expressions (`re`) to detect and mask email addresses, phone numbers, and URLs (`[EMAIL REDACTED]`, `[PHONE REDACTED]`, `[URL REDACTED]`) before analysis.
- **Domain-Tuned Sentiment Analysis (`analyzer.py`):** Classifies every review into **Positive**, **Neutral**, or **Negative** using VADER polarity compound scores enhanced with app-specific terminology (`crash`, `freeze`, `glitch`, `laggy`, `paywall`, `uninstalled`).
- **Complaint Theme & Evidence Extraction (`analyzer.py`):** Categorizes negative reviews into ranked friction drivers (e.g., *Bugs & Errors*, *Updates & Changes*, *Sync & Calendar*, *Pricing & Paywall*, *Crash & Freeze*) and links each category to verified, redacted customer reviews.
- **Model Validation & Drift Tracking (`metrics.py`):** Computes classification accuracy and a 3×3 confusion matrix against ground-truth star ratings/labels, and tracks monthly average sentiment trajectories over time.
- **Interactive Analytics Dashboard (`dashboard.py` & `visualizer.py`):** Modern dark-mode Tkinter interface featuring an automated Health Score (`0–100`), KPI progress cards, Matplotlib Bar/Donut/Drift charts, a searchable **Review Explorer**, and one-click **Export Analyzed CSV**.

---

## System Pipeline

```text
[Raw Reviews CSV]
       │
       ▼
  redactor.py     ──► Cleans empty rows & masks PII (Emails, Phones, URLs)
       │
       ▼
  analyzer.py     ──► Computes VADER compound scores & ranks negative complaint themes
       │
       ▼
   metrics.py     ──► Calculates validation accuracy, confusion matrix & monthly drift
       │
       ▼
 visualizer.py    ──► Generates Matplotlib charts & exports analyzed CSV
       │
       ▼
  dashboard.py    ──► Interactive Tkinter GUI (Overview, Themes, Validation, Explorer)
