// API configuration and utilities
import { env } from '$env/dynamic/public';

const API_BASE_URL = env.PUBLIC_API_URL || 'http://localhost:1386/api';

let refreshInFlight: Promise<boolean> | null = null;

/**
 * Trade the refresh cookie for a fresh access token.
 * Parallel 401s share one attempt instead of each firing their own.
 */
export function refreshSession(): Promise<boolean> {
	refreshInFlight ??= fetch(`${API_BASE_URL}/auth/refresh`, {
		method: 'POST',
		credentials: 'include'
	})
		.then((r) => r.ok)
		.catch(() => false)
		.finally(() => {
			refreshInFlight = null;
		});
	return refreshInFlight;
}

/**
 * Authenticated fetch. Supabase access tokens expire after an hour, so a 401
 * is usually just staleness: refresh once and replay the request rather than
 * dumping the user back to the landing page mid-flow.
 *
 * Never use this for the auth endpoints themselves - /auth/refresh would recurse.
 */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
	const send = () => fetch(`${API_BASE_URL}${path}`, { ...init, credentials: 'include' });

	const response = await send();
	if (response.status !== 401) return response;

	return (await refreshSession()) ? send() : response;
}

export const api = {
	// Auth endpoints
	auth: {
		googleLogin: async () => {
			const response = await fetch(`${API_BASE_URL}/auth/google/login`);
			if (!response.ok) throw new Error('Failed to get Google auth URL');
			return response.json();
		},
		
		refreshSession,

		getUser: async () => {
			// Backend reads access_token from httpOnly cookie. This is the call
			// that revives an hour-old session on page load.
			const response = await apiFetch('/auth/user');
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
			const response = await apiFetch('/users/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
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
			const response = await apiFetch('/status/user-status');
			if (!response.ok) throw new Error('Failed to check user status');
			return response.json();
		}
	},

	// Chat endpoints
	chat: {
		// Returns the raw Response; callers inspect 429/503 themselves.
		nextQuestion: async (chatHistory: Array<{ q: string; a: string }>) => {
			return apiFetch('/chat/next-question', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ chat_history: chatHistory })
			});
		}
	},

	// Round 1 Results endpoints
	round1: {
		checkResult: async () => {
			const response = await apiFetch('/round1/check-result');
			if (!response.ok) throw new Error('Failed to check Round 1 results');
			return response.json();
		},

		updateMatchStatus: async (applyRound2: boolean) => {
			const response = await apiFetch('/round1/update-match-status', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
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
