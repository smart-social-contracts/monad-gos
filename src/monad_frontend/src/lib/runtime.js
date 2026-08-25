/**
 * Frontend runtime: live canister pair and mock-mode detection.
 *
 * Direct visits to the asset canister (not portal-embedded) used to fall into
 * mock mode because the production build has no VITE_MONAD_GOS_CANISTER_ID.
 * That produced wish-mock-* seals and a silent Monad that never replies.
 */
export const LIVE_FRONTEND_CANISTER_ID = 'sndq3-zqaaa-aaaab-qhexa-cai';
export const LIVE_BACKEND_CANISTER_ID = 'sea3h-pyaaa-aaaab-qhewq-cai';

export function envForcesMock() {
	return import.meta.env.VITE_MONAD_GOS_MOCK === 'true';
}

export function envCanisterId() {
	return import.meta.env.VITE_MONAD_GOS_CANISTER_ID || '';
}

export function isLiveFrontendHost(hostname = currentHostname()) {
	if (!hostname) return false;
	return (
		hostname === `${LIVE_FRONTEND_CANISTER_ID}.icp0.io` ||
		hostname === `${LIVE_FRONTEND_CANISTER_ID}.raw.icp0.io` ||
		hostname === `${LIVE_FRONTEND_CANISTER_ID}.ic0.app` ||
		hostname.startsWith(`${LIVE_FRONTEND_CANISTER_ID}.`)
	);
}

export function inferCanisterIdFromHost(hostname = currentHostname(), bakedId = envCanisterId()) {
	if (bakedId) return bakedId;
	if (isLiveFrontendHost(hostname)) return LIVE_BACKEND_CANISTER_ID;
	return '';
}

function currentHostname() {
	if (typeof window === 'undefined') return '';
	return window.location?.hostname || '';
}
