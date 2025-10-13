import os
import wave
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

# ---------- Resampling ----------
def process_file(filename, desired_sr, input_folder, output_folder, include_sr):
    file_path = os.path.join(input_folder, filename)
    y, sr = sf.read(file_path, always_2d=True)
    n_channels = y.shape[1]
    print(f"Detected {n_channels} channel(s) in file: {filename}")

    y_resampled = soxr.resample(y, sr, desired_sr)

    base, ext = os.path.splitext(filename)
    if include_sr:
        output_filename = f"{base}_{desired_sr}Hz{ext}"
    else:
        output_filename = filename

    output_path = os.path.join(output_folder, output_filename)
    sf.write(output_path, y_resampled, desired_sr)

def process_files(input_folder, output_folder, desired_sr, include_sr, progress, label_status, root):
    files = [f for f in os.listdir(input_folder) if f.lower().endswith((".wav", ".flac"))]
    if not files:
        messagebox.showerror("Error", "No .wav or .flac files found.")
        return

    progress['maximum'] = len(files)

    for idx, filename in enumerate(files, 1):
        process_file(filename, desired_sr, input_folder, output_folder, include_sr)
        progress['value'] = idx
        label_status.config(text=f"Processing: {filename} ({idx}/{len(files)})")
        root.update_idletasks()

    messagebox.showinfo("Info", "Resampling complete.")
    progress['value'] = 0
    label_status.config(text="All files processed.")

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
def analyze_audio_folder(folder_path, output_text):
    output_text.delete(1.0, tk.END)
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".wav", ".flac")):
            file_path = os.path.join(folder_path, filename)
            try:
                if filename.lower().endswith(".wav"):
                    with wave.open(file_path, 'rb') as f:
                        sr = f.getframerate()
                        ch = f.getnchannels()
                else:
                    info = sf.info(file_path)
                    sr = info.samplerate
                    ch = info.channels

                output_text.insert(tk.END, f"{filename}\nRate: {sr} Hz\nChannels: {ch}\n\n")
            except Exception as e:
                output_text.insert(tk.END, f"Error reading {filename}: {e}\n\n")

def select_folder_tab4(output_text):
    folder = filedialog.askdirectory(title="Select audio folder")
    if folder:
        analyze_audio_folder(folder, output_text)
