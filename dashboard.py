import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from redactor import load_and_redact_csv
from analyzer import analyze_sentiment, extract_negative_themes
from metrics import compute_validation, compute_monthly_drift
from visualizer import create_sentiment_figure, create_drift_figure, export_to_csv


class ReviewAnalyzerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Feedback & Review Analyzer")
        self.root.geometry("1000x680")
        self.root.configure(bg="#F5F7FA")

        self.df = None
        self.theme_examples = {}

        self._build_ui()

    def _build_ui(self):
        # Top Action Bar
        top_frame = tk.Frame(self.root, bg="#1F2937", pady=10, padx=15)
        top_frame.pack(fill="x")

        tk.Label(
            top_frame,
            text="Feedback & Review Analyzer",
            fg="white",
            bg="#1F2937",
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        self.export_btn = tk.Button(
            top_frame,
            text="Export Analyzed CSV",
            command=self.handle_export,
            state="disabled",
            bg="#10B981",
            fg="white",
            padx=12,
            pady=4,
        )
        self.export_btn.pack(side="right", padx=5)

        tk.Button(
            top_frame,
            text="Load CSV File",
            command=self.handle_load_csv,
            bg="#3B82F6",
            fg="white",
            padx=12,
            pady=4,
        ).pack(side="right", padx=5)

        # KPI Summary Cards
        kpi_frame = tk.Frame(self.root, bg="#F5F7FA", pady=10, padx=15)
        kpi_frame.pack(fill="x")

        self.kpi_vars = {}
        kpi_items = [
            ("Total Reviews", "Total"),
            ("Positive", "Positive"),
            ("Neutral", "Neutral"),
            ("Negative", "Negative"),
            ("PII Redacted", "PII"),
        ]
        for label_text, key in kpi_items:
            card = tk.Frame(kpi_frame, bg="white", bd=1, relief="solid", padx=12, pady=8)
            card.pack(side="left", expand=True, fill="x", padx=5)
            tk.Label(card, text=label_text, bg="white", fg="#6B7280", font=("Segoe UI", 9)).pack()
            var = tk.StringVar(value="-")
            self.kpi_vars[key] = var
            tk.Label(card, textvariable=var, bg="white", fg="#111827", font=("Segoe UI", 14, "bold")).pack()

        # Tabbed Workspace
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=15, pady=(0, 15))

        # Tab 1: Sentiment Overview
        self.tab_overview = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.tab_overview, text="Sentiment Overview")

        # Tab 2: Negative Themes & Evidence
        self.tab_themes = tk.Frame(self.notebook, bg="white", padx=10, pady=10)
        self.notebook.add(self.tab_themes, text="Negative Themes & Evidence")

        self.tree = ttk.Treeview(
            self.tab_themes, columns=("Keyword", "Mentions"), show="headings", height=10
        )
        self.tree.heading("Keyword", text="Top Negative Keyword")
        self.tree.heading("Mentions", text="Mentions")
        self.tree.pack(side="left", fill="y", padx=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.show_theme_examples)

        right_theme = tk.Frame(self.tab_themes, bg="white")
        right_theme.pack(side="left", expand=True, fill="both")
        tk.Label(
            right_theme,
            text="Real Redacted Example Reviews (click a keyword on the left):",
            bg="white",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        self.examples_box = tk.Text(right_theme, wrap="word", font=("Segoe UI", 10), bg="#F9FAFB")
        self.examples_box.pack(expand=True, fill="both", pady=5)

        # Tab 3: Validation & Drift
        self.tab_metrics = tk.Frame(self.notebook, bg="white", padx=10, pady=10)
        self.notebook.add(self.tab_metrics, text="Validation & Drift")

        self.drift_frame = tk.Frame(self.tab_metrics, bg="white")
        self.drift_frame.pack(side="left", expand=True, fill="both")

        self.val_frame = tk.Frame(self.tab_metrics, bg="#F9FAFB", bd=1, relief="solid", padx=12, pady=12)
        self.val_frame.pack(side="right", fill="y", padx=(10, 0))
        self.val_text = tk.StringVar(value="Validation results will appear here\nif your CSV has a label/rating column.")
        tk.Label(
            self.val_frame,
            textvariable=self.val_text,
            justify="left",
            bg="#F9FAFB",
            font=("Consolas", 10),
        ).pack(anchor="nw")

    def _embed_figure(self, parent_frame, fig):
        for widget in parent_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both")

    def handle_load_csv(self):
        filepath = filedialog.askopenfilename(
            title="Select Reviews CSV", filetypes=[("CSV Files", "*.csv")]
        )
        if not filepath:
            return

        try:
            # 1. Member 1: Load & Redact PII
            df, pii_count = load_and_redact_csv(filepath)

            # 2. Member 2: VADER Sentiment & Negative Themes
            df, summary = analyze_sentiment(df)
            top_keywords, self.theme_examples = extract_negative_themes(df)

            # 3. Member 3: Validation & Monthly Drift
            accuracy, cm = compute_validation(df)
            monthly_drift = compute_monthly_drift(df)

            self.df = df
            self.export_btn.config(state="normal")

            # Update KPIs
            self.kpi_vars["Total"].set(f"{summary['Total']:,}")
            self.kpi_vars["Positive"].set(f"{summary['Positive']:,}")
            self.kpi_vars["Neutral"].set(f"{summary['Neutral']:,}")
            self.kpi_vars["Negative"].set(f"{summary['Negative']:,}")
            self.kpi_vars["PII"].set(f"{pii_count:,}")

            # 4. Member 4: Embed Charts
            self._embed_figure(self.tab_overview, create_sentiment_figure(summary))
            self._embed_figure(self.drift_frame, create_drift_figure(monthly_drift))

            # Populate Themes Table
            for row in self.tree.get_children():
                self.tree.delete(row)
            for kw, cnt in top_keywords:
                self.tree.insert("", "end", values=(kw, cnt))
            self.examples_box.delete("1.0", tk.END)

            # Populate Validation Box
            if accuracy is not None:
                self.val_text.set(f"Validation Accuracy: {accuracy}%\n\nConfusion Matrix:\n{cm.to_string()}")
            else:
                self.val_text.set("No label/rating column detected\nin this CSV for validation.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process CSV:\n{e}")

    def show_theme_examples(self, _event):
        selected = self.tree.selection()
        if not selected:
            return
        keyword = self.tree.item(selected[0])["values"][0]
        examples = self.theme_examples.get(keyword, [])

        self.examples_box.delete("1.0", tk.END)
        for idx, rev in enumerate(examples, 1):
            self.examples_box.insert(tk.END, f"{idx}. {rev}\n\n")

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
