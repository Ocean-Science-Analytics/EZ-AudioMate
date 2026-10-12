import customtkinter as ctk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, Canvas
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import numpy as np
import os, sys, glob, threading, math, webbrowser
from audio_functions import *
from help_texts import *


def resource_path(*parts):
    """Path to a bundled file; works from source and from a PyInstaller build."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


# ══════════════════════════════════════════════════════════════════════════════
#  OCEAN SCIENCE ANALYTICS THEME  (matches SpectraReel)
# ══════════════════════════════════════════════════════════════════════════════
OSA_NAVY  = "#1E3F6E"
OSA_BLUE  = "#2D5DA8"
OSA_STEEL = "#3A74A6"
OSA_SEA   = "#3796CC"
OSA_SKY   = "#62ADD7"
OSA_FOAM  = "#99D0E5"

BG_PAGE   = "#F3F7FA"
BG_CARD   = "#FFFFFF"
BG_INPUT  = "#FFFFFF"
BG_SUBTLE = "#F5F9FC"   # read-only text areas
BG_HOVER  = "#EAF3FA"
TRACK     = "#E3ECF3"   # progress track
SPIN_RING = "#D7EAF5"

BORDER        = "#D6E2EC"
BORDER_STRONG = "#B9CCDC"

TEXT       = "#1B2B3A"
TEXT_LABEL = "#3E5468"
TEXT_MUT   = "#5F7385"
TEXT_CODE  = "#24384B"

BTN_HOVER = "#3A6DBF"   # slightly brighter OSA blue

# Status badge styles: (background, text, border)
BADGE = {
    "idle":    ("#EEF3F7", TEXT_MUT,  BORDER),
    "running": ("#E6F1FA", OSA_BLUE,  "#9CC4E4"),
    "done":    ("#E7F6EF", "#1F7A51", "#9ED6BC"),
    "error":   ("#FDECEC", "#B42318", "#F3B5B0"),
}

# Wave layers: (y, amplitude, colour, opacity, stroke width) in SpectraReel's
# SVG units (header 46 high, footer 28 high).
HEADER_WAVES = [(14, 10, OSA_FOAM, .55, 5), (24, 12, OSA_SKY, .45, 4),
                (34, 9, OSA_SEA, .50, 3.5), (42, 7, "#FFFFFF", .18, 2)]
FOOTER_WAVES = [(8, 6, OSA_FOAM, .9, 3), (15, 7, OSA_SKY, .8, 2.5),
                (21, 5, OSA_BLUE, .7, 2)]
ANIMATE_HEADER_WAVES = True

WIN_W, WIN_H = 880, 740
ORG_URL = "https://oceanscienceanalytics.com"

# Optional brand fonts: drop Inter / Questrial .ttf files into a "fonts" folder
# next to main.py and they'll be used (Windows and Linux).
for _font_file in glob.glob(resource_path("fonts", "*.ttf")) + glob.glob(resource_path("fonts", "*.otf")):
    try:
        ctk.FontManager.load_font(_font_file)
    except Exception:
        pass

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Root ──────────────────────────────────────────────────────────────────────
root = ctk.CTk()
root.title("EZ AudioMate | Ocean Science Analytics")
root.geometry(f"{WIN_W}x{WIN_H}")
root.resizable(False, False)
root.configure(fg_color=BG_PAGE)

try:
    root.iconbitmap(resource_path("OSA_icon.ico"))
except Exception:
    pass

try:
    SCALE = ctk.ScalingTracker.get_window_scaling(root)
except Exception:
    SCALE = 1.0

def px(v):
    """Logical size -> physical pixels (for raw tkinter canvases and images)."""
    return int(round(v * SCALE))

def _pick_font(candidates):
    available = {f.lower() for f in tkfont.families(root)}
    for name in candidates:
        if name.lower() in available:
            return name
    return candidates[-1]

HEAD_FAMILY = _pick_font(["Questrial", "Century Gothic", "Segoe UI", "Helvetica Neue", "Helvetica", "Arial"])
BODY_FAMILY = _pick_font(["Inter", "Segoe UI", "Helvetica Neue", "Helvetica", "Arial"])
MONO_FAMILY = "Courier New"

def F(size, weight="normal", head=False):
    return ctk.CTkFont(family=HEAD_FAMILY if head else BODY_FAMILY, size=size, weight=weight)


# ── Graphics helpers (header gradient, waves) ─────────────────────────────────
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def render_gradient(w, h, stops, angle_deg=120):
    """CSS-style linear-gradient(angle, ...) as a PIL image."""
    a = math.radians(angle_deg)
    dx, dy = math.sin(a), -math.cos(a)
    X, Y = np.meshgrid(np.arange(w), np.arange(h))
    proj = X * dx + Y * dy
    t = (proj - proj.min()) / max(proj.max() - proj.min(), 1)
    pos = [p for p, _ in stops]
    cols = [hex_rgb(c) for _, c in stops]
    out = np.stack([np.interp(t, pos, [c[i] for c in cols]) for i in range(3)], axis=-1)
    return Image.fromarray(out.astype(np.uint8), "RGB")

def render_waves(width, height, layers, period, ref_h, opacity=1.0, ss=2):
    """Smooth, periodic wave lines on a transparent image (supersampled for anti-aliasing)."""
    W, H = width * ss, height * ss
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    k = H / ref_h
    xs = np.arange(0, W + ss, ss, dtype=float)
    for y0, amp, color, alpha, sw in layers:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ys = y0 * k - amp * k * np.sin(2 * np.pi * xs / (period * ss))
        r, g, b = hex_rgb(color)
        ImageDraw.Draw(layer).line(list(zip(xs.tolist(), ys.tolist())),
                                   fill=(r, g, b, int(255 * alpha * opacity)),
                                   width=max(1, int(round(sw * SCALE * ss))), joint="curve")
        img = Image.alpha_composite(img, layer)
    return img.resize((width, height), Image.LANCZOS)

def render_band_frame(W, H, bx, by, bw, bh, radius):
    """
    Page-coloured overlay with a soft drop shadow and a transparent rounded
    window where the header band shows through. Drawn above the moving waves
    so they stay clipped to the band's rounded corners.
    """
    base = Image.new("RGBA", (W, H), hex_rgb(BG_PAGE) + (255,))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (bx + px(4), by + px(5), bx + bw - px(4), by + bh + px(3)), radius,
        fill=hex_rgb(OSA_NAVY) + (int(255 * .20),))
    shadow = shadow.filter(ImageFilter.GaussianBlur(px(8)))
    base = Image.alpha_composite(base, shadow)

    ss = 4
    window = Image.new("L", (W * ss, H * ss), 0)
    ImageDraw.Draw(window).rounded_rectangle(
        (bx * ss, by * ss, (bx + bw) * ss - 1, (by + bh) * ss - 1), radius * ss, fill=255)
    window = window.resize((W, H), Image.LANCZOS)
    base.putalpha(Image.eval(window, lambda v: 255 - v))
    return base

def load_logo(height):
    for name in ("osa_monogram_white.png", "white_square_OSA_med.png", "white_square_OSA_med.jpg"):
        path = resource_path(name)
        if not os.path.exists(path):
            continue
        try:
            im = Image.open(path)
            has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
            im = im.convert("RGBA")
            im = im.resize((max(1, round(im.width * height / im.height)), height), Image.LANCZOS)
            if not has_alpha:   # square photo logo: soften the corners
                mask = Image.new("L", im.size, 0)
                ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1),
                                                       px(7), fill=255)
                im.putalpha(mask)
            return im
        except Exception:
            continue
    return None


class OSAHeader:
    """Gradient header band with logo, divider, title and slowly drifting waves."""
    def __init__(self, parent, title, subtitle):
        W = px(WIN_W)
        bx, by = px(16), px(12)
        bw, bh = W - 2 * bx, px(84)
        H = by + bh + px(16)
        self.canvas = Canvas(parent, width=W, height=H, bg=BG_PAGE,
                             highlightthickness=0, bd=0)
        self.canvas.pack(fill="x", side="top")
        self._keep = []

        self._image(render_gradient(bw, bh, [(0, OSA_NAVY), (.55, OSA_BLUE), (1, OSA_STEEL)]), bx, by)

        wave_h = px(46)
        self.period = bw   # one wave cycle per band width, so shifting by it loops seamlessly
        self.wave_item = self._image(
            render_waves(2 * bw, wave_h, HEADER_WAVES, self.period, 46), bx, by + bh - wave_h)
        self.offset = 0

        self._image(render_band_frame(W, H, bx, by, bw, bh, px(14)), 0, 0)

        mid = by + px(36)
        x = bx + px(22)
        logo = load_logo(px(44))
        if logo is not None:
            self._image(logo, x, mid, anchor="w")
            x += logo.width
        else:
            f = tkfont.Font(root=root, family=HEAD_FAMILY, size=-px(20), weight="bold")
            self._keep.append(f)
            self.canvas.create_text(x, mid, text="OSA", fill="white", font=f, anchor="w")
            x += f.measure("OSA")
        x += px(16)
        self.canvas.create_line(x, mid - px(22), x, mid + px(22), fill="#8FA7C9", width=1)
        x += px(16)

        title_font = tkfont.Font(root=root, family=HEAD_FAMILY, size=-px(26))
        sub_font = tkfont.Font(root=root, family=BODY_FAMILY, size=-px(12))
        self._keep += [title_font, sub_font]
        self.canvas.create_text(x, mid - px(4), text=title, fill="white",
                                font=title_font, anchor="sw")
        self.canvas.create_text(x + px(1), mid + px(4), text=subtitle, fill="#D9E3F0",
                                font=sub_font, anchor="nw")

        if ANIMATE_HEADER_WAVES:
            self.canvas.after(500, self._drift)

    def _image(self, pil_img, x, y, anchor="nw"):
        tk_img = ImageTk.PhotoImage(pil_img, master=self.canvas)
        self._keep.append(tk_img)
        return self.canvas.create_image(x, y, image=tk_img, anchor=anchor)

    def _drift(self):
        self.canvas.move(self.wave_item, -1, 0)
        self.offset += 1
        if self.offset >= self.period:
            self.canvas.move(self.wave_item, self.period, 0)
            self.offset = 0
        self.canvas.after(60, self._drift)


class OSAFooter:
    """Thin wave strip with app name and organisation link."""
    def __init__(self, parent, app_name):
        self.frame = ctk.CTkFrame(parent, fg_color=BG_PAGE, corner_radius=0)
        self.frame.pack(fill="x", side="bottom", pady=(0, 6))
        W, H = px(WIN_W), px(22)
        c = Canvas(self.frame, width=W, height=H, bg=BG_PAGE, highlightthickness=0, bd=0)
        c.pack(fill="x")
        self._img = ImageTk.PhotoImage(
            render_waves(W, H, FOOTER_WAVES, W // 2, 28, opacity=.55), master=c)
        c.create_image(0, 0, image=self._img, anchor="nw")

        row = ctk.CTkFrame(self.frame, fg_color="transparent")
        row.pack()
        ctk.CTkLabel(row, text=f"{app_name}  ·  ", text_color=TEXT_MUT,
                     font=F(11), height=16).pack(side="left")
        link = ctk.CTkLabel(row, text="Ocean Science Analytics", text_color=OSA_BLUE,
                            font=F(11), height=16, cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda _e: webbrowser.open(ORG_URL))


# ── Header, tab bar, footer, content area ────────────────────────────────────
header = OSAHeader(root, "EZ AudioMate",
                   "Resample, adjust gain, convert and inspect audio files")

TAB_NAMES = ["Resampling", "Gain", "FLAC Conversion", "WAV Conversion", "Audio Info"]

tab_strip = ctk.CTkFrame(root, fg_color=BG_CARD, corner_radius=10, height=44,
                         border_width=1, border_color=BORDER)
tab_strip.pack(fill="x", padx=16, pady=(0, 10))
tab_strip.pack_propagate(False)
tab_strip.grid_propagate(False)
tab_strip.rowconfigure(0, weight=1)

footer = OSAFooter(root, "EZ AudioMate")   # packed before content so it stays at the bottom

content_area = ctk.CTkFrame(root, fg_color=BG_PAGE, corner_radius=0)
content_area.pack(fill="both", expand=True)

tab_frames = {}
for name in TAB_NAMES:
    f = ctk.CTkFrame(content_area, fg_color=BG_PAGE, corner_radius=0)
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
            b.configure(fg_color=OSA_BLUE, hover_color=OSA_NAVY, text_color="white",
                        font=F(13, "bold"))
        else:
            b.configure(fg_color=BG_CARD, hover_color=BG_HOVER, text_color=TEXT_LABEL,
                        font=F(13))

N = len(TAB_NAMES)
for i, name in enumerate(TAB_NAMES):
    tab_strip.columnconfigure(i, weight=1, uniform="tabs")
    btn = ctk.CTkButton(tab_strip, text=name, height=32, corner_radius=7,
                        fg_color=BG_CARD, hover_color=BG_HOVER, text_color=TEXT_LABEL,
                        font=F(13), border_width=0,
                        command=lambda n=name: switch_tab(n))
    btn.grid(row=0, column=i, sticky="nsew", pady=5,
             padx=(5 if i == 0 else 2, 5 if i == N - 1 else 2))
    tab_buttons[name] = btn

switch_tab(TAB_NAMES[0])

# ── Widget helpers ────────────────────────────────────────────────────────────
def card(parent, **kwargs):
    defaults = dict(fg_color=BG_CARD, corner_radius=12,
                    border_width=1, border_color=BORDER)
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)

def gradient_rule(parent):
    """1px line fading from the border colour to the card colour (the .sec-head line)."""
    c = Canvas(parent, height=1, bg=BG_CARD, highlightthickness=0, bd=0)
    a, b = hex_rgb(BORDER_STRONG), hex_rgb(BG_CARD)
    def redraw(_e=None):
        c.delete("all")
        w = max(c.winfo_width(), 1)
        steps = max(1, w // 4)
        for i in range(steps):
            t = i / steps
            col = "#%02x%02x%02x" % tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
            c.create_rectangle(i * 4, 0, i * 4 + 4, 1, fill=col, outline="")
    c.bind("<Configure>", redraw)
    return c

def section_head(parent, text, row, reserve=0):
    """Blue uppercase section heading with a fading rule, like SpectraReel's .sec-head.
    reserve leaves room on the right for the card's help buttons."""
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.grid(row=row, column=0, columnspan=3, sticky="ew",
           padx=(20, 20 + reserve), pady=(16, 4))
    f.columnconfigure(1, weight=1)
    ctk.CTkLabel(f, text=text.upper(), text_color=OSA_BLUE, font=F(11, "bold"),
                 height=18).grid(row=0, column=0, sticky="w", padx=(0, 8))
    gradient_rule(f).grid(row=0, column=1, sticky="ew")
    return f

def field_label(parent, text):
    return ctk.CTkLabel(parent, text=text, text_color=TEXT_LABEL,
                        font=F(12, "bold"), height=18)

def hint_label(parent, text):
    return ctk.CTkLabel(parent, text=text, text_color=TEXT_MUT, font=F(11))

def styled_entry(parent, **kwargs):
    e = ctk.CTkEntry(parent, height=36, fg_color=BG_INPUT,
                     border_color=BORDER_STRONG, border_width=1,
                     text_color=TEXT, placeholder_text_color=TEXT_MUT,
                     corner_radius=6, font=F(13), **kwargs)
    e.bind("<FocusIn>", lambda _e: e.configure(border_color=OSA_SEA))
    e.bind("<FocusOut>", lambda _e: e.configure(border_color=BORDER_STRONG))
    return e

def styled_checkbox(parent, text, variable):
    return ctk.CTkCheckBox(parent, text=text, variable=variable,
                           fg_color=OSA_BLUE, hover_color=OSA_SEA,
                           border_color=BORDER_STRONG, border_width=2,
                           checkmark_color="white", corner_radius=4,
                           checkbox_width=18, checkbox_height=18,
                           text_color=TEXT, font=F(12))

def folder_row(parent, var, label_text, row):
    field_label(parent, label_text).grid(row=row, column=0, columnspan=3,
                                         sticky="w", padx=20, pady=(6, 3))
    entry = styled_entry(parent, textvariable=var)
    entry.grid(row=row + 1, column=0, columnspan=2, sticky="ew", padx=(20, 6), pady=2)
    btn = ctk.CTkButton(parent, text="Browse…", width=96, height=36,
                        fg_color=OSA_STEEL, hover_color=OSA_BLUE,
                        text_color="white", corner_radius=6, font=F(12, "bold"),
                        command=lambda: var.set(filedialog.askdirectory()))
    btn.grid(row=row + 1, column=2, padx=(0, 20), pady=2)
    return entry

def gain_entry(parent, row, label_text="Gain (dB)", default="0"):
    """Label + entry for a gain value in dB. Returns the entry widget."""
    field_label(parent, label_text).grid(row=row, column=0, sticky="w", padx=20, pady=(6, 3))
    entry = styled_entry(parent, width=180, placeholder_text="e.g. 3 or -6")
    if default is not None:
        entry.insert(0, default)
    entry.grid(row=row + 1, column=0, sticky="w", padx=20, pady=2)
    return entry

def action_btn(parent, text, cmd):
    return ctk.CTkButton(parent, text=text, command=cmd,
                         height=42, corner_radius=8,
                         fg_color=OSA_BLUE, hover_color=BTN_HOVER,
                         text_color="white", font=F(14, "bold"))

def small_btn(parent, text, cmd, size=32, radius=16):
    """White outlined button (SpectraReel's transport-button style)."""
    short = len(text) == 1
    return ctk.CTkButton(parent, text=text, command=cmd,
                         width=size if short else size + 8, height=size,
                         corner_radius=radius, fg_color=BG_CARD, hover_color=BG_HOVER,
                         text_color=OSA_NAVY, border_color=BORDER_STRONG, border_width=1,
                         font=F(13 if short else 11, "normal" if short else "bold"))

_help_bars = {}

def help_btn(parent, cmd, text="?"):
    """
    Round help button in the card's top-right corner. Buttons are packed into
    one row per card, so each new button sits to the left of the previous one
    and they never overlap, whatever width the text needs.
    """
    bar = _help_bars.get(parent)
    if bar is None:
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.place(relx=1.0, rely=0.0, anchor="ne", x=-14, y=9)
        _help_bars[parent] = bar
    b = small_btn(bar, text, cmd)
    b.pack(side="right", padx=(6, 0))
    return b

_guide_windows = {}

def show_text_window(title, text, width=660, height=580):
    """Themed, read-only window with monospaced text (keeps tables aligned).
    Reopening the same title brings the existing window to the front."""
    win = _guide_windows.get(title)
    if win is not None and win.winfo_exists():
        win.deiconify(); win.lift(); win.focus_force()
        return

    win = ctk.CTkToplevel(root)
    win.title(title)
    win.geometry(f"{width}x{height}")
    win.configure(fg_color=BG_PAGE)
    win.transient(root)
    _guide_windows[title] = win

    ctk.CTkLabel(win, text=title, text_color=OSA_NAVY, font=F(18, head=True)
                 ).pack(anchor="w", padx=18, pady=(14, 4))

    box = ctk.CTkTextbox(win, wrap="word",
                         fg_color=BG_SUBTLE, text_color=TEXT_CODE,
                         font=ctk.CTkFont(family=MONO_FAMILY, size=13),
                         corner_radius=8, border_color=BORDER, border_width=1)
    box.pack(fill="both", expand=True, padx=16, pady=(4, 8))
    box.insert("1.0", text)
    box.configure(state="disabled")

    ctk.CTkButton(win, text="Close", width=110, height=34, corner_radius=8,
                  fg_color=OSA_BLUE, hover_color=BTN_HOVER, text_color="white",
                  font=F(13, "bold"), command=win.destroy).pack(pady=(0, 14))

    # CTkToplevel can open behind the main window on some platforms
    win.after(50, lambda: (win.lift(), win.focus_force()))

def ctk_progress_shim(pbar_ctk):
    class Shim:
        def __init__(self, p): self._p = p; self._max = 1
        def __setitem__(self, k, v):
            if k == 'maximum': self._max = max(v, 1)
            elif k == 'value': self._p.set(v / self._max)
        def __getitem__(self, k):
            return self._max if k == 'maximum' else 0
    return Shim(pbar_ctk)

class StatusBadge:
    """
    Pill-shaped status label (SpectraReel's .badge-*). Offers the same
    .config(text=...) interface the processing functions already call, and
    picks its colour from the message.
    """
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent, corner_radius=12, border_width=1)
        self.label = ctk.CTkLabel(self.frame, text="", font=F(11, "bold"), height=18)
        self.label.pack(padx=12, pady=3)
        self.config(text="Ready")

    @staticmethod
    def _kind(text):
        t = text.lower()
        if "error" in t or "fail" in t:
            return "error"
        if "complete" in t or "processed" in t or "done" in t:
            return "done"
        if t.startswith("ready"):
            return "idle"
        return "running"

    def config(self, **kw):
        if "text" not in kw:
            return
        bg, fg, border = BADGE[self._kind(kw["text"])]
        self.frame.configure(fg_color=bg, border_color=border)
        self.label.configure(text=kw["text"], text_color=fg, fg_color=bg)

    def grid(self, **kw):
        self.frame.grid(**kw)

# ── Spinner ───────────────────────────────────────────────────────────────────
class Spinner:
    """Rotating arc spinner drawn on a bare tkinter Canvas."""
    SIZE  = 28
    ARC   = 90    # degrees of visible arc (like a CSS border-top spinner)
    SPEED = 10    # degrees per frame
    DELAY = 20    # ms per frame
    WIDTH = 3     # stroke width

    def __init__(self, parent, color=OSA_BLUE):
        self._color  = color
        self._angle  = 0
        self._active = False
        self._size   = px(self.SIZE)
        self._width  = max(2, px(self.WIDTH))
        self._canvas = Canvas(parent, width=self._size, height=self._size,
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
        c, s, w = self._canvas, self._size, self._width
        c.delete("all")
        pad = w // 2 + 1
        c.create_oval(pad, pad, s - pad, s - pad, outline=SPIN_RING, width=w)
        c.create_arc(pad, pad, s - pad, s - pad, start=self._angle, extent=self.ARC,
                     outline=self._color, width=w, style="arc")
        self._angle = (self._angle - self.SPEED) % 360
        c.after(self.DELAY, self._animate)


def make_progress_section(parent, grid_row, color=OSA_BLUE):
    """
    Progress bar + spinner on one row, status badge below.
    Returns (progress_shim, status_badge, spinner).
    """
    row_frame = ctk.CTkFrame(parent, fg_color="transparent")
    row_frame.grid(row=grid_row, column=0, columnspan=3, sticky="ew",
                   padx=20, pady=(16, 4))
    row_frame.columnconfigure(0, weight=1)
    row_frame.columnconfigure(1, weight=0)

    pbar = ctk.CTkProgressBar(row_frame, height=7, corner_radius=4,
                              fg_color=TRACK, progress_color=color)
    pbar.set(0)
    pbar.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    spinner = Spinner(row_frame, color=color)
    spinner.grid(row=0, column=1, sticky="e")

    badge = StatusBadge(parent)
    badge.grid(row=grid_row + 1, column=0, columnspan=3, sticky="w", padx=20, pady=(0, 4))

    return ctk_progress_shim(pbar), badge, spinner

# ── Input validation (runs on the main thread, before any work starts) ───────
def parse_gain(entry):
    """Return gain in dB as a float (blank = 0), or None after showing an error."""
    text = entry.get().strip()
    if text == "":
        return 0.0
    try:
        value = float(text)
    except ValueError:
        value = None
    if value is None or not math.isfinite(value):
        messagebox.showerror("Error", "Please enter a valid gain in dB (e.g. 3, -6 or 0).")
        return None
    return value

def check_folders(input_folder, output_folder):
    if not input_folder or not os.path.isdir(input_folder):
        messagebox.showerror("Error", "Please select a valid input folder.")
        return False
    if not output_folder or not os.path.isdir(output_folder):
        messagebox.showerror("Error", "Please select a valid output folder.")
        return False
    return True

def same_folder(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def threaded_run(target_fn, args, spinner, status=None):
    """
    Run target_fn(*args) in ONE background thread.
    Spinner starts before the thread and stops only after it fully finishes.
    target_fn must be a plain blocking function (no internal threading).
    """
    spinner.start()
    def _wrap():
        try:
            target_fn(*args)
        except Exception as e:
            def _report(err=e):
                if status is not None:
                    status.config(text="Error, processing stopped")
                messagebox.showerror("Error", f"Processing failed:\n{err}")
            root.after(0, _report)
        finally:
            root.after(0, spinner.stop)   # stop on main thread — tkinter-safe
    threading.Thread(target=_wrap, daemon=True).start()


def tab_card(tab_name):
    t = tab_frames[tab_name]
    t.columnconfigure(0, weight=1)
    t.rowconfigure(0, weight=1)
    c = card(t)
    c.grid(row=0, column=0, sticky="nsew", padx=16, pady=(0, 6))
    c.columnconfigure((0, 1), weight=1)
    c.columnconfigure(2, weight=0)
    return c

HELP_RESERVE = {1: 50, 2: 96, 3: 142}   # px kept clear for 1/2/3 help buttons


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — RESAMPLING
# ══════════════════════════════════════════════════════════════════════════════
input_folder_var  = ctk.StringVar()
output_folder_var = ctk.StringVar()
include_sr_var    = ctk.IntVar()

c1 = tab_card("Resampling")
help_btn(c1, show_help)
help_btn(c1, lambda: show_text_window(GAIN_GUIDE_TITLE, GAIN_GUIDE_TEXT), text="dB")
help_btn(c1, lambda: show_text_window(RESAMPLE_GUIDE_TITLE, RESAMPLE_GUIDE_TEXT), text="Hz")

section_head(c1, "Files", 0, reserve=HELP_RESERVE[3])
folder_row(c1, input_folder_var,  "Input Folder",  1)
folder_row(c1, output_folder_var, "Output Folder", 3)

section_head(c1, "Settings", 5)
field_label(c1, "Target Sample Rate (Hz)").grid(row=6, column=0, sticky="w", padx=20, pady=(6, 3))
sr_entry = styled_entry(c1, width=180, placeholder_text="e.g. 44100")
sr_entry.grid(row=7, column=0, sticky="w", padx=20, pady=2)
styled_checkbox(c1, "Append sample rate to filename", include_sr_var
                ).grid(row=7, column=1, columnspan=2, sticky="w", padx=10, pady=2)

gain_entry1 = gain_entry(c1, 8, "Gain (dB), optional")
hint_label(c1, "0 = no gain change").grid(row=9, column=1, columnspan=2, sticky="w", padx=10, pady=2)

progress1, label_status1, spinner1 = make_progress_section(c1, 10)

def _run_resample():
    input_folder = input_folder_var.get()
    output_folder = output_folder_var.get()
    if not check_folders(input_folder, output_folder):
        return
    try:
        desired_sr = int(sr_entry.get())
        if desired_sr <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid sample rate.")
        return
    gain_db = parse_gain(gain_entry1)
    if gain_db is None:
        return
    include_sr = include_sr_var.get()
    threaded_run(process_files,
                 (input_folder, output_folder, desired_sr, include_sr,
                  progress1, label_status1, root, gain_db),
                 spinner1, label_status1)

action_btn(c1, "Resample Files", _run_resample
           ).grid(row=12, column=0, columnspan=3, pady=(8, 18), padx=20, sticky="ew")

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — GAIN ADJUSTMENT
# ══════════════════════════════════════════════════════════════════════════════
input_folder_var_g  = ctk.StringVar()
output_folder_var_g = ctk.StringVar()
include_gain_var    = ctk.IntVar(value=1)

cg = tab_card("Gain")
help_btn(cg, show_help5)
help_btn(cg, lambda: show_text_window(GAIN_GUIDE_TITLE, GAIN_GUIDE_TEXT), text="dB")

section_head(cg, "Files", 0, reserve=HELP_RESERVE[2])
folder_row(cg, input_folder_var_g,  "Input Folder (.wav / .flac)", 1)
folder_row(cg, output_folder_var_g, "Output Folder",               3)

section_head(cg, "Gain", 5)
gain_entry_g = gain_entry(cg, 6, default=None)
styled_checkbox(cg, "Append gain to filename (e.g. _+3dB)", include_gain_var
                ).grid(row=7, column=1, columnspan=2, sticky="w", padx=10, pady=2)

progress_g, label_status_g, spinner_g = make_progress_section(cg, 8)

def _run_gain():
    input_folder = input_folder_var_g.get()
    output_folder = output_folder_var_g.get()
    if not check_folders(input_folder, output_folder):
        return
    if gain_entry_g.get().strip() == "":
        messagebox.showerror("Error", "Please enter a gain in dB.")
        return
    gain_db = parse_gain(gain_entry_g)
    if gain_db is None:
        return
    if gain_db == 0:
        messagebox.showinfo("Info", "Gain is 0 dB, so there's nothing to change.")
        return
    include_gain = include_gain_var.get()
    if not include_gain and same_folder(input_folder, output_folder):
        messagebox.showerror(
            "Error",
            "The output folder is the same as the input folder, which would overwrite "
            "your originals.\n\nChoose a different output folder or tick "
            "'Append gain to filename'.")
        return
    threaded_run(process_gain_files,
                 (input_folder, output_folder, gain_db, include_gain,
                  progress_g, label_status_g, root),
                 spinner_g, label_status_g)

action_btn(cg, "Apply Gain", _run_gain
           ).grid(row=10, column=0, columnspan=3, pady=(8, 18), padx=20, sticky="ew")

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — FLAC CONVERSION
# ══════════════════════════════════════════════════════════════════════════════
input_folder_var2  = ctk.StringVar()
output_folder_var2 = ctk.StringVar()

c2 = tab_card("FLAC Conversion")
help_btn(c2, show_help2)

section_head(c2, "Files", 0, reserve=HELP_RESERVE[1])
folder_row(c2, input_folder_var2,  "Input Folder (.wav / .aif)", 1)
folder_row(c2, output_folder_var2, "Output Folder",              3)

progress2, label_status2, spinner2 = make_progress_section(c2, 5)

action_btn(c2, "Convert to FLAC",
           lambda: threaded_run(compress_to_flac,
                                (input_folder_var2.get(), output_folder_var2.get(),
                                 progress2, label_status2, root),
                                spinner2, label_status2)
           ).grid(row=7, column=0, columnspan=3, pady=(8, 18), padx=20, sticky="ew")

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — WAV CONVERSION
# ══════════════════════════════════════════════════════════════════════════════
input_folder_var3  = ctk.StringVar()
output_folder_var3 = ctk.StringVar()

c3 = tab_card("WAV Conversion")
help_btn(c3, show_help3)

section_head(c3, "Files", 0, reserve=HELP_RESERVE[1])
folder_row(c3, input_folder_var3,  "Input Folder (.flac)", 1)
folder_row(c3, output_folder_var3, "Output Folder",        3)

progress3, label_status3, spinner3 = make_progress_section(c3, 5)

action_btn(c3, "Convert to WAV",
           lambda: threaded_run(convert_to_wav,
                                (input_folder_var3.get(), output_folder_var3.get(),
                                 progress3, label_status3, root),
                                spinner3, label_status3)
           ).grid(row=7, column=0, columnspan=3, pady=(8, 18), padx=20, sticky="ew")

# ══════════════════════════════════════════════════════════════════════════════
#  TAB 5 — AUDIO INFO
# ══════════════════════════════════════════════════════════════════════════════
t4 = tab_frames["Audio Info"]
t4.columnconfigure(0, weight=1)
t4.rowconfigure(0, weight=1)

c4 = card(t4)
c4.grid(row=0, column=0, sticky="nsew", padx=16, pady=(0, 6))
c4.columnconfigure(0, weight=1)
c4.columnconfigure((1, 2), weight=0)
c4.rowconfigure(2, weight=1)

action_btn(c4, "Select Folder & Analyze",
           lambda: select_folder_tab4(output_text)
           ).grid(row=0, column=0, padx=(20, 6), pady=(18, 0), sticky="ew")

small_btn(c4, "dB", lambda: show_text_window(GAIN_GUIDE_TITLE, GAIN_GUIDE_TEXT),
          size=42, radius=8).grid(row=0, column=1, padx=(0, 6), pady=(18, 0))
small_btn(c4, "?", show_help4, size=42, radius=8
          ).grid(row=0, column=2, padx=(0, 20), pady=(18, 0))

section_head(c4, "Results", 1)

output_text = ctk.CTkTextbox(c4, wrap="word",
                             fg_color=BG_SUBTLE, text_color=TEXT_CODE,
                             font=ctk.CTkFont(family=MONO_FAMILY, size=12),
                             corner_radius=8, border_color=BORDER, border_width=1)
output_text.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=20, pady=(4, 18))

# ── Launch ────────────────────────────────────────────────────────────────────
root.mainloop()
