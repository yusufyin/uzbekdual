import os

class Config:
    LOCAL_LEXICON_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'lexicon.json')
    REMOTE_API_BASE = 'https://ctild.sitehost.iu.edu/dict/ajax.php'
    CACHE_TIMEOUT = 3600  # 1小时缓存