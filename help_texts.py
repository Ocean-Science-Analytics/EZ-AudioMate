from tkinter import messagebox

def show_help():
    help_text = (
        "Welcome to EZ AudioMate!\n\n"
        "This tab allows you to resample audio files based on a given sampling rate. To use this program, simply:\n\n"
        "   1. Provide the input folder with original audio files.\n"
        "   2. Provide the output folder in which the files will be\n"
        "       downloaded too.\n"
        "   3. Insert the desired sampling rate.\n"
        "   4. Select if the sampling rate should be included in the file\n"
        "       name of the new resampled files. \n"
        "   5. Click 'Resample and Save'.\n\n"
        "Depending on the size of the files being processed this may take a few minutes.\n\n"
        "Thank you for using EZ AudioMate!"
    )
    messagebox.showinfo("Help", help_text)

def show_help2():
    help_text = (
        "This tab allows you to convert .wav, .WAV, or .aif files to .flac format. To use this program, simply:\n\n"
        "   1. Provide the input folder with original audio files.\n"
        "   2. Provide the output folder in which the files will be\n"
        "       downloaded too.\n"
        "   3. Click 'Convert to FLAC'.\n\n"
        "Depending on the size of the files being processed this may take a few minutes.\n\n"
        "Thank you for using EZ AudioMate!"
    )
    messagebox.showinfo("Help", help_text)

def show_help3():
    help_text = (
        "This tab allows you to convert .flac files to .wav format. To use this program, simply:\n\n"
        "   1. Provide the input folder with original audio files.\n"
        "   2. Provide the output folder in which the files will be\n"
        "       downloaded too.\n"
        "   3. Click 'Convert to WAV'\n\n"
        "Depending on the size of the files being processed this may take a few minutes.\n\n"
        "Thank you for using EZ AudioMate!"
    )
    messagebox.showinfo("Help", help_text)

def show_help4():
    help_text = (
        "This tab analyzes all .wav and .flac files in a selected folder.\n\n"
        "It displays each file’s sampling rate and number of channels.\n\n"
        "To use:\n"
        " 1. Click 'Select Folder' and choose the folder.\n"
        " 2. Only .wav and  .flac files are accepted.\n"
        " 3. View results in the output box below.\n\n"
        "Depending on the size of the files being read this may take a few minutes.\n\n"
        "Thank you for using EZ AudioMate!"
    )
    messagebox.showinfo("Help", help_text)
