import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { api } from '$lib/api';

interface User {
	id: string;
	email: string;
	name: string | null;
}

interface Session {
	user: User | null;
	authenticated: boolean;
}

function createAuthStore() {
	const { subscribe, set, update } = writable<Session | null>(null);

	return {
		subscribe,
		setSession: (user: User) => {
			set({ user, authenticated: true });
		},
		loadSession: async () => {
			if (!browser) return;

			try {
				const data = await api.auth.getUser();
				set({
					user: data.user,
					authenticated: true
				});
			} catch (error) {
				set(null);
			}
		},
		clearSession: () => {
			set(null);
		},
		logout: async () => {
			if (!browser) return;

			try {
				await api.auth.logout();
			} catch (error) {
				console.error('Logout error:', error);
			}

			// Drop saved chat progress and user_id so the next person on this device starts clean.
			try {
				localStorage.clear();
				sessionStorage.clear();
			} catch {
				// Storage can be blocked (private mode); nothing to clear then.
			}

			set(null);
		},
	};
}

export const authStore = createAuthStore();
