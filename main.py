
import os
import json
import threading
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from scanner import scan_directory, human_readable_size
from classifier import classify_all
from renamer import assign_new_names
from organizer import organize_files
from reporter import build_report, save_json_report, save_html_report


LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "organizer.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("smart_organizer")

BG       = "#0a0a0f"
SURFACE  = "#111118"
CARD     = "#16161f"
BORDER   = "#2a2a3d"
ACCENT   = "#00e5ff"
ACCENT2  = "#7c4dff"
TEXT     = "#e0e0f0"
MUTED    = "#6b6b8a"
SUCCESS  = "#00e676"
DANGER   = "#ff5252"
WARNING  = "#ff9100"

class SmartOrganizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart File Organizer")
        self.geometry("860x680")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(700, 560)

        self.source_path = tk.StringVar()
        self.output_path = tk.StringVar(
            value=os.path.join(os.path.dirname(__file__), "organized")
        )
        self.dry_run = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready.")
        self.files_data = []
        self.results_data = []

        self._build_ui()
#ui
    def _build_ui(self):
        self._build_header()
        self._build_path_section()
        self._build_options()
        self._build_log_area()
        self._build_progress()
        self._build_buttons()
        self._build_statusbar()

    def _build_header(self):
        hf = tk.Frame(self, bg=BG)
        hf.pack(fill="x", padx=24, pady=(20, 4))

        badge = tk.Label(
            hf, text="  AI SYSTEM  ", bg=CARD, fg=ACCENT,
            font=("Courier New", 8, "bold"), padx=6, pady=3,
            relief="flat", bd=0
        )
        badge.pack(side="left")

        title = tk.Label(
            hf, text="Smart File Organizer",
            bg=BG, fg=TEXT, font=("Helvetica", 20, "bold")
        )
        title.pack(side="left", padx=12)

        sub = tk.Label(
            hf, text="Project",
            bg=BG, fg=MUTED, font=("Courier New", 9)
        )
        sub.pack(side="right")

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", padx=24, pady=(8, 16))

    def _build_path_section(self):
        f = self._card(self)
        f.pack(fill="x", padx=24, pady=(0, 12))

        self._label(f, "SOURCE FOLDER").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
        src_row = tk.Frame(f, bg=CARD)
        src_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        src_row.columnconfigure(0, weight=1)

        self._entry(src_row, self.source_path).grid(row=0, column=0, sticky="ew")
        self._btn(src_row, "Browse", self._browse_source, ACCENT2, small=True).grid(
            row=0, column=1, padx=(8, 0)
        )

        self._label(f, "OUTPUT FOLDER").grid(row=2, column=0, sticky="w", padx=12, pady=(0, 4))
        out_row = tk.Frame(f, bg=CARD)
        out_row.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        out_row.columnconfigure(0, weight=1)

        self._entry(out_row, self.output_path).grid(row=0, column=0, sticky="ew")
        self._btn(out_row, "Browse", self._browse_output, ACCENT2, small=True).grid(
            row=0, column=1, padx=(8, 0)
        )

        f.columnconfigure(0, weight=1)

    def _build_options(self):
        f = tk.Frame(self, bg=BG)
        f.pack(fill="x", padx=24, pady=(0, 8))

        dry_cb = tk.Checkbutton(
            f, text="Dry Run (preview only — don't move files)",
            variable=self.dry_run,
            bg=BG, fg=MUTED, selectcolor=CARD,
            activebackground=BG, activeforeground=TEXT,
            font=("Helvetica", 10),
        )
        dry_cb.pack(side="left")

    def _build_log_area(self):
        lf = self._card(self)
        lf.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        self._label(lf, "ACTIVITY LOG").pack(anchor="w", padx=12, pady=(10, 4))

        txt_frame = tk.Frame(lf, bg=CARD)
        txt_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        scrollbar = tk.Scrollbar(txt_frame)
        scrollbar.pack(side="right", fill="y")

        self.log_box = tk.Text(
            txt_frame, bg="#0d0d14", fg=TEXT, insertbackground=ACCENT,
            font=("Courier New", 9), relief="flat", bd=0,
            yscrollcommand=scrollbar.set, state="disabled",
            wrap="word", height=10,
        )
        self.log_box.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_box.yview)

        # Tag colours
        self.log_box.tag_config("info",    foreground=TEXT)
        self.log_box.tag_config("success", foreground=SUCCESS)
        self.log_box.tag_config("error",   foreground=DANGER)
        self.log_box.tag_config("warn",    foreground=WARNING)
        self.log_box.tag_config("accent",  foreground=ACCENT)

    def _build_progress(self):
        pf = tk.Frame(self, bg=BG)
        pf.pack(fill="x", padx=24, pady=(0, 8))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "custom.Horizontal.TProgressbar",
            troughcolor=CARD, background=ACCENT,
            bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT2,
            thickness=8,
        )

        self.progress = ttk.Progressbar(
            pf, style="custom.Horizontal.TProgressbar",
            orient="horizontal", length=400, mode="determinate"
        )
        self.progress.pack(fill="x")

    def _build_buttons(self):
        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=24, pady=(4, 12))

        self.scan_btn = self._btn(bf, "  Scan Only", self._scan_only, ACCENT2)
        self.scan_btn.pack(side="left")

        self.org_btn = self._btn(bf, "  Scan & Organize", self._run_organize, ACCENT)
        self.org_btn.pack(side="left", padx=(12, 0))

        self.report_btn = self._btn(bf, "📊  Open Report", self._open_report, "#444", small=True)
        self.report_btn.pack(side="right")
        self.report_btn.config(state="disabled")

        self._btn(bf, "🗑  Clear Log", self._clear_log, "#333", small=True).pack(
            side="right", padx=(0, 8)
        )

    def _build_statusbar(self):
        sb = tk.Frame(self, bg=SURFACE, height=26)
        sb.pack(fill="x", side="bottom")
        tk.Label(
            sb, textvariable=self.status_var,
            bg=SURFACE, fg=MUTED, font=("Courier New", 8), anchor="w"
        ).pack(fill="x", padx=12, pady=4)

    # ── Widget helpers ────────────────────────────────
    def _card(self, parent):
        return tk.Frame(parent, bg=CARD, relief="flat", bd=0)

    def _label(self, parent, text):
        return tk.Label(
            parent, text=text, bg=CARD, fg=MUTED,
            font=("Courier New", 8, "bold")
        )

    def _entry(self, parent, var):
        return tk.Entry(
            parent, textvariable=var,
            bg="#0d0d14", fg=TEXT, insertbackground=ACCENT,
            font=("Courier New", 10), relief="flat", bd=0,
        )

    def _btn(self, parent, text, cmd, color, small=False):
        size = 9 if small else 11
        pad_x = 10 if small else 18
        pad_y = 4 if small else 8
        return tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg=BG if color not in ("#333", "#444") else TEXT,
            activebackground=ACCENT, activeforeground=BG,
            font=("Helvetica", size, "bold"), relief="flat",
            bd=0, cursor="hand2", padx=pad_x, pady=pad_y,
        )

    # ── Logging to UI ─────────────────────────────────
    def _log(self, msg: str, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.config(state="normal")
        self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    # ── File Dialogs ──────────────────────────────────
    def _browse_source(self):
        path = filedialog.askdirectory(title="Select Source Folder")
        if path:
            self.source_path.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_path.set(path)

    # ── Core Actions ──────────────────────────────────
    def _validate_paths(self) -> bool:
        if not self.source_path.get():
            messagebox.showwarning("Missing Path", "Please select a source folder.")
            return False
        if not os.path.isdir(self.source_path.get()):
            messagebox.showerror("Invalid Path", "Source folder does not exist.")
            return False
        return True

    def _set_buttons(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.scan_btn.config(state=state)
        self.org_btn.config(state=state)

    def _scan_only(self):
        if not self._validate_paths():
            return
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _run_organize(self):
        if not self._validate_paths():
            return
        threading.Thread(target=self._do_organize, daemon=True).start()

    def _do_scan(self):
        self._set_buttons(False)
        self.progress["value"] = 0
        self.status_var.set("Scanning…")
        src = self.source_path.get()

        try:
            self._log(f"Scanning: {src}", "accent")
            files = scan_directory(src)
            classify_all(files)
            assign_new_names(files)
            self.files_data = files

            self.progress["value"] = 100
            self._log(f"Found {len(files)} files.", "success")

            # Category summary
            from collections import Counter
            cats = Counter(f["category"] for f in files)
            for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
                self._log(f"  {cat}: {count} files")

            self.status_var.set(f"Scan complete — {len(files)} files found.")

        except Exception as e:
            self._log(f"Error: {e}", "error")
            self.status_var.set("Error during scan.")
        finally:
            self._set_buttons(True)

    def _do_organize(self):
        self._set_buttons(False)
        self.progress["value"] = 0
        src = self.source_path.get()
        out = self.output_path.get()
        dry = self.dry_run.get()

        try:
            # Step 1: Scan
            self._log(f"{'[DRY RUN] ' if dry else ''}Scanning: {src}", "accent")
            self.status_var.set("Scanning…")
            files = scan_directory(src)
            classify_all(files)
            assign_new_names(files)
            self.files_data = files
            self._log(f"Found {len(files)} files across {len(set(f['category'] for f in files))} categories.", "success")
            self.progress["value"] = 33

            # Step 2: Organize
            self.status_var.set("Organizing…")
            self._log("Moving files…", "accent")
            results = organize_files(files, out, dry_run=dry)
            self.results_data = results

            ok = sum(1 for r in results if r["status"] in ("success", "dry_run"))
            err = sum(1 for r in results if str(r["status"]).startswith("error"))
            self._log(f"  ✓ {ok} files {'previewed' if dry else 'moved'}  ✗ {err} errors",
                      "success" if err == 0 else "warn")
            self.progress["value"] = 66

            # Step 3: Report
            self.status_var.set("Generating report…")
            report = build_report(files, results, out)
            os.makedirs(out, exist_ok=True)
            json_path = save_json_report(report, out)
            html_path = save_html_report(report, out)
            self._log(f"Report saved → {html_path}", "success")
            self.progress["value"] = 100

            self.report_btn.config(state="normal", command=lambda p=html_path: self._open_html(p))
            self.status_var.set(
                f"Done! {ok} files {'previewed' if dry else 'organized'}. Report ready."
            )
            if not dry:
                messagebox.showinfo("Complete", f"Organized {ok} files!\nReport: {html_path}")

        except Exception as e:
            self._log(f"Error: {e}", "error")
            self.status_var.set("Error during organization.")
            logger.exception("Organize error")
        finally:
            self._set_buttons(True)

    def _open_report(self):
        pass  # Replaced dynamically after run

    def _open_html(self, path: str):
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(path)}")


if __name__ == "__main__":
    app = SmartOrganizerApp()
    app.mainloop()