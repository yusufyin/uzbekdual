from flask import Flask, render_template, jsonify, request
import requests
import json
import sqlite3
from datetime import datetime
import hashlib

app = Flask(__name__)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('search_cache.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS search_history
                 (term_hash TEXT PRIMARY KEY,
                  term TEXT NOT NULL,
                  remote_data TEXT,
                  local_data TEXT,
                  created_at TIMESTAMP,
                  last_accessed TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# 加载本地词典
with open('lexicon.json', 'r', encoding='utf-8') as f:
    LOCAL_LEXICON = json.load(f)

# 浏览器请求头配置
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.google.com/'
}

def get_term_hash(term):
    return hashlib.md5(term.encode('utf-8')).hexdigest()

def cache_search(term, remote_data, local_data):
    term_hash = get_term_hash(term)
    conn = sqlite3.connect('search_cache.db')
    c = conn.cursor()
    
    c.execute('''INSERT OR REPLACE INTO search_history 
                 (term_hash, term, remote_data, local_data, created_at, last_accessed)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (term_hash, term, 
               json.dumps(remote_data), 
               json.dumps(local_data),
               datetime.now(),
               datetime.now()))
    conn.commit()
    conn.close()

def get_cached_search(term):
    term_hash = get_term_hash(term)
    conn = sqlite3.connect('search_cache.db')
    c = conn.cursor()
    
    c.execute('''SELECT remote_data, local_data FROM search_history 
                 WHERE term_hash = ?''', (term_hash,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'remote': json.loads(result[0]),
            'local': json.loads(result[1])
        }
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    term = request.json.get('term', '').strip()
    if not term:
        return jsonify({'error': 'Empty search term'})
    
    # 检查缓存
    cached = get_cached_search(term)
    if cached:
        # 更新最后访问时间
        term_hash = get_term_hash(term)
        conn = sqlite3.connect('search_cache.db')
        conn.execute('''UPDATE search_history 
                       SET last_accessed = ?
                       WHERE term_hash = ?''',
                    (datetime.now(), term_hash))
        conn.commit()
        conn.close()
        
        return jsonify([
            {'source': 'remote', 'data': cached['remote'], 'cached': True},
            {'source': 'local', 'data': cached['local'], 'cached': True}
        ])
    
    # 处理在线搜索词形
    modified_term = term
    if term.lower().endswith('moq'):
        modified_term = term[:-3] + '-'

    # 在线搜索
    try:
        remote_response = requests.post(
            'https://ctild.sitehost.iu.edu/dict/ajax.php',
            data={'do': 'search', 'search': modified_term},
            headers=BROWSER_HEADERS,
            timeout=5
        )
        remote_data = remote_response.text.split('§')[1:]
    except Exception as e:
        remote_data = [f"网络错误: {str(e)}"]

    # 本地搜索
    search_term = term.lower()
    local_data = [
        {"word": k, "definition": v} 
        for k, v in LOCAL_LEXICON.items() 
        if k.lower().startswith(search_term)
    ]
    
    # 缓存结果
    cache_search(term, remote_data, local_data)
    
    return jsonify([
        {'source': 'remote', 'data': remote_data, 'cached': False},
        {'source': 'local', 'data': local_data, 'cached': False}
    ])

if __name__ == '__main__':
    app.run(port=5000, debug=True)