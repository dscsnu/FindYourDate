// API configuration and utilities
import { env } from '$env/dynamic/public';

const API_BASE_URL = env.PUBLIC_API_URL || 'http://localhost:1386/api';

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
		// The backend takes the email from the session cookie, not the body.
		create: async (profile: Record<string, unknown>) => {
			const response = await fetch(`${API_BASE_URL}/users/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify(profile)
			});
			if (!response.ok) {
				const error = await response.json().catch(() => ({}));
				throw new Error(detailToMessage(error.detail) || 'Failed to create user');
			}
			return response.json();
		}
	},

	// Status endpoints
	status: {
		userStatus: async () => {
			const response = await fetch(`${API_BASE_URL}/status/user-status`, {
				credentials: 'include'
			});
			if (!response.ok) throw new Error('Failed to check user status');
			return response.json();
		}
	},

	// Chat endpoints
	chat: {
		nextQuestion: async (chatHistory: Array<{ q: string; a: string }>) => {
			return fetch(`${API_BASE_URL}/chat/next-question`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({ chat_history: chatHistory })
			});
		}
	},

	// Round 1 Results endpoints
	round1: {
		checkResult: async () => {
			const response = await fetch(`${API_BASE_URL}/round1/check-result`, {
				credentials: 'include',
			});
			if (!response.ok) throw new Error('Failed to check Round 1 results');
			return response.json();
		},

		updateMatchStatus: async (applyRound2: boolean) => {
			const response = await fetch(`${API_BASE_URL}/round1/update-match-status`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				credentials: 'include',
				body: JSON.stringify({ apply_round2: applyRound2 })
			});
			if (!response.ok) throw new Error('Failed to update match status');
			return response.json();
		}
	}
};

/** FastAPI validation errors arrive as an array, which renders as [object Object]. */
function detailToMessage(detail: unknown): string {
	if (typeof detail === 'string') return detail;
	if (Array.isArray(detail)) return detail.map((d) => d?.msg ?? String(d)).join(', ');
	return '';
}

export { API_BASE_URL };
