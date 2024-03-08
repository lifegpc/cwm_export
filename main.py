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
parser.add_argument('-r', '--real', help='Use default locations. Needed running on Android machine. Root is required.', action='store_true')  # noqa: E501
parser.add_argument('-B', '--bid', '--book-id', help='The book id.', type=int)
parser.add_argument('-t', '--type', help='Export type. Available types: epub, txt. Default: epub,txt')  # noqa: E501
parser.add_argument('--ebt', '--export-book-template', help='The template of the exported book. Available key: <ext>, <book_id>, <book_name>, <author_name> eta.')  # noqa: E501
parser.add_argument('--icd', '--image-cache-dir', help='Path to image cache directory.')  # noqa: E501
parser.add_argument('-s', '--page-size', help='Maximum size of a page when asking for choices.', type=int)  # noqa: E501
parser.add_argument('action', help='The action to do.', choices=['importkey', 'exportchapter', 'exportbook', 'export', 'ik', 'ec', 'eb', 'e'], nargs='?', default='export')  # noqa: E501


def main(args=None):
    arg = parser.parse_intermixed_args(args)
    cfg = Config(arg.config)
    if arg.real:
        base_dir = '/data/data/com.kuangxiangciweimao.novel/'
        arg.cwmdb = f'{base_dir}databases/novelCiwei'
        arg.key = f'{base_dir}files/Y2hlcy8'
        arg.booksnew = f'{base_dir}files/novelCiwei/reader/booksnew'
    cfg.add_args(arg)
    try:
        db = CwmDb(cfg.db)
        if arg.action == 'importkey' or arg.action == 'ik':
            if cfg.key is None:
                raise ValueError('The key is not specified.')
            from key import import_keys
            import_keys(cfg.key, db)
        elif arg.action == 'exportchapter' or arg.action == 'ec':
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
        elif arg.action == 'exportbook' or arg.action == 'eb':
            if cfg.cwmdb is None:
                raise ValueError('The cwmdb is not specified.')
            ncw = NovelCiwei(cfg.cwmdb)
            if cfg.booksnew is None:
                raise ValueError('The booksnew is not specified.')
            bn = BooksNew(cfg.booksnew)
            if cfg.book_id is None:
                raise ValueError('The book id is not specified.')
            if not cfg.export_epub and not cfg.export_txt:
                raise ValueError('At least one export type should be specified.')  # noqa: E501
            from export import export_book
            export_book(ncw, db, cfg, bn, cfg.book_id)
        elif arg.action == 'export' or arg.action == 'e':
            if cfg.cwmdb is None:
                raise ValueError('The cwmdb is not specified.')
            ncw = NovelCiwei(cfg.cwmdb)
            if cfg.booksnew is None:
                raise ValueError('The booksnew is not specified.')
            bn = BooksNew(cfg.booksnew)
            if not cfg.export_epub and not cfg.export_txt:
                raise ValueError('At least one export type should be specified.')  # noqa: E501
            from export import export
            export(ncw, db, cfg, bn)
    finally:
        cfg.save()


if __name__ == '__main__':
    main()
