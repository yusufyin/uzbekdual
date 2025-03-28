const API_ENDPOINTS = {
    search: '/search'
};

let searchDebounce;
document.getElementById('searchInput').addEventListener('input', function(e) {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => handleSearch(e.target.value), 300);
});

async function handleSearch(term) {
    try {
        const response = await fetch(API_ENDPOINTS.search, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({term})
        });
        
        const [local, remote] = await response.json();
        renderResults(local, document.getElementById('localResults'));
        renderResults(remote, document.getElementById('remoteResults'));
    } catch (error) {
        console.error('搜索失败:', error);
    }
}

function renderResults({source, data}, container) {
    container.innerHTML = `
        <div class="source-header">${source === 'local' ? '本地词典' : '扩展词库'}</div>
        ${data.slice(0, 20).map(item => `
            <div class="result-item">
                <div class="word">${item}</div>
                ${source === 'local' ? 
                    `<div class="definition">${LOCAL_LEXICON[item]}</div>` : 
                    `<div class="external">点击查看详细解释 →</div>`
                }
            </div>
        `).join('')}
    `;
}