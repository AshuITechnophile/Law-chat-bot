class DocumentManager {
    constructor() {
        this.apiUrl = 'http://localhost:5000/api';
        this.documents = [];
        this.setupEventListeners();
        this.initializeDropZone();
    }

    setupEventListeners() {
        // Browse files button
        document.getElementById('browse-files').addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf,.doc,.docx,.txt';
            input.multiple = true;
            input.onchange = (e) => this.handleFileSelect(e.target.files);
            input.click();
        });

        // Scan documents button
        document.getElementById('scan-documents').addEventListener('click', () => {
            alert('Document scanning feature coming soon!');
        });

        // Analyze document button
        document.getElementById('analyze-document').addEventListener('click', () => {
            this.analyzeCurrentDocument();
        });

        // Delete document buttons
        document.querySelectorAll('.document-actions .btn-outline-danger').forEach(button => {
            button.addEventListener('click', (e) => {
                const card = e.target.closest('.card');
                if (card) {
                    const title = card.querySelector('.card-title').textContent;
                    this.deleteDocument(title);
                }
            });
        });
    }

    initializeDropZone() {
        const dropZone = document.querySelector('.upload-area');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-over');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFileSelect(files);
        });
    }

    async handleFileSelect(files) {
        for (const file of files) {
            if (this.isValidFileType(file)) {
                await this.uploadDocument(file);
            } else {
                alert(`Invalid file type: ${file.name}. Please upload PDF, DOC, DOCX, or TXT files only.`);
            }
        }
    }

    isValidFileType(file) {
        const validTypes = ['.pdf', '.doc', '.docx', '.txt'];
        return validTypes.some(type => file.name.toLowerCase().endsWith(type));
    }

    async uploadDocument(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${this.apiUrl}/documents/upload`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.addDocumentToList(result.document);
                alert('Document uploaded successfully!');
            } else {
                throw new Error('Failed to upload document');
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            alert('Failed to upload document. Please try again.');
        }
    }

    addDocumentToList(document) {
        const documentList = document.querySelector('.document-list .row');
        const documentCard = this.createDocumentCard(document);
        documentList.insertBefore(documentCard, documentList.firstChild);
        this.documents.push(document);
    }

    createDocumentCard(document) {
        const col = document.createElement('div');
        col.className = 'col-md-6';
        col.innerHTML = `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="card-title">${document.title}</h5>
                            <p class="card-text text-muted">Uploaded on: ${new Date(document.uploadDate).toLocaleDateString()}</p>
                        </div>
                        <div class="document-actions">
                            <button class="btn btn-sm btn-outline-primary me-2" data-bs-toggle="modal" data-bs-target="#documentPreviewModal">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add event listeners to the new buttons
        const previewButton = col.querySelector('.btn-outline-primary');
        previewButton.addEventListener('click', () => this.previewDocument(document));

        const deleteButton = col.querySelector('.btn-outline-danger');
        deleteButton.addEventListener('click', () => this.deleteDocument(document.title));

        return col;
    }

    async previewDocument(document) {
        try {
            const response = await fetch(`${this.apiUrl}/documents/${document.id}/preview`);
            if (response.ok) {
                const preview = await response.text();
                document.getElementById('document-preview').innerHTML = preview;
            } else {
                throw new Error('Failed to load document preview');
            }
        } catch (error) {
            console.error('Error loading document preview:', error);
            document.getElementById('document-preview').innerHTML = 'Failed to load document preview';
        }
    }

    async analyzeCurrentDocument() {
        const documentId = this.getCurrentDocumentId();
        if (!documentId) {
            alert('No document selected for analysis');
            return;
        }

        try {
            const response = await fetch(`${this.apiUrl}/documents/${documentId}/analyze`);
            if (response.ok) {
                const analysis = await response.json();
                this.displayAnalysisResults(analysis);
            } else {
                throw new Error('Failed to analyze document');
            }
        } catch (error) {
            console.error('Error analyzing document:', error);
            alert('Failed to analyze document. Please try again.');
        }
    }

    getCurrentDocumentId() {
        // This should be implemented based on your document selection logic
        return null;
    }

    displayAnalysisResults(analysis) {
        const summaryElement = document.querySelector('.analysis-summary p');
        const keyPointsList = document.querySelector('.analysis-details .list-group');

        summaryElement.textContent = analysis.summary;
        keyPointsList.innerHTML = analysis.keyPoints
            .map(point => `<li class="list-group-item">${point}</li>`)
            .join('');
    }

    async deleteDocument(title) {
        if (confirm(`Are you sure you want to delete "${title}"?`)) {
            try {
                const document = this.documents.find(doc => doc.title === title);
                if (!document) return;

                const response = await fetch(`${this.apiUrl}/documents/${document.id}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    const card = document.querySelector(`.card-title:contains("${title}")`).closest('.col-md-6');
                    card.remove();
                    this.documents = this.documents.filter(doc => doc.title !== title);
                    alert('Document deleted successfully!');
                } else {
                    throw new Error('Failed to delete document');
                }
            } catch (error) {
                console.error('Error deleting document:', error);
                alert('Failed to delete document. Please try again.');
            }
        }
    }
}

// Initialize document manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.documentManager = new DocumentManager();
}); 