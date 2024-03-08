# Setup
## Termux
```shell
pkg install git libxml2 libxslt python ffmpeg
git clone https://github.com/lifegpc/cwm_export
cd cwm_export
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
# Usage
## Termux
```shell
sudo python main.py -r
# Only export as txt file
sudo python main.py --type=txt -r
# Only export as epub file
sudo python main.py --type=epub -r
# Export all supported type
sudo python main.py --type=epub,txt -r
# Export single chapter with chapter id
sudo python main.py ec -C <chapterid>
# Export book with book id
sudo python main.py eb -B <bookid>
```
