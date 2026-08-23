<script lang="ts">
	import type { ConnectionStatus } from '../lib/types';
	import brandIcon from '../assets/monad-gos-icon.png';

	let {
		connectionStatus = 'connecting' as ConnectionStatus,
		isLoggedIn = false,
		principalShort = '',
		logoSrc = '',
		onlogin,
		onlogout,
		onsettings,
	}: {
		connectionStatus?: ConnectionStatus;
		isLoggedIn?: boolean;
		principalShort?: string;
		logoSrc?: string;
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

<div class="app-header">
	<div class="brand">
		<img class="brand-logo" src={logoSrc || brandIcon} alt="Monad" />
		<span class="brand-name">Monad</span>
		<span
			class="status"
			class:connected={connectionStatus === 'connected'}
			class:error={connectionStatus === 'error'}
			role="status"
			aria-live="polite"
		>
			{statusLabel}
		</span>
	</div>

	<div class="auth">
		{#if isLoggedIn}
			<span class="principal monad-gos-muted">{principalShort}</span>
			<button type="button" class="monad-gos-btn monad-gos-btn-ghost auth-btn" onclick={() => onsettings?.()}>
				Settings
			</button>
			<button type="button" class="monad-gos-btn monad-gos-btn-ghost auth-btn" onclick={() => onlogout?.()}>
				Sign out
			</button>
		{:else}
			<button type="button" class="monad-gos-btn auth-btn" onclick={() => onlogin?.()}>
				Sign in
			</button>
		{/if}
	</div>
</div>

<style>
	.app-header {
		display: contents;
	}

	.brand {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		grid-area: brand;
		font-family: var(--monad-gos-font-ui);
		font-weight: 600;
		font-size: 0.9rem;
		color: var(--monad-gos-text);
		min-width: 0;
	}

	.brand-logo {
		width: 2.2rem;
		height: 2.2rem;
		object-fit: contain;
		flex-shrink: 0;
	}

	.brand-name {
		flex-shrink: 0;
		font-family: Palatino, 'Palatino Linotype', 'Iowan Old Style', Georgia, serif;
		font-style: italic;
		font-weight: 500;
		letter-spacing: 0.02em;
		color: #50663e;
	}

	.status {
		font-weight: 400;
		font-size: 0.65rem;
		color: var(--monad-gos-text-muted);
		font-variant-numeric: tabular-nums;
	}

	.status.connected {
		color: var(--monad-gos-yes);
	}

	.status.error {
		color: var(--monad-gos-no);
	}

	.auth {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		grid-area: auth;
		justify-self: end;
		min-width: 0;
	}

	.auth-btn {
		padding: 0.3rem 0.55rem;
		font-size: 0.75rem;
	}

	.principal {
		font-size: 0.65rem;
		font-variant-numeric: tabular-nums;
		max-width: 5rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
