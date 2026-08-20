<script lang="ts">
	import type { AlignmentData } from '../lib/types';

	let { data }: { data: AlignmentData | null } = $props();

	const percent = $derived(
		data ? Math.round(data.coefficient * 1000) / 10 : null,
	);

	const trendDelta = $derived(
		!data || data.trend.length < 2
			? null
			: Math.round(
					(data.trend[data.trend.length - 1].coefficient - data.trend[0].coefficient) *
						1000,
				) / 10,
	);

	function sparklinePoints(trend: AlignmentData['trend']): string {
		if (!trend.length) return '';
		const w = 80;
		const h = 24;
		const min = Math.min(...trend.map((p) => p.coefficient));
		const max = Math.max(...trend.map((p) => p.coefficient));
		const span = max - min || 0.01;
		return trend
			.map((p, i) => {
				const x = (i / (trend.length - 1 || 1)) * w;
				const y = h - ((p.coefficient - min) / span) * h;
				return `${x},${y}`;
			})
			.join(' ');
	}
</script>

<aside class="alignment" aria-label="Alignment coefficient">
	<div class="label">Alignment</div>
	{#if data && percent !== null}
		<div class="value-row">
			<span class="value">{percent}%</span>
			{#if trendDelta !== null}
				<span class="trend" class:up={trendDelta >= 0} class:down={trendDelta < 0}>
					{trendDelta >= 0 ? '+' : ''}{trendDelta}%
				</span>
			{/if}
		</div>
		<p class="hint chora-muted">
			Citizens current on membership due ({data.membership_due} credits)
		</p>
		{#if data.trend.length > 1}
			<svg
				class="spark"
				viewBox="0 0 80 24"
				role="img"
				aria-label="Recent alignment trend"
			>
				<polyline
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					points={sparklinePoints(data.trend)}
				/>
			</svg>
		{/if}
	{:else}
		<p class="chora-muted">Loading…</p>
	{/if}
</aside>

<style>
	.alignment {
		padding: 1rem 1.25rem;
		background: var(--chora-surface);
		border: 1px solid var(--chora-border);
		border-radius: var(--chora-radius);
		font-family: var(--chora-font-ui);
	}

	.label {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--chora-text-muted);
		margin-bottom: 0.35rem;
	}

	.value-row {
		display: flex;
		align-items: baseline;
		gap: 0.5rem;
	}

	.value {
		font-size: 1.75rem;
		font-weight: 600;
		font-variant-numeric: tabular-nums;
		line-height: 1.2;
	}

	.trend {
		font-size: 0.875rem;
		font-variant-numeric: tabular-nums;
	}

	.trend.up {
		color: var(--chora-yes);
	}

	.trend.down {
		color: var(--chora-no);
	}

	.hint {
		margin: 0.35rem 0 0.5rem;
	}

	.spark {
		width: 80px;
		height: 24px;
		color: var(--chora-accent);
		opacity: 0.8;
	}
</style>
