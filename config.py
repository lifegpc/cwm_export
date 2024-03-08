from argparse import Namespace
from os.path import exists
import json
try:
    from functools import cached_property
except Exception:
    cached_property = property


class Config:
    def __init__(self, cfg_path: str):
        self._path = cfg_path
        self._data = {}
        self._args = Namespace()
        if exists(cfg_path):
            with open(cfg_path, 'r', encoding='UTF-8') as f:
                self._data = json.load(f)
        else:
            self._data['db'] = 'cwm.db'
            self._data['save_to_config'] = True
            self._data['type'] = 'epub,txt'
            self._data['export_book_template'] = 'exported/<book_name> - <author_name>.<ext>'  # noqa: E501
            self._data['export_chapter_template'] = 'exported/<book_id>/<chapter_id>.txt'  # noqa: E501
            self.save()

    def add_args(self, args: Namespace):
        self._args = args

    def get_arg(self, key: str, default):
        x = getattr(self._args, key, None)
        if x is not None:
            if self.save_to_config:
                self._data[key] = x
            return x
        if key in self._data:
            return self._data[key]
        else:
            if default is not None:
                self._data[key] = default
            return default

    @cached_property
    def book_id(self):
        return getattr(self._args, 'bid', None)

    @cached_property
    def booksnew(self):
        return self.get_arg('booksnew', None)

    @cached_property
    def chapter_id(self):
        return getattr(self._args, 'cid', None)

    @cached_property
    def cwmdb(self):
        return self.get_arg('cwmdb', None)

    @cached_property
    def db(self):
        return self.get_arg('db', 'cwm.db')

    @cached_property
    def export_book_template(self):
        return self.get_arg('export_book_template', 'exported/<book_name> - <author_name>.<ext>')  # noqa: E501

    @cached_property
    def export_chapter_template(self):
        return self.get_arg('export_chapter_template', 'exported/<book_id>/<chapter_id>.txt')  # noqa: E501

    @cached_property
    def export_epub(self):
        return self.export_type.find('epub') >= 0

    @cached_property
    def export_txt(self):
        return self.export_type.find('txt') >= 0

    @cached_property
    def export_type(self):
        return self.get_arg('type', 'epub,txt')

    def get_export_book(self, book, ext):
        temp = self.export_book_template
        for k in book.keys():
            temp = temp.replace(f'<{k}>', str(book[k]))
        temp = temp.replace('<ext>', ext)
        return temp

    def get_export_chapter(self, chapter):
        temp = self.export_chapter_template
        for k in chapter.keys():
            temp = temp.replace(f'<{k}>', str(chapter[k]))
        return temp

    @cached_property
    def img_cache_dir(self):
        return self.get_arg('img_cache_dir', 'img_cache')

    @cached_property
    def key(self):
        return self.get_arg('key', None)

    @cached_property
    def save_to_config(self):
        return getattr(self._args, 'save_to_config', True)

    def save(self):
        with open(self._path, 'w', encoding='UTF-8') as f:
            json.dump(self._data, f, ensure_ascii=False)
