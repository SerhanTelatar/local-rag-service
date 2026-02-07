/**
 * Local RAG Service - Frontend JavaScript
 * Handles document upload, chat interactions, and API communication
 */

// API Configuration
const API_BASE = '/api';

// DOM Elements
const elements = {
    statusBadge: document.getElementById('statusBadge'),
    docCount: document.getElementById('docCount'),
    fileUpload: document.getElementById('fileUpload'),
    documentList: document.getElementById('documentList'),
    messagesContainer: document.getElementById('messagesContainer'),
    questionInput: document.getElementById('questionInput'),
    askButton: document.getElementById('askButton'),
    toastContainer: document.getElementById('toastContainer')
};

// State
let isLoading = false;
let documents = [];

// ===========================
// Initialization
// ===========================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    setupEventListeners();
    await checkHealth();
    await loadDocuments();
}

function setupEventListeners() {
    // File upload
    elements.fileUpload.addEventListener('change', handleFileUpload);

    // Question input
    elements.questionInput.addEventListener('input', handleInputChange);
    elements.questionInput.addEventListener('keydown', handleKeyDown);

    // Ask button
    elements.askButton.addEventListener('click', handleAskQuestion);
}

// ===========================
// Health Check
// ===========================

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        updateStatus(data.llm_status === 'connected', data.documents_count);
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatus(false, 0);
    }
}

function updateStatus(isConnected, docCount) {
    const dot = elements.statusBadge.querySelector('.status-dot');
    const text = elements.statusBadge.querySelector('.status-text');

    dot.classList.remove('connected', 'disconnected');

    if (isConnected) {
        dot.classList.add('connected');
        text.textContent = 'Connected';
    } else {
        dot.classList.add('disconnected');
        text.textContent = 'Disconnected';
    }

    elements.docCount.textContent = docCount;
    updateAskButton();
}

// ===========================
// Document Management
// ===========================

async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/documents`);
        const data = await response.json();

        documents = data.documents;
        renderDocumentList();
        elements.docCount.textContent = data.total_count;
        updateAskButton();
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

function renderDocumentList() {
    if (documents.length === 0) {
        elements.documentList.innerHTML = '<p class="empty-state">No documents uploaded yet</p>';
        return;
    }

    elements.documentList.innerHTML = documents.map(doc => `
        <div class="document-item" data-filename="${escapeHtml(doc.filename)}">
            <span class="doc-icon">${getFileIcon(doc.filename)}</span>
            <div class="doc-info">
                <div class="doc-name" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</div>
                <div class="doc-meta">${formatFileSize(doc.size_bytes)}</div>
            </div>
            <button class="doc-delete" onclick="deleteDocument('${escapeHtml(doc.filename)}')" title="Delete">🗑️</button>
        </div>
    `).join('');
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    showToast('Uploading...', 'warning');

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showToast(`✓ ${data.filename} uploaded (${data.chunks_created} chunks)`, 'success');
            await loadDocuments();
            await checkHealth();
        } else {
            showToast(`✗ ${data.detail || 'Upload failed'}`, 'error');
        }
    } catch (error) {
        console.error('Upload failed:', error);
        showToast('✗ Upload error', 'error');
    }

    // Reset file input
    event.target.value = '';
}

async function deleteDocument(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/documents/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast(`✓ ${filename} deleted`, 'success');
            await loadDocuments();
            await checkHealth();
        } else {
            const data = await response.json();
            showToast(`✗ ${data.detail || 'Delete failed'}`, 'error');
        }
    } catch (error) {
        console.error('Delete failed:', error);
        showToast('✗ Delete error', 'error');
    }
}

// ===========================
// Chat / Question Handling
// ===========================

function handleInputChange() {
    // Auto-resize textarea
    const textarea = elements.questionInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';

    updateAskButton();
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleAskQuestion();
    }
}

function updateAskButton() {
    const hasDocuments = parseInt(elements.docCount.textContent) > 0;
    const hasQuestion = elements.questionInput.value.trim().length > 0;

    elements.askButton.disabled = !hasDocuments || !hasQuestion || isLoading;
}

async function handleAskQuestion() {
    const question = elements.questionInput.value.trim();
    if (!question || isLoading) return;

    isLoading = true;
    updateAskButton();

    // Clear welcome message if present
    const welcomeMsg = elements.messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Add user message
    addMessage(question, 'user');
    elements.questionInput.value = '';
    handleInputChange();

    // Show loading
    showButtonLoader(true);
    const loadingMsgId = addLoadingMessage();

    try {
        const response = await fetch(`${API_BASE}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, top_k: 3 })
        });

        const data = await response.json();

        // Remove loading message
        removeMessage(loadingMsgId);

        if (response.ok) {
            addMessage(data.answer, 'assistant', data.sources, data.processing_time);
        } else {
            addMessage(`Error: ${data.detail || 'Something went wrong'}`, 'assistant');
        }
    } catch (error) {
        console.error('Ask failed:', error);
        removeMessage(loadingMsgId);
        addMessage('Error: Could not connect to server', 'assistant');
    }

    isLoading = false;
    showButtonLoader(false);
    updateAskButton();
}

function addMessage(text, type, sources = [], time = null) {
    const id = 'msg-' + Date.now();
    const avatar = type === 'user' ? '👤' : '🤖';

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="message-sources">
                <div class="sources-label">Sources:</div>
                ${sources.map(s => `<span class="source-item" title="${escapeHtml(s.content)}">${escapeHtml(s.source)} (${(s.score * 100).toFixed(0)}%)</span>`).join('')}
            </div>
        `;
    }

    let timeHtml = '';
    if (time !== null) {
        timeHtml = `<div class="message-time">${time.toFixed(1)} seconds</div>`;
    }

    const messageHtml = `
        <div class="message ${type}" id="${id}">
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${escapeHtml(text)}</div>
                ${sourcesHtml}
                ${timeHtml}
            </div>
        </div>
    `;

    elements.messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
    scrollToBottom();

    return id;
}

function addLoadingMessage() {
    const id = 'msg-loading-' + Date.now();

    const messageHtml = `
        <div class="message assistant" id="${id}">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;

    elements.messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
    scrollToBottom();

    return id;
}

function removeMessage(id) {
    const msg = document.getElementById(id);
    if (msg) {
        msg.remove();
    }
}

function showButtonLoader(show) {
    const text = elements.askButton.querySelector('.button-text');
    const loader = elements.askButton.querySelector('.button-loader');

    if (show) {
        text.hidden = true;
        loader.hidden = false;
    } else {
        text.hidden = false;
        loader.hidden = true;
    }
}

function scrollToBottom() {
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

// ===========================
// Toast Notifications
// ===========================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.25s ease reverse';
        setTimeout(() => toast.remove(), 250);
    }, 3000);
}

// ===========================
// Utility Functions
// ===========================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📕',
        'txt': '📄',
        'md': '📝',
        'docx': '📘'
    };
    return icons[ext] || '📄';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Expose deleteDocument to global scope for onclick handlers
window.deleteDocument = deleteDocument;
