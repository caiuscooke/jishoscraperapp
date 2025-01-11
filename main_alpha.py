import csv
import tkinter as tk
from tkinter import FLAT, filedialog

import requests
from customtkinter import (CTkCheckBox, CTk, CTkButton, CTkFont, CTkFrame,
                           CTkLabel, CTkScrollableFrame, CTkTextbox)


class JishoApp:
    def __init__(self, root: CTk):
        self.root = root
        self.root.title('J2A')
        self.word_frame = CTkFrame(root)
        self.word_frame.pack(fill='both', expand=True, pady=20)
        self.word_list = []
        self.saved_data = {}

        self.root.geometry("900x500")

        self.defaultFont = CTkFont(
            'Microsoft Sans Serif', size=16, weight='normal')
        self.show_file_upload_screen()

    def show_file_upload_screen(self):
        self.grid_setup()
        CTkLabel(self.word_frame,
                 text='Welcome to J2A!\nBrowse to upload a txt file to get started',
                 font=self.defaultFont).grid(row=0, column=1, sticky='s')
        CTkButton(self.word_frame, text="Browse",
                  command=self.open_file, font=self.defaultFont).grid(row=1, column=1)

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a Text File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, 'r', encoding="utf-8") as file:
                self.word_list.extend(file.read().splitlines())
            self.show_possible_matches(0)

    def grid_setup(self):
        self.word_frame.destroy()
        self.word_frame = CTkFrame(self.root)
        self.word_frame.pack(fill='both', expand=True)
        self.word_frame.columnconfigure((0, 2), weight=1, uniform='a')
        self.word_frame.columnconfigure(1, weight=8, uniform='a')
        self.word_frame.rowconfigure((0, 2), weight=1, uniform='a')
        self.word_frame.rowconfigure(1, weight=8, uniform='a')

    def header_setup(self, word, index):
        header = CTkLabel(self.word_frame, text=(
            'Word'
            + f'{index+1}/{len(self.word_list)}: {word}'),
            font=self.defaultFont
        )
        header.grid(row=0, column=1, sticky='nsew')

    def create_scrollable_frame(self):
        scrollable_frame = CTkScrollableFrame(
            self.word_frame, corner_radius=4, border_width=.2, border_color='lightgrey')
        scrollable_frame.grid(row=1, column=1, sticky='nsew',)
        scrollable_frame.columnconfigure(
            [i for i in range(10)], weight=1, uniform='a')

        return scrollable_frame

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
                    scrollframe = self.create_scrollable_frame()
                    scrollframe.configure(
                        label_text='Choose which of the following matches you want to add')
                    for ind, candidate in enumerate(candidates):
                        reading_variations = candidate.get('japanese')
                        reading_variations_list = []
                        for variant in reading_variations:
                            kanji = variant.get('word')
                            kana = variant.get('reading')
                            if kanji and kana:
                                reading_variations_list.append(
                                    f'{kanji}|{kana}')

                        definition_variations = candidate.get('senses')
                        definitions = []
                        for sense in definition_variations:
                            definitions.append(', '.join(
                                sense.get('english_definitions')))

                        if len(reading_variations) > 1:
                            CTkButton(scrollframe,
                                      text=('Candidate' + f' {ind + 1}'),
                                      command=lambda candidate=candidate:
                                      self.show_reading_variations(
                                          candidate, index), font=self.defaultFont
                                      ).grid(row=ind, column=0, columnspan=3, padx=10, pady=10)
                        elif len(reading_variations) == 1 and len(definition_variations) > 1:
                            CTkButton(scrollframe,
                                      text=('Candidate' + f' {ind + 1}'),
                                      command=lambda candidate=candidate:
                                      self.show_definitions(
                                          candidate, index), font=self.defaultFont
                                      ).grid(row=ind, column=0, columnspan=3, padx=10, pady=10)
                        elif len(reading_variations) != 0 and len(definition_variations) != 0:
                            CTkButton(scrollframe,
                                      text=('Candidate' + f' {ind + 1}'),
                                      command=lambda candidate=candidate:
                                      self.save_unique(word, candidate, index), font=self.defaultFont
                                      ).grid(row=ind, column=0, columnspan=3, padx=10, pady=10)

                        label = CTkLabel(
                            scrollframe,
                            wraplength=200,
                            text="\n".join(reading_variations_list), font=self.defaultFont,
                            anchor='w'
                        )
                        label.grid(row=ind, column=3,  columnspan=3,
                                   sticky='nsew', padx=10, pady=10)

                        numbered_definitions = [
                            f'{num + 1}) {definition}' for num, definition in enumerate(definitions)]
                        numbered_defs_str = " ".join(numbered_definitions)

                        definitions_label = CTkLabel(
                            scrollframe, text=numbered_defs_str, font=self.defaultFont,
                            anchor='w')
                        definitions_label.grid(
                            row=ind, column=6, columnspan=3, sticky='nsew', padx=10, pady=10)
                elif len(candidates) == 1:
                    readings = candidates[0].get('japanese')
                    definitions = candidates[0].get('senses')
                    if len(readings) > 1:
                        self.show_reading_variations(candidates[0], index)
                    elif len(definitions) > 1:
                        self.save_variations(word, readings)
                        self.show_definitions(candidates[0], index)
                    else:
                        self.save_unique(word, candidates[0], index)
                else:
                    scrollframe = self.create_scrollable_frame()
                    scrollframe.columnconfigure(
                        (0, 1, 2), weight='1', uniform='a')
                    scrollframe.configure(
                        label_text='Choose the word you want to add')
                    for row, possible_match in enumerate(data):
                        result = possible_match.get('slug')
                        CTkButton(
                            scrollframe, text=result,
                            command=lambda result=result: change_search(
                                result),
                            font=self.defaultFont
                        ).grid(row=row, column=4, columnspan=2, padx=10, pady=10)

                    def change_search(word):
                        self.word_list[index] = word
                        self.show_possible_matches(index)

            elif len(data) == 1:
                reading_variations = data[0].get('japanese')
                definitions = data[0].get('senses')
                if len(reading_variations) > 1:
                    self.show_reading_variations(data[0], index)
                elif len(definitions) > 1:
                    self.save_variations(word, reading_variations)
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
        scrollframe = self.create_scrollable_frame()
        scrollframe.configure(
            label_text='Choose the reading variant you would like to add')

        variations = selected_word_data.get('japanese')  # LIST OF DICTIONARIES

        selected_variations = []
        for ind, variation in enumerate(variations):
            var = tk.BooleanVar()
            kanji = variation.get('word')
            kana = variation.get('reading')
            text = f'{kanji} {kana}'
            slug = selected_word_data.get('slug')
            if kanji == slug or kana == slug:
                text += ' (main reading)'
            checkbox = CTkCheckBox(
                scrollframe, text=text,
                variable=var)
            checkbox.grid(row=ind, column=3, columnspan=6,
                          padx=10, pady=10, sticky='nsew')
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
                self.extract_pos(definitions[0].get('parts_of_speech'), word)
                self.extract_notes(word, selected_word_data)
                self.show_word_summary(word, index)

        definitions = selected_word_data.get('senses')
        CTkButton(self.word_frame, text='Next',
                  command=advance_button, font=self.defaultFont).grid(row=2, column=1)

    def show_definitions(self, candidate, index):
        self.grid_setup()
        scrollframe = self.create_scrollable_frame()

        word = self.word_list[index]
        self.header_setup(word, index)

        senses = candidate.get('senses')

        definitions_list = [definition.get(
            'english_definitions') for definition in senses]
        part_of_speech = [definition.get('parts_of_speech')
                          for definition in senses]

        for sense_num, sense in enumerate(senses):
            if sense.get('info'):
                definitions_list[sense_num] += sense.get('info')
            if sense.get('tags'):
                definitions_list[sense_num] += sense.get('tags')

        selected_definitions = []

        for ind, definition in enumerate(definitions_list):

            formatted_def = f'{
                ind+1}) {", ".join(definition)} {part_of_speech[ind]}'

            var = tk.BooleanVar()
            checkbox = CTkCheckBox(scrollframe,
                                   text=None, variable=var)
            checkbox.grid(row=ind, column=1, sticky='e',
                          padx=(10, 0), pady=10)

            text_box = CTkTextbox(
                scrollframe, height=80, wrap='word',
                font=self.defaultFont, border_spacing=0)
            text_box.grid(row=ind, column=2, columnspan=7,
                          pady=10, sticky='nsew')
            text_box.insert('0.0', formatted_def)

            selected_definitions.append(var)

        def next_button():
            extracted = self.extract_selections(
                selected_definitions, definitions_list, word, part_of_speech)
            self.save_definitions(word, extracted)
            self.extract_notes(key=word, word_data=candidate)
            self.show_word_summary(word, index)

        CTkButton(self.word_frame, text='Confirmation Screen',
                  command=next_button, font=self.defaultFont).grid(row=2, column=1)

    def extract_selections(self, vars_list, original_list, word_key=None, parts=None):
        if parts is not None:
            parts_of_speech_2d = [part for var, part in zip(
                vars_list, parts) if var.get()]
            parts_of_speech = []
            for _list in parts_of_speech_2d:
                for _string in _list:
                    parts_of_speech.append(_string)
            self.extract_pos(list(set(parts_of_speech)), word_key)
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
        self.saved_data.setdefault(
            word, {})['kanji'] = list(set(kanji_selections))
        self.saved_data.setdefault(
            word, {})['kana'] = list(set(kana_selections))

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
        self.extract_pos(candidate.get('senses')[
                         0].get('parts_of_speech'), word)
        self.extract_notes(word, candidate)
        self.show_word_summary(word, index)

    def extract_pos(self, parts_of_speech, word_key):
        parts_list = []
        for part in parts_of_speech:
            if part == "Noun":
                parts_list.append("名")
            elif part == "Suru verb":
                parts_list.append("スル")
            elif part == "Intransitive verb":
                parts_list.append("自動詞")
            elif part == "Transitive verb":
                parts_list.append("他動詞")
            elif part == "Na-adjective (keiyodoshi)":
                parts_list.append("形容動")
            elif part == "I-adjective (keiyoushi)":
                parts_list.append("形容")
            elif part == "Adverb (fukushi)":
                parts_list.append("副詞")
            elif part == "Adverb taking the 'to' particle":
                parts_list.append("と副詞")
            elif part == "Noun which may take the genitive case particle 'no'":
                parts_list.append("の名")
            elif "Expressions" in part:
                parts_list.append("文")
        self.saved_data.setdefault(word_key, {})[
            'parts_of_speech'] = parts_list

    def extract_notes(self, key, word_data):
        jlpt_level = word_data.get('jlpt')
        if jlpt_level:
            jlpt_level = jlpt_level[0]
            self.saved_data.setdefault(key, {})['jlpt'] = [jlpt_level]
        else:
            self.saved_data.setdefault(key, {})['jlpt'] = ['']

        is_common = word_data.get('is_common')
        if is_common:
            self.saved_data.setdefault(key, {})['is_common'] = [str(is_common)]
        else:
            self.saved_data.setdefault(key, {})['is_common'] = ['']

    def show_word_summary(self, word: str, index: int):
        self.grid_setup()
        self.header_setup(word, index)
        scrollframe = self.create_scrollable_frame()
        scrollframe.configure(label_text='Review word before continuing')
        word_summary = self.saved_data.get(word)
        text_box_tracker = {}
        for row, key in enumerate(word_summary):

            scrollframe.rowconfigure(row+1, weight=1, uniform='a')
            CTkLabel(scrollframe, text=key, font=self.defaultFont).grid(
                row=row, column=0, columnspan=2, sticky='nsew')
            text_box = CTkTextbox(scrollframe, wrap='word',
                                  height=50, font=self.defaultFont)
            text_box.grid(row=row, column=2, columnspan=7,
                          pady=10, sticky='nsew')
            entry = word_summary.get(key)
            if entry:
                entry = "\n".join(entry)
                text_box.insert("0.0", entry)
                text_box_tracker[key] = text_box

        def update_changes():
            for key in text_box_tracker:
                text = text_box_tracker.get(key).get(1.0, 'end-1c')
                text = text.split('\n')
                self.saved_data[word][key] = text
            print(self.saved_data.get(word))

        CTkButton(self.word_frame, text='Save Changes and Continue',
                  command=lambda: [
                      update_changes(), self.show_possible_matches(index+1)],
                  font=self.defaultFont).grid(row=2, column=1)

    def show_summary_screen(self):
        self.grid_setup()
        scrollframe = self.create_scrollable_frame()

        CTkLabel(self.word_frame, text="Processing Complete!\nReady to generate CSV.",
                 font=self.defaultFont).grid(row=0, column=1)
        counter = 0
        for word, data in self.saved_data.items():
            text_box = CTkTextbox(scrollframe, height=80, wrap='word',
                                  font=self.defaultFont)
            text_box.configure(state='normal')
            text_box.insert("0.0", data)
            text_box.configure(state='disabled')
            text_box.grid(row=counter, column=1, columnspan=8,
                          sticky='nsew', pady=10)
            counter += 1

        CTkButton(self.word_frame, text="Generate CSV",
                  command=self.generate_csv, font=self.defaultFont).grid(row=2, column=1)

    def csv_column_builder(self, value, key_name):
        if value:
            if key_name != 'definitions':
                return "・".join(value)
            elif key_name == 'definitions':
                return "<br>".join(value)

    def generate_csv(self):
        # Open a "Save As" dialog to get the file path from the user
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save CSV File"
        )

        # If the user cancels the dialog, file_path will be an empty string
        if not file_path:
            return

        # Write the data to the selected file
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            for word_key in self.saved_data:
                word_data = self.saved_data.get(word_key)
                kanji = word_data.get('kanji')
                kana = word_data.get('kana')
                definitions = word_data.get('definitions')
                parts_of_speech = word_data.get('parts_of_speech')
                jlpt = word_data.get('jlpt')
                is_common = word_data.get('is_common')
                if len(kanji) == 0:
                    kanji = kana
                    kana = []
                row = [self.csv_column_builder(kanji, 'kanji'),
                       self.csv_column_builder(kana, 'kana'),
                       self.csv_column_builder(definitions, 'definitions'),
                       self.csv_column_builder(
                           parts_of_speech, 'parts_of_speech'),
                       self.csv_column_builder(jlpt, 'jlpt'),
                       self.csv_column_builder(is_common, 'is_common')]

                writer.writerow(row)

        # Inform the user that the file has been saved
        CTkLabel(self.word_frame, text=f"CSV Generated: {file_path}", font=self.defaultFont).grid(
            row=2, column=0
        )


root = CTk()
app = JishoApp(root)

root.mainloop()
