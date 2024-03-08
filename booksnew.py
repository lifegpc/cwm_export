from os.path import isdir, join
from zipfile import ZipFile


class BooksNew:
    def __init__(self, path: str):
        self._path = path
        self._is_zip = False
        self._contain_dir_name = False
        if not isdir(path):
            self._z = ZipFile(path)
            self._is_zip = True
            try:
                self._z.getinfo("booksnew/")
                self._contain_dir_name = True
            except KeyError:
                pass

    def get_chapter(self, book_id: int, chapter_id: int):
        if self._is_zip:
            if self._contain_dir_name:
                path = f'booksnew/{book_id}/{chapter_id}.txt'
            else:
                path = f'{book_id}/{chapter_id}.txt'
            return self._z.read(path).decode()
        else:
            with open(join(self._path, str(book_id), f"{chapter_id}.txt"), 'r',
                      encoding='UTF-8') as f:
                return f.read()
