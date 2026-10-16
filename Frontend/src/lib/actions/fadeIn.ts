/**
 * Fade an <img> in once it has finished loading and decoding.
 *
 * Pair with `loading="lazy"` for off-screen images: the browser defers the
 * request, and this keeps the image hidden until it can paint in one go.
 */
export function fadeIn(node: HTMLImageElement) {
	node.classList.add('lazy-fade');

	const reveal = () => node.classList.add('is-loaded');

	// Cached images can already be complete before the action runs.
	if (node.complete && node.naturalWidth > 0) {
		reveal();
		return;
	}

	const onLoad = () => {
		node.decode().catch(() => {}).finally(reveal);
	};

	node.addEventListener('load', onLoad, { once: true });
	// Never leave a broken image invisible forever.
	node.addEventListener('error', reveal, { once: true });

	return {
		destroy() {
			node.removeEventListener('load', onLoad);
			node.removeEventListener('error', reveal);
		}
	};
}

const warmed = new Set<string>();

/** Fetch images in the background so a later screen shows them instantly. */
export function preloadImages(urls: string[]) {
	if (typeof window === 'undefined') return;

	const run = () => {
		for (const url of urls) {
			if (warmed.has(url)) continue;
			warmed.add(url);
			const img = new Image();
			img.decoding = 'async';
			img.src = url;
		}
	};

	if ('requestIdleCallback' in window) {
		window.requestIdleCallback(run, { timeout: 2000 });
	} else {
		setTimeout(run, 200);
	}
}
