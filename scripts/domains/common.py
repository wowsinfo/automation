"""Shared helpers for the domain modules (moved from generate.py)."""
import json
import os
from typing import List, Callable


class HelpersMixin:
    #region helper functions
    def _read_lang(self, language: str) -> dict:
        return self._read_json('langs/{}_lang.json'.format(language))

    def _read_supported_langs(self) -> dict:
        """
        Read all language files and return a dict
        """
        lang_dict = {}
        for lang in self._list_dir('langs'):
            if '.git' in lang:
                continue

            lang = lang.replace('_lang.json', '')
            if not lang in ['en', 'ja', 'zh_sg', 'zh_tw']:
                continue
            print('Reading language {}...'.format(lang))
            lang_dict[lang] = self._read_lang(lang)
        return lang_dict

    def _read_json(self, filename: str) -> dict:
        with open(filename, 'r', encoding='utf8') as f:
            json_dict = json.load(f)
        return json_dict

    def _read_gameparams(self) -> dict:
        return self._read_json('GameParams-0.json')

    def _write_json(self, data: dict, filename: str):
        with open(filename, 'w', encoding='utf8') as f:
            json_str = json.dumps(data, ensure_ascii=False)
            f.write(json_str)

    def _sizeof_json(self, filename: str) -> float:
        """
        Get the size of a json file
        """
        return os.path.getsize(filename) / 1024 / 1024

    def _list_dir(self, dir: str) -> list:
        """
        List all files in a directory
        """
        return os.listdir(dir)

    def _roundUp(self, num: float, digits: int = 1) -> float:
        # TODO: in the future, we may need to keep more digits in case our calculation in app is not accurate
        return round(num, digits)

    def _match(self, text: str, patterns: List[str], method: Callable[[str, str], bool]) -> bool:
        """
        Match text with patterns
        """
        for pattern in patterns:
            if method(text, pattern):
                return True
        return False

    def _tree(self, data: any, depth: int = 2, tab: int = 0, show_value: bool = False):
        """
        Show the structure tree of a dict. This is useful when analysing the data.
        """
        if depth == 0:
            if show_value:
                if isinstance(data, dict):
                    print('{}- dict'.format('\t' * tab))
                else:
                    print('{}- {}'.format('\t' * tab, data))
            return
        if not isinstance(data, dict):
            # print empty string when it is empty
            if data == '':
                print('\t' * tab, '- empty string')
            else:
                print('{}- {}'.format('\t' * tab, data))
            return

        for level in data:
            print('\t' * tab + '- ' + level)
            self._tree(data[level], depth - 1, tab + 1, show_value=show_value)

    def _merge(self, weapons: dict) -> dict:
        # join same weapons together into one dict
        merged = []
        counter = []
        for w in weapons:
            if len(merged) == 0:
                merged.append(w)
                counter.append(1)
                continue

            found = False
            for m in merged:
                if w == m:
                    counter[merged.index(m)] += 1
                    found = True
                    break
            if not found:
                merged.append(w)
                counter.append(1)
        for m in merged:
            m['count'] = counter[merged.index(m)]
        return merged

    def _IDS(self, key: str) -> str:
        return 'IDS_' + key.upper()
    #endregion
