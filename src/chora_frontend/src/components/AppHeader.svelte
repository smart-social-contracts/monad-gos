<script lang="ts">
	import type { ConnectionStatus } from '../lib/types';

	let {
		connectionStatus = 'connecting' as ConnectionStatus,
		isLoggedIn = false,
		principalShort = '',
		onlogin,
		onlogout,
		onsettings,
	}: {
		connectionStatus?: ConnectionStatus;
		isLoggedIn?: boolean;
		principalShort?: string;
		onlogin?: () => void | Promise<void>;
		onlogout?: () => void | Promise<void>;
		onsettings?: () => void;
	} = $props();

	const statusLabel = $derived(
		connectionStatus === 'connected'
			? 'connected'
			: connectionStatus === 'error'
				? 'unreachable'
				: 'connecting…',
	);
</script>

<header class="app-header">
	<div class="brand">Chora</div>

	<div
		class="status"
		class:connected={connectionStatus === 'connected'}
		class:error={connectionStatus === 'error'}
		role="status"
		aria-live="polite"
	>
		{statusLabel}
	</div>

	<div class="auth">
		{#if isLoggedIn}
			<span class="principal chora-muted">{principalShort}</span>
			<button type="button" class="chora-btn chora-btn-ghost" onclick={() => onsettings?.()}>
				Settings
			</button>
			<button type="button" class="chora-btn chora-btn-ghost" onclick={() => onlogout?.()}>
				Sign out
			</button>
		{:else}
			<button type="button" class="chora-btn" onclick={() => onlogin?.()}>
				Sign in
			</button>
		{/if}
	</div>
</header>

<style>
	.app-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.65rem 1.25rem;
		border-bottom: 1px solid var(--chora-border);
		background: var(--chora-surface);
		font-family: var(--chora-font-ui);
		font-size: 0.8rem;
	}

	.brand {
		font-weight: 600;
		font-size: 0.95rem;
		color: var(--chora-text);
	}

	.status {
		color: var(--chora-text-muted);
		font-variant-numeric: tabular-nums;
	}

	.status.connected {
		color: var(--chora-yes);
	}

	.status.error {
		color: var(--chora-no);
	}

	.auth {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-left: auto;
	}

	.principal {
		font-size: 0.75rem;
		font-variant-numeric: tabular-nums;
	}
</style>
