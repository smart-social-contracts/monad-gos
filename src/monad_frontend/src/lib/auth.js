/**
 * Internet Identity for Monad GOS — minimal AuthClient wrapper.
 * Portal embed uses scoped II delegations from the host; mock mode skips II entirely.
 */
import { AuthClient } from '@dfinity/auth-client';
import {
	getPortalDelegationIdentity,
	isEmbeddedInPortal,
	requestAuthRefresh,
	waitForPortalDelegation,
} from './portal-bridge.ts';

const IDENTITY_PROVIDER = 'https://identity.ic0.app';

/** @type {AuthClient | null} */
let authClient = null;

export function isAuthMockMode() {
	if (import.meta.env.VITE_MONAD_GOS_MOCK === 'true') return true;
	if (isEmbeddedInPortal()) return false;
	return !import.meta.env.VITE_MONAD_GOS_CANISTER_ID;
}

async function getAuthClient() {
	if (!authClient) {
		authClient = await AuthClient.create();
	}
	return authClient;
}

/** @returns {Promise<boolean>} whether a session already exists */
export async function initAuth() {
	if (isAuthMockMode()) return true;
	if (isEmbeddedInPortal()) {
		return !!getPortalDelegationIdentity();
	}
	const client = await getAuthClient();
	return client.isAuthenticated();
}

export async function login() {
	if (isAuthMockMode()) return;
	if (isEmbeddedInPortal()) {
		requestAuthRefresh();
		await waitForPortalDelegation();
		return;
	}
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
	if (isAuthMockMode()) return;
	if (isEmbeddedInPortal()) {
		// Host owns the portal session; clear local view only.
		return;
	}
	const client = await getAuthClient();
	await client.logout();
}

export function isAnonymous() {
	if (isAuthMockMode()) return false;
	if (isEmbeddedInPortal()) {
		const identity = getPortalDelegationIdentity();
		return !identity || identity.getPrincipal().isAnonymous();
	}
	const identity = authClient?.getIdentity();
	return !identity || identity.getPrincipal().isAnonymous();
}

export function getPrincipalText() {
	if (isAuthMockMode()) return 'citizen-mock';
	if (isEmbeddedInPortal()) {
		return getPortalDelegationIdentity()?.getPrincipal().toText() ?? '';
	}
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
	if (isAuthMockMode()) return authClient?.getIdentity();
	if (isEmbeddedInPortal()) {
		return getPortalDelegationIdentity() ?? undefined;
	}
	return authClient?.getIdentity();
}
