import { writable } from 'svelte/store';

interface AppConfig {
	formsClosed: boolean;
	round1ResultPublished: boolean;
}

function createConfigStore() {
	const { subscribe, set, update } = writable<AppConfig>({
		formsClosed: true, // Set to true to show the forms closed page
		round1ResultPublished: true // Set to true to show Round 1 results
	});

	return {
		subscribe,
		setFormsClosed: (closed: boolean) => {
			update(config => ({ ...config, formsClosed: closed }));
		},
		setRound1ResultPublished: (published: boolean) => {
			update(config => ({ ...config, round1ResultPublished: published }));
		}
	};
}

export const configStore = createConfigStore();
