import tkinter as tk
from tkinter import ttk
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import threading
from audio_functions import *
from help_texts import *

#--------- GUI CODE ---------------
# Create the main application window
root = tk.Tk()
root.title("EZ AudioMate")
root.configure(bg='DodgerBlue4')
root.geometry("800x600")

# Create a notebook for tabs at the very top
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Create frames for the two tabs
tab1 = tk.Frame(notebook, bg='DodgerBlue4')
tab2 = tk.Frame(notebook, bg='DodgerBlue4')
tab3 = tk.Frame(notebook, bg='DodgerBlue4')
tab4 = tk.Frame(notebook, bg='DodgerBlue4')

notebook.add(tab1, text="Resampling")
notebook.add(tab2, text="FLAC Conversion")
notebook.add(tab3, text="WAV Conversion")
notebook.add(tab4, text="Audio Info")

# Shared header: Logo and title in each tab
def create_tab_header(parent):
    # Create a frame for the header inside the parent tab
    header_frame = tk.Frame(parent, bg='DodgerBlue4')
    header_frame.pack(side=tk.TOP, anchor='nw', pady=10, padx=10, fill=tk.X)

    # Load the company logo image
    logo_image = Image.open("white_square_OSA_med.jpg")
    logo_image = logo_image.resize((100, 100), Image.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_image)

    # Display the company logo
    logo_label = tk.Label(header_frame, image=logo_photo, bg='DodgerBlue4')
    logo_label.image = logo_photo  # Keep reference to avoid garbage collection
    logo_label.pack(side=tk.LEFT)

    # Add a label for "EZ Decimator" next to the logo
    ez_decimator_label = tk.Label(
        header_frame, text="EZ AudioMate", bg='DodgerBlue4', fg='white',
        font=("Times New Roman", 24, "bold")
    )
    ez_decimator_label.pack(side=tk.LEFT, padx=10)

# Add the shared header to each tab
create_tab_header(tab1)
create_tab_header(tab2)
create_tab_header(tab3)
create_tab_header(tab4)

##########################################################################
#       GUI --> TAB 1 = VARIABLES, HELP BUTTON, AND BOARDER
##########################################################################

# Tab 1: Resampling UI
input_folder_var = tk.StringVar()
output_folder_var = tk.StringVar()
include_sr_in_filename_var = tk.IntVar()

# Add help button function and placement on tab1
help_button_tab1 = tk.Button(tab1, text="HELP", bg='gray', fg='white', font=("Times New Roman", 16), command=show_help)
help_button_tab1.pack(padx=10, pady=10)
help_button_tab1.place(relx=0.95, rely=0.06, anchor=tk.NE)

# Add a canvas to draw the border around the widgets
canvas_border1= tk.Canvas(tab1, bg='DodgerBlue4', highlightthickness=0)
canvas_border1.place(relx=0.5, rely=0.55, anchor=tk.CENTER, width=695, height=395)
# Draw the initial border
canvas_border1.create_rectangle(10, 10, 685, 385, outline="white", width=2)


##########################################################################
#       GUI --> TAB 1 = WIDGETS AND INPUTS
##########################################################################

# Input folder selection
input_folder_label = tk.Label(tab1, text="Select Input Folder:", bg='DodgerBlue4', fg='white', font=("Times New Roman", 16))
input_folder_label.pack(pady=5)
input_folder_label.place(relx=0.3, rely=0.28, anchor=tk.CENTER)
input_folder_entry = tk.Entry(tab1, textvariable=input_folder_var, width=40)
input_folder_entry.pack(pady=5)
input_folder_entry.place(relx=0.3, rely=0.32, anchor=tk.CENTER)
browse_input_button = tk.Button(tab1, text="Browse", command=lambda: browse_input_folder(input_folder_var), font=("Times New Roman", 12), bd=0, width=18)
browse_input_button.pack(pady=5)
browse_input_button.place(relx=0.3, rely=0.37, anchor=tk.CENTER)

# Output folder selection
output_folder_label = tk.Label(tab1, text="Select Output Folder:", bg='DodgerBlue4', fg='white', font=("Times New Roman", 16))
output_folder_label.pack(pady=5)
output_folder_label.place(relx=0.3, rely=0.47, anchor=tk.CENTER)
output_folder_entry = tk.Entry(tab1, textvariable=output_folder_var, width=40)
output_folder_entry.pack(pady=5)
output_folder_entry.place(relx=0.3, rely=0.51, anchor=tk.CENTER)
browse_output_button = tk.Button(tab1, text="Browse", command=lambda: browse_output_folder(output_folder_var), font=("Times New Roman", 12), bd=0, width=18)
browse_output_button.pack(pady=5)
browse_output_button.place(relx=0.3, rely=0.56, anchor=tk.CENTER)

# Desired sampling rate
desired_sr_label = tk.Label(tab1, text="Desired Sampling Rate (Hz):", bg='DodgerBlue4', fg='white', font=("Times New Roman", 16))
desired_sr_label.pack(pady=5)
desired_sr_label.place(relx=0.7, rely=0.28, anchor=tk.CENTER)
desired_sr_entry = tk.Entry(tab1, width=40)
desired_sr_entry.pack(pady=5)
desired_sr_entry.place(relx=0.7, rely=0.32, anchor=tk.CENTER)

# Checkbox for including desired sampling rate in the filename
include_sr_checkbox = tk.Checkbutton(tab1, text="Include Desired SR in Filename", variable=include_sr_in_filename_var, bg='DodgerBlue4', fg='white', font=("Times New Roman", 16), selectcolor='DodgerBlue4')
include_sr_checkbox.pack(pady=5)
include_sr_checkbox.place(relx=0.73, rely=0.51, anchor=tk.CENTER)

# Resample button
resample_button = tk.Button(
    tab1, text="Resample and Save", bg='light blue', fg='black',
    font=("Times New Roman", 16),
    command=lambda: resample_and_save(
        input_folder_var, output_folder_var, desired_sr_entry,
        include_sr_in_filename_var, progress, label_status, root
    ),
    width=20
)
resample_button.pack(pady=20)
resample_button.place(relx=0.5, rely=0.75, anchor=tk.CENTER)

# Progress bar and status label
progress = Progressbar(tab1, length=300, mode='determinate')
progress.pack(pady=5)
progress.place(relx=0.5, rely=0.81, anchor=tk.CENTER)
label_status = tk.Label(tab1, text='', bg='DodgerBlue4', fg='white', font=("Times New Roman", 12))
label_status.pack(pady=5)
label_status.place(relx=0.5, rely=0.85, anchor=tk.CENTER)

##########################################################################
#       GUI --> TAB 2 = CONVERT TO FLAC
##########################################################################

# Tab 2: Compress to FLAC
input_folder_var2 = tk.StringVar()
output_folder_var2 = tk.StringVar()

help_button_tab2 = tk.Button(tab2, text="HELP", bg='gray', fg='white', font=("Times New Roman", 16), command=show_help2)
help_button_tab2.pack(padx=10, pady=10)
help_button_tab2.place(relx=0.95, rely=0.06, anchor=tk.NE)

# Add a canvas to draw the border around the widgets
canvas_border2= tk.Canvas(tab2, bg='DodgerBlue4', highlightthickness=0)
canvas_border2.place(relx=0.5, rely=0.55, anchor=tk.CENTER, width=695, height=395)
# Draw the initial border
canvas_border2.create_rectangle(10, 10, 685, 385, outline="white", width=2)

# Input folder selection
input_folder_label = tk.Label(tab2, text="Select Input Folder:", bg='DodgerBlue4', fg='white', font=("Times New Roman", 16))
input_folder_label.pack(pady=5)
input_folder_label.place(relx=0.3, rely=0.28, anchor=tk.CENTER)
input_folder_entry = tk.Entry(tab2, textvariable=input_folder_var2, width=50)
input_folder_entry.pack(pady=5)
input_folder_entry.place(relx=0.6, rely=0.34, anchor=tk.CENTER)
browse_input_button = tk.Button(tab2, text="Browse", command=lambda: browse_input_folder(input_folder_var2), font=("Times New Roman", 12), bd=0, width=16)
browse_input_button.pack(pady=5)
browse_input_button.place(relx=0.3, rely=0.34, anchor=tk.CENTER)

# Output folder selection
output_folder_label = tk.Label(tab2, text="Select Output Folder:", bg='DodgerBlue4', fg='white', font=("Times New Roman", 16))
output_folder_label.pack(pady=5)
output_folder_label.place(relx=0.3, rely=0.47, anchor=tk.CENTER)
output_folder_entry = tk.Entry(tab2, textvariable=output_folder_var2, width=50)
output_folder_entry.pack(pady=5)
output_folder_entry.place(relx=0.6, rely=0.53, anchor=tk.CENTER)
browse_output_button = tk.Button(tab2, text="Browse", command=lambda: browse_output_folder(output_folder_var2), font=("Times New Roman", 12), bd=0, width=16)
browse_output_button.pack(pady=5)
browse_output_button.place(relx=0.3, rely=0.53, anchor=tk.CENTER)

# Compress to  FLAC button
compress_button = tk.Button( tab2, text="Convert to FLAC", bg='light blue', fg='black', font=("Times New Roman", 16),
    command=lambda: threading.Thread( target=compress_to_flac, args=(input_folder_var2.get(), output_folder_var2.get(), progress_tab2, label_status_tab2, root)).start(),
    width=20
)
compress_button.pack(pady=20)
compress_button.place(relx=0.5, rely=0.75, anchor=tk.CENTER)

# Progress bar and status label for Tab 2
progress_tab2 = Progressbar(tab2, length=300, mode='determinate')
progress_tab2.pack(pady=5)
progress_tab2.place(relx=0.5, rely=0.81, anchor=tk.CENTER)

label_status_tab2 = tk.Label(tab2, text='', bg='DodgerBlue4', fg='white', font=("Times New Roman", 12))
label_status_tab2.pack(pady=5)
label_status_tab2.place(relx=0.5, rely=0.85, anchor=tk.CENTER)

##########################################################################
#       GUI --> TAB 3 = CONVERT TO WAV
##########################################################################

# Tab 3: Convert to WAV
input_folder_var3= tk.StringVar()
output_folder_var3 = tk.StringVar()

help_button_tab3 = tk.Button(tab3, text="HELP", bg='gray', fg='white', font=("Times New Roman", 16), command=show_help3)
help_button_tab3.pack(padx=10, pady=10)
help_button_tab3.place(relx=0.95, rely=0.06, anchor=tk.NE)

# Add a canvas to draw the border around the widgets
canvas_border3= tk.Canvas(tab3, bg='DodgerBlue4', highlightthickness=0)
canvas_border3.place(relx=0.5, rely=0.55, anchor=tk.CENTER, width=695, height=395)
# Draw the initial border
canvas_border3.create_rectangle(10, 10, 685, 385, outline="white", width=2)

# Input folder selection
input_folder_label = tk.Label(tab3, text="Select Input Folder:", bg='DodgerBlue4', fg='white', font=("Times New Roman", 16))
input_folder_label.pack(pady=5)
input_folder_label.place(relx=0.3, rely=0.28, anchor=tk.CENTER)
input_folder_entry = tk.Entry(tab3, textvariable=input_folder_var3, width=50)
input_folder_entry.pack(pady=5)
input_folder_entry.place(relx=0.6, rely=0.34, anchor=tk.CENTER)
browse_input_button = tk.Button(tab3, text="Browse", command=lambda: browse_input_folder(input_folder_var3), font=("Times New Roman", 12), bd=0, width=16)
browse_input_button.pack(pady=5)
browse_input_button.place(relx=0.3, rely=0.34, anchor=tk.CENTER)

# Output folder selection
output_folder_label = tk.Label(tab3, text="Select Output Folder:", bg='DodgerBlue4', fg='white', font=("Times New Roman", 16))
output_folder_label.pack(pady=5)
output_folder_label.place(relx=0.3, rely=0.47, anchor=tk.CENTER)
output_folder_entry = tk.Entry(tab3, textvariable=output_folder_var3, width=50)
output_folder_entry.pack(pady=5)
output_folder_entry.place(relx=0.6, rely=0.53, anchor=tk.CENTER)
browse_output_button = tk.Button(tab3, text="Browse", command=lambda: browse_output_folder(output_folder_var3), font=("Times New Roman", 12), bd=0, width=16)
browse_output_button.pack(pady=5)
browse_output_button.place(relx=0.3, rely=0.53, anchor=tk.CENTER)

# Convert to WAV button
compress_button = tk.Button(tab3, text="Convert to WAV", bg='light blue', fg='black', font=("Times New Roman", 16),
    command=lambda: convert_to_wav(input_folder_var3.get(), output_folder_var3.get(), progress_tab3, label_status_tab3, root),
    width=20
)
compress_button.pack(pady=20)
compress_button.place(relx=0.5, rely=0.75, anchor=tk.CENTER)

# Progress bar and status label for Tab 3
progress_tab3 = Progressbar(tab3, length=300, mode='determinate')
progress_tab3.pack(pady=5)
progress_tab3.place(relx=0.5, rely=0.81, anchor=tk.CENTER)

label_status_tab3 = tk.Label(tab3, text='', bg='DodgerBlue4', fg='white', font=("Times New Roman", 12))
label_status_tab3.pack(pady=5)
label_status_tab3.place(relx=0.5, rely=0.85, anchor=tk.CENTER)

##########################################################################
#       GUI --> TAB 4 = AUDIO INFO (SAMPLE SIZE + CHANNELS)
##########################################################################

help_button_tab4 = tk.Button(tab4, text="HELP", bg='gray', fg='white',
                             font=("Times New Roman", 16), command=show_help4)
help_button_tab4.pack(padx=10, pady=10)
help_button_tab4.place(relx=0.95, rely=0.06, anchor=tk.NE)

# Canvas border
canvas_border4 = tk.Canvas(tab4, bg='DodgerBlue4', highlightthickness=0)
canvas_border4.place(relx=0.5, rely=0.55, anchor=tk.CENTER, width=695, height=395)
canvas_border4.create_rectangle(10, 10, 685, 385, outline="white", width=2)

# Folder selection and analyze button
analyze_button = tk.Button(tab4, text="Select Folder",
                           bg='light blue', fg='black',
                           font=("Times New Roman", 16))
analyze_button.place(relx=0.5, rely=0.30, anchor=tk.CENTER)

# Text output area
output_text = tk.Text(tab4, width=80, height=18, wrap=tk.WORD,
                      font=("Courier New", 10))
output_text.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

# Attach button action
analyze_button.config(command=lambda: select_folder_tab4(output_text))

# Start the main event loop
root.mainloop()
