VERSION = "1.12"

import sys
import subprocess
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

try:
    import torch, tqdm, safetensors, gguf, sentencepiece, yaml, numpy
except ImportError:
    print("Some required packages are missing. Installing from requirements.txt...")
    install("requirements.txt")
    import torch, tqdm, safetensors, gguf, sentencepiece, yaml, numpy

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import shutil
import winsound
import tkinter.scrolledtext as scrolledtext

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#f7fafc"
SURFACE   = "#ffffff"
SURFACE2  = "#f0f4f8"
BORDER    = "#e2e8f0"
ACCENT    = "#2563eb"
ACCENT2   = "#7c3aed"
SUCCESS   = "#059669"
WARNING   = "#b45309"
DANGER    = "#dc2626"
TEXT      = "#1d283b"
TEXT_MUTED= "#475569"
TEXT_DIM  = "#64748b"
WHITE     = "#ffffff"

FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_SUB    = ("Segoe UI", 10)
FONT_LABEL  = ("Segoe UI", 9, "bold")
FONT_BODY   = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 9)
FONT_BADGE  = ("Segoe UI", 8, "bold")

SUPPORTED_MODELS = [
    "Flux",
    "SD3",
    "Aurora",
    "HiDream",
    "Hyvid",
    "Wan",
    "LTXV",
    "SDXL",
    "SD1",
]

QUANTIZE_LEVELS = [
    "Q2_K", "Q2_K_S",
    "Q3_K", "Q3_K_L", "Q3_K_M", "Q3_K_S",
    "Q4_0", "Q4_1", "Q4_K", "Q4_K_M", "Q4_K_S",
    "Q5_0", "Q5_1", "Q5_K", "Q5_K_M", "Q5_K_S",
    "Q6_K", "Q8_0",
    "F16", "BF16", "F32",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def scroll_entry_to_end(entry):
    entry.xview_moveto(1)

# ── Styled widgets ────────────────────────────────────────────────────────────
def make_entry(parent, **kwargs):
    e = tk.Entry(
        parent,
        bg=SURFACE2, fg=TEXT,
        insertbackground=ACCENT,
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
        font=FONT_BODY,
        **kwargs,
    )
    return e

def make_button(parent, text, command, color=ACCENT, fg=TEXT, width=None, font=None, hover_bg=None):
    kw = dict(width=width) if width else {}

    # default hover selection: accent for primary buttons, subtle gray for surface buttons
    if hover_bg is None:
        hover_bg = BORDER if color == SURFACE2 else ACCENT2

    b = tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg=fg,
        disabledforeground=fg,
        activebackground=hover_bg,
        activeforeground=BG,
        relief="flat",
        cursor="hand2",
        font=font or FONT_LABEL,
        padx=12,
        pady=6,
        bd=0,
        **kw,
    )

    # closures capture current colors to avoid late-binding issues
    def _on_enter(event, bg=hover_bg):
        b.config(bg=bg)

    def _on_leave(event, bg=color):
        b.config(bg=bg)

    b.bind("<Enter>", _on_enter)
    b.bind("<Leave>", _on_leave)
    return b

def make_label(parent, text, font=None, fg=TEXT, **kwargs):
    return tk.Label(parent, text=text, bg=BG, fg=fg, font=font or FONT_BODY, **kwargs)

def divider(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=8, padx=0)

# ── Main App ──────────────────────────────────────────────────────────────────
class EasyQuantGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Easy Quantization GUI  v{VERSION}")
        self.root.geometry("900x680")
        self.root.minsize(760, 580)
        self.root.configure(bg=BG)
        self._set_icon()

        self.quantize_level_var = tk.StringVar(value="Q8_0")
        self._build_ui()
        self.root.mainloop()

    def _set_icon(self):
        try:
            self.root.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

    # ── UI Builder ────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header
        header = tk.Frame(self.root, bg=SURFACE, pady=14)
        header.pack(fill="x")

        tk.Label(
            header, text="Easy Quantization GUI",
            bg=SURFACE, fg=TEXT, font=FONT_TITLE,
        ).pack(side="left", padx=20)
        tk.Label(
            header, text=f"v{VERSION}",
            bg=SURFACE, fg=TEXT_MUTED, font=FONT_SUB,
        ).pack(side="left")

        # ── Body (two-column: left=form, right=models)
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=0, pady=0)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    def _build_left(self, parent):
        left = tk.Frame(parent, bg=BG, padx=20, pady=16)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)

        # ── Section: Files
        self._section_label(left, "Files")

        # Input
        self._field_row(
            left,
            label="Input file",
            hint=".safetensors · .gguf · .sft",
            entry_attr="input_entry",
            browse_cmd=self._browse_input,
            browse_attr="input_browse",
        )

        # Output
        self._field_row(
            left,
            label="Output file",
            hint=".gguf",
            entry_attr="output_entry",
            browse_cmd=self._browse_output,
            browse_attr="output_browse",
        )

        divider(left)

        # ── Section: Quantization
        self._section_label(left, "Quantization")

        q_frame = tk.Frame(left, bg=BG)
        q_frame.pack(fill="x", pady=(0, 12))

        make_label(q_frame, "Level:", font=FONT_LABEL, fg=TEXT_DIM).pack(side="left")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TCombobox",
            fieldbackground=SURFACE2, background=SURFACE2,
            foreground=TEXT, selectforeground=TEXT,
            selectbackground=ACCENT,
            bordercolor=BORDER, arrowcolor=ACCENT,
            relief="flat",
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", SURFACE2)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", SURFACE2)],
        )

        self.quantize_dropdown = ttk.Combobox(
            q_frame,
            textvariable=self.quantize_level_var,
            values=QUANTIZE_LEVELS,
            state="readonly",
            width=14,
            style="Dark.TCombobox",
            font=FONT_BODY,
        )
        self.quantize_dropdown.pack(side="left", padx=(8, 0))
        self.quantize_dropdown.bind("<<ComboboxSelected>>", lambda _: self._suggest_output())

        # Quant description badge
        self.quant_desc_var = tk.StringVar(value=self._quant_hint("Q8_0"))
        tk.Label(
            q_frame,
            textvariable=self.quant_desc_var,
            bg=SURFACE2, fg=ACCENT,
            font=FONT_BADGE,
            padx=8, pady=3, relief="flat",
        ).pack(side="left", padx=10)

        self.quantize_level_var.trace_add("write", lambda *_: self.quant_desc_var.set(self._quant_hint(self.quantize_level_var.get())))

        divider(left)

        # ── Run button
        run_row = tk.Frame(left, bg=BG)
        run_row.pack(fill="x", pady=(0, 4))

        self.run_button = make_button(
            run_row, "▶  Run Quantization",
            self._run,
            color=ACCENT, fg=BG,
            font=("Segoe UI", 10, "bold"),
        )
        self.run_button.pack(side="left")

        self.status_label = tk.Label(
            run_row, text="", bg=BG, fg=TEXT_MUTED, font=FONT_BODY,
        )
        self.status_label.pack(side="left", padx=14)

        divider(left)

        # ── Process log
        self._section_label(left, "Process log")

        log_frame = tk.Frame(left, bg=SURFACE2, relief="flat", highlightthickness=1, highlightbackground=BORDER)
        log_frame.pack(fill="both", expand=True, pady=(0, 8))

        self.process_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            bg=SURFACE2, fg=TEXT_DIM,
            insertbackground=ACCENT,
            font=FONT_MONO,
            relief="flat",
            borderwidth=0,
            padx=10, pady=8,
        )
        self.process_text.pack(fill="both", expand=True)
        self.process_text.tag_config("ok",   foreground=SUCCESS)
        self.process_text.tag_config("err",  foreground=DANGER)
        self.process_text.tag_config("info", foreground=ACCENT)
        self.process_text.tag_config("warn", foreground=WARNING)

        # Clear log button
        make_button(
            left, "Clear log",
            lambda: self.process_text.delete("1.0", tk.END),
            color=SURFACE2, fg=TEXT_DIM, font=FONT_BODY,
        ).pack(side="right", pady=(0, 2))

    def _build_right(self, parent):
        right = tk.Frame(parent, bg=SURFACE, padx=16, pady=16, width=200)
        right.grid(row=0, column=1, sticky="nsew")
        right.pack_propagate(False)

        self._section_label(right, "Supported models", bg=SURFACE)

        canvas = tk.Canvas(right, bg=SURFACE, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=SURFACE)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())

        inner.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_configure)

        for name in SUPPORTED_MODELS:
            row = tk.Frame(inner, bg=SURFACE2, relief="flat")
            row.pack(fill="x", pady=2)

            tk.Label(row, text="●", bg=SURFACE2, fg=ACCENT, font=("Segoe UI", 8)).pack(side="left", padx=(8, 4), pady=5)
            tk.Label(row, text=name, bg=SURFACE2, fg=TEXT, font=FONT_BODY, anchor="w").pack(side="left", pady=5)

        # bind mousewheel
        # Remove scrollbar: keep simple static layout without scroll controls

    # ── Field helper ──────────────────────────────────────────────────────────
    def _field_row(self, parent, label, hint, entry_attr, browse_cmd, browse_attr):
        tk.Label(parent, text=label, bg=BG, fg=TEXT_DIM, font=FONT_LABEL, anchor="w").pack(fill="x", pady=(6, 2))

        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0, 8))
        row.columnconfigure(0, weight=1)

        e = make_entry(row)
        e.grid(row=0, column=0, sticky="ew", ipady=6)
        e.bind("<FocusIn>",  lambda _: scroll_entry_to_end(e))
        e.bind("<FocusOut>", lambda _: scroll_entry_to_end(e))
        setattr(self, entry_attr, e)

        btn = make_button(row, "Browse", browse_cmd, color=SURFACE2, fg=TEXT_DIM, font=FONT_BODY)
        btn.grid(row=0, column=1, padx=(6, 0))
        setattr(self, browse_attr, btn)

        tk.Label(parent, text=hint, bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 8), anchor="w").pack(fill="x")

    def _section_label(self, parent, text, bg=BG):
        tk.Label(parent, text=text.upper(), bg=bg, fg=TEXT_MUTED, font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(0, 6))

    # ── Quantization hint ────────────────────────────────────────────────────
    def _quant_hint(self, level):
        hints = {
            "Q2_K": "Extreme compression — very small size, low accuracy",
            "Q2_K_S": "Ultra-compact — lowest precision, smallest footprint",

            "Q3_K": "Very small — strong compression, reduced fidelity",
            "Q3_K_L": "Low-precision 3-bit — smaller size, lower quality",
            "Q3_K_M": "Medium 3-bit — balanced size vs. quality",
            "Q3_K_S": "Small 3-bit — slightly better quality than lowest",

            "Q4_0": "4-bit baseline — compact with reasonable accuracy",
            "Q4_1": "4-bit variant — slightly different trade-offs",
            "Q4_K": "4-bit k-means — efficient with good accuracy",
            "Q4_K_M": "4-bit high-quality — improved fidelity",
            "Q4_K_S": "4-bit small — optimized for minimal size",

            "Q5_0": "5-bit baseline — better fidelity than 4-bit",
            "Q5_1": "5-bit variant — alternate trade-offs",
            "Q5_K": "5-bit k-means — higher precision for quality",
            "Q5_K_M": "5-bit medium — balanced precision and size",
            "Q5_K_S": "5-bit small — space-optimized 5-bit",

            "Q6_K": "6-bit k-means — near-lossless, high quality",
            "Q8_0": "8-bit — highest quantized precision, best quality",

            "F16": "Float16 — lower-precision float, good accuracy",
            "BF16": "BFloat16 — float variant with wide dynamic range",
            "F32": "Float32 — full precision, no quantization",
        }
        return hints.get(level, "")

    # ── Browse callbacks ──────────────────────────────────────────────────────
    def _browse_input(self):
        path = filedialog.askopenfilename(filetypes=[("Model files", "*.safetensors *.gguf *.sft")])
        if path:
            path = path.replace("\\", "/")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)
            scroll_entry_to_end(self.input_entry)
            self._suggest_output()

    def _browse_output(self):
        input_file = self.input_entry.get()
        level = self.quantize_level_var.get()
        if input_file:
            idir = os.path.dirname(input_file)
            iname = os.path.splitext(os.path.basename(input_file))[0]
            default = f"{iname}-{level}.gguf"
        else:
            idir, default = "/", f"output-{level}.gguf"

        path = filedialog.asksaveasfilename(
            initialdir=idir, initialfile=default,
            defaultextension=".gguf", filetypes=[("GGUF files", "*.gguf")],
        )
        if path:
            path = path.replace("\\", "/")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)
            scroll_entry_to_end(self.output_entry)

    def _suggest_output(self):
        inp = self.input_entry.get()
        level = self.quantize_level_var.get()
        if inp:
            idir = os.path.dirname(inp)
            iname = os.path.splitext(os.path.basename(inp))[0]
            out = f"{idir}/{iname}-{level}.gguf"
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, out)
            scroll_entry_to_end(self.output_entry)

    # ── UI state ──────────────────────────────────────────────────────────────
    def _disable_ui(self):
        for w in (self.input_entry, self.output_entry, self.input_browse,
                  self.output_browse, self.quantize_dropdown, self.run_button):
            w.config(state="disabled")
        self.status_label.config(text="⏳  Running…", fg=WARNING)

    def _enable_ui(self):
        self.input_entry.config(state="normal")
        self.output_entry.config(state="normal")
        self.input_browse.config(state="normal")
        self.output_browse.config(state="normal")
        self.quantize_dropdown.config(state="readonly")
        self.run_button.config(state="normal")
        self.status_label.config(text="")

    # ── Log helpers ───────────────────────────────────────────────────────────
    def _log(self, text, tag=None):
        self.process_text.insert(tk.END, text, tag or "")
        self.process_text.see(tk.END)
        self.root.update()

    # ── Run ───────────────────────────────────────────────────────────────────
    def _run(self):
        input_file  = self.input_entry.get().strip()
        output_file = self.output_entry.get().strip()
        level       = self.quantize_level_var.get()

        if not input_file or not output_file:
            messagebox.showerror("Missing files", "Please select both input and output files.")
            return

        if os.path.abspath(input_file) == os.path.abspath(output_file):
            messagebox.showerror("Same file", "Input and output files cannot be the same.")
            return

        output_dir = os.path.dirname(output_file)
        required   = 40_000_000_000
        available  = shutil.disk_usage(output_dir).free
        if available < required:
            messagebox.showerror(
                "Not enough space",
                f"Need {required/1e9:.1f} GB free, only {available/1e9:.1f} GB available.",
            )
            return

        self._disable_ui()
        self.process_text.delete("1.0", tk.END)
        self.root.update()

        is_gguf      = input_file.lower().endswith(".gguf")
        temp_gguf    = None

        # ── Step 1: Convert if needed
        if not is_gguf:
            self._log("── Step 1/2: Converting to GGUF…\n", "info")
            out_name  = os.path.splitext(os.path.basename(output_file))[0]
            temp_gguf = os.path.join(output_dir, f"{out_name}_temp_conversion.gguf")

            if os.path.exists(temp_gguf):
                try:
                    os.remove(temp_gguf)
                    self._log("Cleaned up existing temp file.\n")
                except Exception as e:
                    self._log(f"Error removing temp file: {e}\n", "err")
                    self._enable_ui()
                    return

            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE

                proc = subprocess.Popen(
                    [sys.executable, resource_path("convert.py"), "--src", input_file, "--dst", temp_gguf],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, universal_newlines=True, startupinfo=si,
                )
                for line in proc.stdout:
                    self._log(line)
                proc.wait()
                if proc.returncode != 0:
                    raise subprocess.CalledProcessError(proc.returncode, proc.args)
                self._log("Conversion complete.\n", "ok")
            except Exception as e:
                self._log(f"Conversion failed: {e}\n", "err")
                if temp_gguf and os.path.exists(temp_gguf):
                    os.remove(temp_gguf)
                self._enable_ui()
                return
        else:
            self._log("Input is GGUF — skipping conversion.\n", "info")

        # ── Step 2: Quantize
        quant_input = temp_gguf if temp_gguf else input_file
        step_label  = "2/2" if not is_gguf else "1/1"
        self._log(f"\n── Step {step_label}: Quantizing ({level})…\n", "info")

        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE

            proc = subprocess.Popen(
                [resource_path("llama-quantize.exe"), quant_input, output_file, level],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True, startupinfo=si,
            )
            for line in proc.stdout:
                self._log(line)
            proc.wait()
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, proc.args)
            self._log("\nQuantization complete!\n", "ok")
        except Exception as e:
            self._log(f"Quantization failed: {e}\n", "err")
        finally:
            if temp_gguf and os.path.exists(temp_gguf):
                try:
                    os.remove(temp_gguf)
                    self._log("Temp file cleaned up.\n")
                except Exception as e:
                    self._log(f"Could not remove temp file: {e}\n", "warn")

        self._log("\n── Done ──\n", "info")
        self.status_label.config(text="✔  Done", fg=SUCCESS)
        self._enable_ui()
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)


if __name__ == "__main__":
    EasyQuantGUI()