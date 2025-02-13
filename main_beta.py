import csv
import shutil
import tkinter as tk
from os import path, remove
from pprint import pp
from tkinter import END, Event, filedialog
from typing import Any, Dict, List, Optional, Tuple

import customtkinter as ctk
from api_tools import api_get

from helpers import Helpers as BetterJson
import settings as app_setup


class JishoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = app_setup.load_settings()

        self.title("J2A")
        self.geometry("900x500")

        self.bind('<Destroy>', self.on_destroy)

        self.defaultFont = ctk.CTkFont(
            self.settings.get('font'), size=self.settings.get('font_size'), weight='normal')

        self.main_frame = None

        self.current_word = None

        if path.exists('./new_words.csv'):
            remove('./new_words.csv')

        self.word_list = []

        self.saved_data = {}

        self.main_frame_init()
        self.program_start()

    def main_frame_init(self):
        if self.main_frame:
            self.main_frame.destroy()

        self.main_frame = ctk.CTkFrame(self)

        self.main_frame.pack(fill='both', expand=True)
        self.main_frame.columnconfigure((0, 2), weight=1, uniform='a')
        self.main_frame.columnconfigure(1, weight=8, uniform='a')
        self.main_frame.rowconfigure((0, 2), weight=1, uniform='a')
        self.main_frame.rowconfigure(1, weight=8, uniform='a')

        if self.current_word:
            ctk.CTkLabel(
                self.main_frame,
                text=f'Searching for: {self.current_word}\n{
                    self.word_number+1}/{len(self.word_list)}',
                font=self.defaultFont
            ).grid(
                row=0,
                column=1,
                sticky='nsew'
            )

        settings_button = ctk.CTkButton(
            self.main_frame,
            text='Settings',
            command=self.settings_window,
            font=self.defaultFont,
            corner_radius=0)
        settings_button.grid(row=0, column=0, sticky='nw')

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.main_frame, corner_radius=4, border_width=.2, border_color='lightgrey')

        self.scrollable_frame.grid(row=1, column=1, sticky='nsew',)
        self.scrollable_frame.columnconfigure(
            [i for i in range(10)], weight=1, uniform='a')

    def program_start(self):
        self.main_frame_init()
        ctk.CTkLabel(self.main_frame,
                     text='Welcome to J2A!\nBrowse to upload a txt file to get started',
                     font=self.defaultFont).grid(row=0, column=1, sticky='s')
        ctk.CTkButton(self.main_frame, text="Browse",
                      command=self.open_file, font=self.defaultFont).grid(row=1, column=1)

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a Text File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            with open(file_path, 'r', encoding="utf-8") as file:
                self.word_list.extend(file.read().splitlines())
            self.main_logic(0)

    def retrieve_candidates(self, data: List[Dict[str, Any]], word: str) -> List[Dict[str, Any]]:
        """
        Loops through each json object in the 'data' paramater and 
        returns a list of objects that exactly matched the lookup
        paramater 'word'
        """
        candidates = []
        for possible_match in data:
            reading_variations = possible_match.get('readings')
            for kanji, kana in reading_variations:
                if kanji == word or kana == word:
                    candidates.append(possible_match)
                    break
        return candidates

    def write_row(self, row: Dict[str, Any]):
        with open('new_words.csv', "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(row.values())

    def show_summary(self, word_data: Dict[str, Any]):
        self.main_frame_init()
        kanji = list(set([reading[0] for reading in word_data.get(
            'readings') if reading[0] is not None]))
        kana = list(set([reading[1] for reading in word_data.get(
            'readings') if reading[1] is not None]))
        if len(kanji) == 0 and len(kana) >= 1:
            kanji = kana[:]
            kana = []
        parts_of_speech = []
        for parts_list in word_data.get('parts_of_speech'):
            parts_of_speech += parts_list
        parts_of_speech = list(set(parts_of_speech))
        fields = {
            'Kanji': '・'.join(kanji),
            'Kana': '・'.join(kana),
            'Definitions': '<br>'.join(word_data.get('definitions', [])),
            'Parts of Speech': '・'.join(parts_of_speech),
            'JLPT Level': '・'.join(word_data.get('jlpt', [])),
            'Is Common': str(word_data.get('is_common'))
        }

        text_box_tracker = {}
        for row, field in enumerate(fields):
            label = ctk.CTkLabel(self.scrollable_frame,
                                 text=field, font=self.defaultFont)
            label.grid(
                row=row,
                column=0,
                columnspan=3,
                sticky='nsew',
            )
            text_box = ctk.CTkTextbox(self.scrollable_frame, wrap='word',
                                      height=80, font=self.defaultFont)
            text_box.grid(
                row=row,
                column=3,
                columnspan=6,
                pady=10,
                sticky='nsew'
            )
            data = fields.get(field)
            text_box_tracker[field] = text_box
            if data:
                text_box.insert("0.0", data)

        word_number = self.word_number

        def update_changes():
            for field in text_box_tracker:
                text_box_tracker[field] = text_box_tracker.get(
                    field).get(1.0, 'end-1c')

            self.saved_data[word_number] = text_box_tracker
            self.write_row(self.saved_data.get(word_number))
            self.main_logic(word_number+1)

        next_button = ctk.CTkButton(
            self.main_frame, text="next", command=update_changes)
        next_button.grid(row=2, column=1)

    def extract_selections(self, word_data: Dict[str, Any], type: str, selections: List[bool], original_data: Any):
        word_data[f'{type}'] = [
            definition for var,
            definition in zip(selections, original_data)
            if var.get()
        ]

    def toggle_next(self, bool_vars: List[ctk.BooleanVar], next_button: ctk.CTkButton):
        if any(var.get() for var in bool_vars):
            next_button.configure(state='normal')
        else:
            next_button.configure(state='disabled')

    def show_definitions(self, word_data: Dict[str, Any]):

        self.main_frame_init()

        definitions: List[str] = word_data.get('definitions')

        if len(definitions) == 1:
            word_data['parts_of_speech'] = [
                word_data.get('parts_of_speech')[1]]
            return self.show_summary(word_data)

        vars = [ctk.BooleanVar() for _ in range(len(definitions))]
        selections = []
        for row, definition in enumerate(definitions):
            check_button = ctk.CTkCheckBox(
                self.scrollable_frame,
                text=definition,
                font=self.defaultFont,
                variable=vars[row],
                command=lambda:
                self.toggle_next(vars, next_button)
            )
            check_button.grid(
                row=row,
                column=1,
                columnspan=6,
                sticky='nsew',
                padx=10,
                pady=10
            )
            selections.append(vars[row])

        def go_next():
            self.extract_selections(
                word_data, 'definitions',
                selections, definitions)

            self.extract_selections(
                word_data, 'parts_of_speech',
                selections, word_data.get('parts_of_speech').values())

            self.show_summary(word_data)

        next_button = ctk.CTkButton(
            self.main_frame, text="next", command=go_next, state='disabled')
        next_button.grid(row=2, column=1)

    def show_readings(self, word_data: Dict[str, Any]):
        self.main_frame_init()

        readings: List[Tuple[Optional[str], Optional[str]]
                       ] = word_data.get('readings')

        if len(readings) == 1:
            return self.show_definitions(word_data)

        vars = [ctk.BooleanVar() for _ in range(len(readings))]
        selections = []
        for row, reading in enumerate(readings):
            kanji, kana = reading
            check_button = ctk.CTkCheckBox(
                self.scrollable_frame,
                text=(f'{kanji}「{kana}」'),
                font=self.defaultFont,
                variable=vars[row],
                command=lambda:
                self.toggle_next(vars, next_button)
            )
            check_button.grid(
                row=row,
                column=3,
                columnspan=3,
                sticky='nsew',
                padx=10,
                pady=10
            )
            selections.append(vars[row])

        def go_next():
            self.extract_selections(
                word_data,
                'readings',
                selections,
                readings
            )
            self.show_definitions(word_data)

        next_button = ctk.CTkButton(
            self.main_frame, text="next", command=go_next, state='disabled')
        next_button.grid(row=2, column=1)

    def show_final_summary(self):
        self.main_frame_init()
        ctk.CTkLabel(
            self.main_frame,
            text='All words have been searched. Select a browse to save the CSV.',
            font=self.defaultFont
        ).grid(row=0, column=1, sticky='s')
        ctk.CTkButton(
            self.main_frame,
            text='Browse',
            command=self.save_csv,
            font=self.defaultFont
        ).grid(row=1, column=1)

    def save_csv(self):
        folder_path = filedialog.askdirectory(
            title="Select a folder to save to")
        if folder_path:
            save_path = path.join(folder_path, "new_words.csv")
            shutil.copy('./new_words.csv', save_path)

            self.main_frame_init()

            ctk.CTkLabel(
                self.main_frame,
                text=(
                    '終わり! If you\'d like to add more words then click below.\n'
                    + 'Otherwise, feel free to quit the program.'
                ),
                font=self.defaultFont
            ).grid(row=0, column=1, sticky='s')
            ctk.CTkButton(
                self.main_frame,
                text='Main Menu',
                command=self.program_start,
                font=self.defaultFont
            ).grid(row=1, column=1)

    def main_logic(self, word_number):

        self.word_number = word_number
        if word_number >= len(self.word_list):
            return self.show_final_summary()

        self.current_word = self.word_list[word_number]
        print(self.current_word)
        self.main_frame_init()
        url = (
            f'https://jisho.org/api/v1/search/words?keyword={self.current_word}')
        json = api_get(url)
        data = [BetterJson(result).better_data for result in json.get('data')]

        if len(data) < 1:
            # no matches found at all
            self.main_logic(word_number+1)

        candidates = self.retrieve_candidates(
            data=data, word=self.current_word)

        if len(candidates) == 1:
            self.show_readings(candidates[0])

        elif len(candidates) > 1:
            for row, candidate in enumerate(candidates):
                readings = [f'{kanji} {kana}' for kanji,
                            kana in candidate.get('readings')]
                button = ctk.CTkButton(
                    self.scrollable_frame,
                    text='・'.join(readings),
                    font=self.defaultFont,
                    command=lambda
                    candidate=candidate:
                    self.show_readings(candidate)
                )
                button.grid(row=row, column=3,  columnspan=3,
                            sticky='nsew', padx=10, pady=10)

        else:
            ctk.CTkLabel(
                self.scrollable_frame,
                text=(
                    'The word you searched for has no matching results.\n'
                    + 'Please enter a different word below'),
                font=self.defaultFont
            ).grid(row=1, column=2, columnspan=6, sticky='nsew')
            text_box = ctk.CTkTextbox(
                self.scrollable_frame,
                wrap='word',
                height=80,
                font=self.defaultFont)
            text_box.grid(
                row=3,
                column=2,
                columnspan=6,
                pady=10,
                sticky='nsew'
            )

            def retry():
                print(self.word_list[self.word_number])
                self.word_list[self.word_number] = text_box.get(
                    '1.0', END).strip()
                print(self.word_list[self.word_number])
                self.main_logic(self.word_number)

            ctk.CTkButton(
                self.main_frame,
                text="search again",
                command=retry
            ).grid(row=2, column=1)

    def on_destroy(self, event: Event) -> None:
        if event.widget != self:
            return
        print('app closed')

    def settings_window(self):
        _settings_window = ctk.CTkToplevel(self)
        _settings_window.title("Setup")
        _settings_window.geometry('900x500')
        for row, setting in enumerate(self.settings):
            ctk.CTkLabel(
                _settings_window,
                text=setting
            ).grid(
                row=row,
                column=0,
                sticky='nsew'
            )


if __name__ == "__main__":
    app = JishoApp()
    app.mainloop()
