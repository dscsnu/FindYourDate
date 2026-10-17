import { describe, expect, it } from 'vitest';
import { deriveOrientation } from './orientation';

describe('deriveOrientation', () => {
	it.each([
		['male', 'women', 'straight'],
		['female', 'men', 'straight'],
		['male', 'men', 'gay'],
		['female', 'women', 'lesbian'],
		['male', 'everyone', 'bisexual'],
		['female', 'everyone', 'bisexual']
	])('%s interested in %s -> %s', (gender, interestedIn, expected) => {
		expect(deriveOrientation(gender, interestedIn)).toBe(expected);
	});
});
