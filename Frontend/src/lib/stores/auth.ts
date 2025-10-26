import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { api } from '$lib/api';

interface User {
	id: string;
	email: string;
	user_metadata: Record<string, any>;
	app_metadata: Record<string, any>;
	created_at: string;
}

interface Session {
	access_token: string;
	refresh_token: string;
	expires_at: number;
	user: User | null;
}

// Store session in sessionStorage (not localStorage for security)
function createAuthStore() {
	const { subscribe, set, update } = writable<Session | null>(null);

	return {
		subscribe,
		setSession: (session: Session) => {
			if (browser) {
				// Store tokens in sessionStorage (cleared when browser closes)
				sessionStorage.setItem('access_token', session.access_token);
				sessionStorage.setItem('refresh_token', session.refresh_token);
				sessionStorage.setItem('expires_at', session.expires_at.toString());
			}
			set(session);
		},
		loadSession: async () => {
			if (!browser) return;

			const access_token = sessionStorage.getItem('access_token');
			const refresh_token = sessionStorage.getItem('refresh_token');
			const expires_at = sessionStorage.getItem('expires_at');

			if (!access_token || !refresh_token || !expires_at) {
				set(null);
				return;
			}

			// Check if token is expired
			const now = Math.floor(Date.now() / 1000);
			if (parseInt(expires_at) < now) {
				// Try to refresh
				try {
					const data = await api.auth.refreshSession(refresh_token);
					const session = {
						access_token: data.access_token,
						refresh_token: data.refresh_token,
						expires_at: data.expires_at,
						user: null,
					};

					// Update storage
					sessionStorage.setItem('access_token', data.access_token);
					sessionStorage.setItem('refresh_token', data.refresh_token);
					sessionStorage.setItem('expires_at', data.expires_at.toString());

					// Fetch user info
					await fetchUserInfo(session);
				} catch (error) {
					console.error('Failed to refresh session:', error);
					set(null);
					sessionStorage.clear();
				}
			} else {
				// Token is valid, fetch user info
				const session = {
					access_token,
					refresh_token,
					expires_at: parseInt(expires_at),
					user: null,
				};
				await fetchUserInfo(session);
			}

			async function fetchUserInfo(session: Session) {
				try {
					const data = await api.auth.getUser(session.access_token);
					set({
						...session,
						user: data.user,
					});
				} catch (error) {
					console.error('Failed to fetch user info:', error);
					set(session);
				}
			}
		},
		clearSession: () => {
			if (browser) {
				sessionStorage.clear();
			}
			set(null);
		},
		logout: async () => {
			if (!browser) return;

			const access_token = sessionStorage.getItem('access_token');
			if (access_token) {
				try {
					await api.auth.logout(access_token);
				} catch (error) {
					console.error('Logout error:', error);
				}
			}

			sessionStorage.clear();
			set(null);
		},
	};
}

export const authStore = createAuthStore();
