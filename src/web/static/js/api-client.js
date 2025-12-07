/**
 * API Client for Dimpressionist
 * Handles REST API calls and WebSocket connections
 */

class APIClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || window.location.origin;
        this.apiBase = `${this.baseUrl}/api/v1`;
    }

    /**
     * Make a fetch request with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * Generate a new image
     */
    async generateNew(prompt, params = {}) {
        return this.request('/generate/new', {
            method: 'POST',
            body: JSON.stringify({
                prompt,
                steps: params.steps || 28,
                guidance_scale: params.guidanceScale || 3.5,
                seed: params.seed || null,
                width: params.width || 1024,
                height: params.height || 1024
            })
        });
    }

    /**
     * Refine current image
     */
    async refine(modification, params = {}) {
        return this.request('/generate/refine', {
            method: 'POST',
            body: JSON.stringify({
                modification,
                strength: params.strength || 0.6,
                steps: params.steps || 28,
                guidance_scale: params.guidanceScale || 3.5
            })
        });
    }

    /**
     * Cancel ongoing generation
     */
    async cancelGeneration() {
        return this.request('/generate/cancel', { method: 'POST' });
    }

    /**
     * Get current session
     */
    async getCurrentSession() {
        return this.request('/session/current');
    }

    /**
     * Get generation history
     */
    async getHistory(limit = 50, offset = 0, type = 'all') {
        return this.request(`/session/history?limit=${limit}&offset=${offset}&type=${type}`);
    }

    /**
     * Clear session
     */
    async clearSession() {
        return this.request('/session/clear', { method: 'POST' });
    }

    /**
     * Get system status
     */
    async getStatus() {
        return this.request('/system/status');
    }

    /**
     * Get configuration
     */
    async getConfig() {
        return this.request('/config');
    }

    /**
     * Get image URL
     */
    getImageUrl(imageName) {
        return `${this.apiBase}/images/${imageName}`;
    }

    /**
     * Get thumbnail URL
     */
    getThumbnailUrl(imageName) {
        const stem = imageName.replace(/\.[^/.]+$/, '');
        return `${this.apiBase}/thumbnails/${stem}_thumb.jpg`;
    }
}


/**
 * WebSocket handler for real-time updates
 */
class WSHandler {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || window.location.origin;
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = this.baseUrl.replace(/^https?:\/\//, '');
        this.wsUrl = `${wsProtocol}//${host}/api/v1/ws`;

        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;

        this.callbacks = {
            progress: [],
            complete: [],
            error: [],
            sessionUpdate: [],
            connected: [],
            disconnected: []
        };
    }

    /**
     * Connect to WebSocket
     */
    connect() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            this.socket = new WebSocket(this.wsUrl);

            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this._emit('connected');

                // Subscribe to progress updates
                this.socket.send(JSON.stringify({
                    type: 'subscribe',
                    channel: 'generation_progress'
                }));
            };

            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this._handleMessage(message);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this._emit('disconnected');
                this._attemptReconnect();
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this._attemptReconnect();
        }
    }

    /**
     * Disconnect from WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    /**
     * Handle incoming messages
     */
    _handleMessage(message) {
        switch (message.type) {
            case 'progress':
                this._emit('progress', message.data);
                break;
            case 'complete':
                this._emit('complete', message.data);
                break;
            case 'error':
                this._emit('error', message.error);
                break;
            case 'session_update':
                this._emit('sessionUpdate', message.data);
                break;
            case 'pong':
                // Heartbeat response
                break;
            case 'subscribed':
                console.log('Subscribed to:', message.channel);
                break;
        }
    }

    /**
     * Attempt to reconnect
     */
    _attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnect attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Register a callback for an event
     */
    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
        return this;
    }

    /**
     * Remove a callback
     */
    off(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event] = this.callbacks[event].filter(cb => cb !== callback);
        }
        return this;
    }

    /**
     * Emit an event to all registered callbacks
     */
    _emit(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (e) {
                    console.error(`Error in ${event} callback:`, e);
                }
            });
        }
    }

    /**
     * Send a ping to keep connection alive
     */
    ping() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type: 'ping' }));
        }
    }
}

// Export for use
window.APIClient = APIClient;
window.WSHandler = WSHandler;
