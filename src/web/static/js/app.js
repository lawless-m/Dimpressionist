/**
 * Dimpressionist - Main Application
 */

class App {
    constructor() {
        // Initialize API client and WebSocket
        this.api = new APIClient();
        this.ws = new WSHandler();

        // Application state
        this.state = {
            session: null,
            currentImage: null,
            history: [],
            isGenerating: false,
            params: {
                steps: 28,
                guidanceScale: 3.5,
                strength: 0.6,
                seed: null
            }
        };

        // DOM elements
        this.elements = {};

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Initialize the application
     */
    async init() {
        this.cacheElements();
        this.setupEventListeners();
        this.setupWebSocket();
        await this.loadSession();
    }

    /**
     * Cache DOM elements
     */
    cacheElements() {
        this.elements = {
            // Header
            sessionInfo: document.getElementById('session-info'),
            settingsBtn: document.getElementById('settings-btn'),

            // Sidebar
            sidebar: document.getElementById('sidebar'),
            historyList: document.getElementById('history-list'),
            historyEmpty: document.getElementById('history-empty'),
            clearBtn: document.getElementById('clear-btn'),

            // Canvas
            canvasContainer: document.getElementById('canvas-container'),
            emptyCanvas: document.getElementById('empty-canvas'),
            imageDisplay: document.getElementById('image-display'),
            currentImage: document.getElementById('current-image'),
            downloadBtn: document.getElementById('download-btn'),

            // Progress
            progressOverlay: document.getElementById('progress-overlay'),
            progressText: document.getElementById('progress-text'),
            progressBar: document.getElementById('progress-bar'),
            progressDetails: document.getElementById('progress-details'),

            // Metadata
            imageMeta: document.getElementById('image-meta'),
            metaPrompt: document.getElementById('meta-prompt'),
            metaSeed: document.getElementById('meta-seed'),
            metaSteps: document.getElementById('meta-steps'),
            metaTime: document.getElementById('meta-time'),

            // Input
            promptInput: document.getElementById('prompt-input'),
            generateBtn: document.getElementById('generate-btn'),
            paramsToggle: document.getElementById('params-toggle'),
            paramsPanel: document.getElementById('params-panel'),

            // Parameters
            paramSteps: document.getElementById('param-steps'),
            paramStepsValue: document.getElementById('param-steps-value'),
            paramGuidance: document.getElementById('param-guidance'),
            paramGuidanceValue: document.getElementById('param-guidance-value'),
            paramStrength: document.getElementById('param-strength'),
            paramStrengthValue: document.getElementById('param-strength-value'),
            paramSeed: document.getElementById('param-seed'),
            randomSeedBtn: document.getElementById('random-seed-btn'),

            // Modal
            settingsModal: document.getElementById('settings-modal'),
            settingsClose: document.getElementById('settings-close')
        };
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Generate button
        this.elements.generateBtn.addEventListener('click', () => this.handleGenerate());

        // Prompt input - Enter to generate, Shift+Enter for newline
        this.elements.promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleGenerate();
            }
        });

        // Ctrl+K to clear prompt
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                this.elements.promptInput.value = '';
                this.elements.promptInput.focus();
            }
        });

        // Parameters toggle
        this.elements.paramsToggle.addEventListener('click', () => {
            const panel = this.elements.paramsPanel;
            panel.style.display = panel.style.display === 'none' ? 'grid' : 'none';
        });

        // Parameter sliders
        this.elements.paramSteps.addEventListener('input', (e) => {
            this.state.params.steps = parseInt(e.target.value);
            this.elements.paramStepsValue.textContent = e.target.value;
        });

        this.elements.paramGuidance.addEventListener('input', (e) => {
            this.state.params.guidanceScale = parseFloat(e.target.value);
            this.elements.paramGuidanceValue.textContent = e.target.value;
        });

        this.elements.paramStrength.addEventListener('input', (e) => {
            this.state.params.strength = parseFloat(e.target.value);
            this.elements.paramStrengthValue.textContent = e.target.value;
        });

        this.elements.paramSeed.addEventListener('input', (e) => {
            this.state.params.seed = e.target.value ? parseInt(e.target.value) : null;
        });

        this.elements.randomSeedBtn.addEventListener('click', () => {
            this.elements.paramSeed.value = '';
            this.state.params.seed = null;
        });

        // Clear session
        this.elements.clearBtn.addEventListener('click', () => this.handleClear());

        // Download
        this.elements.downloadBtn.addEventListener('click', () => this.handleDownload());

        // Settings modal
        this.elements.settingsBtn.addEventListener('click', () => {
            this.elements.settingsModal.style.display = 'flex';
        });

        this.elements.settingsClose.addEventListener('click', () => {
            this.elements.settingsModal.style.display = 'none';
        });

        this.elements.settingsModal.querySelector('.modal-backdrop').addEventListener('click', () => {
            this.elements.settingsModal.style.display = 'none';
        });

        // Sample prompts
        document.querySelectorAll('.sample-prompt').forEach(btn => {
            btn.addEventListener('click', () => {
                this.elements.promptInput.value = btn.dataset.prompt;
                this.elements.promptInput.focus();
            });
        });
    }

    /**
     * Set up WebSocket connection and handlers
     */
    setupWebSocket() {
        this.ws.on('connected', () => {
            this.updateStatus('Connected');
        });

        this.ws.on('disconnected', () => {
            this.updateStatus('Disconnected');
        });

        this.ws.on('progress', (data) => {
            this.showProgress(data);
        });

        this.ws.on('complete', (data) => {
            this.handleGenerationComplete(data);
        });

        this.ws.on('error', (error) => {
            this.handleGenerationError(error);
        });

        // Connect
        this.ws.connect();

        // Keep connection alive
        setInterval(() => this.ws.ping(), 30000);
    }

    /**
     * Load session state from API
     */
    async loadSession() {
        try {
            const session = await this.api.getCurrentSession();
            this.state.session = session;

            if (session.current_image) {
                this.state.currentImage = session.current_image;
                this.showImage(session.current_image);
            }

            await this.loadHistory();
            this.updateStatus(`${session.generation_count} images`);

        } catch (error) {
            console.error('Failed to load session:', error);
            this.updateStatus('Ready');
        }
    }

    /**
     * Load generation history
     */
    async loadHistory() {
        try {
            const response = await this.api.getHistory(100);
            this.state.history = response.generations;
            this.renderHistory();
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    /**
     * Handle generate button click
     */
    async handleGenerate() {
        const prompt = this.elements.promptInput.value.trim();
        if (!prompt || this.state.isGenerating) return;

        this.state.isGenerating = true;
        this.elements.generateBtn.disabled = true;
        this.showProgress({ step: 0, total_steps: this.state.params.steps, status: 'starting' });

        try {
            let result;

            // Determine if this is a new generation or refinement
            if (this.state.currentImage) {
                // Refinement
                result = await this.api.refine(prompt, this.state.params);
            } else {
                // New generation
                result = await this.api.generateNew(prompt, this.state.params);
            }

            // Result is handled by WebSocket complete event
            // But we also update here in case WebSocket missed it
            if (result && result.image_url) {
                this.handleGenerationComplete({
                    image_url: result.image_url,
                    metadata: result.metadata
                });
            }

        } catch (error) {
            this.handleGenerationError({ message: error.message });
        }
    }

    /**
     * Handle generation complete
     */
    handleGenerationComplete(data) {
        this.state.isGenerating = false;
        this.elements.generateBtn.disabled = false;
        this.hideProgress();

        // Clear prompt input
        this.elements.promptInput.value = '';

        // Update placeholder for refinement
        this.elements.promptInput.placeholder = 'How would you like to refine this image?';

        // Reload session and history
        this.loadSession();
    }

    /**
     * Handle generation error
     */
    handleGenerationError(error) {
        this.state.isGenerating = false;
        this.elements.generateBtn.disabled = false;
        this.hideProgress();

        // Show error message
        alert(`Generation failed: ${error.message}`);
    }

    /**
     * Show progress overlay
     */
    showProgress(data) {
        this.elements.progressOverlay.style.display = 'flex';

        const percentage = data.total_steps > 0
            ? Math.round((data.step / data.total_steps) * 100)
            : 0;

        this.elements.progressBar.style.width = `${percentage}%`;
        this.elements.progressText.textContent = data.status === 'starting'
            ? 'Preparing...'
            : 'Generating...';

        const eta = data.eta_seconds ? `${Math.round(data.eta_seconds)}s` : '--';
        this.elements.progressDetails.textContent = `Step ${data.step}/${data.total_steps} • ETA: ${eta}`;
    }

    /**
     * Hide progress overlay
     */
    hideProgress() {
        this.elements.progressOverlay.style.display = 'none';
        this.elements.progressBar.style.width = '0%';
    }

    /**
     * Show an image
     */
    showImage(imageData) {
        const imageUrl = imageData.image_url.startsWith('/')
            ? imageData.image_url
            : `/${imageData.image_url}`;

        this.elements.currentImage.src = imageUrl;
        this.elements.emptyCanvas.style.display = 'none';
        this.elements.imageDisplay.style.display = 'block';
        this.elements.imageMeta.style.display = 'block';

        // Update metadata
        const meta = imageData.metadata || imageData;
        this.elements.metaPrompt.textContent = meta.prompt || '-';
        this.elements.metaSeed.textContent = meta.seed || '-';
        this.elements.metaSteps.textContent = meta.steps || '-';
        this.elements.metaTime.textContent = meta.generation_time
            ? `${meta.generation_time.toFixed(1)}s`
            : '-';

        this.state.currentImage = imageData;
    }

    /**
     * Render history list
     */
    renderHistory() {
        if (this.state.history.length === 0) {
            this.elements.historyEmpty.style.display = 'block';
            return;
        }

        this.elements.historyEmpty.style.display = 'none';

        // Clear existing items (except empty state)
        const items = this.elements.historyList.querySelectorAll('.history-item');
        items.forEach(item => item.remove());

        // Render history items (newest first)
        this.state.history.forEach(item => {
            const el = this.createHistoryItem(item);
            this.elements.historyList.insertBefore(el, this.elements.historyEmpty);
        });
    }

    /**
     * Create a history item element
     */
    createHistoryItem(item) {
        const el = document.createElement('div');
        el.className = 'history-item';
        if (this.state.currentImage && this.state.currentImage.id === item.id) {
            el.classList.add('active');
        }

        const thumbnailUrl = item.thumbnail_url || item.image_url;

        el.innerHTML = `
            <img src="${thumbnailUrl}" alt="${item.prompt}" loading="lazy">
            <div class="history-item-overlay">
                <span class="history-item-type ${item.type === 'refinement' ? 'refine' : ''}">${item.type === 'refinement' ? '✏️' : '✨'}</span>
            </div>
        `;

        el.addEventListener('click', () => {
            this.showImage(item);
            // Update active state
            this.elements.historyList.querySelectorAll('.history-item').forEach(i => {
                i.classList.remove('active');
            });
            el.classList.add('active');
        });

        return el;
    }

    /**
     * Handle clear session
     */
    async handleClear() {
        if (!confirm('Clear all generated images?')) return;

        try {
            await this.api.clearSession();

            this.state.currentImage = null;
            this.state.history = [];

            this.elements.emptyCanvas.style.display = 'block';
            this.elements.imageDisplay.style.display = 'none';
            this.elements.imageMeta.style.display = 'none';
            this.elements.promptInput.placeholder = 'Describe the image you want to create...';

            this.renderHistory();
            this.updateStatus('Ready');

        } catch (error) {
            console.error('Failed to clear session:', error);
            alert('Failed to clear session');
        }
    }

    /**
     * Handle download
     */
    handleDownload() {
        if (!this.state.currentImage) return;

        const imageUrl = this.state.currentImage.image_url;
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = imageUrl.split('/').pop();
        link.click();
    }

    /**
     * Update status display
     */
    updateStatus(text) {
        this.elements.sessionInfo.textContent = text;
    }
}

// Initialize app
const app = new App();
