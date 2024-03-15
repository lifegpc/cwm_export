from novelCiwei import NovelCiwei
from db import CwmDb
from config import Config
from key import import_keys
from booksnew import BooksNew
from crypto import decrypt
from os.path import dirname
from os import makedirs
from epub import EpubFile
from utils import ask_choice
import json
from random import choice


key_imported = False
key_force_imported = False


def get_key(db: CwmDb, cfg: Config, chapter_id: int):
    global key_imported
    keys = db.get_key(chapter_id)
    if len(keys) == 0:
        if key_imported:
            raise ValueError('The key is not found.')
        else:
            import_keys(cfg.key, db)
            key_imported = True
        keys = db.get_key(chapter_id)
        if len(keys) == 0:
            raise ValueError('The key is not found.')
    return keys


def try_decrypt(db: CwmDb, cfg: Config, content, chapter_id: int):
    global key_force_imported
    keys = get_key(db, cfg, chapter_id)
    for key in keys:
        try:
            return decrypt(content, key).decode()
        except Exception:
            pass
    if not key_force_imported:
        import_keys(cfg.key, db, True)
        key_force_imported = True
        return try_decrypt(db, cfg, content, chapter_id)
    raise ValueError('Failed to decrypt the content.')


def export_chapter(ncw: NovelCiwei, db: CwmDb, cfg: Config, bn: BooksNew,
                   chapter_id: int):
    chapter = ncw.get_chapter(chapter_id)
    book_id = int(chapter['book_id'])
    raw_content = bn.get_chapter(book_id, chapter_id)
    content = try_decrypt(db, cfg, raw_content, chapter_id)
    filename = cfg.get_export_chapter(chapter)
    d = dirname(filename)
    makedirs(d, exist_ok=True)
    with open(filename, 'w', encoding='UTF-8') as f:
        f.write(chapter['chapter_title'] + '\n')
        f.write(content)


def export_book(ncw: NovelCiwei, db: CwmDb, cfg: Config, bn: BooksNew,
                book_id: int):
    book = ncw.get_book_in_shelf(book_id)
    if book is None:
        book = ncw.get_book_in_readhistory(book_id)
    if book is None:
        raise ValueError('The book is not found.')
    if cfg.export_txt:
        txt_filename = cfg.get_export_book(book, 'txt')
        d = dirname(txt_filename)
        makedirs(d, exist_ok=True)
        txt = open(txt_filename, 'w', encoding='UTF-8')
    if cfg.export_epub:
        try:
            epub = EpubFile(cfg, cfg.get_export_book(book, 'epub'))
            epub.set_book(book)
        except Exception as e:
            if cfg.export_txt:
                txt.close()
            raise e
    try:
        chapters = ncw.get_chapter_with_bookid(book_id)
        divisions = ncw.get_divisions_with_bookid(book_id)
        maps = {}
        count = 0
        for chapter in chapters:
            division_id = chapter['division_id']
            if division_id in maps:
                maps[division_id].append(chapter)
            else:
                maps[division_id] = [chapter]
        for division in divisions:
            division_name = division['division_name']
            division_id = division['division_id']
            is_linear = db.get_mark(division_id)
            if cfg.export_txt:
                txt.write(f"第{division['division_index']}卷 {division_name}\n")
                if division['description']:
                    txt.write(division['description'] + '\n\n')
            if cfg.export_epub and division['description']:
                print('TODO: add division description to epub.')
            if division_id not in maps:
                continue
            chapter_index = 1
            for chapter in maps[division_id]:
                chapter_id = chapter['chapter_id']
                chapter_title = chapter['chapter_title']
                if chapter['is_download']:
                    raw_content = bn.get_chapter(book_id, chapter_id)
                    content = try_decrypt(db, cfg, raw_content, chapter_id)
                    if cfg.export_txt:
                        txt.write(f"第{chapter_index}章 {chapter_title}\n")
                        txt.write(content + '\n\n')
                    if cfg.export_epub:
                        epub.add_chapter(chapter, content, division_name,
                                         is_linear)
                    count += 1
                elif cfg.export_nodownload:
                    if cfg.export_txt:
                        txt.write(f"第{chapter_index}章 {chapter_title} (未下载)\n\n")  # noqa: E501
                    if cfg.export_epub:
                        epub.add_nodownload_chapter(chapter, division_name,
                                                    is_linear)
                chapter_index += 1
        print(f'Exported {count} chapters.')
    finally:
        if cfg.export_txt:
            txt.close()
        if cfg.export_epub:
            epub.save_epub_file()


def export_all(ncw: NovelCiwei, db: CwmDb, cfg: Config, bn: BooksNew):
    books = ncw.get_all_books()
    for book in books:
        book_id = int(book[0])
        try:
            export_book(ncw, db, cfg, bn, book_id)
        except Exception as e:
            print(f'Failed to export book {book_id}: {e}')


class ExportCli:
    def __init__(self, ncw: NovelCiwei, db: CwmDb, cfg: Config, bn: BooksNew):
        self.ncw = ncw
        self.db = db
        self.cfg = cfg
        self.bn = bn
        self.action = None
        self.shelf = None
        self.shelfs = None
        self.book = None
        self.book_id = None
        self.division_id = None
        self.fns = [self.ask_action]

    def ask_action(self):
        self.action = ask_choice(self.cfg, [], '请选择要导出的类型：', extra=[
            ('b', '整本书', 'book'), ('c', '单章', 'chapter'), ('a', '所有书', 'all'),
            ('m', '标记为非线性卷', 'mark')])
        if self.action == 'all':
            export_all(self.ncw, self.db, self.cfg, self.bn)
            return
        self.fns.append(self.ask_shelf)

    def ask_book(self):
        if self.shelf == 'readhistory':
            books = [json.loads(b['book_info']) for b in self.ncw.get_read_history()]  # noqa: E501
        elif self.shelf == 'all':
            bookids = [int(b[0]) for b in self.ncw.get_all_books()]
            books = []
            for bid in bookids:
                book = self.ncw.get_book_in_shelf(bid) or self.ncw.get_book_in_readhistory(bid)  # noqa: E501
                if book:
                    books.append(book)
        else:
            books = [json.loads(b['book_info']) for b in self.shelfs[self.shelf]]  # noqa: E501
        self.book = ask_choice(self.cfg, books, '请选择书：', lambda b: f"{b['book_name']} - {b['author_name']}", [('b', '返回', 'back')])  # noqa: E501
        if self.book == 'back':
            self.fns.append(self.ask_shelf)
            return
        self.book_id = int(self.book['book_id'])
        if self.action == 'book':
            export_book(self.ncw, self.db, self.cfg, self.bn, self.book_id)
            return
        self.fns.append(self.ask_division)

    def ask_chapter(self):
        chapters = self.ncw.get_chapter_with_bookid_division(self.book_id, self.division_id)  # noqa: E501
        chapter = ask_choice(self.cfg, chapters, '请选择章节：', lambda b: b['chapter_title'], [('b', '返回', 'back')])  # noqa: E501
        if chapter == 'back':
            self.fns.append(self.ask_division)
            return
        chapter_id = int(chapter['chapter_id'])
        export_chapter(self.ncw, self.db, self.cfg, self.bn, chapter_id)

    def ask_division(self):
        divisions = self.ncw.get_divisions_with_bookid(self.book_id)
        extras = [('b', '返回', 'back')]
        if self.action == 'mark':
            extras.append(('q', '退出', 'quit'))

        def show_division(division):
            name = division['division_name']
            if self.action == 'mark':
                division_id = int(division['division_id'])
                if not self.db.get_mark(division_id):
                    name += ' (非线性卷)'
            return name
        division = ask_choice(self.cfg, divisions, '请选择卷：', show_division, extras)  # noqa: E501
        if division == 'back':
            self.fns.append(self.ask_book)
            return
        if division == 'quit':
            return
        self.division_id = int(division['division_id'])
        if self.action == 'mark':
            now = self.db.get_mark(self.division_id)
            self.db.set_mark(self.division_id, not now)
            self.fns.append(self.ask_division)
            return
        self.fns.append(self.ask_chapter)

    def ask_shelf(self):
        books = self.ncw.get_books()
        self.shelfs = {}
        for book in books:
            shelf_id = book['shelf_id']
            if shelf_id in self.shelfs:
                self.shelfs[shelf_id].append(book)
            else:
                self.shelfs[shelf_id] = [book]

        def show_shelf(shelf: str):
            data = f"{shelf} ({len(self.shelfs[shelf])} 本书)"
            book = json.loads(choice(self.shelfs[shelf])['book_info'])
            data += f"\n书架内有 {book['book_name']} - {book['author_name']}"
            return data
        self.shelf = ask_choice(self.cfg, [i for i in self.shelfs.keys()],
                                '请选择书架：', show_shelf,
                                [('r', '阅读历史', 'readhistory'),
                                 ('a', '所有书', 'all'),
                                 ('b', '返回', 'back')])
        if self.shelf == 'back':
            self.fns.append(self.ask_action)
            return
        self.fns.append(self.ask_book)

    def start(self):
        while True:
            if len(self.fns) == 0:
                break
            self.fns.pop(0)()
