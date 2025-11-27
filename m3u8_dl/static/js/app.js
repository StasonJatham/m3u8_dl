function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`.tab[onclick="switchTab('${tabId}')"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

function toggleFields() {
    const type = document.getElementById('type-select').value;
    const movieFields = document.getElementById('movie-fields');
    const seriesFields = document.getElementById('series-fields');
    
    if (type === 'movie') {
        movieFields.classList.remove('hidden');
        seriesFields.classList.add('hidden');
    } else {
        movieFields.classList.add('hidden');
        seriesFields.classList.remove('hidden');
    }
}

async function saveSettings() {
    const form = document.getElementById('settings-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (response.ok) {
            alert('Settings saved successfully!');
        } else {
            alert('Failed to save settings.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving settings.');
    }
}

async function retryDownload(id) {
    if (!confirm('Retry this download?')) return;
    try {
        await fetch(`/api/retry/${id}`, { method: 'POST' });
    } catch (e) {
        alert('Failed to retry download');
    }
}

async function cancelDownload(id) {
    if (!confirm('Cancel this download?')) return;
    try {
        await fetch(`/api/cancel/${id}`, { method: 'POST' });
    } catch (e) {
        alert('Failed to cancel download');
    }
}

async function deleteDownload(id) {
    if (!confirm('Delete this download and file?')) return;
    try {
        const res = await fetch(`/api/download/${id}`, { method: 'DELETE' });
        if (res.ok) {
            document.getElementById(`download-${id}`).remove();
        } else {
            alert('Failed to delete download');
        }
    } catch (e) {
        alert('Failed to delete download');
    }
}

async function indexDownload(id) {
    try {
        const res = await fetch(`/api/index/${id}`, { method: 'POST' });
        if (res.ok) {
            alert('Indexing started');
        } else {
            const data = await res.json();
            alert('Failed to start indexing: ' + data.detail);
        }
    } catch (e) {
        alert('Failed to start indexing');
    }
}

function playVideo(path) {
    const modal = document.getElementById('video-modal');
    const player = document.getElementById('video-player');
    // Convert absolute path to relative /downloads/ path
    // Assuming path starts with configured download dir, but for simplicity we can just use the filename if we serve the dir
    const filename = path.split('/').pop();
    player.src = `/downloads/${filename}`;
    modal.classList.add('active');
    player.play();
}

function closeVideoModal() {
    const modal = document.getElementById('video-modal');
    const player = document.getElementById('video-player');
    player.pause();
    player.src = '';
    modal.classList.remove('active');
}

function getActionButtons(download) {
    let buttons = '';
    if (download.status === 'failed') {
        buttons += `<button class="action-btn" onclick="retryDownload(${download.id})">Retry</button>`;
        buttons += `<button class="action-btn" onclick="deleteDownload(${download.id})">Delete</button>`;
    }
    if (download.status === 'completed') {
        if (download.file_path) {
            buttons += `<button class="action-btn" onclick="playVideo('${download.file_path.replace(/\\/g, '/')}')">Play</button>`;
            buttons += `<button class="action-btn" onclick="indexDownload(${download.id})">Index</button>`;
        }
        buttons += `<button class="action-btn" onclick="deleteDownload(${download.id})">Delete</button>`;
    }
    if (download.status === 'downloading' || download.status === 'queued') {
        buttons += `<button class="action-btn" onclick="cancelDownload(${download.id})">Cancel</button>`;
    }
    return buttons;
}

// WebSocket for real-time updates
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'new') {
        // Add new row to table
        const tbody = document.querySelector('#history-table tbody');
        const tr = document.createElement('tr');
        tr.id = `download-${data.download.id}`;
        tr.innerHTML = `
            <td>${data.download.title}</td>
            <td>${data.download.type}</td>
            <td><span class="status-badge">${data.download.status}</span></td>
            <td>
                ${data.download.progress}
                <div class="progress-bar" style="width: ${data.download.progress}"></div>
            </td>
            <td>
                <span class="task-text">${data.download.task}</span>
                <div class="actions">${getActionButtons(data.download)}</div>
            </td>
        `;
        tbody.insertBefore(tr, tbody.firstChild);
    } else if (data.type === 'update') {
        // Update existing row
        const tr = document.getElementById(`download-${data.id}`);
        if (tr) {
            tr.querySelector('.status-badge').textContent = data.status;
            tr.querySelector('td:nth-child(4)').innerHTML = `
                ${data.progress}
                <div class="progress-bar" style="width: ${data.progress}"></div>
            `;
            
            const taskCell = tr.querySelector('td:nth-child(5)');
            let taskText = data.task;
            if (data.error) {
                taskText = data.error;
                taskCell.style.color = 'red';
            } else {
                taskCell.style.color = 'inherit';
            }
            
            // Update actions based on new status
            // We construct a mock download object to reuse getActionButtons
            const mockDownload = { id: data.id, status: data.status };
            taskCell.innerHTML = `
                <span class="task-text">${taskText}</span>
                <div class="actions">${getActionButtons(mockDownload)}</div>
            `;
        }
    }
};

// Initialize state
document.addEventListener('DOMContentLoaded', () => {
    toggleFields();
});
