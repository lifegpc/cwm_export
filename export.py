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
