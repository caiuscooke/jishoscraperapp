import tkinter as tk
from tkinter import filedialog
import csv
import requests

root = tk.Tk()
root.title("Jisho Auto Scraper 0.0.1")
root.geometry("900x500")

word_list = []  # Store words from the uploaded file
saved_data = {}  # Store user selections
word_frame = tk.Frame(root)
word_frame.pack(fill="both", expand=True, pady=20)


def save_selections(word, selected_defs, definitions):
    saved_data[word] = [definition for var, definition in zip(
        selected_defs, definitions) if var.get()]


def show_summary_screen():
    word_frame.destroy()
    summary_frame = tk.Frame(root)
    summary_frame.pack(fill="both", expand=True, pady=20)

    tk.Label(summary_frame, text="Processing Complete!").pack(pady=10)
    tk.Label(summary_frame, text="Ready to generate CSV.").pack(pady=10)

    def generate_csv():
        with open("output.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Word", "Selected Definitions"])
            for word, defs in saved_data.items():
                writer.writerow([word, ", ".join(defs)])
        tk.Label(summary_frame, text="CSV Generated: output.csv").pack(pady=10)

    tk.Button(summary_frame, text="Generate CSV",
              command=generate_csv).pack(pady=10)


def validate_data(data):
    japanese = data.get('japanese')
    for each in japanese:
        if each.get('reading') is None:
            return False
    return True


def show_reading_variations(selected_word_data, index):
    word_frame.destroy()
    word_frame = tk.Frame(root)
    word_frame.pack(fill="both", expand=True, pady=20)

    word = selected_word_data.get('japanese')
    tk.Label(word_frame, text=f"Word {
        index+1}/{len(word_list)}: {word}").pack(pady=10)

    if len(word) > 1:
        for variant in word:
            for kanji in variant.get('word'):
                var = tk.BooleanVar()
                checkbox = tk.Checkbutton(word_frame, text=kanji, variable=var)
            for kana in variant.get('reading'):
                checkbox = tk.Checkbutton(word_frame, text=kana, variable=var)
    elif len(word) == 1:
        word = selected_word_data.get('japanese')[0].get('word')
        senses = selected_word_data.get("senses")
        definitions = [", ".join(sense.get("english_definitions"))
                       for sense in senses]

        # Create checkboxes for each definition
        selected_defs = []
        for definition in definitions:
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(
                word_frame, text=definition, variable=var)
            checkbox.pack(anchor="w")
            selected_defs.append(var)

        # Navigation buttons
        def next_word():
            save_selections(word, selected_defs, definitions)
            show_candidates(index + 1)

        tk.Button(word_frame, text="Next", command=next_word).pack(pady=10)


def show_candidates(index):

    word_frame.destroy()
    word_frame = tk.Frame(root)
    word_frame.pack(fill="both", expand=True, pady=20)
    if index < len(word_list):
        word = word_list[index]
        tk.Label(word_frame, text=f"Word {
                 index+1}/{len(word_list)}: {word}").pack(pady=10)
        url = f'https://jisho.org/api/v1/search/words?keyword={word}'
        response = requests.get(url)
        if response.status_code != 200:
            return f'Error: {response.status_code}'

        data = response.json().get('data')
        if len(data) > 1:
            for candidate in data:
                tk.Button(
                    word_frame,
                    text=candidate.get("japanese"),
                    command=lambda candidate=candidate:
                    show_reading_variations(candidate, index)).pack()

    else:
        show_summary_screen()  # Move to summary when all words are processed


def open_file():
    file_path = filedialog.askopenfilename(
        title="Select a Text File",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        with open(file_path, 'r', encoding="utf-8") as file:
            # Save words to a global list
            word_list.extend(file.read().splitlines())
        show_candidates(0)  # Move to the first word's screen


def show_file_upload_screen():
    tk.Button(word_frame, text="Browse", command=open_file).pack()


show_file_upload_screen()
root.mainloop()
