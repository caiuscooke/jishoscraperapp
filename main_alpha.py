import csv
import tkinter as tk
from tkinter import Checkbutton, Tk, filedialog
from tkinter import font

import requests


class JishoApp:
    def __init__(self, root: Tk):
        self.root = root
        self.title = "Jisho Auto Scraper 9000"
        self.word_frame = tk.Frame(root)
        self.word_frame.pack(fill='both', expand=True, pady=20)
        self.word_list = []
        self.saved_data = {}

        self.root.geometry("1400x1000")
        self.show_file_upload_screen()

        self.defaultFont = font.nametofont("TkDefaultFont")
        self.defaultFont.configure(family="Microsoft Sans Serif",
                                   size=12,
                                   weight=font.NORMAL)

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
            self.show_possible_matches(0)  # Move to the first word's screen

    def grid_setup(self):
        self.word_frame.destroy()
        self.word_frame = tk.Frame(self.root)
        self.word_frame.pack(fill='both', expand=True)
        self.word_frame.columnconfigure((0, 2), weight=1, uniform='a')
        self.word_frame.columnconfigure(1, weight=3, uniform='a')
        self.word_frame.rowconfigure((0, 2), weight=1, uniform='a')
        self.word_frame.rowconfigure(1, weight=3, uniform='a')

    def header_setup(self, word, index):
        header = tk.Label(self.word_frame, text=(
            'Word'
            + f'{index+1}/{len(self.word_list)}: {word}')
        )
        header.grid(row=0, column=1)

    def create_scrollable_canvas(self):
        # Create a canvas
        canvas = tk.Canvas(self.word_frame)
        canvas.grid(row=1, column=1, sticky="nsew", padx=15, pady=15)
        canvas.columnconfigure((0, 1), weight=1, uniform='a')
        canvas.columnconfigure(2, weight=3, uniform='a')
        # Add a vertical scrollbar linked to the canvas
        scrollbar = tk.Scrollbar(
            self.word_frame, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=1, column=2, sticky="nsw")
        canvas.configure(yscrollcommand=scrollbar.set)
        return canvas

    def show_possible_matches(self, index):
        self.grid_setup()
        if index < len(self.word_list):
            word = self.word_list[index]
            self.header_setup(word, index)
            url = f'https://jisho.org/api/v1/search/words?keyword={word}'
            response = requests.get(url)
            if response.status_code != 200:
                return f'Error: {response.status_code}'

            data = response.json().get('data')

            if len(data) > 1:  # data > 1 means that there is more than 1 result for the requested word
                candidates = []
                for possible_match in data:
                    reading_variations = possible_match.get('japanese')
                    for term in reading_variations:
                        kanji = term.get('word')
                        reading = term.get('reading')
                        if kanji == word or reading == word:
                            candidates.append(possible_match)
                            break
                if len(candidates) > 1:
                    canvas = self.create_scrollable_canvas()
                    for ind, candidate in enumerate(candidates):

                        reading_variations = candidate.get('japanese')
                        reading_variations_list = []
                        for variant in reading_variations:
                            kanji = variant.get('word')
                            if kanji:
                                reading_variations_list.append(kanji)
                            kana = variant.get('reading')
                            if kana:
                                reading_variations_list.append(kana)
                        definition_variations = candidate.get('senses')
                        definitions = []
                        for sense in definition_variations:
                            definitions.append(', '.join(
                                sense.get('english_definitions')))

                        if len(reading_variations) > 1:
                            tk.Button(canvas,
                                      text=('Candidate' + f' {ind + 1}'),
                                      command=lambda candidate=candidate:
                                      self.show_reading_variations(
                                          candidate, index)
                                      ).grid(row=1+ind, column=0, sticky='w')
                        elif len(reading_variations) == 1 and len(definition_variations) > 1:
                            tk.Button(canvas,
                                      text=('Candidate' + f' {ind + 1}'),
                                      command=lambda candidate=candidate:
                                      self.show_definitions(
                                          candidate, index)
                                      ).grid(row=1+ind, column=0, sticky='w')
                        elif len(reading_variations) != 0 and len(definition_variations) != 0:
                            tk.Button(canvas,
                                      text=('Candidate' + f' {ind + 1}'),
                                      command=lambda candidate=candidate:
                                      self.save_unique(word, candidate, index)
                                      ).grid(row=1+ind, column=0, sticky='w')

                        tk.Label(
                            canvas,
                            text="|".join(reading_variations_list),
                        ).grid(row=ind+1, column=1, sticky='w')

                        numbered_definitions = [
                            f'{num + 1}) {definition}' for num, definition in enumerate(definitions)]
                        numbered_defs_str = " ".join(numbered_definitions)
                        definitions_label = tk.Label(
                            canvas, text=numbered_defs_str)
                        definitions_label.grid(row=1+ind, column=2, sticky='w')
                elif len(candidates) == 1:
                    self.show_reading_variations(candidates[0], index)

            elif len(data) == 1:
                reading_variations = data[0].get('japanese')
                definitions = data[0].get('senses')
                if len(reading_variations) > 1:
                    self.show_reading_variations(data[0], index)
                elif len(definitions) > 1:
                    self.show_definitions(data[0], index)
                elif len(definitions) != 0 and len(reading_variations) != 0:
                    self.save_unique(word, data[0], index)

            elif len(data) < 1:
                # HANDLE SKIPPED WORDS HERE
                self.show_possible_matches(index+1)

        else:
            self.show_summary_screen()  # Move to summary when all words are processed

    def show_reading_variations(self, selected_word_data, index):
        self.grid_setup()

        word = self.word_list[index]
        self.header_setup(word, index)
        label = tk.Label(self.word_frame, wraplength=300, justify='center',
                         text='Choose the Kanji/Reading variants you would like to save')
        label.grid(row=1, column=0, sticky='nsew')
        label.bind('<Configure>', lambda e: label.config(
            wraplength=label.winfo_width()))
        canvas = self.create_scrollable_canvas()

        variations = selected_word_data.get('japanese')  # LIST OF DICTIONARIES

        selected_variations = []
        for ind, variation in enumerate(variations):
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(
                canvas, text=f'{variation.get('word')} {variation.get('reading')}', variable=var)
            checkbox.grid(row=0+ind, column=0, columnspan=3, sticky='ew')
            selected_variations.append(var)

        def advance_button():
            extracted = self.extract_selections(
                selected_variations, variations)
            self.save_variations(word, extracted)

            if len(definitions) > 1:
                self.show_definitions(selected_word_data, index)
            elif len(definitions) == 1:
                self.save_definitions(self.word_list[index], [
                                      definitions[0].get('english_definitions')])
                self.show_word_summary(word, index)

        definitions = selected_word_data.get('senses')
        tk.Button(self.word_frame, text='Advance',
                  command=advance_button).grid(row=2, column=1)

    def show_definitions(self, candidate, index):
        self.grid_setup()
        canvas = self.create_scrollable_canvas()

        word = self.word_list[index]
        self.header_setup(word, index)

        definitions_list = [definition.get(
            'english_definitions') for definition in candidate.get('senses')]
        selected_definitions = []
        for ind, definition in enumerate(definitions_list):
            var = tk.BooleanVar()
            checkbox = Checkbutton(
                canvas, text=definition, variable=var)
            checkbox.grid(row=ind+1, column=0, columnspan=3, sticky='w')
            selected_definitions.append(var)

        def next_button():
            extracted = self.extract_selections(
                selected_definitions, definitions_list)
            self.save_definitions(word, extracted)
            self.show_word_summary(word, index)

        tk.Button(self.word_frame, text='Next Word',
                  command=next_button).grid(row=2, column=1)

    def csv_column_builder(self, word_info, key_name):
        value = word_info.get(key_name)
        if value:
            if key_name != 'definitions':
                return "・".join(value)
            elif key_name == 'definitions':
                return "<br>".join(value)

    def generate_csv(self):
        with open("output.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            for word_info in self.saved_data.values():
                row = [self.csv_column_builder(word_info, 'kanji'),
                       self.csv_column_builder(word_info, 'kana'),
                       self.csv_column_builder(word_info, 'definitions')]

                writer.writerow(row)
        tk.Label(self.word_frame, text="CSV Generated: output.csv").grid(
            row=2, column=0)

    def show_summary_screen(self):
        self.grid_setup()
        canvas = self.create_scrollable_canvas()

        tk.Label(self.word_frame, text="Processing Complete!").grid(
            row=0, column=0)
        tk.Label(self.word_frame, text="Ready to generate CSV.").grid(
            row=0, column=1)
        counter = 0
        for word, data in self.saved_data.items():
            tk.Label(canvas, text=word).grid(row=0+counter, column=0)
            tk.Label(canvas, text=data).grid(
                row=0+counter, column=1, columnspan=2)
            counter += 1

        tk.Button(self.word_frame, text="Generate CSV",
                  command=self.generate_csv).grid(row=2, column=1)

    def extract_selections(self, vars_list, original_list):
        return [selection for var, selection in zip(vars_list, original_list) if var.get()]

    def save_variations(self, word, terms):
        kanji_selections = []
        kana_selections = []
        for term in terms:
            kanji = term.get('word')
            if kanji:
                kanji_selections.append(kanji)
            kana = term.get('reading')
            if kana:
                kana_selections.append(kana)
        self.saved_data.setdefault(word, {})['kanji'] = kanji_selections
        self.saved_data.setdefault(word, {})['kana'] = kana_selections

    def save_definitions(self, word, terms):
        selected_defs_list = [
            f'{ind+1}) {", ".join(definition)}' for ind, definition in enumerate(terms)]
        self.saved_data.setdefault(
            word, {})["definitions"] = selected_defs_list

    def save_unique(self, word, candidate, index):
        term = candidate.get('japanese')
        self.save_variations(word, term)

        definitions = [candidate.get(
            'senses')[0].get('english_definitions')]
        self.save_definitions(word, definitions)
        self.show_word_summary(word, index)

    def show_word_summary(self, word, index):
        self.grid_setup()
        tk.Label(self.word_frame, text='Review word before continuing').grid(
            row=0, column=1)
        canvas = self.create_scrollable_canvas()
        word_summary = self.saved_data.get(word)
        for row, each in enumerate(word_summary):
            canvas.rowconfigure(row+1, weight=1, uniform='a')
            tk.Label(canvas, text=each).grid(row=row, column=0, sticky='e')
            text_box = tk.Text(canvas, wrap='word', height=4, width=50)
            text_box.grid(row=row, column=1, columnspan=2)
            text_box.insert("1.0", word_summary.get(each))

        canvas.config(scrollregion=canvas.bbox("all"))
        tk.Button(self.word_frame, text='Next Word',
                  command=lambda: self.show_possible_matches(index+1)).grid(row=2, column=1)


root = Tk()
app = JishoApp(root)
root.mainloop()
