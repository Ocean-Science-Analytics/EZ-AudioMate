import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
from PIL import Image
import threading, math
from audio_functions import *
from help_texts import *

# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT   = "#2196F3"
ACCENT2  = "#1565C0"
BG_DARK  = "#0F1923"
BG_CARD  = "#162130"
BG_INPUT = "#1E2D3D"
TEXT_PRI = "#E8F0FE"
TEXT_MUT = "#7B9BB8"
SUCCESS  = "#00C896"
BORDER   = "#243447"
TAB_ACT  = "#2196F3"   # active tab bg
TAB_INACT= "#1A2A3A"   # inactive tab bg
TAB_H    = 40          # tab button height px

# ── Root ──────────────────────────────────────────────────────────────────────
root = ctk.CTk()
root.title("EZ AudioMate")
root.geometry("860x660")
root.resizable(False, False)
root.configure(fg_color=BG_DARK)

# ── Header ────────────────────────────────────────────────────────────────────
header = ctk.CTkFrame(root, fg_color=BG_CARD, corner_radius=0, height=70,
                      border_width=1, border_color=BORDER)
header.pack(fill="x", side="top")
header.pack_propagate(False)

try:
    _logo_pil = Image.open("white_square_OSA_med.jpg").resize((46, 46), Image.LANCZOS)
    _logo_ctk = ctk.CTkImage(light_image=_logo_pil, dark_image=_logo_pil, size=(46, 46))
    logo_lbl  = ctk.CTkLabel(header, image=_logo_ctk, text="")
except Exception:
    logo_lbl  = ctk.CTkLabel(header, text="OSA", font=ctk.CTkFont(size=13, weight="bold"),
                              text_color=ACCENT, fg_color=BG_INPUT,
                              corner_radius=6, width=46, height=46)
logo_lbl.place(x=14, y=12)

ctk.CTkLabel(header, text="EZ AudioMate",
             font=ctk.CTkFont(family="Helvetica Neue", size=22, weight="bold"),
             text_color=TEXT_PRI).place(x=70, y=14)
ctk.CTkLabel(header, text="Audio Processing Suite",
             font=ctk.CTkFont(size=11),
             text_color=TEXT_MUT).place(x=71, y=43)

# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOM TAB BAR
#  CTkTabview's segmented-button tabs are hard to style boldly, so we build
#  our own tab strip + stacked content frames.
# ══════════════════════════════════════════════════════════════════════════════
TAB_NAMES = ["Resampling", "FLAC Conversion", "WAV Conversion", "Audio Info"]

tab_strip = ctk.CTkFrame(root, fg_color=BG_CARD, corner_radius=0,
                          height=TAB_H, border_width=1, border_color=BORDER)
tab_strip.pack(fill="x", padx=0, pady=0)
tab_strip.pack_propagate(False)

content_area = ctk.CTkFrame(root, fg_color=BG_DARK, corner_radius=0)
content_area.pack(fill="both", expand=True, padx=0, pady=0)

# One content frame per tab, stacked — only one visible at a time
tab_frames = {}
for name in TAB_NAMES:
    f = ctk.CTkFrame(content_area, fg_color=BG_DARK, corner_radius=0)
    f.place(relx=0, rely=0, relwidth=1, relheight=1)
    tab_frames[name] = f

active_tab = ctk.StringVar(value=TAB_NAMES[0])
tab_buttons = {}

def switch_tab(name):
    active_tab.set(name)
    for n, f in tab_frames.items():
        f.lift() if n == name else f.lower()
    for n, b in tab_buttons.items():
        if n == name:
            b.configure(fg_color=TAB_ACT, text_color="white",
                        font=ctk.CTkFont(size=13, weight="bold"))
        else:
            b.configure(fg_color=TAB_INACT, text_color=TEXT_MUT,
                        font=ctk.CTkFont(size=13))

N = len(TAB_NAMES)
for i, name in enumerate(TAB_NAMES):
    btn = ctk.CTkButton(
        tab_strip,
        text=name,
        height=TAB_H,
        corner_radius=0,
        fg_color=TAB_INACT,
        hover_color=ACCENT2,
        text_color=TEXT_MUT,
        font=ctk.CTkFont(size=13),
        border_width=0,
        command=lambda n=name: switch_tab(n)
    )
    btn.place(relx=i/N, rely=0, relwidth=1/N, relheight=1)
    tab_buttons[name] = btn

switch_tab(TAB_NAMES[0])

# ── Helpers ───────────────────────────────────────────────────────────────────
def card(parent, **kwargs):
    defaults = dict(fg_color=BG_CARD, corner_radius=12,
                    border_width=1, border_color=BORDER)
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)

def section_label(parent, text):
    return ctk.CTkLabel(parent, text=text,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_MUT)

def folder_row(parent, var, label_text, row):
    section_label(parent, label_text).grid(row=row, column=0, columnspan=3,
                                            sticky="w", padx=20, pady=(14, 2))
    entry = ctk.CTkEntry(parent, textvariable=var, height=36,
                          fg_color=BG_INPUT, border_color=BORDER,
                          text_color=TEXT_PRI, corner_radius=8)
    entry.grid(row=row+1, column=0, columnspan=2, sticky="ew", padx=(20, 6), pady=2)
    btn = ctk.CTkButton(parent, text="Browse", width=90, height=36,
                         fg_color=BG_INPUT, hover_color=BORDER,
                         text_color=ACCENT, border_color=ACCENT,
                         border_width=1, corner_radius=8,
                         command=lambda: var.set(filedialog.askdirectory()))
    btn.grid(row=row+1, column=2, padx=(0, 20), pady=2)
    return entry

def action_btn(parent, text, cmd):
    return ctk.CTkButton(parent, text=text, command=cmd,
                          height=42, corner_radius=10,
                          fg_color=ACCENT, hover_color=ACCENT2,
                          text_color="white",
                          font=ctk.CTkFont(size=14, weight="bold"))

def help_btn(parent, cmd):
    b = ctk.CTkButton(parent, text="?", width=32, height=32,
                       corner_radius=16, fg_color=BG_INPUT,
                       hover_color=BORDER, text_color=TEXT_MUT,
                       border_color=BORDER, border_width=1, command=cmd)
    b.place(relx=1.0, rely=0.0, anchor="ne", x=-12, y=8)

def ctk_progress_shim(pbar_ctk):
    class Shim:
        def __init__(self, p): self._p = p; self._max = 1
        def __setitem__(self, k, v):
            if k == 'maximum': self._max = max(v, 1)
            elif k == 'value': self._p.set(v / self._max)
        def __getitem__(self, k):
            return self._max if k == 'maximum' else 0
    return Shim(pbar_ctk)

def status_shim(lbl_ctk):
    class Shim:
        def __init__(self, l): self._l = l
        def config(self, **kw):
            if 'text' in kw: self._l.configure(text=kw['text'])
    return Shim(lbl_ctk)

# ── Spinner ───────────────────────────────────────────────────────────────────
class Spinner:
    """Rotating arc spinner drawn on a bare tkinter Canvas."""
    SIZE  = 32
    ARC   = 260   # degrees of visible arc
    SPEED = 8     # degrees per frame
    DELAY = 20    # ms per frame
    WIDTH = 4     # stroke width

    def __init__(self, parent, color=ACCENT):
        self._color  = color
        self._angle  = 0
        self._active = False
        self._canvas = Canvas(parent, width=self.SIZE, height=self.SIZE,
                              bg=BG_CARD, highlightthickness=0)

    def grid(self, **kwargs):
        self._canvas.grid(**kwargs)

    def start(self):
        if self._active:
            return
        self._active = True
        self._animate()

    def stop(self):
        self._active = False
        self._canvas.delete("all")

    def _animate(self):
        if not self._active:
            return
        self._canvas.delete("all")
        pad = self.WIDTH // 2 + 1
        # faint background ring
        self._canvas.create_oval(pad, pad, self.SIZE - pad, self.SIZE - pad,
                                  outline=BG_INPUT, width=self.WIDTH)
        # spinning arc
        self._canvas.create_arc(pad, pad, self.SIZE - pad, self.SIZE - pad,
                                  start=self._angle, extent=self.ARC,
                                  outline=self._color, width=self.WIDTH,
                                  style="arc")
        self._angle = (self._angle + self.SPEED) % 360
        self._canvas.after(self.DELAY, self._animate)


def make_progress_section(parent, color, grid_row):
    """
    Uses an inner frame so the progress bar and spinner are naturally
    adjacent with no column-weight gaps.
    Returns (progress_shim, status_shim, spinner).
    """
    row_frame = ctk.CTkFrame(parent, fg_color="transparent")
    row_frame.grid(row=grid_row, column=0, columnspan=3, sticky="ew",
                   padx=20, pady=(18, 2))
    row_frame.columnconfigure(0, weight=1)   # bar expands
    row_frame.columnconfigure(1, weight=0)   # spinner fixed width

    pbar = ctk.CTkProgressBar(row_frame, height=6, corner_radius=3,
                               fg_color=BG_INPUT, progress_color=color)
    pbar.set(0)
    pbar.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    spinner = Spinner(row_frame, color=color)
    spinner.grid(row=0, column=1, sticky="e")

    status_lbl = ctk.CTkLabel(parent, text="Ready", text_color=TEXT_MUT,
                               font=ctk.CTkFont(size=11))
    status_lbl.grid(row=grid_row + 1, column=0, columnspan=3,
                    sticky="w", padx=20, pady=(0, 6))

    return ctk_progress_shim(pbar), status_shim(status_lbl), spinner


def threaded_run(target_fn, args, spinner):
    """
    Run target_fn(*args) in ONE background thread.
    Spinner starts before the thread and stops only after it fully finishes.
    target_fn must be a plain blocking function (no internal threading).
    """
    spinner.start()
    def _wrap():
        try:
            target_fn(*args)
        finally:
            root.after(0, spinner.stop)   # stop on main thread — tkinter-safe
    threading.Thread(target=_wrap, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — RESAMPLING
# ══════════════════════════════════════════════════════════════════════════════
t1 = tab_frames["Resampling"]
t1.columnconfigure(0, weight=1)
t1.rowconfigure(0, weight=1)

input_folder_var  = ctk.StringVar()
output_folder_var = ctk.StringVar()
include_sr_var    = ctk.IntVar()

c1 = card(t1)
c1.grid(row=0, column=0, sticky="nsew", padx=20, pady=16)
c1.columnconfigure((0, 1), weight=1)
c1.columnconfigure(2, weight=0)

help_btn(c1, show_help)
folder_row(c1, input_folder_var,  "INPUT FOLDER",  0)
folder_row(c1, output_folder_var, "OUTPUT FOLDER", 2)

section_label(c1, "TARGET SAMPLE RATE (Hz)").grid(
    row=4, column=0, sticky="w", padx=20, pady=(14, 2))
sr_entry = ctk.CTkEntry(c1, height=36, width=180,
                         fg_color=BG_INPUT, border_color=BORDER,
                         text_color=TEXT_PRI, corner_radius=8,
                         placeholder_text="e.g. 44100")
sr_entry.grid(row=5, column=0, sticky="w", padx=20, pady=2)

sr_check = ctk.CTkCheckBox(c1, text="Append sample rate to filename",
                             variable=include_sr_var,
                             fg_color=ACCENT, hover_color=ACCENT2,
                             text_color=TEXT_PRI, font=ctk.CTkFont(size=12))
sr_check.grid(row=5, column=1, columnspan=2, sticky="w", padx=10, pady=2)

progress1, label_status1, spinner1 = make_progress_section(c1, ACCENT, 6)

def _run_resample():
    # Call process_files directly so threaded_run owns the full lifecycle
    input_folder = input_folder_var.get()
    output_folder = output_folder_var.get()
    try:
        desired_sr = int(sr_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid sample rate.")
        return
    include_sr = include_sr_var.get()
    process_files(input_folder, output_folder, desired_sr, include_sr,
                  progress1, label_status1, root)

action_btn(c1, "Resample Files",
           lambda: threaded_run(_run_resample, (), spinner1)
           ).grid(row=8, column=0, columnspan=3, pady=(6, 18), padx=20, sticky="ew")

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — FLAC CONVERSION
# ══════════════════════════════════════════════════════════════════════════════
t2 = tab_frames["FLAC Conversion"]
t2.columnconfigure(0, weight=1)
t2.rowconfigure(0, weight=1)

input_folder_var2  = ctk.StringVar()
output_folder_var2 = ctk.StringVar()

c2 = card(t2)
c2.grid(row=0, column=0, sticky="nsew", padx=20, pady=16)
c2.columnconfigure((0, 1), weight=1)
c2.columnconfigure(2, weight=0)

help_btn(c2, show_help2)
folder_row(c2, input_folder_var2,  "INPUT FOLDER  (.wav / .aif)", 0)
folder_row(c2, output_folder_var2, "OUTPUT FOLDER",               2)

progress2, label_status2, spinner2 = make_progress_section(c2, SUCCESS, 4)

action_btn(c2, "Convert to FLAC",
           lambda: threaded_run(compress_to_flac,
                                (input_folder_var2.get(), output_folder_var2.get(),
                                 progress2, label_status2, root),
                                spinner2)
           ).grid(row=6, column=0, columnspan=3, pady=(6, 18), padx=20, sticky="ew")

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — WAV CONVERSION
# ══════════════════════════════════════════════════════════════════════════════
t3 = tab_frames["WAV Conversion"]
t3.columnconfigure(0, weight=1)
t3.rowconfigure(0, weight=1)

input_folder_var3  = ctk.StringVar()
output_folder_var3 = ctk.StringVar()

c3 = card(t3)
c3.grid(row=0, column=0, sticky="nsew", padx=20, pady=16)
c3.columnconfigure((0, 1), weight=1)
c3.columnconfigure(2, weight=0)

help_btn(c3, show_help3)
folder_row(c3, input_folder_var3,  "INPUT FOLDER  (.flac)", 0)
folder_row(c3, output_folder_var3, "OUTPUT FOLDER",         2)

progress3, label_status3, spinner3 = make_progress_section(c3, SUCCESS, 4)

action_btn(c3, "Convert to WAV",
           lambda: threaded_run(convert_to_wav,
                                (input_folder_var3.get(), output_folder_var3.get(),
                                 progress3, label_status3, root),
                                spinner3)
           ).grid(row=6, column=0, columnspan=3, pady=(6, 18), padx=20, sticky="ew")

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — AUDIO INFO
# ══════════════════════════════════════════════════════════════════════════════
t4 = tab_frames["Audio Info"]
t4.columnconfigure(0, weight=1)
t4.rowconfigure(0, weight=1)

c4 = card(t4)
c4.grid(row=0, column=0, sticky="nsew", padx=20, pady=16)
c4.columnconfigure(0, weight=1)
c4.columnconfigure(1, weight=0)
c4.rowconfigure(1, weight=1)

action_btn(c4, "Select Folder & Analyze",
           lambda: select_folder_tab4(output_text)
           ).grid(row=0, column=0, padx=(20, 6), pady=(18, 10), sticky="ew")

ctk.CTkButton(c4, text="?", width=42, height=42,
              corner_radius=10, fg_color=BG_INPUT,
              hover_color=BORDER, text_color=TEXT_MUT,
              border_color=BORDER, border_width=1,
              command=show_help4
              ).grid(row=0, column=1, padx=(0, 20), pady=(18, 10))

output_text = ctk.CTkTextbox(c4, wrap="word",
                              fg_color=BG_INPUT, text_color=TEXT_PRI,
                              font=ctk.CTkFont(family="Courier New", size=12),
                              corner_radius=8, border_color=BORDER, border_width=1)
output_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 18))

# ── Launch ────────────────────────────────────────────────────────────────────
root.mainloop()
