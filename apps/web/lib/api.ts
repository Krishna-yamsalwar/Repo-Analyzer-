// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function to make API calls
export async function apiCall(endpoint: string, options?: RequestInit) {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });
    return response;
}

// Auth API endpoints
export const authApi = {
    register: async (name: string, email: string, password: string) => {
        return apiCall('/api/v1/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password }),
        });
    },

    login: async (email: string, password: string) => {
        return apiCall('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    refresh: async (refreshToken: string) => {
        return apiCall('/api/v1/auth/refresh', {
            method: 'POST',
            body: JSON.stringify({ refresh_token: refreshToken }),
        });
    },
};

// Repos API endpoints
export const reposApi = {
    getAll: async () => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        return apiCall('/api/v1/repos/', {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
    },

    create: async (name: string, url?: string, description?: string, local_path?: string) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        return apiCall('/api/v1/repos/', {
            method: 'POST',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            body: JSON.stringify({ name, url, description, local_path }),
        });
    },

    delete: async (id: number) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        return apiCall(`/api/v1/repos/${id}/`, {
            method: 'DELETE',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
    },

    getStructure: async (id: number) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        return apiCall(`/api/v1/repos/${id}/structure/`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
    },
};

// Chat API endpoints
export const chatApi = {
    stream: async (message: string, repoId?: number, conversationId?: number) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        return fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
                message,
                repo_id: repoId,
                conversation_id: conversationId,
            }),
        });
    },
};
