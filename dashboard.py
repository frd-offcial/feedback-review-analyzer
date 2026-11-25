import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from redactor import load_and_redact_csv, redact_text
from analyzer import analyze_sentiment, extract_negative_themes, COMPLAINT_THEMES
from metrics import compute_validation, compute_monthly_drift
from visualizer import create_sentiment_figure, create_drift_figure, export_to_csv

# Modern Dark Palette ("Midnight Slate")
BG_DARK = "#0F172A"
BG_SIDEBAR = "#111827"
BG_CARD = "#1E293B"
BG_INPUT = "#0B1220"
BORDER = "#334155"
TEXT_MAIN = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
ACCENT_BLUE = "#3B82F6"
ACCENT_INDIGO = "#6366F1"
ACCENT_GREEN = "#10B981"
ACCENT_AMBER = "#F59E0B"
ACCENT_ROSE = "#F43F5E"
ACCENT_PURPLE = "#A855F7"


class ReviewAnalyzerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Feedback & Review Analyzer — Analytics Dashboard")
        self.root.geometry("1180x720")
        self.root.minsize(1020, 640)
        self.root.configure(bg=BG_DARK)

        self.df = None
        self.theme_examples = {}
        self.nav_buttons = {}
        self.pages = {}
        self.sia = SentimentIntensityAnalyzer()

        self._configure_styles()
        self._build_layout()
        self.show_page("overview")

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Dark.Treeview",
            background=BG_CARD,
            foreground=TEXT_MAIN,
            fieldbackground=BG_CARD,
            rowheight=32,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Dark.Treeview.Heading",
            background="#0F172A",
            foreground=TEXT_MUTED,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padding=(8, 6),
        )
        style.map(
            "Dark.Treeview",
            background=[("selected", ACCENT_INDIGO)],
            foreground=[("selected", TEXT_MAIN)],
        )

    def _build_layout(self):
        # 1. Left Sidebar
        sidebar = tk.Frame(self.root, bg=BG_SIDEBAR, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Brand Header
        brand_frame = tk.Frame(sidebar, bg=BG_SIDEBAR, pady=22, padx=18)
        brand_frame.pack(fill="x")
        tk.Label(
            brand_frame, text="ReviewPulse", fg=TEXT_MAIN, bg=BG_SIDEBAR,
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w")
        tk.Label(
            brand_frame, text="NLP Feedback Analyzer", fg=TEXT_MUTED, bg=BG_SIDEBAR,
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(2, 0))

        # Divider
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 14))

        # Navigation Menu
        nav_items = [
            ("overview", "  Sentiment Overview"),
            ("themes", "  Complaint Themes"),
            ("metrics", "  Validation & Drift"),
            ("tester", "  Live Review Tester"),
        ]
        for key, label in nav_items:
            btn = tk.Button(
                sidebar,
                text=label,
                anchor="w",
                command=lambda k=key: self.show_page(k),
                bg=BG_SIDEBAR,
                fg=TEXT_MUTED,
                activebackground=BG_CARD,
                activeforeground=TEXT_MAIN,
                bd=0,
                padx=18,
                pady=11,
                font=("Segoe UI", 10, "bold"),
                cursor="hand2",
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[key] = btn

        # Bottom Action Controls in Sidebar
        bottom_box = tk.Frame(sidebar, bg=BG_SIDEBAR, padx=14, pady=18)
        bottom_box.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value="No dataset loaded")
        tk.Label(
            bottom_box,
            textvariable=self.status_var,
            bg=BG_SIDEBAR,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
            wraplength=195,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        tk.Button(
            bottom_box,
            text="Load CSV Dataset",
            command=self.handle_load_csv,
            bg=ACCENT_BLUE,
            fg="white",
            activebackground="#2563EB",
            activeforeground="white",
            bd=0,
            pady=9,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        ).pack(fill="x", pady=(0, 8))

        self.export_btn = tk.Button(
            bottom_box,
            text="Export Analyzed CSV",
            command=self.handle_export,
            state="disabled",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            activebackground="#059669",
            activeforeground="white",
            bd=0,
            pady=8,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        self.export_btn.pack(fill="x")

        # 2. Main Content Area
        main_area = tk.Frame(self.root, bg=BG_DARK, padx=22, pady=18)
        main_area.pack(side="left", expand=True, fill="both")

        # Top KPI Strip
        self._build_kpi_cards(main_area)

        # Page Container
        self.page_container = tk.Frame(main_area, bg=BG_DARK)
        self.page_container.pack(expand=True, fill="both", pady=(16, 0))

        self._build_overview_page()
        self._build_themes_page()
        self._build_metrics_page()
        self._build_tester_page()

    def _build_kpi_cards(self, parent):
        kpi_row = tk.Frame(parent, bg=BG_DARK)
        kpi_row.pack(fill="x")

        self.kpi_vars = {}
        self.kpi_sub_vars = {}
        cards = [
            ("TOTAL REVIEWS", "Total", ACCENT_INDIGO),
            ("POSITIVE", "Positive", ACCENT_GREEN),
            ("NEUTRAL", "Neutral", ACCENT_AMBER),
            ("NEGATIVE", "Negative", ACCENT_ROSE),
            ("PII REDACTED", "PII", ACCENT_PURPLE),
        ]

        for idx, (title, key, color) in enumerate(cards):
            card = tk.Frame(kpi_row, bg=BG_CARD)
            card.pack(side="left", expand=True, fill="x", padx=(0 if idx == 0 else 8, 0))

            # Colored Top Accent Bar
            tk.Frame(card, bg=color, height=3).pack(fill="x")

            body = tk.Frame(card, bg=BG_CARD, padx=14, pady=10)
            body.pack(fill="both")

            tk.Label(
                body, text=title, bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8, "bold")
            ).pack(anchor="w")

            val_var = tk.StringVar(value="—")
            self.kpi_vars[key] = val_var
            tk.Label(
                body, textvariable=val_var, bg=BG_CARD, fg=TEXT_MAIN, font=("Segoe UI", 17, "bold")
            ).pack(anchor="w", pady=(2, 0))

            sub_var = tk.StringVar(value="Waiting for CSV")
            self.kpi_sub_vars[key] = sub_var
            tk.Label(
                body, textvariable=sub_var, bg=BG_CARD, fg=color, font=("Segoe UI", 8)
            ).pack(anchor="w")

    def _build_overview_page(self):
        page = tk.Frame(self.page_container, bg=BG_CARD, padx=12, pady=12)
        self.pages["overview"] = page
        self.overview_chart_holder = tk.Frame(page, bg=BG_CARD)
        self.overview_chart_holder.pack(expand=True, fill="both")

        tk.Label(
            self.overview_chart_holder,
            text="Click 'Load CSV Dataset' on the left to generate sentiment charts.",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=("Segoe UI", 11),
        ).pack(expand=True)

    def _build_themes_page(self):
        page = tk.Frame(self.page_container, bg=BG_DARK)
        self.pages["themes"] = page

        # Left Card: Ranked Themes Table
        left_card = tk.Frame(page, bg=BG_CARD, padx=14, pady=14)
        left_card.pack(side="left", fill="y", padx=(0, 12))

        tk.Label(
            left_card, text="Top Complaint Categories", bg=BG_CARD, fg=TEXT_MAIN,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))

        self.tree = ttk.Treeview(
            left_card,
            columns=("Theme", "Mentions"),
            show="headings",
            style="Dark.Treeview",
            height=13,
        )
        self.tree.heading("Theme", text="Complaint Theme")
        self.tree.heading("Mentions", text="Mentions")
        self.tree.column("Theme", width=190, anchor="w")
        self.tree.column("Mentions", width=85, anchor="center")
        self.tree.pack(expand=True, fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.show_theme_examples)

        # Right Card: Traceable Redacted Examples
        right_card = tk.Frame(page, bg=BG_CARD, padx=16, pady=14)
        right_card.pack(side="left", expand=True, fill="both")

        self.theme_header_var = tk.StringVar(
            value="Real Redacted Evidence — Select a complaint theme on the left"
        )
        tk.Label(
            right_card, textvariable=self.theme_header_var, bg=BG_CARD, fg=TEXT_MAIN,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.examples_box = tk.Text(
            right_card,
            wrap="word",
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            bd=0,
            padx=14,
            pady=12,
            font=("Segoe UI", 10),
            spacing3=8,
        )
        self.examples_box.pack(expand=True, fill="both")
        self.examples_box.tag_configure("badge", foreground="#38BDF8", font=("Segoe UI", 10, "bold"))
        self.examples_box.tag_configure("redacted", foreground=ACCENT_ROSE, font=("Segoe UI", 10, "bold"))

    def _build_metrics_page(self):
        page = tk.Frame(self.page_container, bg=BG_DARK)
        self.pages["metrics"] = page

        # Left Card: Drift Chart
        drift_card = tk.Frame(page, bg=BG_CARD, padx=12, pady=12)
        drift_card.pack(side="left", expand=True, fill="both", padx=(0, 12))
        self.drift_frame = tk.Frame(drift_card, bg=BG_CARD)
        self.drift_frame.pack(expand=True, fill="both")
        tk.Label(
            self.drift_frame, text="Load a CSV with dates to view Monthly Drift.",
            bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 10)
        ).pack(expand=True)

        # Right Card: Visual Accuracy & Confusion Matrix
        val_card = tk.Frame(page, bg=BG_CARD, padx=16, pady=16, width=320)
        val_card.pack(side="right", fill="y")
        val_card.pack_propagate(False)

        tk.Label(
            val_card, text="Model Validation", bg=BG_CARD, fg=TEXT_MAIN,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        self.acc_var = tk.StringVar(value="—")
        tk.Label(
            val_card, textvariable=self.acc_var, bg=BG_CARD, fg=ACCENT_GREEN,
            font=("Segoe UI", 26, "bold")
        ).pack(anchor="w", pady=(8, 2))

        self.acc_sub_var = tk.StringVar(value="Load a labelled CSV to compute accuracy")
        tk.Label(
            val_card, textvariable=self.acc_sub_var, bg=BG_CARD, fg=TEXT_MUTED,
            font=("Segoe UI", 9), wraplength=280, justify="left"
        ).pack(anchor="w", pady=(0, 14))

        self.cm_container = tk.Frame(val_card, bg=BG_CARD)
        self.cm_container.pack(fill="x", pady=(4, 0))

    def _build_tester_page(self):
        """Unique Interactive Viva Feature: Test any review live."""
        page = tk.Frame(self.page_container, bg=BG_CARD, padx=20, pady=18)
        self.pages["tester"] = page

        tk.Label(
            page, text="Live Review Tester (Interactive Demo)", bg=BG_CARD, fg=TEXT_MAIN,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")
        tk.Label(
            page,
            text="Type any sample review (try including an email, phone number, or URL) to test PII Redaction, VADER Sentiment, and Theme Detection live.",
            bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(2, 12))

        self.live_input = tk.Text(
            page, height=5, wrap="word", bg=BG_INPUT, fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN, bd=0, padx=12, pady=10, font=("Segoe UI", 10)
        )
        self.live_input.pack(fill="x")
        self.live_input.insert(
            "1.0",
            "App keeps crashing after the latest update! Email me at student@bennett.edu.in or call 9876543210."
        )

        tk.Button(
            page,
            text="Analyze Review Live",
            command=self.run_live_test,
            bg=ACCENT_INDIGO,
            fg="white",
            activebackground="#4F46E5",
            activeforeground="white",
            bd=0,
            padx=18,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        ).pack(anchor="w", pady=12)

        self.live_output = tk.Text(
            page, height=9, wrap="word", bg=BG_INPUT, fg=TEXT_MAIN,
            bd=0, padx=14, pady=12, font=("Consolas", 10), state="disabled"
        )
        self.live_output.pack(expand=True, fill="both")

    def show_page(self, page_key: str):
        for key, frame in self.pages.items():
            frame.pack_forget()
        self.pages[page_key].pack(expand=True, fill="both")

        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.config(bg=BG_CARD, fg=TEXT_MAIN)
            else:
                btn.config(bg=BG_SIDEBAR, fg=TEXT_MUTED)

    def _embed_figure(self, parent_frame, fig):
        for widget in parent_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")

    def _render_confusion_matrix(self, cm):
        for widget in self.cm_container.winfo_children():
            widget.destroy()

        tk.Label(
            self.cm_container, text="Confusion Matrix (Rows = Actual)",
            bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        headers = [""] + list(cm.columns)
        for c, text in enumerate(headers):
            tk.Label(
                self.cm_container, text=text, bg=BG_DARK, fg=TEXT_MUTED,
                font=("Segoe UI", 8, "bold"), width=9, pady=6
            ).grid(row=1, column=c, padx=1, pady=1)

        for r, row_label in enumerate(cm.index):
            tk.Label(
                self.cm_container, text=row_label, bg=BG_DARK, fg=TEXT_MUTED,
                font=("Segoe UI", 8, "bold"), width=9, pady=7
            ).grid(row=r + 2, column=0, padx=1, pady=1)

            for c, val in enumerate(cm.iloc[r]):
                cell_bg = "#064E3B" if r == c else "#1E293B"
                cell_fg = "#6EE7B7" if r == c else TEXT_MAIN
                tk.Label(
                    self.cm_container, text=f"{int(val):,}", bg=cell_bg, fg=cell_fg,
                    font=("Segoe UI", 9, "bold"), width=9, pady=7
                ).grid(row=r + 2, column=c + 1, padx=1, pady=1)

    def handle_load_csv(self):
        filepath = filedialog.askopenfilename(
            title="Select Reviews CSV", filetypes=[("CSV Files", "*.csv")]
        )
        if not filepath:
            return

        try:
            self.status_var.set("Processing dataset...")
            self.root.update_idletasks()

            df, pii_count = load_and_redact_csv(filepath)
            df, summary = analyze_sentiment(df)
            top_themes, self.theme_examples = extract_negative_themes(df)
            accuracy, cm = compute_validation(df)
            monthly_drift = compute_monthly_drift(df)

            self.df = df
            self.status_var.set(f"Loaded: {os.path.basename(filepath)}")
            self.export_btn.config(state="normal", bg=ACCENT_GREEN, fg="white")

            total = max(summary["Total"], 1)
            self.kpi_vars["Total"].set(f"{summary['Total']:,}")
            self.kpi_sub_vars["Total"].set("100% processed")

            self.kpi_vars["Positive"].set(f"{summary['Positive']:,}")
            self.kpi_sub_vars["Positive"].set(f"{summary['Positive'] / total * 100:.1f}% of total")

            self.kpi_vars["Neutral"].set(f"{summary['Neutral']:,}")
            self.kpi_sub_vars["Neutral"].set(f"{summary['Neutral'] / total * 100:.1f}% of total")

            self.kpi_vars["Negative"].set(f"{summary['Negative']:,}")
            self.kpi_sub_vars["Negative"].set(f"{summary['Negative'] / total * 100:.1f}% of total")

            self.kpi_vars["PII"].set(f"{pii_count:,}")
            self.kpi_sub_vars["PII"].set("Emails / Phones / URLs")

            # Charts
            self._embed_figure(self.overview_chart_holder, create_sentiment_figure(summary))
            self._embed_figure(self.drift_frame, create_drift_figure(monthly_drift))

            # Themes Table
            for row in self.tree.get_children():
                self.tree.delete(row)
            for theme, cnt in top_themes:
                self.tree.insert("", "end", values=(theme, f"{cnt:,}"))
            self.examples_box.delete("1.0", tk.END)
            if self.tree.get_children():
                first_id = self.tree.get_children()[0]
                self.tree.selection_set(first_id)
                self.show_theme_examples(None)

            # Validation
            if accuracy is not None:
                self.acc_var.set(f"{accuracy}%")
                self.acc_sub_var.set("VADER agreement with dataset ratings/labels")
                self._render_confusion_matrix(cm)
            else:
                self.acc_var.set("N/A")
                self.acc_sub_var.set("No label/rating column detected in this CSV.")
                for w in self.cm_container.winfo_children():
                    w.destroy()

        except Exception as e:
            self.status_var.set("Error loading file")
            messagebox.showerror("Error", f"Failed to process CSV:\n{e}")

    def show_theme_examples(self, _event):
        selected = self.tree.selection()
        if not selected:
            return
        theme = self.tree.item(selected[0])["values"][0]
        examples = self.theme_examples.get(theme, [])

        self.theme_header_var.set(f"Real Redacted Evidence for '{theme}'")
        self.examples_box.delete("1.0", tk.END)

        for idx, rev in enumerate(examples, 1):
            self.examples_box.insert(tk.END, f"Example #{idx}\n", "badge")
            # Highlight [REDACTED] tags if present
            parts = re.split(r"(\[(?:EMAIL|URL|PHONE) REDACTED\])", rev)
            for part in parts:
                tag = "redacted" if part.endswith("REDACTED]") else None
                self.examples_box.insert(tk.END, part, tag)
            self.examples_box.insert(tk.END, "\n\n" + "─" * 58 + "\n\n")

    def run_live_test(self):
        raw_text = self.live_input.get("1.0", tk.END).strip()
        if not raw_text:
            return

        redacted, pii_hits = redact_text(raw_text)
        score = self.sia.polarity_scores(redacted)["compound"]
        sentiment = "Positive" if score >= 0.05 else ("Negative" if score <= -0.05 else "Neutral")

        matched_themes = []
        for theme, words in COMPLAINT_THEMES.items():
            pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.IGNORECASE)
            if pattern.search(redacted):
                matched_themes.append(theme)

        output = (
            f"Redacted Text : {redacted}\n"
            f"PII Masked    : {pii_hits}\n"
            f"VADER Score   : {score:+.3f}\n"
            f"Sentiment     : {sentiment}\n"
            f"Themes Found  : {', '.join(matched_themes) if matched_themes else 'None'}"
        )

        self.live_output.config(state="normal")
        self.live_output.delete("1.0", tk.END)
        self.live_output.insert("1.0", output)
        self.live_output.config(state="disabled")

    def handle_export(self):
        if self.df is None:
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
        )
        if filepath:
            export_to_csv(self.df, filepath)
            messagebox.showinfo("Export Complete", f"Saved analyzed reviews to:\n{filepath}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewAnalyzerApp(root)
    root.mainloop()
