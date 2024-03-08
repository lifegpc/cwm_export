import sqlite3
import json


class NovelCiwei:
    def __init__(self, db_path: str):
        self._db = sqlite3.connect(db_path, check_same_thread=False)

    def get_book_in_shelf(self, book_id: int):
        cur = self._db.execute(
            'SELECT book_info FROM shelf_book_info WHERE book_id = ?;',
            [str(book_id)])
        for i in cur:
            return json.loads(i[0])

    def get_chapter_with_bookid(self, book_id: int):
        cur = self._db.execute(
            'SELECT * FROM catalog1 WHERE book_id = ? ORDER BY chapter_index;',
            [str(book_id)])
        cur.row_factory = sqlite3.Row
        return cur.fetchall()

    def get_divisions_with_bookid(self, book_id: int):
        cur = self._db.execute('SELECT * FROM division WHERE book_id = ? ORDER BY division_index;', [str(book_id)])  # noqa: E501
        cur.row_factory = sqlite3.Row
        return cur.fetchall()

    def get_chapter(self, chapter_id: int):
        cur = self._db.execute(
            'SELECT * FROM catalog1 WHERE chapter_id = ?;', [str(chapter_id)])
        cur.row_factory = sqlite3.Row
        return cur.fetchone()
