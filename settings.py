import json

SETTINGS_FILE = 'settings.json'


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'font': 'メイリオ',
            'font_size': 20
        }
