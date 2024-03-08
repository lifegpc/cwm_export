from config import Config
from math import ceil


def ask_choice(cfg: Config, choices: list, prompt='请选择：', fn=None, extra=None):
    count = len(choices)
    total_pages = ceil(count / cfg.page_size)
    page = 1

    def show_page():
        nonlocal page
        base = (page - 1) * cfg.page_size
        if total_pages > 1:
            print(f"第{page}/{total_pages}页")
        for i in range(cfg.page_size):
            index = base + i
            if index >= count:
                break
            s = fn(choices[index]) if fn else choices[index]
            print(f"{i}. {s}")
        if page > 1:
            print("f. 第一页")
            print("p. 上一页")
        if page < total_pages:
            print("n. 下一页")
            print("l. 最后一页")
        if extra is not None:
            for t in extra:
                print(f"{t[0]}. {t[1]}")

    while True:
        show_page()
        s = input(prompt)
        if s == "f":
            page = 1
        elif s == "p":
            page = max(1, page - 1)
        elif s == "n":
            page = min(total_pages, page + 1)
        elif s == "l":
            page = total_pages
        else:
            if extra is not None:
                for t in extra:
                    if t[0] == s:
                        return t[2]
            try:
                index = int(s)
            except Exception:
                continue
            base = (page - 1) * cfg.page_size
            index += base
            if index < 0 or index >= count:
                continue
            return choices[index]
