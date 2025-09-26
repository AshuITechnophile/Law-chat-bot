class ChatInterface {
    constructor() {
        this.currentChatId = null;
        this.chatHistory = [];
        this.isProcessing = false;
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.currentLanguage = localStorage.getItem('chatLanguage') || 'en';
        this.currentJurisdiction = localStorage.getItem('chatJurisdiction') || 'us';
        this.apiUrl = 'http://localhost:5000/api';
        this.apiAvailable = false;
        this.offlineMode = localStorage.getItem('offlineMode') === 'true';
        this.sessionId = localStorage.getItem('chat_session_id') || this.generateSessionId();
        this.messages = [];
        this.lastApiCheck = 0;
        this.apiCheckInterval = 30000;
        this.setupEventListeners();
        this.loadChatHistory();
        this.setupTheme();
        this.setupBackToTop();
        this.setupAccessibility();
        this.setupFileUpload();
        this.checkApiAvailability();
        this.cache = {};
    }

    async init() {
        await this.checkApiAvailability();
        this.showWelcomeMessage();
        setInterval(() => this.checkApiAvailability(), this.apiCheckInterval);
    }

    debounce(func, wait) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    async fetchWithCache(url) {
        if (this.cache[url]) {
            return this.cache[url];
        }
        const response = await fetch(url);
        const data = await response.json();
        this.cache[url] = data;
        return data;
    }

    log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        console[level](`[${timestamp}] ${message}`);
    }

    async checkApiAvailability() {
        try {
            const now = Date.now();
            if (now - this.lastApiCheck < this.apiCheckInterval && this.lastApiCheck !== 0) {
                return;
            }
            this.lastApiCheck = now;
            const response = await this.fetchWithCache(`${this.apiUrl}/health`);
            this.apiAvailable = response.ok;
            this.updateApiStatusIndicator();
            this.log(`API status: ${this.apiAvailable ? 'Available' : 'Unavailable'}`);
            return this.apiAvailable;
        } catch (error) {
            this.log('Error checking API availability: ' + error.message, 'error');
            this.apiAvailable = false;
            this.updateApiStatusIndicator();
            return false;
        }
    }

    updateApiStatusIndicator() {
        const statusElement = document.getElementById('api-status');
        if (!statusElement) {
            const chatHeader = document.querySelector('.chat-header');
            if (chatHeader) {
                const statusIndicator = document.createElement('div');
                statusIndicator.id = 'api-status';
                statusIndicator.className = `status-indicator ${this.apiAvailable ? 'online' : 'offline'}`;
                statusIndicator.innerHTML = `
                    <span class="status-dot"></span>
                    <span class="status-text">${this.apiAvailable ? 'Online' : 'Offline'}</span>
                `;
                chatHeader.appendChild(statusIndicator);
            }
        } else {
            statusElement.className = `status-indicator ${this.apiAvailable ? 'online' : 'offline'}`;
            statusElement.querySelector('.status-text').textContent = this.apiAvailable ? 'Online' : 'Offline';
        }
    }

    setupEventListeners() {
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const uploadButton = document.getElementById('upload-button');
        const clearChatBtn = document.getElementById('clear-chat');

        if (!userInput || !sendButton) {
            console.error('Chat input elements not found');
            return;
        }

        sendButton.addEventListener('click', () => this.handleSendMessage());
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });

        if (uploadButton) {
            uploadButton.addEventListener('click', () => {
                const fileUploadModal = new bootstrap.Modal(document.getElementById('uploadModal'));
                fileUploadModal.show();
            });
        }

        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => this.clearCurrentChat());
        }

        const documentFile = document.getElementById('document-file');
        const uploadSubmit = document.getElementById('upload-submit');

        if (documentFile && uploadSubmit) {
            documentFile.addEventListener('change', () => this.handleFileSelection());
            uploadSubmit.addEventListener('click', () => this.handleFileUpload());
        }

        if (userInput) {
            userInput.addEventListener('input', () => this.autoResizeTextarea(userInput));
            setTimeout(() => this.autoResizeTextarea(userInput), 100);
        }

        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
            languageSelect.addEventListener('change', (e) => this.setLanguage(e.target.value));
        }

        const jurisdictionSelect = document.getElementById('jurisdiction-select');
        if (jurisdictionSelect) {
            jurisdictionSelect.addEventListener('change', (e) => this.setJurisdiction(e.target.value));
        }

        window.addEventListener('scroll', () => this.handleScroll());
    }

    setupFileUpload() {
        const fileUploadWrapper = document.querySelector('.file-upload-wrapper');
        const fileInput = document.getElementById('documentUpload');
        
        if (!fileUploadWrapper || !fileInput) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUploadWrapper.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUploadWrapper.addEventListener(eventName, () => {
                fileUploadWrapper.classList.add('dragover');
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileUploadWrapper.addEventListener(eventName, () => {
                fileUploadWrapper.classList.remove('dragover');
            });
        });
        
        fileUploadWrapper.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt.files.length) {
                fileInput.files = dt.files;
                this.handleFileSelection();
            }
        });
        
        fileUploadWrapper.addEventListener('click', () => {
            fileInput.click();
        });
    }

    setupTheme() {
        document.body.classList.toggle('dark-theme', this.currentTheme === 'dark');
        const themeIcon = document.querySelector('#theme-toggle i');
        if (themeIcon) {
            themeIcon.className = this.currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.currentTheme);
        this.setupTheme();
    }

    setLanguage(language) {
        this.currentLanguage = language;
        localStorage.setItem('chatLanguage', language);
        
        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
            languageSelect.value = language;
        }

        this.addMessage('system', `Language changed to ${language}`);
    }

    setJurisdiction(jurisdiction) {
        this.currentJurisdiction = jurisdiction;
        localStorage.setItem('chatJurisdiction', jurisdiction);
        
        const jurisdictionSelect = document.getElementById('jurisdiction-select');
        if (jurisdictionSelect) {
            jurisdictionSelect.value = jurisdiction;
        }

        this.addMessage('system', `Jurisdiction changed to ${jurisdiction}`);
    }

    setupBackToTop() {
        const backToTop = document.getElementById('back-to-top');
        if (!backToTop) return;
        
        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    handleScroll() {
        const backToTop = document.getElementById('back-to-top');
        if (backToTop) {
            if (window.scrollY > 300) {
                backToTop.classList.add('show');
            } else {
                backToTop.classList.remove('show');
            }
        }
    }

    setupAccessibility() {
        const userInput = document.getElementById('userInput');
        const sendButton = document.getElementById('sendMessageBtn');
        const attachFileBtn = document.getElementById('attachFileBtn');

        if (userInput) userInput.setAttribute('aria-label', 'Type your message');
        if (sendButton) sendButton.setAttribute('aria-label', 'Send message');
        if (attachFileBtn) attachFileBtn.setAttribute('aria-label', 'Attach file');

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = bootstrap.Modal.getInstance(document.getElementById('fileUploadModal'));
                if (modal) {
                    modal.hide();
                }
            }
        });
    }

    showLoadingState(element) {
        if (!element) return;
        element.classList.add('loading');
        element.setAttribute('aria-busy', 'true');
    }

    hideLoadingState(element) {
        if (!element) return;
        element.classList.remove('loading');
        element.setAttribute('aria-busy', 'false');
    }

    sanitizeInput(input) {
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }

    handleSendMessage = this.debounce(async function() {
        const rawMessage = document.getElementById('user-input').value.trim();
        const message = this.sanitizeInput(rawMessage);
        if (!message) return;
        this.addMessage('user', message);
        this.log('User sent a message: ' + message);
        try {
            if (!this.apiAvailable) {
                const apiAvailable = await this.checkApiAvailability();
                if (!apiAvailable) {
                    this.addMessage('assistant', 'The server is currently offline. Please try again later.');
                    return;
                }
            }
            this.showTypingIndicator();
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, sessionId: this.sessionId })
            });
            this.hideTypingIndicator();
            if (response.ok) {
                const data = await response.json();
                this.addMessage('assistant', data.response);
                this.log('Assistant responded: ' + data.response);
            } else {
                this.addMessage('assistant', 'Error processing your request. Please try again later.');
                this.log('Error processing request: ' + response.statusText, 'error');
            }
        } catch (error) {
            this.log('Error sending message: ' + error.message, 'error');
            this.hideTypingIndicator();
            this.addMessage('assistant', 'Error processing your request. Please try again later.');
            this.apiAvailable = false;
            this.updateApiStatusIndicator();
        }
    }, 300);

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    }

    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success alert-dismissible fade show';
        successDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.chat-container');
        if (container) {
            const messagesEl = container.querySelector('.chat-messages');
            if (messagesEl) {
                container.insertBefore(successDiv, messagesEl);
            } else {
                container.prepend(successDiv);
            }
            
            setTimeout(() => {
                if (successDiv.parentNode) {
                    successDiv.parentNode.removeChild(successDiv);
                }
            }, 5000);
        }
    }

    addMessageToChat(sender, content) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessageContent(content)}
            </div>
            <div class="message-timestamp">
                <i class="fas fa-clock"></i> ${timestamp}
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    formatMessageContent(content) {
        if (!content) return '';
        
        content = content.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank">$1</a>'
        );

        content = content.replace(
            /^\s*[-*]\s+(.+)$/gm,
            '<li>$1</li>'
        );

        content = content.replace(
            /(<li>.*<\/li>)/gs,
            '<ul>$1</ul>'
        );

        content = content.replace(
            /^#{1,6}\s+(.+)$/gm,
            (match, p1, offset, string) => {
                const level = match.indexOf(' ');
                return `<h${level}>${p1}</h${level}>`;
            }
        );

        content = content.replace(
            /\*\*(.*?)\*\*/g,
            '<strong>$1</strong>'
        );

        content = content.replace(
            /\*(.*?)\*/g,
            '<em>$1</em>'
        );

        return content;
    }

    async handleFileSelection() {
        const fileInput = document.getElementById('document-file');
        const file = fileInput.files[0];
        if (file) {
            const fileNameDisplay = document.getElementById('file-name');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = file.name;
            }
        }
    }

    async handleFileUpload() {
        const fileInput = document.getElementById('document-file');
        const file = fileInput.files[0];
        if (!file) {
            this.showError('Please select a file to upload');
            this.log('File upload failed: No file selected', 'error');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${this.apiUrl}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const result = await response.json();
            this.addMessage('assistant', `File "${file.name}" uploaded successfully. I'll analyze it for you.`);
            this.log(`File uploaded successfully: ${file.name}`);
            
            const uploadModal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
            if (uploadModal) {
                uploadModal.hide();
            }

            fileInput.value = '';
            const fileNameDisplay = document.getElementById('file-name');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = 'No file selected';
            }
        } catch (error) {
            this.log('Upload error: ' + error.message, 'error');
            this.showError('Failed to upload file. Please try again.');
        }
    }

    startNewChat() {
        this.currentChatId = Date.now().toString();
        const titleElement = document.getElementById('currentChatTitle');
        if (titleElement) titleElement.textContent = 'New Chat';
        
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        chatMessages.innerHTML = `
            <div class="chat-message assistant">
                <div class="message-content">
                    <h4>Welcome to Ritvika Legal AI Assistant!</h4>
                    <p>I'm here to help you with:</p>
                    <ul>
                        <li>Legal questions and guidance</li>
                        <li>Document analysis and explanation</li>
                        <li>Case law research</li>
                        <li>Legal terminology clarification</li>
                        <li>Basic legal procedures</li>
                    </ul>
                    <p>How can I assist you today?</p>
                </div>
                <div class="message-timestamp">
                    <i class="fas fa-clock"></i> Just now
                </div>
            </div>
        `;
        this.updateChatHistory();
    }

    clearCurrentChat() {
        const chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.innerHTML = '';
            this.chatHistory = [];
            this.saveChatHistory();
            this.showWelcomeMessage();
        }
    }

    async exportChat() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const messages = Array.from(chatMessages.children).map(msg => {
            const content = msg.querySelector('.message-content').innerHTML;
            const timestamp = msg.querySelector('.message-timestamp').textContent;
            const sender = msg.classList.contains('user') ? 'You' : 'Assistant';
            return `${sender} (${timestamp}): ${content}`;
        }).join('\n\n');

        const blob = new Blob([messages], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-export-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        this.showSuccess('Chat exported successfully');
    }

    loadChatHistory() {
        try {
            const history = localStorage.getItem('chatHistory');
            if (history) {
                this.chatHistory = JSON.parse(history);
                this.updateChatHistoryList();
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            localStorage.removeItem('chatHistory');
            this.chatHistory = [];
        }
    }

    updateChatHistory() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        try {
            const messages = Array.from(chatMessages.children).map(msg => ({
                sender: msg.classList.contains('user') ? 'user' : 'assistant',
                content: msg.querySelector('.message-content').innerHTML,
                timestamp: msg.querySelector('.message-timestamp').textContent
            }));

            const chatTitle = document.getElementById('currentChatTitle');
            const title = chatTitle ? chatTitle.textContent : 'New Chat';
            
            if (messages.length <= 1) return;
            
            const existingChatIndex = this.chatHistory.findIndex(chat => chat.id === this.currentChatId);
            if (existingChatIndex !== -1) {
                this.chatHistory[existingChatIndex] = {
                    id: this.currentChatId,
                    title: title,
                    messages: messages,
                    lastUpdated: new Date().toISOString()
                };
            } else {
                this.chatHistory.push({
                    id: this.currentChatId,
                    title: title,
                    messages: messages,
                    lastUpdated: new Date().toISOString()
                });
            }

            this.chatHistory = this.chatHistory
                .sort((a, b) => new Date(b.lastUpdated) - new Date(a.lastUpdated))
                .slice(0, 20);

            localStorage.setItem('chatHistory', JSON.stringify(this.chatHistory));
            this.updateChatHistoryList();
        } catch (error) {
            console.error('Error updating chat history:', error);
        }
    }

    updateChatHistoryList() {
        const historyList = document.getElementById('chatHistoryList');
        if (!historyList) return;
        
        historyList.innerHTML = '';

        const sortedHistory = [...this.chatHistory].sort((a, b) => {
            return new Date(b.lastUpdated || 0) - new Date(a.lastUpdated || 0);
        });

        if (sortedHistory.length === 0) {
            historyList.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-history fa-2x mb-2"></i>
                    <p>No chat history yet</p>
                </div>
            `;
            return;
        }

        sortedHistory.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = `chat-history-item ${chat.id === this.currentChatId ? 'active' : ''}`;
            
            let title = chat.title;
            if (title === 'New Chat') {
                const firstUserMessage = chat.messages.find(m => m.sender === 'user');
                if (firstUserMessage) {
                    const plainText = firstUserMessage.content.replace(/<[^>]*>/g, '');
                    title = plainText.substring(0, 25) + (plainText.length > 25 ? '...' : '');
                }
            }
            
            chatItem.innerHTML = `
                <i class="fas fa-comments"></i>
                <span>${title}</span>
            `;
            chatItem.addEventListener('click', () => this.loadChat(chat));
            historyList.appendChild(chatItem);
        });
    }

    loadChat(chat) {
        this.currentChatId = chat.id;
        const titleElement = document.getElementById('currentChatTitle');
        if (titleElement) titleElement.textContent = chat.title;
        
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        chatMessages.innerHTML = '';
        
        chat.messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chat-message ${msg.sender}`;
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${msg.content}
                </div>
                <div class="message-timestamp">
                    <i class="fas fa-clock"></i> ${msg.timestamp}
                </div>
            `;
            chatMessages.appendChild(messageDiv);
        });
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
        this.updateChatHistoryList();
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    }

    toggleOfflineMode() {
        this.offlineMode = !this.offlineMode;
        localStorage.setItem('offlineMode', this.offlineMode.toString());
        
        if (this.offlineMode) {
            this.apiAvailable = false;
            this.showSuccess('Offline mode enabled. The application will not attempt to connect to the backend.');
        } else {
            this.showSuccess('Offline mode disabled. Attempting to connect to the backend...');
            this.checkApiAvailability();
        }
        
        this.updateApiStatusIndicator();
    }

    showTypingIndicator() {
        const chatContainer = document.querySelector('.chat-messages');
        if (!chatContainer) return;

        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message assistant typing';
        typingIndicator.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        chatContainer.appendChild(typingIndicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    showWelcomeMessage() {
        const welcomeMessage = `
            Hello! I'm your AI legal assistant. I can help you with:
            <ul>
                <li>General legal information and guidance</li>
                <li>Document analysis and review</li>
                <li>Case law research</li>
                <li>Legal document generation</li>
                <li>Connecting with legal professionals</li>
            </ul>
            Please note that I provide general information only and cannot replace professional legal advice.
            How can I assist you today?
        `;
        this.addMessage('assistant', welcomeMessage);
    }

    generateSessionId() {
        const sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('chat_session_id', sessionId);
        return sessionId;
    }

    addMessage(role, content) {
        const chatContainer = document.querySelector('.chat-messages');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${content}
            </div>
        `;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        this.messages.push({ role, content, timestamp: new Date().toISOString() });
        this.saveChatHistory();
    }

    saveChatHistory() {
        localStorage.setItem('chat_history', JSON.stringify(this.messages));
    }

    loadChatHistory() {
        const savedHistory = localStorage.getItem('chat_history');
        if (savedHistory) {
            try {
                this.messages = JSON.parse(savedHistory);
                this.messages.forEach(msg => this.addMessage(msg.role, msg.content));
            } catch (error) {
                console.error('Error loading chat history:', error);
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        const chatInterface = new ChatInterface();
        if (!chatInterface.currentChatId) {
            chatInterface.startNewChat();
        }
        
        const chatStatus = document.getElementById('chatStatus');
        if (chatStatus) {
            chatStatus.addEventListener('click', (e) => {
                if (e.target === chatStatus || e.target.tagName === 'I') {
                    chatInterface.toggleOfflineMode();
                }
            });
        }
        
        window.chatInterface = chatInterface;
    } catch (error) {
        console.error('Error initializing chat interface:', error);
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML += `
                <div class="chat-message assistant">
                    <div class="message-content">
                        <p>An error occurred while initializing the chat interface. Please try refreshing the page.</p>
                    </div>
                    <div class="message-timestamp">
                        <i class="fas fa-clock"></i> Just now
                    </div>
                </div>
            `;
        }
    }
}); 