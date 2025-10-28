import { writable } from 'svelte/store';

interface AppConfig {
	formsClosed: boolean;
}

function createConfigStore() {
	const { subscribe, set, update } = writable<AppConfig>({
		formsClosed: true // Set to true to show the forms closed page
	});

	return {
		subscribe,
		setFormsClosed: (closed: boolean) => {
			update(config => ({ ...config, formsClosed: closed }));
		}
	};
}

export const configStore = createConfigStore();
