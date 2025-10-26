// API configuration and utilities
import { PUBLIC_API_URL } from '$env/static/public';

const API_BASE_URL = PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
	// Auth endpoints
	auth: {
		googleLogin: async () => {
			const response = await fetch(`${API_BASE_URL}/auth/google/login`);
			if (!response.ok) throw new Error('Failed to get Google auth URL');
			return response.json();
		},
		
		refreshSession: async (refreshToken: string) => {
			const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ refresh_token: refreshToken }),
			});
			if (!response.ok) throw new Error('Failed to refresh session');
			return response.json();
		},
		
		getUser: async (accessToken: string) => {
			const response = await fetch(
				`${API_BASE_URL}/auth/user?access_token=${accessToken}`
			);
			if (!response.ok) throw new Error('Failed to get user');
			return response.json();
		},
		
		logout: async (accessToken: string) => {
			const response = await fetch(`${API_BASE_URL}/auth/logout`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ access_token: accessToken }),
			});
			if (!response.ok) throw new Error('Failed to logout');
			return response.json();
		},
	},
	
	// Users endpoints
	users: {
		// Add user endpoints here as needed
	},
	
	// Chat endpoints
	chat: {
		// Add chat endpoints here as needed
	},
};

export { API_BASE_URL };
