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


def get_key(db: CwmDb, cfg: Config, chapter_id: int):
    keys = db.get_key(chapter_id)
    if len(keys) == 0:
        if key_imported:
            raise ValueError('The key is not found.')
        else:
            import_keys(cfg.key, db)
        keys = db.get_key(chapter_id)
        if len(keys) == 0:
            raise ValueError('The key is not found.')
    return keys


def try_decrypt(db: CwmDb, cfg: Config, content, chapter_id: int):
    keys = get_key(db, cfg, chapter_id)
    for key in keys:
        try:
            return decrypt(content, key).decode()
        except Exception:
            pass
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
            if cfg.export_txt:
                txt.write(f"第{division['division_index']}卷 {division_name}\n")
                if division['description']:
                    txt.write(division['description'] + '\n\n')
            if cfg.export_epub and division['description']:
                print('TODO: add division description to epub.')
            chapter_index = 1
            for chapter in maps[division['division_id']]:
                chapter_id = chapter['chapter_id']
                chapter_title = chapter['chapter_title']
                if chapter['is_download']:
                    raw_content = bn.get_chapter(book_id, chapter_id)
                    content = try_decrypt(db, cfg, raw_content, chapter_id)
                    if cfg.export_txt:
                        txt.write(f"第{chapter_index}章 {chapter_title}\n")
                        txt.write(content + '\n\n')
                    if cfg.export_epub:
                        epub.add_chapter(chapter, content, division_name)
                    count += 1
                else:
                    if cfg.export_txt:
                        txt.write(f"第{chapter_index}章 {chapter_title} (未下载)\n\n")  # noqa: E501
                chapter_index += 1
        print(f'Exported {count} chapters.')
    finally:
        if cfg.export_txt:
            txt.close()
        if cfg.export_epub:
            epub.save_epub_file()


def export(ncw: NovelCiwei, db: CwmDb, cfg: Config, bn: BooksNew):
    action = ask_choice(cfg, [], '请选择要导出的类型：', extra=[
                        ('b', '整本书', 'book'), ('c', '单章', 'chapter')])
    books = ncw.get_books()
    shelfs = {}
    for book in books:
        shelf_id = book['shelf_id']
        if shelf_id in shelfs:
            shelfs[shelf_id].append(book)
        else:
            shelfs[shelf_id] = [book]

    def show_shelf(shelf: str):
        data = f"{shelf} ({len(shelfs[shelf])} 本书)"
        book = json.loads(choice(shelfs[shelf])['book_info'])
        data += f"\n书架内有 {book['book_name']} - {book['author_name']}"
        return data
    shelf = ask_choice(cfg, [i for i in shelfs.keys()], '请选择书架：', show_shelf)
    books = [json.loads(b['book_info']) for b in shelfs[shelf]]
    book = ask_choice(cfg, books, '请选择书：', lambda b: f"{b['book_name']} - {b['author_name']}")  # noqa: E501
    book_id = int(book['book_id'])
    if action == 'book':
        export_book(ncw, db, cfg, bn, book_id)
    elif action == 'chapter':
        divisions = ncw.get_divisions_with_bookid(book_id)
        division = ask_choice(cfg, divisions, '请选择卷：', lambda b: b['division_name'])  # noqa: E501
        division_id = int(division['division_id'])
        chapters = ncw.get_chapter_with_bookid_division(book_id, division_id)
        chapter = ask_choice(cfg, chapters, '请选择章节：', lambda b: b['chapter_title'])  # noqa: E501
        chapter_id = int(chapter['chapter_id'])
        export_chapter(ncw, db, cfg, bn, chapter_id)
