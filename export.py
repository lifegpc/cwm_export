from novelCiwei import NovelCiwei
from db import CwmDb
from config import Config
from key import import_keys
from booksnew import BooksNew
from crypto import decrypt
from os.path import dirname
from os import makedirs


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
            if cfg.export_txt:
                txt.write(f"第{division['division_index']}卷 {division['division_name']}\n")  # noqa: E501
                if division['description']:
                    txt.write(division['description'] + '\n\n')
            chapter_index = 1
            for chapter in maps[division['division_id']]:
                if chapter['is_download']:
                    chapter_id = chapter['chapter_id']
                    chapter_title = chapter['chapter_title']
                    raw_content = bn.get_chapter(book_id, chapter_id)
                    content = try_decrypt(db, cfg, raw_content, chapter_id)
                    if cfg.export_txt:
                        txt.write(f"第{chapter_index}章 {chapter_title}\n")
                        txt.write(content + '\n\n')
                    count += 1
                else:
                    if cfg.export_txt:
                        txt.write(f"第{chapter_index}章 {chapter_title} (未下载)\n\n")  # noqa: E501
                chapter_index += 1
        print(f'Exported {count} chapters.')
    finally:
        if cfg.export_txt:
            txt.close()
