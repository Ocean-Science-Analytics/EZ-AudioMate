import os
import wave
import numpy as np
import soundfile as sf
import librosa
import soxr
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

def browse_input_folder(var):
    folder_path = filedialog.askdirectory()
    var.set(folder_path)

def browse_output_folder(var):
    folder_path = filedialog.askdirectory()
    var.set(folder_path)

# ---------- Gain helpers ----------
# Float formats can store values above full scale; integer (PCM) formats can't.
FLOAT_SUBTYPES = ("FLOAT", "DOUBLE")

def apply_gain(y, gain_db):
    """Scale samples by gain_db decibels. A gain of 0 returns the data untouched."""
    if gain_db == 0:
        return y
    return y * (10 ** (gain_db / 20))

def limit_to_format(y, subtype):
    """
    Clip to [-1, 1] when the output format is integer PCM.
    Returns (data, clipped) where clipped is True if any samples exceeded full scale.
    """
    if y.size == 0:
        return y, False
    if np.max(np.abs(y)) > 1.0 and subtype not in FLOAT_SUBTYPES:
        return np.clip(y, -1.0, 1.0), True
    return y, False

def format_gain(gain_db):
    """Filename-friendly gain label, e.g. +3dB, -6.5dB."""
    return f"{gain_db:+g}dB"

# ---------- Resampling ----------
def process_file(filename, desired_sr, input_folder, output_folder, include_sr, gain_db=0):
    file_path = os.path.join(input_folder, filename)
    info = sf.info(file_path)
    y, sr = sf.read(file_path, always_2d=True)
    n_channels = y.shape[1]
    print(f"Detected {n_channels} channel(s) in file: {filename}")

    y_resampled = soxr.resample(y, sr, desired_sr)
    y_resampled = apply_gain(y_resampled, gain_db)
    y_resampled, clipped = limit_to_format(y_resampled, info.subtype)

    base, ext = os.path.splitext(filename)
    if include_sr:
        output_filename = f"{base}_{desired_sr}Hz{ext}"
    else:
        output_filename = filename

    output_path = os.path.join(output_folder, output_filename)
    sf.write(output_path, y_resampled, desired_sr, subtype=info.subtype)
    return clipped and gain_db != 0

def process_files(input_folder, output_folder, desired_sr, include_sr, progress, label_status, root, gain_db=0):
    files = [f for f in os.listdir(input_folder) if f.lower().endswith((".wav", ".flac"))]
    if not files:
        messagebox.showerror("Error", "No .wav or .flac files found.")
        return

    progress['maximum'] = len(files)
    clipped_files = []

    for idx, filename in enumerate(files, 1):
        if process_file(filename, desired_sr, input_folder, output_folder, include_sr, gain_db):
            clipped_files.append(filename)
        progress['value'] = idx
        label_status.config(text=f"Processing: {filename} ({idx}/{len(files)})")
        root.update_idletasks()

    msg = "Resampling complete."
    if gain_db != 0:
        msg += f"\nGain applied: {format_gain(gain_db)}"
    msg += clip_report(clipped_files)
    messagebox.showinfo("Info", msg)
    progress['value'] = 0
    label_status.config(text="All files processed.")

def clip_report(clipped_files):
    if not clipped_files:
        return ""
    shown = "\n".join(f"  • {f}" for f in clipped_files[:10])
    more = f"\n  …and {len(clipped_files) - 10} more" if len(clipped_files) > 10 else ""
    return (f"\n\nWarning: {len(clipped_files)} file(s) exceeded full scale and were clipped:\n"
            f"{shown}{more}")

# ---------- Gain Adjustment ----------
def gain_file(filename, gain_db, input_folder, output_folder, include_gain):
    file_path = os.path.join(input_folder, filename)
    info = sf.info(file_path)
    y, sr = sf.read(file_path, always_2d=True)

    y = apply_gain(y, gain_db)
    y, clipped = limit_to_format(y, info.subtype)

    base, ext = os.path.splitext(filename)
    output_filename = f"{base}_{format_gain(gain_db)}{ext}" if include_gain else filename
    sf.write(os.path.join(output_folder, output_filename), y, sr, subtype=info.subtype)
    return clipped

def process_gain_files(input_folder, output_folder, gain_db, include_gain, progress, label_status, root):
    files = [f for f in os.listdir(input_folder) if f.lower().endswith((".wav", ".flac"))]
    if not files:
        messagebox.showerror("Error", "No .wav or .flac files found.")
        return

    progress['maximum'] = len(files)
    progress['value'] = 0
    clipped_files = []

    for idx, filename in enumerate(files, 1):
        if gain_file(filename, gain_db, input_folder, output_folder, include_gain):
            clipped_files.append(filename)
        progress['value'] = idx
        label_status.config(text=f"Processing: {filename} ({idx}/{len(files)})")
        root.update_idletasks()

    messagebox.showinfo("Info", f"Gain adjustment complete ({format_gain(gain_db)})."
                                + clip_report(clipped_files))
    progress['value'] = 0
    label_status.config(text="Gain Adjustment Complete.")

# ---------- FLAC Compression ----------
def compress_to_flac(input_folder, output_folder, progress, label_status, root):
    label_status.config(text="FLAC conversion started")
    root.update_idletasks()
    
    files = [f for f in os.listdir(input_folder) if f.lower().endswith((".wav", ".aif"))]
    if not files:
        messagebox.showerror("Error", "No .wav or .aif files found.")
        return

    progress['maximum'] = len(files)
    progress['value'] = 0

    for idx, filename in enumerate(files, 1):
        y, sr = librosa.load(os.path.join(input_folder, filename), sr=None)
        out_name = os.path.splitext(filename)[0] + ".flac"
        sf.write(os.path.join(output_folder, out_name), y, sr, format='FLAC')

        progress['value'] = idx
        label_status.config(text=f"Processing: {filename} ({idx}/{len(files)})")
        root.update_idletasks()

    messagebox.showinfo("Info", "FLAC conversion complete.")
    progress['value'] = 0
    label_status.config(text="FLAC Conversion Complete.")

# ---------- WAV Conversion ----------
def convert_to_wav(input_folder, output_folder, progress, label_status, root):
    label_status.config(text="WAV conversion started")
    root.update_idletasks()
    
    files = [f for f in os.listdir(input_folder) if f.lower().endswith(".flac")]
    if not files:
        messagebox.showerror("Error", "No .flac files found.")
        return

    progress['maximum'] = len(files)
    progress['value'] = 0

    for idx, filename in enumerate(files, 1):
        y, sr = librosa.load(os.path.join(input_folder, filename), sr=None)
        out_name = os.path.splitext(filename)[0] + ".wav"
        sf.write(os.path.join(output_folder, out_name), y, sr, format='WAV')

        progress['value'] = idx
        label_status.config(text=f"Processing: {filename} ({idx}/{len(files)})")
        root.update_idletasks()

    messagebox.showinfo("Info", "WAV conversion complete.")
    progress['value'] = 0
    label_status.config(text="WAV Conversion Complete.")

#--------- Threading & Filename Change --------
# Perform process threading
def resample_and_save(input_folder_var, output_folder_var, desired_sr_entry, include_sr_in_filename_var, progress, label_status, root):
    input_folder = input_folder_var.get()
    output_folder = output_folder_var.get()
    desired_sr = int(desired_sr_entry.get())
    include_sr = include_sr_in_filename_var.get()

    processing_thread = threading.Thread(
        target=process_files,
        args=(input_folder, output_folder, desired_sr, include_sr, progress, label_status, root)
    )
    processing_thread.start()

# Function to get the modified output filename based on the checkbox state
def get_output_filename(filename, desired_sr):
    if include_sr_in_filename_var.get() == 1:
        base, ext = os.path.splitext(filename)
        return f"{base}_{desired_sr}Hz{ext}"
    else:
        return filename


# ---------- Audio Info ----------
# Integer formats can't represent exactly +1.0, so a sample at positive full
# scale reads back as slightly less (e.g. 32767/32768). This threshold catches it.
FULL_SCALE_THRESHOLD = 0.9999

def to_dbfs(value):
    """Linear amplitude (0..1) -> dB relative to full scale."""
    return 20 * np.log10(value) if value > 0 else float("-inf")

def format_db(db, unit="dBFS"):
    if db == float("-inf"):
        return "silent"
    return f"{round(db, 1) + 0.0:.1f} {unit}"   # + 0.0 turns -0.0 into 0.0

def format_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h}:{m:02d}:{s:05.2f}" if h else f"{m}:{s:05.2f}"

def measure_levels(file_path, blocksize=262144):
    """
    Read the file in blocks (keeps memory low for long recordings) and return
    (peak, rms, full_scale_count) as linear values across all channels.
    """
    peak = 0.0
    sum_sq = 0.0
    n = 0
    full_scale = 0
    for block in sf.blocks(file_path, blocksize=blocksize, always_2d=True, dtype="float64"):
        a = np.abs(block)
        if a.size:
            peak = max(peak, float(a.max()))
            full_scale += int(np.count_nonzero(a >= FULL_SCALE_THRESHOLD))
        sum_sq += float(np.sum(block * block))
        n += block.size
    rms = float(np.sqrt(sum_sq / n)) if n else 0.0
    return peak, rms, full_scale

def describe_file(file_path):
    info = sf.info(file_path)
    peak, rms, full_scale = measure_levels(file_path)
    peak_db = to_dbfs(peak)
    rms_db = to_dbfs(rms)

    lines = [
        os.path.basename(file_path),
        f"  Sample rate : {info.samplerate} Hz",
        f"  Channels    : {info.channels}",
        f"  Format      : {info.subtype_info}",
        f"  Duration    : {format_duration(info.duration)}",
        f"  Peak level  : {format_db(peak_db)}",
        f"  RMS level   : {format_db(rms_db)}",
    ]
    if peak_db > 0.05:
        # Only possible in float files, which can store values above 1.0
        lines.append(f"  Headroom    : none, peak is {peak_db:.1f} dB over full scale")
    elif peak_db != float("-inf"):
        headroom = max(0.0, -peak_db)
        lines.append(f"  Headroom    : {headroom:.1f} dB (max gain before clipping)")
    if full_scale:
        lines.append(f"  WARNING     : {full_scale:,} sample(s) at full scale "
                     f"(possible clipping)")
    return "\n".join(lines) + "\n\n"

_analysis_running = threading.Event()

def analyze_audio_folder(folder_path, output_text):
    """
    Analyze every .wav/.flac file in folder_path. Runs in a background thread
    because measuring levels reads the whole file; results are posted back to
    the text box on the main thread as each file finishes.
    """
    if _analysis_running.is_set():
        return
    _analysis_running.set()

    def post(text, clear=False):
        def _do():
            if clear:
                output_text.delete(1.0, tk.END)
            output_text.insert(tk.END, text)
            output_text.see(tk.END)
        output_text.after(0, _do)

    def work():
        try:
            files = sorted(f for f in os.listdir(folder_path)
                           if f.lower().endswith((".wav", ".flac")))
            if not files:
                post("No .wav or .flac files found in this folder.\n", clear=True)
                return
            post(f"Analyzing {len(files)} file(s) in {folder_path}\n\n", clear=True)
            for filename in files:
                file_path = os.path.join(folder_path, filename)
                try:
                    post(describe_file(file_path))
                except Exception as e:
                    post(f"Error reading {filename}: {e}\n\n")
            post("Done.\n")
        finally:
            _analysis_running.clear()

    threading.Thread(target=work, daemon=True).start()

def select_folder_tab4(output_text):
    folder = filedialog.askdirectory(title="Select audio folder")
    if folder:
        analyze_audio_folder(folder, output_text)
