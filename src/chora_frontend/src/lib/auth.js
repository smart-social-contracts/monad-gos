/**
 * Internet Identity for Chora — minimal AuthClient wrapper.
 * Mock mode (VITE_CHORA_MOCK=true) skips II entirely.
 */
import { AuthClient } from '@dfinity/auth-client';

const MOCK_MODE =
	import.meta.env.VITE_CHORA_MOCK === 'true' ||
	!import.meta.env.VITE_CHORA_CANISTER_ID;

const IDENTITY_PROVIDER = 'https://identity.ic0.app';

/** @type {AuthClient | null} */
let authClient = null;

export function isAuthMockMode() {
	return MOCK_MODE;
}

async function getAuthClient() {
	if (!authClient) {
		authClient = await AuthClient.create();
	}
	return authClient;
}

/** @returns {Promise<boolean>} whether a session already exists */
export async function initAuth() {
	if (MOCK_MODE) return true;
	const client = await getAuthClient();
	return client.isAuthenticated();
}

export async function login() {
	if (MOCK_MODE) return;
	const client = await getAuthClient();
	await new Promise((resolve, reject) => {
		client.login({
			identityProvider: IDENTITY_PROVIDER,
			onSuccess: () => resolve(),
			onError: (err) => reject(err ?? new Error('Internet Identity login failed')),
		});
	});
}

export async function logout() {
	if (MOCK_MODE) return;
	const client = await getAuthClient();
	await client.logout();
}

export function isAnonymous() {
	if (MOCK_MODE) return false;
	const identity = authClient?.getIdentity();
	return !identity || identity.getPrincipal().isAnonymous();
}

export function getPrincipalText() {
	if (MOCK_MODE) return 'citizen-mock';
	const identity = authClient?.getIdentity();
	return identity?.getPrincipal().toText() ?? '';
}

/** Short principal for header display: first 5 … last 3 */
export function formatPrincipalShort(principal = getPrincipalText()) {
	if (!principal) return '';
	if (principal.length <= 8) return principal;
	return `${principal.slice(0, 5)}…${principal.slice(-3)}`;
}

export function getIdentity() {
	if (MOCK_MODE) return authClient?.getIdentity();
	return authClient?.getIdentity();
}
