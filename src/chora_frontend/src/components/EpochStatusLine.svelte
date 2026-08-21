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

<div class="epoch-chip" role="status" aria-live="polite">
	<span>Epoch {epochId}</span>
	<span class="divider">·</span>
	<span>{phaseLabels[phase]}</span>
	{#if phase === 'converse'}
		<span class="divider">·</span>
		<span class="countdown">{formatCountdown(countdownSeconds)}</span>
	{/if}
</div>

<style>
	.epoch-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.25rem 0.6rem;
		border: 1px solid var(--chora-border);
		border-radius: 999px;
		font-family: var(--chora-font-ui);
		font-size: 0.65rem;
		color: var(--chora-text-muted);
		background: color-mix(in srgb, var(--chora-surface) 70%, transparent);
		white-space: nowrap;
	}

	.divider {
		opacity: 0.45;
	}

	.countdown {
		font-variant-numeric: tabular-nums;
	}
</style>
