// Saved chat progress lives in localStorage under a per-season key. Bump the season
// when a new edition opens so chats saved in earlier years are no longer picked up.
const CHAT_KEY_ROOT = 'chat_';
const CHAT_SEASON = '2026';

export function chatStorageKey(email: string): string {
	return `${CHAT_KEY_ROOT}${CHAT_SEASON}_${email}`;
}

// Remove saved chats; with onlyStale, keep the current season's and drop earlier ones.
export function clearSavedChats({ onlyStale = false } = {}): void {
	const current = `${CHAT_KEY_ROOT}${CHAT_SEASON}_`;
	try {
		Object.keys(localStorage)
			.filter((key) => key.startsWith(CHAT_KEY_ROOT))
			.filter((key) => !onlyStale || !key.startsWith(current))
			.forEach((key) => localStorage.removeItem(key));
	} catch {
		// Storage can be blocked (private mode); nothing to clear then.
	}
}
