<script lang="ts">
	import type { McpTokenCreated, McpTokenMeta, McpTokenScope } from '../lib/types';
	import LoginPrompt from './LoginPrompt.svelte';
	import {
		claudeDesktopConfig,
		createMcpToken,
		getMcpEndpointUrl,
		listMcpTokens,
		revokeMcpToken,
	} from '../lib/mcp_settings.js';

	let {
		needsAuth = false,
		onlogin,
	}: {
		needsAuth?: boolean;
		onlogin?: () => void | Promise<void>;
	} = $props();

	const mcpUrl = getMcpEndpointUrl();

	let tokens = $state<McpTokenMeta[]>([]);
	let loading = $state(true);
	let listError = $state<string | null>(null);

	let label = $state('');
	let scope = $state<McpTokenScope>('read');
	let ttlDays = $state('');
	let minting = $state(false);
	let mintError = $state<string | null>(null);

	let freshToken = $state<McpTokenCreated | null>(null);
	let revokingId = $state<number | null>(null);
	let copyNotice = $state<string | null>(null);

	const claudeSnippet = $derived(
		freshToken ? claudeDesktopConfig(freshToken.token) : '',
	);

	function formatDate(iso: string) {
		const d = new Date(iso);
		return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
	}

	async function copyText(text: string, what: string) {
		try {
			await navigator.clipboard.writeText(text);
			copyNotice = `${what} copied`;
		} catch {
			copyNotice = 'Copy failed';
		}
	}

	async function loadTokens() {
		loading = true;
		listError = null;
		try {
			tokens = await listMcpTokens();
		} catch (e) {
			listError = e instanceof Error ? e.message : 'Could not load tokens';
		} finally {
			loading = false;
		}
	}

	async function handleMint() {
		mintError = null;
		minting = true;
		try {
			const ttl =
				ttlDays.trim() === '' ? undefined : Number.parseInt(ttlDays.trim(), 10);
			if (ttl != null && (Number.isNaN(ttl) || ttl <= 0)) {
				throw new Error('TTL must be a positive number of days');
			}
			freshToken = await createMcpToken({
				label: label.trim(),
				scope,
				ttlDays: ttl,
			});
			label = '';
			ttlDays = '';
			await loadTokens();
		} catch (e) {
			mintError = e instanceof Error ? e.message : 'Could not create token';
		} finally {
			minting = false;
		}
	}

	async function handleRevoke(id: number) {
		revokingId = id;
		listError = null;
		try {
			await revokeMcpToken(id);
			if (freshToken?.id === id) {
				freshToken = null;
			}
			await loadTokens();
		} catch (e) {
			listError = e instanceof Error ? e.message : 'Could not revoke token';
		} finally {
			revokingId = null;
		}
	}

	$effect(() => {
		if (!needsAuth) {
			loadTokens();
		}
	});
</script>

<section class="settings chora-prose" aria-label="MCP settings">
	<header class="section-header">
		<h1>Settings</h1>
		<p class="chora-muted intro">
			Connect Claude, ChatGPT, or another MCP client to <strong>Chora MCP</strong> — not
			Geister. Pairing tokens let your assistant act on your behalf within the scope you choose.
		</p>
	</header>

	{#if needsAuth}
		<LoginPrompt message="Sign in to manage MCP pairing tokens." onlogin={onlogin} />
	{:else}
		<div class="panel">
			<h2 class="panel-title">MCP endpoint</h2>
			<p class="chora-muted panel-hint">Use this URL in your MCP client configuration.</p>
			<div class="copy-row">
				<code class="endpoint">{mcpUrl}</code>
				<button
					type="button"
					class="chora-btn"
					onclick={() => copyText(mcpUrl, 'MCP URL')}
				>
					Copy
				</button>
			</div>
		</div>

		<div class="panel">
			<h2 class="panel-title">Create pairing token</h2>
			<form
				class="mint-form"
				onsubmit={(e) => {
					e.preventDefault();
					handleMint();
				}}
			>
				<label class="field">
					<span class="field-label">Label</span>
					<input
						class="chora-input"
						type="text"
						placeholder="e.g. Claude Desktop"
						bind:value={label}
					/>
				</label>

				<label class="field">
					<span class="field-label">Scope</span>
					<select class="chora-input" bind:value={scope}>
						<option value="read">read — query Chora</option>
						<option value="full">full — read and write</option>
					</select>
				</label>

				<label class="field">
					<span class="field-label">TTL (days, optional)</span>
					<input
						class="chora-input"
						type="number"
						min="1"
						placeholder="No expiry"
						bind:value={ttlDays}
					/>
				</label>

				<button type="submit" class="chora-btn chora-btn-primary" disabled={minting}>
					{minting ? 'Creating…' : 'Create token'}
				</button>
			</form>

			{#if mintError}
				<p class="error">{mintError}</p>
			{/if}
		</div>

		{#if freshToken}
			<div class="panel fresh">
				<h2 class="panel-title">New token — copy now</h2>
				<p class="chora-muted panel-hint">
					This secret is shown once. Store it somewhere safe; you cannot view it again.
				</p>
				<div class="copy-row">
					<code class="token">{freshToken.token}</code>
					<button
						type="button"
						class="chora-btn"
						onclick={() => copyText(freshToken?.token ?? '', 'Token')}
					>
						Copy token
					</button>
				</div>

				<h3 class="sub-title">Claude Desktop</h3>
				<pre class="snippet">{claudeSnippet}</pre>
				<button
					type="button"
					class="chora-btn"
					onclick={() => copyText(claudeSnippet, 'Claude config')}
				>
					Copy JSON
				</button>
			</div>
		{/if}

		<div class="panel">
			<h2 class="panel-title">Your tokens</h2>
			{#if loading}
				<p class="chora-muted">Loading tokens…</p>
			{:else if listError}
				<p class="error">{listError}</p>
			{:else if tokens.length === 0}
				<p class="chora-muted">No pairing tokens yet.</p>
			{:else}
				<ul class="token-list">
					{#each tokens as row (row.id)}
						<li class="token-row">
							<div class="token-meta">
								<span class="token-label">{row.label || 'Untitled'}</span>
								<span class="token-scope chora-muted">{row.scope}</span>
								<span class="token-created chora-muted">{formatDate(row.created_at)}</span>
							</div>
							<button
								type="button"
								class="chora-btn chora-btn-no"
								disabled={revokingId === row.id}
								onclick={() => handleRevoke(row.id)}
							>
								{revokingId === row.id ? 'Revoking…' : 'Revoke'}
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</div>

		{#if copyNotice}
			<p class="copy-notice chora-muted" role="status">{copyNotice}</p>
		{/if}
	{/if}
</section>

<style>
	.section-header h1 {
		margin: 0 0 0.35rem;
		font-family: var(--chora-font-ui);
		font-size: 1.35rem;
		font-weight: 600;
	}

	.intro {
		margin: 0 0 1.5rem;
		max-width: var(--chora-prose);
	}

	.panel {
		margin-bottom: 1.75rem;
		padding-bottom: 1.75rem;
		border-bottom: 1px solid var(--chora-border);
	}

	.panel:last-child {
		border-bottom: none;
	}

	.panel-title {
		margin: 0 0 0.25rem;
		font-family: var(--chora-font-ui);
		font-size: 1rem;
		font-weight: 600;
	}

	.panel-hint {
		margin: 0 0 0.75rem;
	}

	.copy-row {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
	}

	.endpoint,
	.token {
		flex: 1 1 12rem;
		padding: 0.5rem 0.65rem;
		border: 1px solid var(--chora-border);
		border-radius: var(--chora-radius);
		background: var(--chora-surface);
		font-family: ui-monospace, monospace;
		font-size: 0.8rem;
		word-break: break-all;
	}

	.mint-form {
		display: grid;
		gap: 0.85rem;
		max-width: 24rem;
	}

	.field {
		display: grid;
		gap: 0.25rem;
	}

	.field-label {
		font-family: var(--chora-font-ui);
		font-size: 0.8rem;
		color: var(--chora-text-muted);
	}

	.fresh {
		background: var(--chora-accent-soft);
		padding: 1rem;
		border-radius: var(--chora-radius);
		border: 1px solid var(--chora-border);
	}

	.sub-title {
		margin: 1rem 0 0.35rem;
		font-family: var(--chora-font-ui);
		font-size: 0.9rem;
		font-weight: 600;
	}

	.snippet {
		margin: 0 0 0.75rem;
		padding: 0.75rem;
		border: 1px solid var(--chora-border);
		border-radius: var(--chora-radius);
		background: var(--chora-surface);
		font-family: ui-monospace, monospace;
		font-size: 0.75rem;
		overflow-x: auto;
		white-space: pre-wrap;
		word-break: break-all;
	}

	.token-list {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.token-row {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0.65rem 0;
		border-bottom: 1px solid var(--chora-border);
	}

	.token-row:last-child {
		border-bottom: none;
	}

	.token-meta {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0.5rem 1rem;
		min-width: 0;
	}

	.token-label {
		font-family: var(--chora-font-ui);
		font-weight: 500;
	}

	.error {
		color: var(--chora-no);
		margin: 0.5rem 0 0;
		font-family: var(--chora-font-ui);
		font-size: 0.85rem;
	}

	.copy-notice {
		margin: 0;
		font-family: var(--chora-font-ui);
		font-size: 0.8rem;
	}
</style>
