import { describe, expect, it } from 'vitest';
import {
	inferCanisterIdFromHost,
	isLiveFrontendHost,
	LIVE_BACKEND_CANISTER_ID,
	LIVE_FRONTEND_CANISTER_ID,
} from './runtime.js';

describe('live frontend host', () => {
	it('recognizes the deployed asset canister host', () => {
		expect(isLiveFrontendHost(`${LIVE_FRONTEND_CANISTER_ID}.icp0.io`)).toBe(true);
		expect(isLiveFrontendHost(`${LIVE_FRONTEND_CANISTER_ID}.raw.icp0.io`)).toBe(true);
		expect(isLiveFrontendHost('localhost')).toBe(false);
	});

	it('infers the live backend canister so direct visits are not mock mode', () => {
		expect(inferCanisterIdFromHost(`${LIVE_FRONTEND_CANISTER_ID}.icp0.io`, '')).toBe(
			LIVE_BACKEND_CANISTER_ID,
		);
		expect(inferCanisterIdFromHost('localhost', '')).toBe('');
		expect(inferCanisterIdFromHost(`${LIVE_FRONTEND_CANISTER_ID}.icp0.io`, 'aaaaa-aa')).toBe(
			'aaaaa-aa',
		);
	});
});
