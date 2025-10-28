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
		
		refreshSession: async () => {
			// Backend reads refresh_token from httpOnly cookie
			const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
				method: 'POST',
				credentials: 'include', // Send cookies
			});
			if (!response.ok) throw new Error('Failed to refresh session');
			return response.json();
		},
		
		getUser: async () => {
			// Backend reads access_token from httpOnly cookie
			const response = await fetch(`${API_BASE_URL}/auth/user`, {
				credentials: 'include', // Send cookies
			});
			if (!response.ok) throw new Error('Failed to get user');
			return response.json();
		},
		
		logout: async () => {
			// Backend reads access_token from httpOnly cookie and clears cookies
			const response = await fetch(`${API_BASE_URL}/auth/logout`, {
				method: 'POST',
				credentials: 'include', // Send cookies
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
	
	// Round 1 Results endpoints
	round1: {
		checkResult: async (email: string) => {
			const response = await fetch(`${API_BASE_URL}/round1/check-result?email=${encodeURIComponent(email)}`, {
				credentials: 'include',
			});
			if (!response.ok) throw new Error('Failed to check Round 1 results');
			return response.json();
		},
		
		updateMatchStatus: async (email: string, applyRound2: boolean) => {
			const response = await fetch(`${API_BASE_URL}/round1/update-match-status`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				credentials: 'include',
				body: JSON.stringify({
					user_email: email,
					apply_round2: applyRound2
				})
			});
			if (!response.ok) throw new Error('Failed to update match status');
			return response.json();
		}
	}
};

export { API_BASE_URL };
