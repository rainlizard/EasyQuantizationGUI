import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import sys
import os
import subprocess
import shutil
import winsound
import tkinter.scrolledtext as scrolledtext
import importlib.util

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def scroll_entry_to_end(entry):
    entry.xview_moveto(1)

def browse_file(entry):
    file_path = filedialog.askopenfilename(filetypes=[("Model files", "*.safetensors *.sft")])
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)
        scroll_entry_to_end(entry)
        update_output_filename()

def browse_output_file(entry):
    file_path = filedialog.asksaveasfilename(defaultextension=".gguf", 
                                             filetypes=[("GGUF files", "*.gguf")])
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)
        scroll_entry_to_end(entry)

def update_output_filename(*args):
    input_file = input_entry.get()
    quantize_level = quantize_level_var.get()
    if input_file:
        input_dir = os.path.dirname(input_file)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(input_dir, f"{base_name}-{quantize_level}.gguf")
        if '/' in input_file:
            output_file = output_file.replace('\\', '/')
        elif '\\' in input_file:
            output_file = output_file.replace('/', '\\')
        output_entry.delete(0, tk.END)
        output_entry.insert(0, output_file)
        scroll_entry_to_end(output_entry)

def disable_ui():
    input_entry.config(state='disabled')
    output_entry.config(state='disabled')
    input_browse.config(state='disabled')
    output_browse.config(state='disabled')
    quantize_dropdown.config(state='disabled')
    run_button.config(state='disabled')

def enable_ui():
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

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen(["python", convert_py_path, "--src", input_file, "--dst", temp_gguf_file], 
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

def setup_environment():
    process_text.insert(tk.END, "Checking environment...\n")
    root.update()

    # Check for GitPython
    try:
        from git import Repo
        process_text.insert(tk.END, "GitPython is already installed.\n")
    except ImportError:
        process_text.insert(tk.END, "Installing GitPython...\n")
        root.update()
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "GitPython"])
            process_text.insert(tk.END, "Successfully installed GitPython.\n")
        except subprocess.CalledProcessError as e:
            process_text.insert(tk.END, f"Error installing GitPython: {e}\n")
            return False

    # List of other required packages
    required_packages = ['torch', 'tqdm', 'safetensors']

    for package in required_packages:
        try:
            __import__(package)
            process_text.insert(tk.END, f"{package} is already installed.\n")
        except ImportError:
            process_text.insert(tk.END, f"Installing {package}...\n")
            root.update()
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                process_text.insert(tk.END, f"Successfully installed {package}.\n")
            except subprocess.CalledProcessError as e:
                process_text.insert(tk.END, f"Error installing {package}: {e}\n")
                return False

    # Check if gguf-py is installed
    gguf_installed = False
    try:
        __import__('gguf')
        process_text.insert(tk.END, "gguf-py is already installed.\n")
        gguf_installed = True
    except ImportError:
        pass

    if not gguf_installed:
        # Clone llama.cpp repository only if gguf-py is not installed
        if not os.path.exists("llama.cpp"):
            try:
                Repo.clone_from("https://github.com/ggerganov/llama.cpp", "llama.cpp")
                process_text.insert(tk.END, "Successfully cloned llama.cpp repository.\n")
            except Exception as e:
                process_text.insert(tk.END, f"Error cloning repository: {e}\n")
                return False

        # Install gguf-py
        process_text.insert(tk.END, "Installing gguf-py...\n")
        root.update()
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "llama.cpp/gguf-py"])
            process_text.insert(tk.END, "Successfully installed gguf-py.\n")
        except subprocess.CalledProcessError as e:
            process_text.insert(tk.END, f"Error installing gguf-py: {e}\n")
            return False

    process_text.insert(tk.END, "Environment check completed. All dependencies are in place.\n")
    root.update()
    return True

root = tk.Tk()
root.title("Easy Quantization GUI")
root.geometry("800x600")  # Enlarge the main window

# Quantize level selection
quantize_frame = tk.Frame(root)
quantize_frame.pack(pady=10, padx=10)

quantize_label = tk.Label(quantize_frame, text="Quantize Level:")
quantize_label.pack(side=tk.LEFT)

quantize_levels = ["Q2_K", "Q3_K_S", "Q4_0", "Q4_1", "Q4_K_S", "Q5_0", "Q5_1", "Q5_K_S", "Q6_K", "Q8_0"]
quantize_level_var = tk.StringVar(root)
quantize_level_var.set("Q8_0")  # Set default value to Q8_0

quantize_dropdown = ttk.Combobox(quantize_frame, textvariable=quantize_level_var, values=quantize_levels, state="readonly")
quantize_dropdown.pack(side=tk.LEFT)
quantize_dropdown.bind("<<ComboboxSelected>>", lambda event: scroll_entry_to_end(output_entry))

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

# Setup environment before creating other UI elements
if not setup_environment():
    messagebox.showerror("Setup Error", "Failed to set up the environment. Please check the process log for details.")
    root.quit()

# Bind events to update output filename
input_entry.bind("<KeyRelease>", update_output_filename)
quantize_level_var.trace_add("write", update_output_filename)

def on_window_resize(event):
    scroll_entry_to_end(input_entry)
    scroll_entry_to_end(output_entry)

root.bind("<Configure>", on_window_resize)

root.mainloop()
