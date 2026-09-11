import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiFetch } from './api';

const ok = () => new Response('{}', { status: 200 });
const unauthorized = () => new Response('{}', { status: 401 });

function mockFetch(handler: (url: string, init?: RequestInit) => Response | Promise<Response>) {
	const spy = vi.fn((url: string, init?: RequestInit) => Promise.resolve(handler(url, init)));
	vi.stubGlobal('fetch', spy);
	return spy;
}

const calls = (spy: ReturnType<typeof mockFetch>) => spy.mock.calls.map((c) => String(c[0]));

describe('apiFetch', () => {
	beforeEach(() => {
		vi.unstubAllGlobals();
	});

	it('passes a successful response straight through', async () => {
		const spy = mockFetch(ok);
		const res = await apiFetch('/status/user-status');

		expect(res.status).toBe(200);
		expect(spy).toHaveBeenCalledTimes(1);
	});

	it('refreshes and replays the request when the token has expired', async () => {
		let refreshed = false;
		const spy = mockFetch((url) => {
			if (url.includes('/auth/refresh')) {
				refreshed = true;
				return ok();
			}
			return refreshed ? ok() : unauthorized();
		});

		const res = await apiFetch('/status/user-status');

		expect(res.status).toBe(200);
		expect(calls(spy)).toEqual([
			expect.stringContaining('/status/user-status'),
			expect.stringContaining('/auth/refresh'),
			expect.stringContaining('/status/user-status')
		]);
	});

	it('replays the original method and body, not a bare GET', async () => {
		let refreshed = false;
		const spy = mockFetch((url) => {
			if (url.includes('/auth/refresh')) {
				refreshed = true;
				return ok();
			}
			return refreshed ? ok() : unauthorized();
		});

		await apiFetch('/users/', { method: 'POST', body: '{"name":"x"}' });

		const replay = spy.mock.calls.at(-1)![1]!;
		expect(replay.method).toBe('POST');
		expect(replay.body).toBe('{"name":"x"}');
		expect(replay.credentials).toBe('include');
	});

	it('gives up after one refresh instead of looping', async () => {
		const spy = mockFetch((url) => (url.includes('/auth/refresh') ? ok() : unauthorized()));

		const res = await apiFetch('/status/user-status');

		expect(res.status).toBe(401);
		// original + refresh + one replay, then stop
		expect(spy).toHaveBeenCalledTimes(3);
	});

	it('surfaces the 401 when the refresh token is also dead', async () => {
		const spy = mockFetch(unauthorized);

		const res = await apiFetch('/status/user-status');

		expect(res.status).toBe(401);
		expect(spy).toHaveBeenCalledTimes(2); // original + failed refresh, no replay
	});

	it('shares one refresh across simultaneous 401s', async () => {
		let refreshed = false;
		const spy = mockFetch(async (url) => {
			if (url.includes('/auth/refresh')) {
				await new Promise((r) => setTimeout(r, 10));
				refreshed = true;
				return ok();
			}
			return refreshed ? ok() : unauthorized();
		});

		// The chat room fires status + question together on mount.
		const results = await Promise.all([
			apiFetch('/status/user-status'),
			apiFetch('/chat/next-question'),
			apiFetch('/round1/check-result')
		]);

		expect(results.every((r) => r.status === 200)).toBe(true);
		expect(calls(spy).filter((u) => u.includes('/auth/refresh'))).toHaveLength(1);
	});

	it('does not try to refresh a non-401 failure', async () => {
		const spy = mockFetch(() => new Response('{}', { status: 503 }));

		const res = await apiFetch('/chat/next-question');

		expect(res.status).toBe(503);
		expect(spy).toHaveBeenCalledTimes(1);
	});
});
