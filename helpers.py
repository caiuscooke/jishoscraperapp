"""
Helpers module is made to simplify the json data returned from
the jisho.org API. The original format and refactored format are
as follows:

Original
{
  "data": [
    {
      "slug": "{lookup}",
      "is_common": {bool},
      "tags": {list[str]},
      "jlpt": {list[str]},
      "japanese": [
        {
          "word": "{kanji}",
          "reading": "{kana}"
        },
      ],
      "senses": [
        {
          "english_definitions": {list[str]},
          "parts_of_speech": {list[str]},
          "tags": {list[str]},
        },
      ],
    },
  ]
}

Reformatted
{
    'readings': List[
        Tuple[Optional[str], Optional[Str]]
    ],
    'definitions': List[str],
    'parts_of_speech': Dict[int, List[str]],
    'jlpt': List[str],
    'is_common': Bool
}
"""
from typing import Any, Dict, List, Optional, Tuple


class Helpers:
    def __init__(self, term: Dict[str, Any]):
        self.term = term
        self.senses = self.get_senses(self.term)
        self.better_data = {
            'readings': self.get_readings(),
            'definitions': self.get_definitions(),
            'parts_of_speech': self.get_pos(),
            'jlpt': self.term.get('jlpt'),
            'is_common': self.term.get('is_common')
        }

    def get_senses(self, term: Dict[str, Any]) -> List[Dict[str, Any]]:
        return term.get('senses', [])

    def get_readings(self) -> List[Tuple[Optional[str], Optional[str]]]:
        """
        Takes the term and returns all the kanji/kana for that term. 
        If either is none, then the tuple will look like (none, {kana})
        or vice versa. 
        """
        variations_list: List[Dict[str, str]] = self.term.get('japanese', [])

        return [(variation_dict.get('word'), variation_dict.get('reading'))
                for variation_dict in variations_list]

    def get_definitions(self) -> List[str]:
        """
        Takes the term and returns all the definitions for that term. 
        Each will be numbered and seperated into its own 
        list item such as ['1) definition',]
        """
        tags = self.get_info('tags')
        info = self.get_info('info')
        english_definitions: List[List[str]] = [sense.get('english_definitions')
                                                for sense in self.senses]
        for tag_number in tags:
            if tags[tag_number]:
                english_definitions[tag_number-1] += tags[tag_number]
        for info_number in info:
            if tags[info_number]:
                english_definitions[info_number-1] += info[info_number]

        return [f'{index+1}) {', '.join(english_definition)}'
                for index, english_definition in enumerate(english_definitions)]

    def get_info(self, type: str) -> Dict[int, List[str]]:
        """
        Extracts each of the extra notes/tags for each of the
        definitions and returns a dictionary where the key
        is the definition number theses notes pertains to
        and the value is a list of the notes. Parameter
        'type' is either 'tags' for retrieving the tags kvp
        or 'info' for retrieving the info kvp. 
        """
        info_dict = {}
        for index, sense in enumerate(self.senses):
            info: List[str] = sense.get(f'{type}')
            if info:
                info_dict[index + 1] = info
        return info_dict

    def get_pos(self) -> Dict[int, List[str]]:
        """
        Extracts all the parts of speech for each of the term's
        'senses' key and returns a dictionary where the key is 
        the definition number this parts list pertains to and 
        the value is the list of parts of speech. Each list is 
        passed through the translator first. 
        """
        parts_dict = {}
        for index, sense in enumerate(self.senses):
            parts_dict[index + 1] = (
                self.translate_pos(sense.get('parts_of_speech'))
            )
        return parts_dict

    def translate_pos(self, parts_list: List[str]) -> List[str]:
        """
        Takes the list of parts of speech as a parameter and converts
        each one to its Japanese counterpart word. 
        """
        translated_parts = []
        for part in parts_list:
            if part == 'Noun':
                translated_parts.append('名')
            elif part == 'Suru verb':
                translated_parts.append('スル')
            elif part == 'Intransitive verb':
                translated_parts.append('自動詞')
            elif part == 'Transitive verb':
                translated_parts.append('他動詞')
            elif part == 'Na-adjective (keiyodoshi)':
                translated_parts.append('形容動')
            elif part == 'I-adjective (keiyoushi)':
                translated_parts.append('形容')
            elif part == 'Adverb (fukushi)':
                translated_parts.append('副詞')
            elif part == 'Adverb taking the \'to\' particle':
                translated_parts.append('と副詞')
            elif part == 'Noun which may take the genitive case particle \'no\'':
                translated_parts.append('の名')
            elif 'Expressions' in part:
                translated_parts.append('文')
        return translated_parts
