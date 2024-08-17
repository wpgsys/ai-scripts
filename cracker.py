import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import platform
import pycuda.driver as cuda
import pycuda.autoinit
import hashlib

class HashCrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hash Cracker")
        self.root.geometry("700x600")
        self.setup_styles()
        self.create_widgets()
        self.check_gpu_availability()

    def setup_styles(self):
        # Define flat UI green color scheme
        self.bg_color = "#2ecc71"  # Flat UI Green
        self.accent_color = "#27ae60"  # Darker green for accents
        self.text_color = "#ffffff"  # White for text
        self.button_color = "#1e8449"  # Slightly darker green for buttons
        self.button_hover_color = "#16a085"  # Hover color for buttons

        # Set the theme colors
        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.configure('TButton',
                             background=self.button_color,
                             foreground=self.text_color,
                             padding=6,
                             relief='flat',
                             borderwidth=0)
        self.style.map('TButton',
                       background=[('active', self.button_hover_color)])
        self.style.configure('TLabel', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TEntry', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TCombobox', background=self.bg_color, foreground=self.text_color)
        self.style.configure('TNotebook', background=self.bg_color, tabmargins=[0, 0, 0, 0])
        self.style.configure('TNotebook.Tab', background=self.accent_color, foreground=self.text_color)
        self.style.map('TNotebook.Tab', background=[('selected', self.bg_color)])

    def create_widgets(self):
        # Create Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Create tabs
        self.input_tab = ttk.Frame(self.notebook)
        self.output_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.input_tab, text='Input')
        self.notebook.add(self.output_tab, text='Output')

        # Input tab widgets
        self.create_input_tab()

        # Output tab widgets
        self.create_output_tab()

    def create_input_tab(self):
        # Hash type selection
        ttk.Label(self.input_tab, text="Hash Type:").pack(pady=5)
        self.hash_type_combobox = ttk.Combobox(self.input_tab, values=[
            'MD5',
            'SHA-1',
            'SHA-256',
            'SHA-512',
            'NTLM',
            'MD4',
            'RIPEMD-160',
            'WHIRLPOOL',
            'Tiger',
            'Skein',
            'BLAKE2',
            'HMAC-SHA1',
            'HMAC-SHA256',
            'HMAC-SHA512',
            'CRC32'
        ])
        self.hash_type_combobox.pack(pady=5)
        self.hash_type_combobox.set('MD5')

        # Hash to crack
        ttk.Label(self.input_tab, text="Hash to Crack:").pack(pady=5)
        self.hash_entry = ttk.Entry(self.input_tab, width=50)
        self.hash_entry.pack(pady=5)

        # Charset selection
        ttk.Label(self.input_tab, text="Charset:").pack(pady=5)
        self.charset_combobox = ttk.Combobox(self.input_tab, values=[
            'abcdefghijklmnopqrstuvwxyz',
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            '0123456789',
            '0123456789abcdefghijklmnopqrstuvwxyz',
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()',
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()[]{}|;:,.<>?/',
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=~`',
            '0123456789abcdef',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_',
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|;:,.<>?',
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|;:,.<>?/',
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '一二三四五六七八九十百千万',
            '你我他她他它',
            'абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
            'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
        ])
        self.charset_combobox.pack(pady=5)
        self.charset_combobox.set('abcdefghijklmnopqrstuvwxyz')

        # Max length
        ttk.Label(self.input_tab, text="Max Length:").pack(pady=5)
        self.max_length_entry = ttk.Entry(self.input_tab, width=50)
        self.max_length_entry.pack(pady=5)

        # Start button
        self.start_button = ttk.Button(self.input_tab, text="Start Cracking", command=self.start_cracking)
        self.start_button.pack(pady=20)

        # Result text area
        ttk.Label(self.input_tab, text="Result:").pack(pady=5)
        self.result_text = tk.Text(self.input_tab, height=5, width=60)
        self.result_text.pack(pady=5)

    def create_output_tab(self):
        # Output text area
        self.output_text = tk.Text(self.output_tab, height=15, width=80)
        self.output_text.pack(expand=True, fill='both', pady=5, padx=5)

    def check_gpu_availability(self):
        try:
            cuda.Device(0)  # Check if there's an available GPU
            self.use_gpu = True
            self.output_text.insert(tk.END, "GPU is available and will be used for cracking.\n")
        except cuda.Error:
            self.use_gpu = False
            self.output_text.insert(tk.END, "GPU not available. Falling back to CPU.\n")

    def start_cracking(self):
        hash_value = self.hash_entry.get()
        hash_type = self.hash_type_combobox.get()
        charset = self.charset_combobox.get()
        max_length = self.max_length_entry.get()

        self.output_text.insert(tk.END, f"Started cracking hash: {hash_value}\nHash Type: {hash_type}\nCharset: {charset}\nMax Length: {max_length}\n\n")

        # Placeholder for cracking function
        # Example:
        try:
            if self.use_gpu:
                # Call your GPU hash cracking function here
                result = self.crack_hash_with_gpu(hash_value, hash_type, charset, max_length)
            else:
                # Call your CPU hash cracking function here
                result = self.crack_hash_with_cpu(hash_value, hash_type, charset, max_length)
            self.output_text.insert(tk.END, f"Result: {result}\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {str(e)}\n")

    def crack_hash_with_gpu(self, hash_value, hash_type, charset, max_length):
        # GPU hash cracking logic here
        return "GPU-based hash cracking not implemented."

    def crack_hash_with_cpu(self, hash_value, hash_type, charset, max_length):
        # CPU hash cracking logic here
        return "CPU-based hash cracking not implemented."

if __name__ == "__main__":
    root = tk.Tk()
    app = HashCrackerApp(root)
    root.mainloop()
