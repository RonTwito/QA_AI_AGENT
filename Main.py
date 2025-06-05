import tkinter as tk
from tkinter import filedialog, scrolledtext
import requests  # Use requests for OpenRouter API
  # For DeepSeek-compatible SDK
import os

# === SETUP YOUR CLIENT HERE ===
# === SETUP ===
def load_api_key(filename="API_KEY_CLASSIFIED.txt"):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except Exception as e:
        raise RuntimeError(f"Failed to load API key from {filename}: {e}")

API_KEY = load_api_key()
  # Use your actual OpenRouter key here or from env

# === APP STATE ===
app_state = {
    "file_path": None
}

# === GUI CALLBACKS ===
def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Code/Text Files", "*.java *.txt")])
    if file_path:
        filename = os.path.basename(file_path)
        file_label.config(text=f"Selected File: {filename}")
        app_state["file_path"] = file_path

def run_sessions():
    clear_response()

    file_path = app_state.get("file_path")
    explanation = input_output_entry.get().strip()

    if not file_path or not os.path.exists(file_path):
        show_response("Error: No valid file selected.")
        return

    if not explanation:
        show_response("Error: Please enter a description in 'Desired INPUT/OUTPUT'.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            method_code = f.read().strip()
    except Exception as e:
        show_response(f"Error reading file: {e}")
        return

    prompt = (
        f"QA this Java function strictly:\n"
        f"Function: {method_code}\n"
        f"Requirement: {explanation}\n"
        f"If correct, respond with exactly: congrats - and skip the following inccorect part\n"
        f"If incorrect, return only the fixed Java function code.\n"
        f"No explanation. No repetition. One line of code only. Respond strictly."
    )

    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()
        show_response(reply)

        # === NEW LOGIC HERE ===
        if reply.lower() != "congrats":
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(reply)
            except Exception as e:
                show_response(f"\n\nError writing to file: {e}")

    except Exception as e:
        show_response(f"API Error: {e}")


def show_response(text):
    response_text.config(state='normal')
    response_text.insert(tk.END, text)
    response_text.config(state='disabled')

def clear_response():
    response_text.config(state='normal')
    response_text.delete('1.0', tk.END)
    response_text.config(state='disabled')

# === GUI SETUP ===
root = tk.Tk()
root.title("AI QA Code Checker")
root.geometry("600x520")
root.resizable(False, False)

# File Browser
browse_button = tk.Button(root, text="Browse File", command=browse_file)
browse_button.pack(pady=(10, 5))

file_label = tk.Label(root, text="Selected File: None", fg="blue")
file_label.pack()

# Input/Output Explanation
input_output_label = tk.Label(root, text="Desired INPUT/OUTPUT")
input_output_label.pack(pady=(20, 0))

input_output_entry = tk.Entry(root, width=80)
input_output_entry.pack(pady=5)

# AI Response Section
response_label = tk.Label(root, text="AI RESPONSE CODE")
response_label.pack(pady=(20, 5))

response_frame = tk.Frame(root)
response_frame.pack(expand=True, fill='both', padx=10, pady=5)

response_text = scrolledtext.ScrolledText(response_frame, wrap=tk.WORD, height=10)
response_text.pack(fill='both', expand=True)
response_text.config(state='disabled')

# Run Button
run_button = tk.Button(root, text="Run Sessions", command=run_sessions)
run_button.pack(pady=10)

# Start App
root.mainloop()
