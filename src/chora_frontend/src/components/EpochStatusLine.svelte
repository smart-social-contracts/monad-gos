<script lang="ts">
	import type { EpochPhase } from '../lib/types';

	let {
		epochId = '',
		phase = 'converse' as EpochPhase,
		countdownSeconds = 0,
	}: {
		epochId?: string;
		phase?: EpochPhase;
		countdownSeconds?: number;
	} = $props();

	const phaseLabels: Record<EpochPhase, string> = {
		converse: 'Converse',
		sealed: 'Sealed',
		deliberate: 'Deliberate',
		ratify: 'Ratify',
		execute: 'Execute',
	};

	function formatCountdown(seconds: number): string {
		if (seconds <= 0) return 'seal imminent';
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		if (h > 0) return `${h}h ${m}m to seal`;
		return `${m}m to seal`;
	}
</script>

<div class="epoch-line" role="status" aria-live="polite">
	<span class="epoch-label">Epoch</span>
	<span class="epoch-id">{epochId}</span>
	<span class="divider">·</span>
	<span class="phase">{phaseLabels[phase]}</span>
	{#if phase === 'converse'}
		<span class="divider">·</span>
		<span class="countdown">{formatCountdown(countdownSeconds)}</span>
	{/if}
</div>

<style>
	.epoch-line {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.35rem 1.25rem;
		font-family: var(--chora-font-ui);
		font-size: 0.75rem;
		color: var(--chora-text-muted);
		background: var(--chora-surface);
		border-bottom: 1px solid var(--chora-border);
	}

	.epoch-label {
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}

	.epoch-id {
		font-variant-numeric: tabular-nums;
	}

	.divider {
		opacity: 0.5;
	}

	.phase {
		color: var(--chora-text);
	}

	.countdown {
		font-variant-numeric: tabular-nums;
	}
</style>
