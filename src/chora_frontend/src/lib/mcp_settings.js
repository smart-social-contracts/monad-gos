/**
 * Chora MCP pairing-token API (Settings page).
 *
 * Pairing codes come from the canister via createMcpPairing(); they are never
 * treated as trusted user identity on the MCP server.
 */
import { createMcpPairing, isMockMode } from '../chora_api.js';

const DEFAULT_MCP_BASE = 'http://127.0.0.1:5002';

/** @returns {string} MCP server base URL (no trailing slash). */
export function getMcpBaseUrl() {
	const raw = import.meta.env.VITE_CHORA_MCP_URL || DEFAULT_MCP_BASE;
	return String(raw).replace(/\/$/, '');
}

/** @returns {string} Streamable HTTP MCP endpoint shown to users. */
export function getMcpEndpointUrl() {
	return `${getMcpBaseUrl()}/mcp`;
}

/** @type {string | null} */
let pairingCode = null;

/** @type {Array<import('./types.ts').McpTokenMeta & { token?: string }>} */
const mockTokens = [];
let mockNextId = 1;

function delay(ms = 80) {
	return new Promise((r) => setTimeout(r, ms));
}

async function refreshPairingCode() {
	pairingCode = await createMcpPairing();
	return pairingCode;
}

async function getPairingCode() {
	if (!pairingCode) {
		await refreshPairingCode();
	}
	return pairingCode;
}

async function readError(res) {
	try {
		const data = await res.json();
		if (typeof data?.error === 'string') return data.error;
		if (typeof data?.message === 'string') return data.message;
		return JSON.stringify(data);
	} catch {
		return res.statusText || `HTTP ${res.status}`;
	}
}

/**
 * @param {string} path
 * @param {{ method?: string, body?: Record<string, unknown> }} [opts]
 */
async function mcpFetch(path, { method = 'GET', body } = {}) {
	async function attempt(code) {
		const url = new URL(path, `${getMcpBaseUrl()}/`);
		const init = {
			method,
			headers: { 'Content-Type': 'application/json' },
		};
		if (method === 'GET') {
			url.searchParams.set('pairing_code', code);
		} else {
			init.body = JSON.stringify({ ...body, pairing_code: code });
		}
		return fetch(url.toString(), init);
	}

	let code = await getPairingCode();
	let res = await attempt(code);
	if (res.status === 401) {
		code = await refreshPairingCode();
		res = await attempt(code);
	}
	return res;
}

function stripSecret(row) {
	const { token: _token, token_hash: _hash, ...meta } = row;
	return meta;
}

async function mockListTokens() {
	await delay();
	return mockTokens.map(stripSecret);
}

/**
 * @param {{ label?: string, scope: 'read' | 'full', ttlDays?: number }} input
 */
async function mockCreateToken({ label = '', scope, ttlDays }) {
	await delay();
	const createdAt = new Date().toISOString();
	const id = mockNextId++;
	const token = `chmcp_mock_${id}_${Date.now().toString(36)}`;
	const row = {
		id,
		label,
		scope,
		created_at: createdAt,
		expires_at: ttlDays
			? new Date(Date.now() + ttlDays * 86_400_000).toISOString()
			: null,
		token,
	};
	mockTokens.unshift(row);
	return { ...stripSecret(row), token };
}

async function mockRevokeToken(id) {
	await delay();
	const idx = mockTokens.findIndex((t) => t.id === id);
	if (idx < 0) return false;
	mockTokens.splice(idx, 1);
	return true;
}

/** @returns {Promise<import('./types.ts').McpTokenMeta[]>} */
export async function listMcpTokens() {
	if (isMockMode()) {
		return mockListTokens();
	}
	const res = await mcpFetch('/api/tokens');
	if (!res.ok) {
		throw new Error(await readError(res));
	}
	const data = await res.json();
	const rows = Array.isArray(data?.tokens) ? data.tokens : data;
	return rows.map(stripSecret);
}

/**
 * @param {{ label?: string, scope: 'read' | 'full', ttlDays?: number }} input
 * @returns {Promise<import('./types.ts').McpTokenCreated>}
 */
export async function createMcpToken({ label = '', scope, ttlDays }) {
	if (isMockMode()) {
		return mockCreateToken({ label, scope, ttlDays });
	}
	const body = { label, scope };
	if (ttlDays != null && ttlDays > 0) {
		body.ttl_days = ttlDays;
	}
	const res = await mcpFetch('/api/tokens', { method: 'POST', body });
	if (!res.ok) {
		throw new Error(await readError(res));
	}
	const data = await res.json();
	const meta =
		data?.metadata && typeof data.metadata === 'object' ? data.metadata : data;
	return { ...stripSecret(meta), token: data.token };
}

/** @param {number} id */
export async function revokeMcpToken(id) {
	if (isMockMode()) {
		const ok = await mockRevokeToken(id);
		if (!ok) throw new Error('Token not found');
		return;
	}
	const res = await mcpFetch(`/api/tokens/${id}`, { method: 'DELETE', body: {} });
	if (!res.ok) {
		throw new Error(await readError(res));
	}
}

/** Claude Desktop config snippet for a freshly minted token. */
export function claudeDesktopConfig(token) {
	return JSON.stringify(
		{
			mcpServers: {
				chora: {
					command: 'npx',
					args: [
						'-y',
						'mcp-remote',
						getMcpEndpointUrl(),
						'--header',
						`Authorization: Bearer ${token}`,
					],
				},
			},
		},
		null,
		2,
	);
}
