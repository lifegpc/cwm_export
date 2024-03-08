from argparse import ArgumentParser
from config import Config
from db import CwmDb
from novelCiwei import NovelCiwei
from booksnew import BooksNew


parser = ArgumentParser(description='A tool to export CiWeiMao novel cache.')
parser.add_argument('-c', '--config', help='The path of the config file.', default='config.json')  # noqa: E501
parser.add_argument('-d', '--db', help='The path of the database file.')
parser.add_argument('-k', '--key', help='The path to Y2hlcy8 key directory or zip file.')  # noqa: E501
parser.add_argument('--cwmdb', help='The path to NovelCiwei file.')
parser.add_argument('-b', '--booksnew', help='The path to booksnew directory or zip file.')  # noqa: E501
parser.add_argument('-C', '--cid', '--chapter-id', help='The chapter id.', type=int)  # noqa: E501
parser.add_argument('--ect', '--export-chapter-template', help='The template of the exported chapter. Available key: <book_id>, <chapter_id> eta.')  # noqa: E501
parser.add_argument('action', help='The action to do.', choices=['importkey', 'exportchapter'])  # noqa: E501


def main(args=None):
    arg = parser.parse_intermixed_args(args)
    cfg = Config(arg.config)
    cfg.add_args(arg)
    try:
        db = CwmDb(cfg.db)
        if arg.action == 'importkey':
            if cfg.key is None:
                raise ValueError('The key is not specified.')
            from key import import_keys
            import_keys(cfg.key, db)
        elif arg.action == 'exportchapter':
            if cfg.cwmdb is None:
                raise ValueError('The cwmdb is not specified.')
            ncw = NovelCiwei(cfg.cwmdb)
            if cfg.booksnew is None:
                raise ValueError('The booksnew is not specified.')
            bn = BooksNew(cfg.booksnew)
            if cfg.chapter_id is None:
                raise ValueError('The chapter id is not specified.')
            from export import export_chapter
            export_chapter(ncw, db, cfg, bn, cfg.chapter_id)
    finally:
        cfg.save()


if __name__ == '__main__':
    main()
