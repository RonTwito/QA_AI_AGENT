import tkinter as tk
from tkinter import filedialog, scrolledtext
import requests
import os

# === LOAD API KEY ===
def load_api_key(filename="API_KEY_CLASSIFIED.txt"):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except Exception as e:
        raise RuntimeError(f"Failed to load API key from {filename}: {e}")

API_KEY = load_api_key()

# === APP STATE ===
app_state = {
    "file_path": None,
    "methods": {}
}

# === GUI CALLBACKS ===
def browse_file():
    file_path = filedialog.askopenfilename(
    filetypes=[
        ("All Files", "*.*"),
        ("Java Files", "*.java"),
        ("Python Files", "*.py"),
        ("C++ Files", "*.cpp"),
        ("Text Files", "*.txt")
    ]
)
    if file_path:
        filename = os.path.basename(file_path)
        file_label.config(text=f"Selected File: {filename}")
        app_state["file_path"] = file_path
        show_method_inputs(file_path)

def show_method_inputs(file_path):
    for widget in method_input_frame.winfo_children():
        widget.destroy()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        show_response(f"Error reading file: {e}")
        return

    methods = extract_method_names(code)
    app_state["methods"] = {}

    for name in methods:
        label = tk.Label(method_input_frame, text=f"{name} requirement:")
        label.pack()
        entry = tk.Entry(method_input_frame, width=80)
        entry.pack(pady=2)
        app_state["methods"][name] = entry


def extract_method_names(code):
    import re
    method_names = set()

    # Python methods
    python_methods = re.findall(r'^\s*def\s+(\w+)\s*\(', code, re.MULTILINE)
    method_names.update(python_methods)

    # Java/C#/C++ style methods with return type
    cpp_like_methods = re.findall(
        r'^\s*(?:public|private|protected)?\s*(?:static\s+)?[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{',
        code,
        re.MULTILINE
    )
    method_names.update(cpp_like_methods)

    # JavaScript named functions
    js_functions = re.findall(r'\bfunction\s+(\w+)\s*\(', code)
    method_names.update(js_functions)

    # JavaScript/TypeScript arrow functions
    arrow_functions = re.findall(r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>', code)
    method_names.update(arrow_functions)

    # JavaScript/TypeScript class or object methods (excluding control keywords)
    js_class_methods = re.findall(
        r'^\s*(?!if|for|while|switch|catch|else)([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{',
        code,
        re.MULTILINE
    )
    method_names.update(js_class_methods)

    return sorted(method_names)



def run_sessions():
    clear_response()
    file_path = app_state.get("file_path")
    if not file_path or not os.path.exists(file_path):
        show_response("Error: No valid file selected.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read().strip()
    except Exception as e:
        show_response(f"Error reading file: {e}")
        return

    requirement_section = "\n".join([
        f"- {name}: {entry.get().strip()}" for name, entry in app_state["methods"].items() if entry.get().strip()
    ])

    full_prompt = (
        "You are a code fixer bot. Your task is to check the given code against the method requirements.\n"
        "Return ONLY the full corrected code without ANY explanations, comments, or text.\n"
        "If the code already meets the requirements, return it EXACTLY as given.\n"
        "Do NOT include markdown formatting (no ```), no explanations, no comments, only code.\n\n"
        "=== Code ===\n"
        f"{code}\n\n"
        "=== Requirements ===\n"
        f"{requirement_section}\n\n"
        "Return only the corrected or original code as plain text."
    )

    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
            "messages": [
                {"role": "user", "content": full_prompt}
            ]
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()
        show_response(reply)

        if reply != code:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(reply)
            except Exception as e:
                show_response(f"\n\nError writing to file: {e}")

    except Exception as e:
        show_response(f"API Error: {e}")

def show_response(text):
    response_text.config(state='normal')
    response_text.delete('1.0', tk.END)
    response_text.insert(tk.END, text)
    response_text.config(state='disabled')

def clear_response():
    response_text.config(state='normal')
    response_text.delete('1.0', tk.END)
    response_text.config(state='disabled')

# === GUI SETUP ===
root = tk.Tk()
root.title("AI QA Code Checker")
root.geometry("700x700")

browse_button = tk.Button(root, text="Browse File", command=browse_file)
browse_button.pack(pady=(10, 5))

file_label = tk.Label(root, text="Selected File: None", fg="blue")
file_label.pack()

method_input_frame = tk.Frame(root)
method_input_frame.pack(pady=10)

run_button = tk.Button(root, text="Run QA", command=run_sessions)
run_button.pack(pady=10)

response_label = tk.Label(root, text="AI Response")
response_label.pack()

response_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15)
response_text.pack(fill='both', expand=True, padx=10, pady=10)
response_text.config(state='disabled')

root.mainloop()
