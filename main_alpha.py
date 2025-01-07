import csv
import tkinter as tk
from tkinter import Tk, filedialog

import requests


class JishoApp:
    def __init__(self, root: Tk):
        self.root = root
        self.title = "Jisho Auto Scraper 9000"
        self.geometry = self.root.geometry("900x500")
        self.word_frame = tk.Frame(root)
        self.word_frame.pack(fill='both', expand=True, pady=20)
        self.word_list = []
        self.saved_data = {}

        self.show_file_upload_screen()

    def show_file_upload_screen(self):
        tk.Button(self.word_frame, text="Browse",
                  command=self.open_file).pack()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a Text File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, 'r', encoding="utf-8") as file:
                # Save words to a global list
                self.word_list.extend(file.read().splitlines())
            self.show_candidates(0)  # Move to the first word's screen

    def show_candidates(self, index):
        self.word_frame.destroy()
        self.word_frame = tk.Frame(self.root)
        self.word_frame.pack(fill="both", expand=True, pady=20)
        if index < len(self.word_list):
            word = self.word_list[index]
            tk.Label(self.word_frame, text=f"Word {
                index+1}/{len(self.word_list)}: {word}").pack(pady=10)
            url = f'https://jisho.org/api/v1/search/words?keyword={word}'
            response = requests.get(url)
            if response.status_code != 200:
                return f'Error: {response.status_code}'

            data = response.json().get('data')
            if len(data) > 1:
                for candidate in data:
                    tk.Button(
                        self.word_frame,
                        text=candidate.get("japanese"),
                        command=lambda candidate=candidate:
                        self.show_reading_variations(candidate, index)).pack()

        else:
            self.show_summary_screen()  # Move to summary when all words are processed

    def show_reading_variations(self, selected_word_data, index):
        self.word_frame.destroy()
        self.word_frame = tk.Frame(self.root)
        self.word_frame.pack(fill="both", expand=True, pady=20)

        word = selected_word_data.get('japanese')
        tk.Label(self.word_frame, text=f"Word {
            index+1}/{len(self.word_list)}: {word}").pack(pady=10)

        if len(word) > 1:
            for variant in word:
                for kanji in variant.get('word'):
                    var = tk.BooleanVar()
                    checkbox = tk.Checkbutton(
                        self.word_frame, text=kanji, variable=var)
                for kana in variant.get('reading'):
                    checkbox = tk.Checkbutton(
                        self.word_frame, text=kana, variable=var)
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
                    self.word_frame, text=definition, variable=var)
                checkbox.pack(anchor="w")
                selected_defs.append(var)

            # Navigation buttons
            def next_word():
                self.save_selections(word, selected_defs, definitions)
                self.show_candidates(index + 1)

            tk.Button(self.word_frame, text="Next",
                      command=next_word).pack(pady=10)

    def show_summary_screen(self):
        self.word_frame.destroy()
        summary_frame = tk.Frame(self.root)
        summary_frame.pack(fill="both", expand=True, pady=20)

        tk.Label(summary_frame, text="Processing Complete!").pack(pady=10)
        tk.Label(summary_frame, text="Ready to generate CSV.").pack(pady=10)

        def generate_csv():
            with open("output.csv", "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Word", "Selected Definitions"])
                for word, defs in self.saved_data.items():
                    writer.writerow([word, ", ".join(defs)])
            tk.Label(summary_frame, text="CSV Generated: output.csv").pack(
                pady=10)

        tk.Button(summary_frame, text="Generate CSV",
                  command=generate_csv).pack(pady=10)

    def save_selections(self, word, selected_defs, definitions):
        self.saved_data[word] = [definition for var, definition in zip(
            selected_defs, definitions) if var.get()]


root = Tk()
app = JishoApp(root)
root.mainloop()
