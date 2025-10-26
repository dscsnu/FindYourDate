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

			set(null);
		},
	};
}

export const authStore = createAuthStore();
