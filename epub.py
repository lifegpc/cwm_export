from ebooklib import epub, ITEM_IMAGE
from lxml import etree
import subprocess
from typing import Optional
import os
from config import Config
from image_cache import get_cache
from traceback import print_exc
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
try:
    import magic
    have_magic = True
    have_filetype = False
except ImportError:
    have_magic = False
    try:
        import filetype
        have_filetype = True
    except ImportError:
        have_filetype = False
        print('Warning: python-magic or filetype not found. The mimetype in EPUB file may wrong.')  # noqa: E501
        import platform
        if platform.system() == "Windows":
            print('python-magic-bin is also needed on Windows if you use magic.')  # noqa: E501


# Add fallback property to ebooklib
# ebooklib does not support fallback
class EpubItem(epub.EpubItem):
    def __init__(self, uid=None, file_name='', media_type='',
                 content=epub.six.b(''), manifest=True):
        super().__init__(uid, file_name, media_type, content, manifest)
        self.fallback = None


class EpubImage(EpubItem):
    def __init__(self):
        super().__init__()

    def get_type(self):
        return ITEM_IMAGE

    def __str__(self):
        return '<EpubImage:%s:%s>' % (self.id, self.file_name)


class EpubPathImage(EpubImage):
    def __init__(self):
        super().__init__()
        self.path = None

    def get_content(self, default=b''):
        if self.path:
            with open(self.path, 'rb') as f:
                return f.read()
        return default


class EpubWriter(epub.EpubWriter):
    def _write_opf_manifest(self, root):
        manifest = epub.etree.SubElement(root, 'manifest')
        _ncx_id = None

        for item in self.book.get_items():
            if not item.manifest:
                continue

            if isinstance(item, epub.EpubNav):
                etree.SubElement(manifest, 'item', {'href': item.get_name(),
                                                    'id': item.id,
                                                    'media-type': item.media_type,  # noqa: E501
                                                    'properties': 'nav'})
            elif isinstance(item, epub.EpubNcx):
                _ncx_id = item.id
                etree.SubElement(manifest, 'item', {'href': item.file_name,
                                                    'id': item.id,
                                                    'media-type': item.media_type})  # noqa: E501

            elif isinstance(item, epub.EpubCover):
                etree.SubElement(manifest, 'item', {'href': item.file_name,
                                                    'id': item.id,
                                                    'media-type': item.media_type,  # noqa: E501
                                                    'properties': 'cover-image'})  # noqa: E501
            else:
                opts = {'href': item.file_name,
                        'id': item.id,
                        'media-type': item.media_type}

                if hasattr(item, 'properties') and len(item.properties) > 0:
                    opts['properties'] = ' '.join(item.properties)

                if hasattr(item, 'media_overlay') and item.media_overlay is not None:  # noqa: E501
                    opts['media-overlay'] = item.media_overlay

                if hasattr(item, 'media_duration') and item.media_duration is not None:  # noqa: E501
                    opts['duration'] = item.media_duration

                if hasattr(item, 'fallback') and item.fallback is not None:
                    opts['fallback'] = item.fallback

                etree.SubElement(manifest, 'item', opts)

        return _ncx_id


have_ffmpeg = None


def check_ffmpeg():
    p = subprocess.Popen(['ffmpeg', '-h'], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    p.communicate()
    global have_ffmpeg
    have_ffmpeg = not p.wait()
    if not have_ffmpeg:
        print('Warning: Can not find ffmpeg. Some epub readers may failed to open these pictures.')  # noqa: E501


def perform_convert(image_path: str) -> Optional[str]:
    output_path = os.path.splitext(image_path)[0] + '_fallback.jpg'
    if os.path.exists(output_path) and os.path.getsize(output_path) > 4096:
        return output_path
    if have_ffmpeg is None:
        check_ffmpeg()
    if have_ffmpeg:
        p = subprocess.Popen(['ffmpeg', '-y', '-i', image_path, output_path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        p.communicate()
        code = p.wait()
        if not code:
            return output_path
        else:
            print(f'Warning: Can not convert images by using ffmpeg. (Exit code: {code}) Some epub readers may failed to open these pictures.')  # noqa: E501
            return None
    else:
        return None


class HTMLImage:
    def __init__(self, attrs, cfg: Config):
        self.src = None
        self.alt = None
        self.path = None
        self.epub_path = None
        for key, value in attrs:
            if key == 'src':
                self.src = value
            elif key == 'alt':
                self.alt = value
        self.cfg = cfg
        self.footnote = ''

    def is_valid(self):
        return self.src is not None and self.src != ''

    def download_image(self):
        if not self.is_valid():
            return False
        try:
            self.path = get_cache(self.cfg, self.src)
            return True
        except Exception:
            print_exc()

    def to_local(self, index: int):
        if not self.is_valid():
            return ""
        if not self.download_image():
            raise ValueError("Failed to download image.")
        self.epub_path = os.path.basename(self.path)
        if have_magic:
            with open(self.path, 'rb') as f:
                mime = magic.from_buffer(f.read(4096), True)
            self.epub_path = os.path.splitext(self.epub_path)[0] + get_extension(mime)  # noqa: E501
        if have_filetype:
            with open(self.path, 'rb') as f:
                mime = filetype.guess_mime(f.read(4096))
            self.epub_path = os.path.splitext(self.epub_path)[0] + get_extension(mime)  # noqa: E501
        d = {'src': self.epub_path}
        if self.alt:
            d['alt'] = self.alt
        img = ET.Element('img', d)
        if self.cfg.image_type == 'inline':
            return ET.tostring(img, 'unicode')
        else:
            link = ET.Element('a', {'href': f'#img{index}',
                                    'epub:type': 'noteref'})
            if self.alt:
                link.text = self.alt
            aside = ET.Element('aside', {'epub:type': 'footnote',
                                         'id': f'img{index}'})
            p = ET.Element('p')
            p.append(img)
            aside.append(p)
            self.footnote = ET.tostring(aside, 'unicode') + '\n'
            return ET.tostring(link, 'unicode')


# Used to parse content
class ContentParser(HTMLParser):
    def __init__(self, cfg: Config):
        super().__init__()
        self._in_paragraph = False
        self.data = []
        # Local image file lists
        self.images = []
        self._paragraph_data = ''
        self.cfg = cfg
        self.footnote = ''

    def handle_data(self, data: str):
        if self._in_paragraph:
            if isinstance(self._paragraph_data, str):
                self._paragraph_data += data
            elif isinstance(self._paragraph_data, list):
                self._paragraph_data.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            if self._in_paragraph:
                if self._paragraph_data:
                    self._paragraph_data = [self._paragraph_data]
                else:
                    self._paragraph_data = []
                self._paragraph_data.append(HTMLImage(attrs, self.cfg))
            else:
                self.data.append(HTMLImage(attrs, self.cfg))
        elif tag == 'p':
            self._in_paragraph = True
        elif tag == 'book':
            pass
        else:
            raise NotImplementedError()

    def handle_endtag(self, tag: str):
        if tag == 'img':
            pass
        elif tag == 'p':
            self._in_paragraph = False
            if self._paragraph_data:
                self.data.append(self._paragraph_data)
                self._paragraph_data = ''
        else:
            raise NotImplementedError()

    def have_image(self, data_list=None) -> bool:
        if data_list is None:
            data_list = self.data
        for i in data_list:
            if isinstance(i, HTMLImage):
                if i.is_valid():
                    return True
            elif isinstance(i, list):
                if self.have_image(i):
                    return True
        return False

    def to_local(self, data_list=None, root=None) -> str:
        default_data_list = False
        if data_list is None:
            data_list = self.data
            default_data_list = True
            root = self
            self.footnote = ''
        data = ''
        img_index = 0
        for i in data_list:
            if isinstance(i, str):
                if default_data_list:
                    data += f'<p>{i}</p>\n'
                else:
                    data += i
            elif isinstance(i, HTMLImage):
                if i.is_valid():
                    try:
                        data += i.to_local(img_index)
                        self.images.append(i)
                        if i.footnote:
                            root.footnote += i.footnote
                        img_index += 1
                    except ValueError:
                        print("the image is not valid.", i.src)
            elif isinstance(i, list):
                data += f'<p>{self.to_local(i, root)}</p>\n'
            else:
                raise NotImplementedError()
        if self._paragraph_data:
            data += f'<p>{self._paragraph_data}</p>\n'
        if default_data_list:
            data += self.footnote
        return data


def get_extension(mime: str) -> str:
    if mime == 'image/gif':
        return '.gif'
    elif mime == 'image/jpeg':
        return '.jpeg'
    elif mime == 'image/png':
        return '.png'
    elif mime == 'image/svg+xml':
        return '.svg'
    elif mime == 'image/webp':  # EPUB 3.3 Draft
        return '.webp'
    else:
        print(mime)
        raise NotImplementedError()


class EpubFile:
    def __init__(self, cfg: Config, out: str):
        self.epub = epub.EpubBook()
        self.EpubList = list()
        self.epub.set_language('zh-CN')
        self.cfg = cfg
        self.out = out

    def set_book(self, book):
        self.epub.set_identifier(str(book['book_id']))
        self.epub.set_title(book['book_name'])
        self.epub.add_author(book['author_name'])
        cover_path = get_cache(self.cfg, book['cover'])
        with open(cover_path, 'rb') as f:
            cover = f.read()
        if have_magic:
            mime_type = magic.from_buffer(cover, mime=True)
            file_name = 'cover' + get_extension(mime_type)
        elif have_filetype:
            mime_type = filetype.guess_mime(cover)
            file_name = 'cover' + get_extension(mime_type)
        else:
            file_name = 'cover.png'
        self.epub.set_cover(file_name, cover)
        intro = epub.EpubHtml(title='book-detailed', file_name='intro.xhtml',
                              lang='zh-CN')
        intro.content = f'''<html><head></head><body>
<h1>书名：{book['book_name']}</h1><p>ID：{book['book_id']}</p>
<p>作者：{book['author_name']}</p><p>更新时间：{book['uptime']}</p>
<p>最新章节：{book['last_chapter_info']['chapter_title']}</p></body></html>'''
        self.epub.add_item(intro)
        self.EpubList.append(intro)
        self.epub.spine.append(intro)
        self.last_division_name = ''

    def add_chapter(self, chapter, content: str, division_name: str):
        chapter_title = chapter['chapter_title']
        chapter_id = chapter['chapter_id']
        ch = epub.EpubHtml(
            title=chapter_title,
            file_name=f'ch{chapter_id}.xhtml',
            lang='zh-CN',
            uid=f'ch{chapter_id}',
        )
        if division_name == '作品相关':
            ch.is_linear = False
        parser = ContentParser(self.cfg)
        contents = content.splitlines()
        try:
            parser.feed('<p>' + '</p>\n<p>'.join(contents) + '</p>')
        except Exception as e:
            print('<p>' + '</p>\n<p>'.join(contents) + '</p>')
            raise e
        parser.close()
        ch.content = f'<h1 style="text-align: center;">{chapter_title}</h1>\n{parser.to_local()}'  # noqa: E501
        self.epub.add_item(ch)
        count = 0
        for oimg in parser.images:
            img = EpubPathImage()
            img.file_name = oimg.epub_path
            img.path = oimg.path
            img.id = f'i{chapter_id}_{count}'
            self.epub.add_item(img)
            if oimg.epub_path.endswith('.webp'):
                img.media_type = 'image/webp'
                jpg_path = perform_convert(oimg.path)
                if jpg_path is not None:
                    jpg_img = EpubPathImage()
                    jpg_img.file_name = os.path.basename(jpg_path)
                    jpg_img.path = jpg_path
                    jpg_img.id = img.id + 'f'
                    img.fallback = jpg_img.id
                    self.epub.add_item(jpg_img)
            count += 1
        if self.last_division_name != division_name:
            self.EpubList.append([epub.Link(ch.file_name, division_name), []])
            self.last_division_name = division_name
        if isinstance(self.EpubList[-1], list):
            self.EpubList[-1][-1].append(ch)
        else:
            self.EpubList.append(ch)
        self.epub.spine.append(ch)

    def add_nodownload_chapter(self, chapter, division_name: str):
        chapter_title = chapter['chapter_title']
        chapter_id = chapter['chapter_id']
        ch = epub.EpubHtml(
            title=f"{chapter_title} (未下载)",
            file_name=f'ch{chapter_id}.xhtml',
            lang='zh-CN',
            uid=f'ch{chapter_id}',
        )
        if division_name == '作品相关':
            ch.is_linear = False
        ch.content = f'<h1 style="text-align: center;">{chapter_title}</h1>\n<p>本章未下载</p>'  # noqa: E501
        self.epub.add_item(ch)
        if self.last_division_name != division_name:
            self.EpubList.append([epub.Link(ch.file_name, division_name), []])
            self.last_division_name = division_name
        if isinstance(self.EpubList[-1], list):
            self.EpubList[-1][-1].append(ch)
        else:
            self.EpubList.append(ch)
        self.epub.spine.append(ch)

    def save_epub_file(self):  # save epub file to local
        # the path to save epub file to local
        self.epub.toc = self.EpubList
        self.epub.add_item(epub.EpubNcx()), self.epub.add_item(epub.EpubNav())
        book = EpubWriter(self.out, self.epub, {})
        book.process()
        try:
            book.write()
        except IOError:
            print_exc()
