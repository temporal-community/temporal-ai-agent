const API_BASE_URL = 'http://127.0.0.1:8000';

const resolveRequestTimeout = () => {
    const env = typeof import.meta !== 'undefined' ? import.meta.env : undefined;
    const configured = env?.VITE_API_TIMEOUT_MS;
    const parsed = Number.parseInt(configured, 10);
    if (Number.isFinite(parsed) && parsed > 0) {
        return parsed;
    }
    return 15000;
};

const REQUEST_TIMEOUT_MS = resolveRequestTimeout(); // default to 15s, overridable via Vite env

class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
        this.name = 'ApiError';
    }
}

async function handleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
            errorData.message || 'An error occurred',
            response.status
        );
    }
    return response.json();
}

async function fetchWithTimeout(url, options = {}, timeout = REQUEST_TIMEOUT_MS) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        return await fetch(url, { ...options, signal: controller.signal });
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new ApiError('Request timed out', 408);
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

export const apiService = {
    async getConversationHistory() {
        try {
            const res = await fetchWithTimeout(`${API_BASE_URL}/get-conversation-history`);
            return handleResponse(res);
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError(
                'Failed to fetch conversation history',
                error.status || 500
            );
        }
    },

    async sendMessage(message) {
        if (!message?.trim()) {
            throw new ApiError('Message cannot be empty', 400);
        }

        try {
            const res = await fetchWithTimeout(
                `${API_BASE_URL}/send-prompt?prompt=${encodeURIComponent(message)}`,
                { 
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );
            return handleResponse(res);
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError(
                'Failed to send message',
                error.status || 500
            );
        }
    },

    async startWorkflow() {
        try {
            const res = await fetchWithTimeout(
                `${API_BASE_URL}/start-workflow`,
                { 
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );
            return handleResponse(res);
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError(
                'Failed to start workflow',
                error.status || 500
            );
        }
    },

    async confirm() {
        try {
            const res = await fetchWithTimeout(`${API_BASE_URL}/confirm`, { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            return handleResponse(res);
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError(
                'Failed to confirm action',
                error.status || 500
            );
        }
    }
}; 
