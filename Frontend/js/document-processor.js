class DocumentProcessor {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/api';
        this.currentLanguage = localStorage.getItem('language') || 'en';
        this.currentJurisdiction = localStorage.getItem('jurisdiction') || 'us';
        this.setupEventListeners();
        this.loadDocumentTemplates();
        this.setupFileUpload();
        this.setupThemeToggle();
        this.setupBackToTop();
        this.setupLocalization();
        this.loadTranslations();
        this.setupComplianceFeatures();
        this.setupNewsFeatures();
        this.setupFaqFeatures();
        this.newsWebSocket = null;
        this.newsPage = 1;
        this.newsLoading = false;
        this.newsHasMore = true;
        this.faqs = [];
        this.faqCategories = [];
        this.searchHistory = [];
        this.feedbackHistory = [];
    }

    setupEventListeners() {
        // Document Analysis
        document.getElementById('analyze-document').addEventListener('click', () => this.handleDocumentAnalysis());
        
        // Document Generation
        document.getElementById('template-select').addEventListener('change', () => this.updateTemplateForm());
        document.getElementById('generate-document').addEventListener('click', () => this.handleDocumentGeneration());
        
        // Document Monitoring
        document.getElementById('register-monitoring').addEventListener('click', () => this.handleDocumentMonitoring());
        document.getElementById('check-updates').addEventListener('click', () => this.checkDocumentUpdates());
        
        // Theme Toggle
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());
        
        // Back to Top
        window.addEventListener('scroll', () => this.handleScroll());
        document.getElementById('back-to-top').addEventListener('click', () => this.scrollToTop());

        // Lawyer connection event listeners
        document.getElementById('startLiveChatBtn').addEventListener('click', () => this.initiateLiveChat());
        document.getElementById('findExpertBtn').addEventListener('click', () => this.findExpertMatch());
        document.getElementById('bookAppointmentBtn').addEventListener('click', () => this.bookAppointment());
        document.getElementById('sendMessageBtn')?.addEventListener('click', () => this.sendChatMessage());
        document.getElementById('chatInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });

        // Setup appointment form handlers
        document.getElementById('caseCategorySelect')?.addEventListener('change', () => this.updateLawyerList());
        document.getElementById('appointmentDate')?.addEventListener('change', () => this.updateAvailableTimeSlots());
    }

    setupFileUpload() {
        const fileUpload = document.getElementById('document-upload');
        const dropZone = document.querySelector('.file-upload-wrapper');

        // Handle drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length) {
                this.handleFileUpload(files[0]);
            }
        });

        // Handle file input change
        fileUpload.addEventListener('change', (e) => {
            if (e.target.files.length) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
    }

    async handleFileUpload(file) {
        try {
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('document-text').value = e.target.result;
            };
            reader.readAsText(file);
        } catch (error) {
            this.showError('Error reading file: ' + error.message);
        }
    }

    async loadDocumentTemplates() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/document/templates`);
            const templates = await response.json();
            
            const templateSelect = document.getElementById('template-select');
            templateSelect.innerHTML = '<option value="">Choose a template...</option>';
            
            Object.entries(templates).forEach(([key, template]) => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = template.name;
                templateSelect.appendChild(option);
            });
        } catch (error) {
            this.showError('Error loading document templates: ' + error.message);
        }
    }

    updateTemplateForm() {
        const templateSelect = document.getElementById('template-select');
        const templateKey = templateSelect.value;
        const parametersContainer = document.getElementById('template-parameters');
        parametersContainer.innerHTML = '';

        if (!templateKey) return;

        const template = this.getTemplateParameters(templateKey);
        template.forEach(param => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group mb-3';
            formGroup.innerHTML = `
                <label for="${param.id}">${param.label}</label>
                <input type="${param.type}" class="form-control" id="${param.id}" required>
            `;
            parametersContainer.appendChild(formGroup);
        });
    }

    getTemplateParameters(templateKey) {
        const parameters = {
            nda: [
                { id: 'party1', label: 'First Party Name', type: 'text' },
                { id: 'party2', label: 'Second Party Name', type: 'text' },
                { id: 'confidentiality_period', label: 'Confidentiality Period (months)', type: 'number' },
                { id: 'purpose', label: 'Purpose of Agreement', type: 'text' }
            ],
            contract: [
                { id: 'party1', label: 'First Party Name', type: 'text' },
                { id: 'party2', label: 'Second Party Name', type: 'text' },
                { id: 'service_description', label: 'Service Description', type: 'text' },
                { id: 'payment_amount', label: 'Payment Amount', type: 'number' },
                { id: 'payment_terms', label: 'Payment Terms', type: 'text' }
            ],
            will: [
                { id: 'testator_name', label: 'Testator Name', type: 'text' },
                { id: 'executor_name', label: 'Executor Name', type: 'text' },
                { id: 'beneficiaries', label: 'Beneficiaries (comma-separated)', type: 'text' },
                { id: 'assets', label: 'Assets to Distribute', type: 'text' }
            ]
        };

        return parameters[templateKey] || [];
    }

    async handleDocumentAnalysis() {
        const documentText = document.getElementById('document-text').value;
        const documentType = document.getElementById('document-type').value;
        const jurisdiction = document.getElementById('document-jurisdiction').value;
        const language = document.getElementById('document-language').value;

        if (!documentText.trim()) {
            this.showError(this.translations?.pleaseEnterDocument || 'Please enter or upload a document to analyze');
            return;
        }

        try {
            this.showLoading('analyze-document');
            const response = await fetch(`${this.apiBaseUrl}/document/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    document_text: documentText,
                    document_type: documentType,
                    jurisdiction: jurisdiction || this.currentJurisdiction,
                    language: language || this.currentLanguage
                })
            });

            const result = await response.json();
            this.displayAnalysis(result);
            this.offerAudioVersion(result.summary);
        } catch (error) {
            this.showError(this.translations?.errorAnalyzingDocument || 'Error analyzing document: ' + error.message);
        } finally {
            this.hideLoading('analyze-document');
        }
    }

    async handleDocumentGeneration() {
        const templateKey = document.getElementById('template-select').value;
        const jurisdiction = document.getElementById('jurisdiction').value;
        const language = document.getElementById('document-language').value;

        if (!templateKey || !jurisdiction) {
            this.showError(this.translations?.pleaseSelectTemplateAndJurisdiction || 'Please select a template and specify jurisdiction');
            return;
        }

        const parameters = {};
        this.getTemplateParameters(templateKey).forEach(param => {
            const value = document.getElementById(param.id).value;
            if (!value) {
                throw new Error(this.translations?.pleaseFillInField.replace('{field}', param.label) || `Please fill in ${param.label}`);
            }
            parameters[param.id] = value;
        });

        try {
            this.showLoading('generate-document');
            const response = await fetch(`${this.apiBaseUrl}/document/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    template_key: templateKey,
                    jurisdiction: jurisdiction,
                    language: language || this.currentLanguage,
                    parameters: parameters
                })
            });

            const result = await response.json();
            this.displayGeneratedDocument(result);
            this.offerAudioVersion(result.document);
        } catch (error) {
            this.showError(this.translations?.errorGeneratingDocument || 'Error generating document: ' + error.message);
        } finally {
            this.hideLoading('generate-document');
        }
    }

    async handleDocumentMonitoring() {
        const documentText = document.getElementById('monitor-document-text').value;
        const legalAreas = document.getElementById('legal-areas').value;

        if (!documentText.trim() || !legalAreas.trim()) {
            this.showError('Please provide both document text and legal areas to monitor');
            return;
        }

        try {
            this.showLoading('register-monitoring');
            const response = await fetch(`${this.apiBaseUrl}/document/monitor`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    document_text: documentText,
                    legal_areas: legalAreas.split(',').map(area => area.trim())
                })
            });

            const result = await response.json();
            this.showSuccess(`Document registered for monitoring. Document ID: ${result.document_id}`);
            this.displayAnalysis(result.analysis);
        } catch (error) {
            this.showError('Error registering document for monitoring: ' + error.message);
        } finally {
            this.hideLoading('register-monitoring');
        }
    }

    async checkDocumentUpdates() {
        const documentId = document.getElementById('document-id').value;

        if (!documentId) {
            this.showError('Please enter a document ID');
            return;
        }

        try {
            this.showLoading('check-updates');
            const response = await fetch(`${this.apiBaseUrl}/document/update-check/${documentId}`);
            const result = await response.json();
            this.displayUpdates(result);
        } catch (error) {
            this.showError('Error checking for updates: ' + error.message);
        } finally {
            this.hideLoading('check-updates');
        }
    }

    async offerAudioVersion(text) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/document/audio`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            const result = await response.json();
            this.displayAudioPlayer(result.audio_url);
        } catch (error) {
            console.error('Error generating audio version:', error);
        }
    }

    displayAnalysis(result) {
        const container = document.getElementById('analysis-result');
        container.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-search"></i> Analysis Results
                    </h5>
                    <div class="analysis-content">
                        <h6>Summary</h6>
                        <p>${result.summary}</p>
                        <h6>Key Points</h6>
                        <ul>
                            ${result.key_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                        <h6>Potential Issues</h6>
                        <ul>
                            ${result.potential_issues.map(issue => `<li>${issue}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    displayGeneratedDocument(result) {
        const container = document.getElementById('generated-document');
        container.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-file-alt"></i> Generated Document
                    </h5>
                    <div class="document-content">
                        <pre>${result.document}</pre>
                    </div>
                    <div class="mt-3">
                        <button class="btn btn-primary" onclick="window.print()">
                            <i class="fas fa-print"></i> Print Document
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    displayUpdates(result) {
        const container = document.getElementById('updates-result');
        container.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-bell"></i> Legal Updates
                    </h5>
                    <div class="updates-content">
                        ${result.updates.length ? `
                            <div class="alert alert-warning">
                                <h6>Recent Legal Changes</h6>
                                <ul>
                                    ${result.updates.map(update => `
                                        <li>
                                            <strong>${update.title}</strong>
                                            <p>${update.description}</p>
                                            <small>Impact Level: ${update.impact_level}</small>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                            <button class="btn btn-primary" onclick="documentProcessor.handleDocumentUpdate('${result.document_id}')">
                                <i class="fas fa-sync"></i> Update Document
                            </button>
                        ` : `
                            <div class="alert alert-success">
                                No relevant legal changes found for your document.
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `;
    }

    displayAudioPlayer(audioUrl) {
        const container = document.getElementById('audio-player');
        if (!container) return;

        container.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-volume-up"></i> Audio Version
                    </h5>
                    <audio controls>
                        <source src="${audioUrl}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                </div>
            </div>
        `;
    }

    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
        }
    }

    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
        }
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.main-card').insertBefore(alert, document.querySelector('.tab-content'));
    }

    showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.main-card').insertBefore(alert, document.querySelector('.tab-content'));
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        const icon = themeToggle.querySelector('i');
        
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-theme');
            icon.classList.replace('fa-moon', 'fa-sun');
        }

        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            icon.classList.replace(isDark ? 'fa-moon' : 'fa-sun', isDark ? 'fa-sun' : 'fa-moon');
        });
    }

    setupBackToTop() {
        const backToTop = document.getElementById('back-to-top');
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });
    }

    scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    // Expert Matching
    async findExpertMatch() {
        const category = document.getElementById('caseCategorySelect').value;
        const description = document.getElementById('caseDescription').value;
        const language = document.getElementById('languageSelect').value;
        const urgency = document.getElementById('urgencyLevel').value;

        if (!category || !description) {
            this.showError('Please fill in all required fields');
            return;
        }

        try {
            this.showLoading('findExpertBtn');
            const response = await fetch(`${this.apiBaseUrl}/lawyers/match`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    category,
                    description,
                    language,
                    urgency
                })
            });

            const result = await response.json();
            this.displayExpertMatches(result.matches);
        } catch (error) {
            this.showError('Error finding expert matches: ' + error.message);
        } finally {
            this.hideLoading('findExpertBtn');
        }
    }

    displayExpertMatches(matches) {
        const modalBody = document.querySelector('#expertMatchModal .modal-body');
        const matchesHtml = matches.map(match => `
            <div class="expert-match-card">
                <div class="expert-info">
                    <img src="${match.avatar}" alt="${match.name}" class="expert-avatar">
                    <div class="expert-details">
                        <h4>${match.name}</h4>
                        <p class="expert-specialty">${match.specialty}</p>
                        <p class="expert-experience">${match.experience} years of experience</p>
                        <div class="expert-rating">
                            ${this.generateStarRating(match.rating)}
                            <span>(${match.reviewCount} reviews)</span>
                        </div>
                    </div>
                </div>
                <div class="expert-actions">
                    <button class="btn btn-primary" onclick="documentProcessor.initiateContactWithLawyer('${match.id}')">
                        Contact Now
                    </button>
                    <button class="btn btn-outline-primary" onclick="documentProcessor.viewLawyerProfile('${match.id}')">
                        View Profile
                    </button>
                </div>
            </div>
        `).join('');

        modalBody.innerHTML = `
            <div class="expert-matches">
                ${matchesHtml}
            </div>
        `;
    }

    generateStarRating(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - Math.ceil(rating);

        return `
            ${Array(fullStars).fill('<i class="fas fa-star"></i>').join('')}
            ${hasHalfStar ? '<i class="fas fa-star-half-alt"></i>' : ''}
            ${Array(emptyStars).fill('<i class="far fa-star"></i>').join('')}
        `;
    }

    // Appointment Booking
    async updateLawyerList() {
        const category = document.getElementById('caseCategorySelect').value;
        const lawyerSelect = document.getElementById('lawyerSelect');

        try {
            const response = await fetch(`${this.apiBaseUrl}/lawyers?category=${category}`);
            const lawyers = await response.json();

            lawyerSelect.innerHTML = '<option value="">Choose a lawyer...</option>';
            lawyers.forEach(lawyer => {
                const option = document.createElement('option');
                option.value = lawyer.id;
                option.textContent = `${lawyer.name} - ${lawyer.specialty}`;
                lawyerSelect.appendChild(option);
            });
        } catch (error) {
            this.showError('Error loading lawyers: ' + error.message);
        }
    }

    async updateAvailableTimeSlots() {
        const date = document.getElementById('appointmentDate').value;
        const lawyerId = document.getElementById('lawyerSelect').value;
        const timeSelect = document.getElementById('appointmentTime');

        if (!date || !lawyerId) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/lawyers/${lawyerId}/availability?date=${date}`);
            const slots = await response.json();

            timeSelect.innerHTML = '<option value="">Select time...</option>';
            slots.forEach(slot => {
                const option = document.createElement('option');
                option.value = slot.time;
                option.textContent = slot.time;
                timeSelect.appendChild(option);
            });
        } catch (error) {
            this.showError('Error loading time slots: ' + error.message);
        }
    }

    async bookAppointment() {
        const lawyerId = document.getElementById('lawyerSelect').value;
        const date = document.getElementById('appointmentDate').value;
        const time = document.getElementById('appointmentTime').value;
        const type = document.getElementById('consultationType').value;
        const description = document.getElementById('appointmentDescription').value;

        if (!lawyerId || !date || !time) {
            this.showError('Please fill in all required fields');
            return;
        }

        try {
            this.showLoading('bookAppointmentBtn');
            const response = await fetch(`${this.apiBaseUrl}/appointments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    lawyer_id: lawyerId,
                    date,
                    time,
                    type,
                    description
                })
            });

            const result = await response.json();
            this.showSuccess('Appointment booked successfully!');
            this.displayAppointmentConfirmation(result);
            document.getElementById('appointmentModal').modal('hide');
        } catch (error) {
            this.showError('Error booking appointment: ' + error.message);
        } finally {
            this.hideLoading('bookAppointmentBtn');
        }
    }

    // Live Chat
    initiateLiveChat() {
        const liveChatModal = new bootstrap.Modal(document.getElementById('liveChatModal'));
        liveChatModal.show();
        this.connectToLiveChatServer();
    }

    async connectToLiveChatServer() {
        try {
            // Initialize WebSocket connection
            this.chatSocket = new WebSocket(`ws://${window.location.hostname}:8001/ws/chat/`);
            
            this.chatSocket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.displayChatMessage(message);
            };

            this.chatSocket.onclose = () => {
                this.showError('Chat connection closed. Please try again.');
            };

            this.chatSocket.onerror = (error) => {
                this.showError('Chat error: ' + error.message);
            };
        } catch (error) {
            this.showError('Error connecting to chat: ' + error.message);
        }
    }

    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        try {
            if (this.chatSocket && this.chatSocket.readyState === WebSocket.OPEN) {
                this.chatSocket.send(JSON.stringify({
                    message: message,
                    type: 'user'
                }));
                input.value = '';
            } else {
                throw new Error('Chat connection not available');
            }
        } catch (error) {
            this.showError('Error sending message: ' + error.message);
        }
    }

    displayChatMessage(message) {
        const chatMessages = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${message.type}`;
        messageElement.textContent = message.message;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Helper Methods
    displayAppointmentConfirmation(appointment) {
        const modalBody = document.querySelector('#appointmentModal .modal-body');
        modalBody.innerHTML = `
            <div class="confirmation-message">
                <i class="fas fa-check-circle text-success"></i>
                <h4>Appointment Confirmed!</h4>
                <p>Your appointment has been scheduled for:</p>
                <div class="appointment-details">
                    <p><strong>Date:</strong> ${appointment.date}</p>
                    <p><strong>Time:</strong> ${appointment.time}</p>
                    <p><strong>Lawyer:</strong> ${appointment.lawyer_name}</p>
                    <p><strong>Type:</strong> ${appointment.type}</p>
                </div>
                <p class="mt-3">You will receive a confirmation email with further details.</p>
            </div>
        `;
    }

    async initiateContactWithLawyer(lawyerId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/lawyers/${lawyerId}/contact`, {
                method: 'POST'
            });
            const result = await response.json();
            this.showSuccess('Contact request sent! The lawyer will respond shortly.');
        } catch (error) {
            this.showError('Error contacting lawyer: ' + error.message);
        }
    }

    async viewLawyerProfile(lawyerId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/lawyers/${lawyerId}/profile`);
            const profile = await response.json();
            this.displayLawyerProfile(profile);
        } catch (error) {
            this.showError('Error loading lawyer profile: ' + error.message);
        }
    }

    displayLawyerProfile(profile) {
        const modalBody = document.querySelector('#expertMatchModal .modal-body');
        modalBody.innerHTML = `
            <div class="lawyer-profile">
                <div class="profile-header">
                    <img src="${profile.avatar}" alt="${profile.name}" class="profile-avatar">
                    <h3>${profile.name}</h3>
                    <p class="profile-title">${profile.title}</p>
                </div>
                <div class="profile-content">
                    <div class="profile-section">
                        <h4>Specializations</h4>
                        <ul>
                            ${profile.specializations.map(spec => `<li>${spec}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="profile-section">
                        <h4>Experience</h4>
                        <p>${profile.experience}</p>
                    </div>
                    <div class="profile-section">
                        <h4>Education</h4>
                        <ul>
                            ${profile.education.map(edu => `<li>${edu}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="profile-section">
                        <h4>Languages</h4>
                        <p>${profile.languages.join(', ')}</p>
                    </div>
                    <div class="profile-section">
                        <h4>Reviews</h4>
                        <div class="rating">
                            ${this.generateStarRating(profile.rating)}
                            <span>(${profile.reviewCount} reviews)</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    setupLocalization() {
        // Language dropdown
        const languageDropdown = document.getElementById('languageDropdown');
        const languageItems = languageDropdown.querySelectorAll('.dropdown-item');
        languageItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const lang = e.target.dataset.lang;
                this.setLanguage(lang);
            });
        });

        // Jurisdiction dropdown
        const jurisdictionDropdown = document.getElementById('jurisdictionDropdown');
        const jurisdictionItems = jurisdictionDropdown.querySelectorAll('.dropdown-item');
        jurisdictionItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const jurisdiction = e.target.dataset.jurisdiction;
                this.setJurisdiction(jurisdiction);
            });
        });

        // Update dropdown text
        this.updateDropdownText();
    }

    async loadTranslations() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/translations/${this.currentLanguage}`);
            const translations = await response.json();
            this.translations = translations;
            this.updateUIWithTranslations();
        } catch (error) {
            console.error('Error loading translations:', error);
        }
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        this.loadTranslations();
        this.updateDropdownText();
    }

    setJurisdiction(jurisdiction) {
        this.currentJurisdiction = jurisdiction;
        localStorage.setItem('jurisdiction', jurisdiction);
        this.updateDropdownText();
    }

    updateDropdownText() {
        const languageDropdown = document.getElementById('languageDropdown');
        const jurisdictionDropdown = document.getElementById('jurisdictionDropdown');
        
        const languageMap = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'hi': 'हिंदी'
        };

        const jurisdictionMap = {
            'us': 'United States',
            'uk': 'United Kingdom',
            'ca': 'Canada',
            'au': 'Australia',
            'in': 'India'
        };

        languageDropdown.querySelector('.dropdown-toggle').textContent = 
            `<i class="fas fa-globe"></i> ${languageMap[this.currentLanguage]}`;
        
        jurisdictionDropdown.querySelector('.dropdown-toggle').textContent = 
            `<i class="fas fa-map-marker-alt"></i> ${jurisdictionMap[this.currentJurisdiction]}`;
    }

    updateUIWithTranslations() {
        if (!this.translations) return;

        // Update document analysis section
        document.querySelector('#analysis .card-title').innerHTML = 
            `<i class="fas fa-search"></i> ${this.translations.analyzeDocument}`;
        
        document.querySelector('#generation .card-title').innerHTML = 
            `<i class="fas fa-file-alt"></i> ${this.translations.generateDocument}`;
        
        document.querySelector('#monitoring .card-title').innerHTML = 
            `<i class="fas fa-bell"></i> ${this.translations.monitorChanges}`;

        // Update form labels
        document.querySelectorAll('.form-label').forEach(label => {
            const key = label.getAttribute('data-translate');
            if (key && this.translations[key]) {
                label.textContent = this.translations[key];
            }
        });

        // Update buttons
        document.querySelectorAll('.btn').forEach(button => {
            const key = button.getAttribute('data-translate');
            if (key && this.translations[key]) {
                button.textContent = this.translations[key];
            }
        });
    }

    setupComplianceFeatures() {
        // Security Whitepaper Download
        const downloadSecurityWhitepaperBtn = document.getElementById('downloadSecurityWhitepaper');
        if (downloadSecurityWhitepaperBtn) {
            downloadSecurityWhitepaperBtn.addEventListener('click', () => this.downloadSecurityWhitepaper());
        }

        // Privacy Settings Form
        const privacySettingsForm = document.getElementById('privacySettingsForm');
        if (privacySettingsForm) {
            privacySettingsForm.addEventListener('submit', (e) => this.handlePrivacySettings(e));
        }

        // Delete Data Button
        const deleteDataBtn = document.getElementById('deleteAllMyData');
        if (deleteDataBtn) {
            deleteDataBtn.addEventListener('click', () => this.handleDataDeletion());
        }

        // Privacy Policy and Terms of Service Downloads
        const downloadPrivacyPolicyBtn = document.getElementById('downloadPrivacyPolicy');
        const downloadTermsBtn = document.getElementById('downloadTermsOfService');
        if (downloadPrivacyPolicyBtn) {
            downloadPrivacyPolicyBtn.addEventListener('click', () => this.downloadPrivacyPolicy());
        }
        if (downloadTermsBtn) {
            downloadTermsBtn.addEventListener('click', () => this.downloadTermsOfService());
        }

        // Save Privacy Settings
        const savePrivacySettingsBtn = document.getElementById('savePrivacySettings');
        if (savePrivacySettingsBtn) {
            savePrivacySettingsBtn.addEventListener('click', () => this.savePrivacySettings());
        }

        // Load saved privacy settings
        this.loadPrivacySettings();
    }

    async downloadSecurityWhitepaper() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/security/whitepaper`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'security-whitepaper.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            this.showError('Error downloading security whitepaper: ' + error.message);
        }
    }

    async handlePrivacySettings(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const settings = {
            documentStorage: formData.get('documentStorage') === 'on',
            analyticsConsent: formData.get('analyticsConsent') === 'on',
            thirdPartySharing: formData.get('thirdPartySharing') === 'on',
            marketingConsent: formData.get('marketingConsent') === 'on',
            dataRetentionPeriod: formData.get('dataRetentionPeriod')
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/privacy/settings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                this.showSuccess('Privacy settings updated successfully');
                this.savePrivacySettingsToLocal(settings);
            } else {
                throw new Error('Failed to update privacy settings');
            }
        } catch (error) {
            this.showError('Error updating privacy settings: ' + error.message);
        }
    }

    async handleDataDeletion() {
        if (!confirm('Are you sure you want to delete all your data? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/privacy/delete-data`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                this.showSuccess('Your data has been deleted successfully');
                this.clearLocalStorage();
                // Reset form to default values
                this.resetPrivacySettings();
            } else {
                throw new Error('Failed to delete data');
            }
        } catch (error) {
            this.showError('Error deleting data: ' + error.message);
        }
    }

    async downloadPrivacyPolicy() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/privacy/policy`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'privacy-policy.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            this.showError('Error downloading privacy policy: ' + error.message);
        }
    }

    async downloadTermsOfService() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/privacy/terms`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'terms-of-service.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            this.showError('Error downloading terms of service: ' + error.message);
        }
    }

    async savePrivacySettings() {
        const form = document.getElementById('privacySettingsForm');
        if (!form) return;

        const formData = new FormData(form);
        const settings = {
            documentStorage: formData.get('documentStorage') === 'on',
            analyticsConsent: formData.get('analyticsConsent') === 'on',
            thirdPartySharing: formData.get('thirdPartySharing') === 'on',
            marketingConsent: formData.get('marketingConsent') === 'on',
            dataRetentionPeriod: formData.get('dataRetentionPeriod')
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/privacy/settings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                this.showSuccess('Privacy settings saved successfully');
                this.savePrivacySettingsToLocal(settings);
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('privacyModal'));
                if (modal) {
                    modal.hide();
                }
            } else {
                throw new Error('Failed to save privacy settings');
            }
        } catch (error) {
            this.showError('Error saving privacy settings: ' + error.message);
        }
    }

    loadPrivacySettings() {
        const savedSettings = localStorage.getItem('privacySettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            this.applyPrivacySettings(settings);
        }
    }

    applyPrivacySettings(settings) {
        const form = document.getElementById('privacySettingsForm');
        if (!form) return;

        // Update form controls
        form.querySelector('#documentStorage').checked = settings.documentStorage;
        form.querySelector('#analyticsConsent').checked = settings.analyticsConsent;
        form.querySelector('#thirdPartySharing').checked = settings.thirdPartySharing;
        form.querySelector('#marketingConsent').checked = settings.marketingConsent;
        form.querySelector('#dataRetentionPeriod').value = settings.dataRetentionPeriod;
    }

    savePrivacySettingsToLocal(settings) {
        localStorage.setItem('privacySettings', JSON.stringify(settings));
    }

    resetPrivacySettings() {
        const defaultSettings = {
            documentStorage: true,
            analyticsConsent: true,
            thirdPartySharing: false,
            marketingConsent: false,
            dataRetentionPeriod: '30days'
        };

        this.applyPrivacySettings(defaultSettings);
        this.savePrivacySettingsToLocal(defaultSettings);
    }

    clearLocalStorage() {
        localStorage.clear();
        this.resetPrivacySettings();
    }

    setupNewsFeatures() {
        // News subscription form
        const saveNewsSubscriptionBtn = document.getElementById('saveNewsSubscription');
        if (saveNewsSubscriptionBtn) {
            saveNewsSubscriptionBtn.addEventListener('click', () => this.saveNewsSubscription());
        }

        // News filters
        const categoryFilter = document.getElementById('newsCategoryFilter');
        const jurisdictionFilter = document.getElementById('newsJurisdictionFilter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => this.filterNews());
        }
        if (jurisdictionFilter) {
            jurisdictionFilter.addEventListener('change', () => this.filterNews());
        }

        // Load more news button
        const loadMoreNewsBtn = document.getElementById('loadMoreNews');
        if (loadMoreNewsBtn) {
            loadMoreNewsBtn.addEventListener('click', () => this.loadMoreNews());
        }

        // Initialize news feed
        this.loadNewsFeed();
        this.setupNewsWebSocket();
    }

    async loadNewsFeed() {
        if (this.newsLoading || !this.newsHasMore) return;

        try {
            this.newsLoading = true;
            this.showLoading('loadMoreNews');

            const category = document.getElementById('newsCategoryFilter').value;
            const jurisdiction = document.getElementById('newsJurisdictionFilter').value;

            const response = await fetch(`${this.apiBaseUrl}/news?page=${this.newsPage}&category=${category}&jurisdiction=${jurisdiction}`);
            const result = await response.json();

            this.displayNewsItems(result.news);
            this.newsHasMore = result.has_more;
            this.newsPage++;

            if (!this.newsHasMore) {
                document.getElementById('loadMoreNews').style.display = 'none';
            }
        } catch (error) {
            this.showError('Error loading news: ' + error.message);
        } finally {
            this.newsLoading = false;
            this.hideLoading('loadMoreNews');
        }
    }

    displayNewsItems(newsItems) {
        const newsFeed = document.getElementById('newsFeed');
        if (!newsFeed) return;

        newsItems.forEach(item => {
            const newsItem = document.createElement('div');
            newsItem.className = 'news-item';
            newsItem.innerHTML = `
                <div class="news-item-header">
                    <span class="news-item-category">${item.category}</span>
                    <span class="news-item-date">${this.formatDate(item.date)}</span>
                </div>
                <h4 class="news-item-title">${item.title}</h4>
                <p class="news-item-summary">${item.summary}</p>
                <div class="news-item-footer">
                    <span class="news-item-jurisdiction">${item.jurisdiction}</span>
                    <div class="news-item-actions">
                        <button onclick="documentProcessor.saveNewsItem('${item.id}')" title="Save">
                            <i class="fas fa-bookmark"></i>
                        </button>
                        <button onclick="documentProcessor.shareNewsItem('${item.id}')" title="Share">
                            <i class="fas fa-share-alt"></i>
                        </button>
                    </div>
                </div>
            `;
            newsFeed.appendChild(newsItem);
        });
    }

    setupNewsWebSocket() {
        try {
            this.newsWebSocket = new WebSocket(`ws://${window.location.hostname}:8001/ws/news/`);
            
            this.newsWebSocket.onmessage = (event) => {
                const newsItem = JSON.parse(event.data);
                this.handleNewNewsItem(newsItem);
            };

            this.newsWebSocket.onclose = () => {
                console.log('News WebSocket connection closed');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.setupNewsWebSocket(), 5000);
            };

            this.newsWebSocket.onerror = (error) => {
                console.error('News WebSocket error:', error);
            };
        } catch (error) {
            console.error('Error setting up news WebSocket:', error);
        }
    }

    handleNewNewsItem(newsItem) {
        // Check if the news item matches current filters
        const category = document.getElementById('newsCategoryFilter').value;
        const jurisdiction = document.getElementById('newsJurisdictionFilter').value;

        if ((category === 'all' || category === newsItem.category) &&
            (jurisdiction === 'all' || jurisdiction === newsItem.jurisdiction)) {
            // Add the new item to the top of the feed
            const newsFeed = document.getElementById('newsFeed');
            if (newsFeed) {
                const newsItemElement = document.createElement('div');
                newsItemElement.className = 'news-item';
                newsItemElement.innerHTML = `
                    <div class="news-item-header">
                        <span class="news-item-category">${newsItem.category}</span>
                        <span class="news-item-date">${this.formatDate(newsItem.date)}</span>
                    </div>
                    <h4 class="news-item-title">${newsItem.title}</h4>
                    <p class="news-item-summary">${newsItem.summary}</p>
                    <div class="news-item-footer">
                        <span class="news-item-jurisdiction">${newsItem.jurisdiction}</span>
                        <div class="news-item-actions">
                            <button onclick="documentProcessor.saveNewsItem('${newsItem.id}')" title="Save">
                                <i class="fas fa-bookmark"></i>
                            </button>
                            <button onclick="documentProcessor.shareNewsItem('${newsItem.id}')" title="Share">
                                <i class="fas fa-share-alt"></i>
                            </button>
                        </div>
                    </div>
                `;
                newsFeed.insertBefore(newsItemElement, newsFeed.firstChild);

                // Show notification if browser notifications are enabled
                if (Notification.permission === 'granted') {
                    new Notification('New Legal Update', {
                        body: newsItem.title,
                        icon: '/static/logo2.jpeg-removebg-preview.png'
                    });
                }
            }
        }
    }

    async saveNewsSubscription() {
        const form = document.getElementById('newsSubscriptionForm');
        if (!form) return;

        const formData = new FormData(form);
        const subscription = {
            legal_areas: Array.from(formData.getAll('legal_areas')),
            jurisdictions: Array.from(formData.getAll('jurisdictions')),
            update_frequency: formData.get('update_frequency'),
            notification_methods: Array.from(formData.getAll('notification_methods'))
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/news/subscribe`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subscription)
            });

            if (response.ok) {
                this.showSuccess('News subscription preferences saved successfully');
                this.saveNewsSubscriptionToLocal(subscription);
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('newsSubscriptionModal'));
                if (modal) {
                    modal.hide();
                }
            } else {
                throw new Error('Failed to save subscription preferences');
            }
        } catch (error) {
            this.showError('Error saving news subscription: ' + error.message);
        }
    }

    saveNewsSubscriptionToLocal(subscription) {
        localStorage.setItem('newsSubscription', JSON.stringify(subscription));
    }

    loadNewsSubscriptionFromLocal() {
        const savedSubscription = localStorage.getItem('newsSubscription');
        if (savedSubscription) {
            const subscription = JSON.parse(savedSubscription);
            this.applyNewsSubscription(subscription);
        }
    }

    applyNewsSubscription(subscription) {
        const form = document.getElementById('newsSubscriptionForm');
        if (!form) return;

        // Reset all checkboxes
        form.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Apply saved preferences
        subscription.legal_areas.forEach(area => {
            const checkbox = form.querySelector(`#${area}Law`);
            if (checkbox) checkbox.checked = true;
        });

        subscription.jurisdictions.forEach(jurisdiction => {
            const checkbox = form.querySelector(`#${jurisdiction}Jurisdiction`);
            if (checkbox) checkbox.checked = true;
        });

        const frequencySelect = form.querySelector('#updateFrequency');
        if (frequencySelect) {
            frequencySelect.value = subscription.update_frequency;
        }

        subscription.notification_methods.forEach(method => {
            const checkbox = form.querySelector(`#${method}Notification`);
            if (checkbox) checkbox.checked = true;
        });
    }

    async saveNewsItem(newsId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/news/save/${newsId}`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showSuccess('News item saved successfully');
            } else {
                throw new Error('Failed to save news item');
            }
        } catch (error) {
            this.showError('Error saving news item: ' + error.message);
        }
    }

    async shareNewsItem(newsId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/news/share/${newsId}`);
            const shareData = await response.json();

            if (navigator.share) {
                await navigator.share({
                    title: shareData.title,
                    text: shareData.summary,
                    url: shareData.url
                });
            } else {
                // Fallback for browsers that don't support Web Share API
                const shareUrl = encodeURIComponent(shareData.url);
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareData.title)}&url=${shareUrl}`);
            }
        } catch (error) {
            this.showError('Error sharing news item: ' + error.message);
        }
    }

    filterNews() {
        const newsFeed = document.getElementById('newsFeed');
        if (!newsFeed) return;

        // Clear existing news items
        newsFeed.innerHTML = '';
        this.newsPage = 1;
        this.newsHasMore = true;
        document.getElementById('loadMoreNews').style.display = 'block';

        // Load filtered news
        this.loadNewsFeed();
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    setupFaqFeatures() {
        // FAQ Search
        const searchInput = document.getElementById('faqSearchInput');
        const searchBtn = document.getElementById('searchFaqBtn');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.handleFaqSearchInput());
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.handleFaqSearch();
            });
        }
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.handleFaqSearch());
        }

        // FAQ Filters
        const categoryFilter = document.getElementById('faqCategoryFilter');
        const jurisdictionFilter = document.getElementById('faqJurisdictionFilter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => this.filterFaqs());
        }
        if (jurisdictionFilter) {
            jurisdictionFilter.addEventListener('change', () => this.filterFaqs());
        }

        // FAQ Feedback
        const submitFeedbackBtn = document.getElementById('submitFeedbackBtn');
        if (submitFeedbackBtn) {
            submitFeedbackBtn.addEventListener('click', () => this.handleFaqFeedback());
        }

        // Load initial data
        this.loadFaqCategories();
        this.loadRecentFaqs();
    }

    async handleFaqSearchInput() {
        const searchInput = document.getElementById('faqSearchInput');
        const suggestionsContainer = document.getElementById('searchSuggestions');
        if (!searchInput || !suggestionsContainer) return;

        const query = searchInput.value.trim();
        if (query.length < 2) {
            suggestionsContainer.classList.remove('active');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/faq/suggestions?query=${encodeURIComponent(query)}`);
            if (response.ok) {
                const suggestions = await response.json();
                this.displaySearchSuggestions(suggestions);
            }
        } catch (error) {
            console.error('Error fetching search suggestions:', error);
        }
    }

    displaySearchSuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('searchSuggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = '';
        suggestions.forEach(suggestion => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.textContent = suggestion;
            div.addEventListener('click', () => {
                document.getElementById('faqSearchInput').value = suggestion;
                suggestionsContainer.classList.remove('active');
                this.handleFaqSearch();
            });
            suggestionsContainer.appendChild(div);
        });
        suggestionsContainer.classList.add('active');
    }

    async handleFaqSearch() {
        const searchInput = document.getElementById('faqSearchInput');
        const searchResults = document.getElementById('searchResults');
        if (!searchInput || !searchResults) return;

        const query = searchInput.value.trim();
        if (!query) return;

        this.showLoading('searchResults');
        try {
            const response = await fetch(`${this.apiBaseUrl}/faq/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            if (response.ok) {
                const results = await response.json();
                this.displaySearchResults(results);
                this.saveSearchHistory(query);
            } else {
                throw new Error('Failed to search FAQs');
            }
        } catch (error) {
            this.showError('Error searching FAQs: ' + error.message);
        } finally {
            this.hideLoading('searchResults');
        }
    }

    displaySearchResults(results) {
        const searchResults = document.getElementById('searchResults');
        if (!searchResults) return;

        searchResults.innerHTML = '';
        results.forEach(result => {
            const div = document.createElement('div');
            div.className = 'search-result-item';
            div.innerHTML = `
                <h4>${result.question}</h4>
                <p>${result.answer}</p>
                <div class="search-result-footer">
                    <span class="confidence-score">Confidence: ${(result.confidence * 100).toFixed(1)}%</span>
                    <div class="search-result-actions">
                        <button onclick="documentProcessor.saveFaqItem('${result.id}')">
                            <i class="fas fa-bookmark"></i> Save
                        </button>
                        <button onclick="documentProcessor.shareFaqItem('${result.id}')">
                            <i class="fas fa-share"></i> Share
                        </button>
                    </div>
                </div>
            `;
            searchResults.appendChild(div);
        });
    }

    async loadFaqCategories() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/faq/categories`);
            if (response.ok) {
                this.faqCategories = await response.json();
                this.displayFaqCategories();
            }
        } catch (error) {
            console.error('Error loading FAQ categories:', error);
        }
    }

    displayFaqCategories() {
        const categoriesGrid = document.querySelector('.categories-grid');
        if (!categoriesGrid) return;

        categoriesGrid.innerHTML = '';
        this.faqCategories.forEach(category => {
            const div = document.createElement('div');
            div.className = 'category-card';
            div.innerHTML = `
                <i class="fas ${category.icon}"></i>
                <h4>${category.name}</h4>
                <p>${category.description}</p>
                <small>${category.count} FAQs</small>
            `;
            div.addEventListener('click', () => this.loadCategoryFaqs(category.id));
            categoriesGrid.appendChild(div);
        });
    }

    async loadCategoryFaqs(categoryId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/faq/category/${categoryId}`);
            if (response.ok) {
                const faqs = await response.json();
                this.displayFaqList(faqs);
            }
        } catch (error) {
            console.error('Error loading category FAQs:', error);
        }
    }

    async loadRecentFaqs() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/faq/recent`);
            if (response.ok) {
                this.faqs = await response.json();
                this.displayFaqList(this.faqs);
            }
        } catch (error) {
            console.error('Error loading recent FAQs:', error);
        }
    }

    displayFaqList(faqs) {
        const faqList = document.getElementById('faqList');
        if (!faqList) return;

        faqList.innerHTML = '';
        faqs.forEach(faq => {
            const div = document.createElement('div');
            div.className = 'faq-item';
            div.innerHTML = `
                <div class="faq-item-header">
                    <span class="faq-item-category">${faq.category}</span>
                    <span class="faq-item-date">${this.formatDate(faq.date)}</span>
                </div>
                <div class="faq-item-question">${faq.question}</div>
                <div class="faq-item-answer">${faq.answer}</div>
                <div class="faq-item-footer">
                    <span class="faq-item-jurisdiction">${faq.jurisdiction}</span>
                    <div class="faq-item-actions">
                        <button onclick="documentProcessor.saveFaqItem('${faq.id}')">
                            <i class="fas fa-bookmark"></i> Save
                        </button>
                        <button onclick="documentProcessor.shareFaqItem('${faq.id}')">
                            <i class="fas fa-share"></i> Share
                        </button>
                    </div>
                </div>
            `;
            faqList.appendChild(div);
        });
    }

    filterFaqs() {
        const categoryFilter = document.getElementById('faqCategoryFilter');
        const jurisdictionFilter = document.getElementById('faqJurisdictionFilter');
        if (!categoryFilter || !jurisdictionFilter) return;

        const category = categoryFilter.value;
        const jurisdiction = jurisdictionFilter.value;

        const filteredFaqs = this.faqs.filter(faq => {
            const categoryMatch = category === 'all' || faq.category === category;
            const jurisdictionMatch = jurisdiction === 'all' || faq.jurisdiction === jurisdiction;
            return categoryMatch && jurisdictionMatch;
        });

        this.displayFaqList(filteredFaqs);
    }

    async handleFaqFeedback() {
        const form = document.getElementById('faqFeedbackForm');
        if (!form) return;

        const formData = new FormData(form);
        const feedback = {
            faqId: formData.get('feedbackFaqSelect'),
            helpful: formData.get('helpful'),
            suggestions: formData.get('feedbackSuggestions'),
            context: formData.get('feedbackContext')
        };

        try {
            const response = await fetch(`${this.apiBaseUrl}/faq/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(feedback)
            });

            if (response.ok) {
                this.showSuccess('Thank you for your feedback!');
                this.saveFeedbackHistory(feedback);
                form.reset();
                
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('faqFeedbackModal'));
                if (modal) {
                    modal.hide();
                }
            } else {
                throw new Error('Failed to submit feedback');
            }
        } catch (error) {
            this.showError('Error submitting feedback: ' + error.message);
        }
    }

    saveSearchHistory(query) {
        this.searchHistory.unshift(query);
        if (this.searchHistory.length > 10) {
            this.searchHistory.pop();
        }
        localStorage.setItem('faqSearchHistory', JSON.stringify(this.searchHistory));
    }

    saveFeedbackHistory(feedback) {
        this.feedbackHistory.unshift(feedback);
        if (this.feedbackHistory.length > 50) {
            this.feedbackHistory.pop();
        }
        localStorage.setItem('faqFeedbackHistory', JSON.stringify(this.feedbackHistory));
    }
}

// Initialize the document processor
const documentProcessor = new DocumentProcessor(); 