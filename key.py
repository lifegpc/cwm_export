from os.path import isdir, join
from os import listdir
from db import CwmDb
from zipfile import ZipFile
from base64 import b64decode


def import_keys(key: str, db: CwmDb, force=False):
    is_zip = False
    file_list = []
    contain_dir_name = False
    if isdir(key):
        file_list = listdir(key)
    else:
        z = ZipFile(key)
        is_zip = True
        file_list = z.namelist()
        if 'Y2hlcy8/' in file_list:
            contain_dir_name = True
            file_list = [i[8:] for i in file_list if i.startswith(
                'Y2hlcy8/') and i != 'Y2hlcy8/']
    try:
        count = 0
        keys = db.get_all_keys_as_origin()
        for i in file_list:
            oid = b64decode(i).decode()
            if oid in keys:
                if not force:
                    continue
            cid = int(oid[0:9])
            uid = int(oid[9:])
            if is_zip:
                if contain_dir_name:
                    path = 'Y2hlcy8/' + i
                else:
                    path = i
                content = z.read(path).decode()
            else:
                content = open(join(key, i), 'r', encoding='UTF-8').read()
            if oid in keys and content == keys[oid]:
                continue
            db.add_key(cid, uid, content)
            count += 1
        print(f'Imported {count} keys.')
    finally:
        db.commit()
        if is_zip:
            z.close()
