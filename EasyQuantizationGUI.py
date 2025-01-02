VERSION = "1.09"

import sys
import subprocess
import importlib
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
import os
import shutil
import winsound
import tkinter.scrolledtext as scrolledtext

def scroll_entry_to_end(entry):
    entry.xview_moveto(1)

def browse_file(entry):
    file_path = filedialog.askopenfilename(filetypes=[("Model files", "*.safetensors *.sft")])
    if file_path:
        file_path = file_path.replace('\\', '/')  # Ensure forward slashes
        entry.delete(0, tk.END)
        entry.insert(0, file_path)
        scroll_entry_to_end(entry)
        suggest_output_file()  # Call this instead of update_output_file

def suggest_output_file():
    input_file = input_entry.get()
    quantize_level = quantize_level_var.get()
    if input_file:
        input_dir = os.path.dirname(input_file)
        input_filename = os.path.basename(input_file)
        input_name, _ = os.path.splitext(input_filename)
        output_file = f"{input_dir}/{input_name}-{quantize_level}.gguf"
        output_entry.delete(0, tk.END)
        output_entry.insert(0, output_file)
        scroll_entry_to_end(output_entry)

def browse_output_file(entry):
    # Get the current input file and quantization level
    input_file = input_entry.get()
    quantize_level = quantize_level_var.get()
    
    # Generate a default output filename
    if input_file:
        input_dir = os.path.dirname(input_file)
        input_filename = os.path.basename(input_file)
        input_name, _ = os.path.splitext(input_filename)
        default_filename = f"{input_name}-{quantize_level}.gguf"
    else:
        default_filename = f"output-{quantize_level}.gguf"
        input_dir = "/"
    
    # Open the file dialog with the default filename
    file_path = filedialog.asksaveasfilename(
        initialdir=input_dir,
        initialfile=default_filename,
        defaultextension=".gguf", 
        filetypes=[("GGUF files", "*.gguf")]
    )
    
    if file_path:
        file_path = file_path.replace('\\', '/')  # Ensure forward slashes
        entry.delete(0, tk.END)
        entry.insert(0, file_path)
        scroll_entry_to_end(entry)

def disable_ui():
    global input_entry, output_entry, input_browse, output_browse, quantize_dropdown, run_button
    input_entry.config(state='disabled')
    output_entry.config(state='disabled')
    input_browse.config(state='disabled')
    output_browse.config(state='disabled')
    quantize_dropdown.config(state='disabled')
    run_button.config(state='disabled')

def enable_ui():
    global input_entry, output_entry, input_browse, output_browse, quantize_dropdown, run_button
    input_entry.config(state='normal')
    output_entry.config(state='normal')
    input_browse.config(state='normal')
    output_browse.config(state='normal')
    quantize_dropdown.config(state='readonly')
    run_button.config(state='normal')

def run_llama_quantize():
    input_file = input_entry.get()
    output_file = output_entry.get()
    quantize_level = quantize_level_var.get()
    
    if not input_file or not output_file:
        messagebox.showerror("Error", "Please select both input and output files.")
        return
    
    output_dir = os.path.dirname(output_file)
    required_space = 40_000_000_000  # ~40 GB (a bit more than 36.5 GB)
    available_space = shutil.disk_usage(output_dir).free

    if available_space < required_space:
        required_gb = required_space / (1024**3)
        available_gb = available_space / (1024**3)
        messagebox.showerror("Error", f"You need {required_gb:.1f} GB of drive space to continue. Only {available_gb:.1f} GB available.")
        return

    disable_ui()
    
    # Clear previous log
    process_text.delete('1.0', tk.END)
    process_text.insert(tk.END, "Starting conversion process...\n")
    process_text.see(tk.END)
    root.update()

    # Convert the input file to GGUF format
    convert_py_path = resource_path("convert.py")
    output_dir = os.path.dirname(output_file)
    temp_gguf_file = os.path.join(output_dir, "temporary_file_during_quantization")

    # Add cleanup of existing temp file
    if os.path.exists(temp_gguf_file):
        try:
            os.remove(temp_gguf_file)
            process_text.insert(tk.END, "Cleaned up existing temporary file.\n")
            process_text.see(tk.END)
            root.update()
        except Exception as e:
            process_text.insert(tk.END, f"Error cleaning up temporary file: {e}\n")
            process_text.see(tk.END)
            root.update()
            enable_ui()
            return

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        # Get the Python executable path from the current environment
        pythonpath = sys.executable
        
        process = subprocess.Popen([pythonpath, convert_py_path, "--src", input_file, "--dst", temp_gguf_file], 
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, 
                                   bufsize=1, universal_newlines=True, startupinfo=startupinfo)
        
        for line in process.stdout:
            process_text.insert(tk.END, line)
            process_text.see(tk.END)
            root.update()
        
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)
        
        process_text.insert(tk.END, "Conversion completed successfully.\n")
    except subprocess.CalledProcessError as e:
        process_text.insert(tk.END, f"Error converting file: {e}\n")
        process_text.insert(tk.END, f"Command: {e.cmd}\n")
        process_text.insert(tk.END, f"Return code: {e.returncode}\n")
        process_text.see(tk.END)
        root.update()
        enable_ui()
        return

    # Quantize the converted file
    llama_quantize_path = resource_path("llama-quantize.exe")
    process_text.insert(tk.END, "Starting quantization process...\n")
    process_text.see(tk.END)
    root.update()

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen([llama_quantize_path, temp_gguf_file, output_file, quantize_level], 
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, 
                                   bufsize=1, universal_newlines=True, startupinfo=startupinfo)
        
        for line in process.stdout:
            process_text.insert(tk.END, line)
            process_text.see(tk.END)
            root.update()
        
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)
        
        process_text.insert(tk.END, "Quantization completed successfully.\n")
    except subprocess.CalledProcessError as e:
        process_text.insert(tk.END, f"Error running llama-quantize: {e}\n")
        process_text.insert(tk.END, f"Command: {e.cmd}\n")
        process_text.insert(tk.END, f"Return code: {e.returncode}\n")
        process_text.see(tk.END)
        root.update()
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_gguf_file):
            os.remove(temp_gguf_file)
        
    process_text.insert(tk.END, "Quantization process completed.")
    process_text.see(tk.END)
    root.update()
    
    enable_ui()
    
    # Play sound effect
    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)

def main():
    global root, process_text, input_entry, output_entry, quantize_dropdown, run_button, quantize_level_var
    global input_browse, output_browse  # Add these two variables
    root = tk.Tk()
    root.title(f"Easy Quantization GUI v{VERSION}")
    root.geometry("800x600")

    # Quantize level selection
    quantize_frame = tk.Frame(root)
    quantize_frame.pack(pady=10, padx=10)

    quantize_label = tk.Label(quantize_frame, text="Quantize Level:")
    quantize_label.pack(side=tk.LEFT)

    quantize_levels = ["Q2_K", "Q3_K_S", "Q4_0", "Q4_1", "Q4_K_S", "Q5_0", "Q5_1", "Q5_K_S", "Q6_K", "Q8_0", "F16"]
    quantize_level_var = tk.StringVar(root)
    quantize_level_var.set("Q8_0")  # Set default value to Q8_0

    quantize_dropdown = ttk.Combobox(quantize_frame, textvariable=quantize_level_var, values=quantize_levels, state="readonly")
    quantize_dropdown.pack(side=tk.LEFT)
    quantize_dropdown.bind("<<ComboboxSelected>>", lambda event: suggest_output_file())

    # Input file selection
    input_frame = tk.Frame(root)
    input_frame.pack(pady=10, padx=10, fill=tk.X)

    input_label = tk.Label(input_frame, text="Input File:")
    input_label.pack(side=tk.LEFT)

    input_entry = tk.Entry(input_frame)
    input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

    input_browse = tk.Button(input_frame, text="Browse", command=lambda: browse_file(input_entry))
    input_browse.pack(side=tk.RIGHT)

    # Add binding to scroll input entry when it gains focus
    input_entry.bind("<FocusIn>", lambda event: scroll_entry_to_end(input_entry))

    # Output file selection
    output_frame = tk.Frame(root)
    output_frame.pack(pady=10, padx=10, fill=tk.X)

    output_label = tk.Label(output_frame, text="Output File:")
    output_label.pack(side=tk.LEFT)

    output_entry = tk.Entry(output_frame)
    output_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

    output_browse = tk.Button(output_frame, text="Browse", command=lambda: browse_output_file(output_entry))
    output_browse.pack(side=tk.RIGHT)

    # Add binding to scroll output entry when it gains focus
    output_entry.bind("<FocusIn>", lambda event: scroll_entry_to_end(output_entry))

    # Run button
    run_button = tk.Button(root, text="Run Quantization", command=run_llama_quantize)
    run_button.pack(pady=20)

    # Add process log to bottom of main window
    process_frame = tk.Frame(root)
    process_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    process_label = tk.Label(process_frame, text="Process Log:")
    process_label.pack(side=tk.TOP, anchor='w')

    process_text = scrolledtext.ScrolledText(process_frame, wrap=tk.WORD, height=15)
    process_text.pack(expand=True, fill=tk.BOTH)

    root.mainloop()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    main()
