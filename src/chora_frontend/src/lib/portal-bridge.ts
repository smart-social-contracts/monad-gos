/**
 * Federation portal iframe bridge (Chora frontend side).
 */
import { DelegationIdentity, DelegationChain, Ed25519KeyIdentity } from '@dfinity/identity';

const BRIDGE_VERSION = '1';
const PORTAL_SESSION_KEY = 'chora:portal-embed';
let port: MessagePort | null = null;
let portalConfig: {
	slug?: string;
	backendCanisterId?: string;
	frontendCanisterId?: string;
	env?: string;
} | null = null;
let pendingDelegationRequest = false;
let pendingUiReady = false;
let uiReadySent = false;
let sessionIdentity: Ed25519KeyIdentity | null = null;
let delegationIdentity: DelegationIdentity | null = null;
let delegationExpiresAt: number | null = null;
let refreshTimer: ReturnType<typeof setTimeout> | null = null;

/** Refresh 5 minutes before expiry to avoid edge-of-expiry failures. */
const REFRESH_BUFFER_MS = 5 * 60 * 1000;

function markPortalEmbedded() {
	if (typeof window === 'undefined') return;
	try {
		sessionStorage.setItem(PORTAL_SESSION_KEY, '1');
	} catch {
		// private mode / sandbox without storage
	}
}

function isPortalEmbedded() {
	if (typeof window === 'undefined') return false;
	if (new URLSearchParams(window.location.search).get('portal') === '1') {
		markPortalEmbedded();
		return true;
	}
	if (port) return true;
	try {
		return sessionStorage.getItem(PORTAL_SESSION_KEY) === '1';
	} catch {
		return false;
	}
}

function post(msg: Record<string, unknown>) {
	if (!port) return;
	port.postMessage(msg);
}

function ensureSessionIdentity() {
	if (!sessionIdentity) {
		sessionIdentity = Ed25519KeyIdentity.generate();
	}
	return sessionIdentity;
}

function onPortMessage(event: MessageEvent) {
	const msg = event.data;
	if (!msg || typeof msg.type !== 'string') return;

	switch (msg.type) {
		case 'config:realm':
			portalConfig = msg.payload || null;
			window.dispatchEvent(
				new CustomEvent('portal:config', { detail: portalConfig })
			);
			break;
		case 'auth:delegation':
			applyDelegation(msg.payload).catch((e) => {
				console.error('[portal-bridge] delegation apply failed:', e);
			});
			break;
		case 'auth:logout':
			delegationIdentity = null;
			delegationExpiresAt = null;
			if (refreshTimer) {
				clearTimeout(refreshTimer);
				refreshTimer = null;
			}
			window.dispatchEvent(new CustomEvent('portal:logout'));
			break;
		case 'auth:pending':
			window.dispatchEvent(
				new CustomEvent('portal:auth-pending', { detail: { error: msg.error || '' } })
			);
			break;
		case 'auth:error':
			window.dispatchEvent(
				new CustomEvent('portal:auth-error', { detail: { error: msg.error || 'auth failed' } })
			);
			break;
		default:
			break;
	}
}

async function applyDelegation(payload: {
	delegation?: unknown;
	backendCanisterId?: string;
	expiresAt?: number;
}) {
	if (!payload?.delegation) return;
	const json =
		typeof payload.delegation === 'string'
			? payload.delegation
			: JSON.stringify(payload.delegation);
	const session = ensureSessionIdentity();
	const chain = DelegationChain.fromJSON(json);
	const next = DelegationIdentity.fromDelegation(session, chain);
	const unchanged =
		!!delegationIdentity &&
		delegationIdentity.getPrincipal().toText() === next.getPrincipal().toText();
	delegationIdentity = next;
	delegationExpiresAt = payload.expiresAt || null;
	scheduleRefresh();
	if (unchanged) return;
	window.dispatchEvent(
		new CustomEvent('portal:auth', {
			detail: {
				identity: delegationIdentity,
				backendCanisterId: payload.backendCanisterId,
				expiresAt: payload.expiresAt,
			},
		})
	);
}

function scheduleRefresh() {
	if (refreshTimer) {
		clearTimeout(refreshTimer);
		refreshTimer = null;
	}
	if (!delegationExpiresAt) return;
	const now = Date.now();
	const refreshAt = delegationExpiresAt - REFRESH_BUFFER_MS;
	const delay = refreshAt - now;
	if (delay <= 0) {
		requestSilentAuthProbe();
		return;
	}
	refreshTimer = setTimeout(() => {
		console.log('[portal-bridge] delegation expiring soon, requesting refresh');
		requestSilentAuthProbe();
	}, delay);
}

function requestDelegation(interactive = false) {
	if (!port) {
		pendingDelegationRequest = true;
		return;
	}
	pendingDelegationRequest = false;
	const session = ensureSessionIdentity();
	post({
		type: 'auth:request-delegation',
		payload: {
			sessionPublicKeyDer: Array.from(new Uint8Array(session.getPublicKey().toDer())),
			interactive,
		},
	});
}

export function getPortalDelegationIdentity() {
	return delegationIdentity;
}

export function getPortalConfig() {
	return portalConfig;
}

export function isEmbeddedInPortal() {
	return isPortalEmbedded();
}

export function initPortalBridge() {
	if (!isPortalEmbedded()) return () => {};
	if (typeof window === 'undefined') return () => {};

	markPortalEmbedded();

	const onWindowMessage = (event: MessageEvent) => {
		if (event.data?.type !== 'bridge:init' || !event.ports?.[0]) return;
		port?.close?.();
		port = event.ports[0];
		if (port) {
			port.onmessage = onPortMessage;
		}
		post({ type: 'bridge:ready', payload: { version: BRIDGE_VERSION } });
		requestDelegation(false);
		if (pendingUiReady && !uiReadySent) {
			uiReadySent = true;
			pendingUiReady = false;
			post({ type: 'ui:ready' });
		}
	};

	window.addEventListener('message', onWindowMessage);

	const sayHello = () => {
		try {
			window.parent?.postMessage({ type: 'bridge:hello', version: BRIDGE_VERSION }, '*');
		} catch {
			// parent may be inaccessible outside a real embed
		}
	};
	let helloAttempts = 0;
	const helloTimer = setInterval(() => {
		if (port || ++helloAttempts > 40) {
			clearInterval(helloTimer);
			return;
		}
		sayHello();
	}, 250);
	sayHello();

	return () => {
		clearInterval(helloTimer);
		if (refreshTimer) {
			clearTimeout(refreshTimer);
			refreshTimer = null;
		}
		window.removeEventListener('message', onWindowMessage);
		port = null;
	};
}

export function portalUiReady() {
	if (!isEmbeddedInPortal()) return false;
	if (uiReadySent) return true;
	if (!port) {
		pendingUiReady = true;
		return false;
	}
	uiReadySent = true;
	post({ type: 'ui:ready' });
	return true;
}

export function requestAuthRefresh() {
	requestDelegation(true);
}

export function requestSilentAuthProbe() {
	requestDelegation(false);
}

export function waitForPortalConfig({ timeoutMs = 30_000 } = {}) {
	const existing = getPortalConfig();
	if (existing?.backendCanisterId) return Promise.resolve(existing);

	return new Promise((resolve) => {
		let settled = false;
		const finish = (
			value: {
				slug?: string;
				backendCanisterId?: string;
				frontendCanisterId?: string;
				env?: string;
			} | null
		) => {
			if (settled) return;
			settled = true;
			clearTimeout(timer);
			clearInterval(poll);
			window.removeEventListener('portal:config', onConfig);
			resolve(value);
		};

		const onConfig = () => {
			const cfg = getPortalConfig();
			if (cfg?.backendCanisterId) finish(cfg);
		};

		const poll = setInterval(() => {
			const cfg = getPortalConfig();
			if (cfg?.backendCanisterId) finish(cfg);
		}, 100);

		const timer = setTimeout(() => finish(getPortalConfig()), timeoutMs);
		window.addEventListener('portal:config', onConfig);
	});
}

export function waitForPortalDelegation({ timeoutMs = 300_000 } = {}) {
	const existing = getPortalDelegationIdentity();
	if (existing) return Promise.resolve(existing);

	return new Promise((resolve) => {
		let settled = false;
		const finish = (value: DelegationIdentity | null) => {
			if (settled) return;
			settled = true;
			clearTimeout(timer);
			window.removeEventListener('portal:auth', onAuth);
			window.removeEventListener('portal:auth-error', onAuthError);
			resolve(value);
		};

		const onAuth = () => {
			const identity = getPortalDelegationIdentity();
			if (identity) finish(identity);
		};

		const onAuthError = (event: Event) => {
			const customEvent = event as CustomEvent;
			console.warn('[portal-bridge] host auth error:', customEvent?.detail?.error);
			finish(null);
		};

		const timer = setTimeout(() => finish(null), timeoutMs);
		window.addEventListener('portal:auth', onAuth);
		window.addEventListener('portal:auth-error', onAuthError);
		requestAuthRefresh();
	});
}
