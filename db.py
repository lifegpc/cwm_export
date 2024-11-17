import sqlite3
from semver import Version
from typing import Dict, Optional, List


VERSION_TABLE = '''CREATE TABLE version (
id TEXT,
version TEXT,
PRIMARY KEY (id)
);'''
KEY_TABLE = '''CREATE TABLE key (
chapter_id INT,
user_id INT,
key TEXT,
PRIMARY KEY (chapter_id, user_id)
);'''
DIVISION_TABLE = '''CREATE TABLE division(
division_id INT,
is_linear BOOL,
PRIMARY KEY(division_id)
);'''


class CwmDb:
    def __init__(self, db_path):
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self.version = Version(0, 0, 0, 1)
        if not self.__check_database():
            self.__create_table()

    def __check_database(self):
        self.__update_exists_tables()
        v = self.__read_version()
        if v is None:
            return False
        if v < self.version:
            if v < Version(0, 0, 0, 1):
                self._db.execute(DIVISION_TABLE)
            self.__update_exists_tables()
            self.__write_version()
        return True

    def __create_table(self):
        if 'version' not in self._exist_tables:
            self._db.execute(VERSION_TABLE)
            self.__write_version()
        if 'key' not in self._exist_tables:
            self._db.execute(KEY_TABLE)
        if 'division' not in self._exist_tables:
            self._db.execute(DIVISION_TABLE)
        self._db.commit()

    def __write_version(self):
        self._db.execute('INSERT OR REPLACE INTO version VALUES (?, ?);', [
                         'main', str(self.version)])
        self._db.commit()

    def __read_version(self) -> Optional[Version]:
        if 'version' not in self._exist_tables:
            return None
        cur = self._db.execute(
            'SELECT version FROM version WHERE id = ?;', ['main'])
        for i in cur:
            try:
                return Version.parse(i[0])
            except Exception:
                return None

    def __update_exists_tables(self):
        cur = self._db.execute('SELECT * FROM main.sqlite_master;')
        self._exist_tables = {}
        for i in cur:
            if i[0] == 'table':
                self._exist_tables[i[1]] = i

    def add_key(self, chapter_id: int, user_id: int, key: str):
        self._db.execute('INSERT OR REPLACE INTO key VALUES (?, ?, ?);', [
                         chapter_id, user_id, key])

    def get_all_keys_as_origin(self) -> Dict[str, str]:
        cur = self._db.execute('SELECT chapter_id, user_id, key FROM key;')
        return {f'{i[0]}{i[1]}': i[2] for i in cur}

    def commit(self):
        self._db.commit()

    def get_key(self, chapter_id: int) -> List[str]:
        cur = self._db.execute('SELECT key FROM key WHERE chapter_id = ?;', [
                              chapter_id])
        return [i[0] for i in cur]

    def get_mark(self, division_id: int):
        cur = self._db.execute(
            'SELECT is_linear FROM division WHERE division_id = ?;',
            [division_id])
        for i in cur:
            return bool(i[0])
        return True

    def set_mark(self, division_id: int, is_linear: bool):
        self._db.execute('INSERT OR REPLACE INTO division VALUES (?, ?);', [
                         division_id, is_linear])
        self._db.commit()
