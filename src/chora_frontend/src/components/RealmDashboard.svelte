<script lang="ts">
	import type { RealmState } from '../lib/types';

	let { data = null }: { data?: RealmState | null } = $props();

	const percent = $derived(data ? Math.round(data.alignment.coefficient * 1000) / 10 : null);

	function shareLabel(bps: number): string {
		return `${bps / 100}%`;
	}
</script>

<section class="realm" aria-label="Realm dashboard">
	<header class="section-header">
		<h1>Realm</h1>
		<p class="chora-muted intro">
			The live accounts of Chora, under the Monad’s Codex.
		</p>
	</header>

	{#if !data}
		<p class="chora-muted">Loading realm state…</p>
	{:else}
		<p class="preamble">{data.codex.preamble}</p>

		<dl class="facts">
			<div>
				<dt>Alignment</dt>
				<dd>{percent}%</dd>
			</div>
			<div>
				<dt>Membership due</dt>
				<dd>{data.membership_due} credits</dd>
			</div>
			<div>
				<dt>Treasury</dt>
				<dd>{data.treasury.balance} credits</dd>
			</div>
			<div>
				<dt>Epoch</dt>
				<dd>{data.epoch_id}</dd>
			</div>
			<div>
				<dt>Codex</dt>
				<dd>v{data.codex.version}</dd>
			</div>
		</dl>

		<h2>Budget</h2>
		<table>
			<thead>
				<tr>
					<th>Line</th>
					<th>Share</th>
					<th>Allocated</th>
					<th>Spent</th>
					<th>Available</th>
				</tr>
			</thead>
			<tbody>
				{#each data.lines as line (line.name)}
					<tr>
						<td>{line.name}</td>
						<td>{shareLabel(line.share_bps)}</td>
						<td>{line.allocated}</td>
						<td>{line.spent}</td>
						<td>{line.available}</td>
					</tr>
				{/each}
			</tbody>
		</table>

		<p class="source">
			<a href={data.codex.source_url} target="_blank" rel="noreferrer">
				Read the Codex on GitHub
			</a>
			{#if data.codex.commit}
				<span class="chora-muted"> · {data.codex.commit.slice(0, 7)}</span>
			{/if}
		</p>
	{/if}
</section>

<style>
	.section-header {
		margin-bottom: 1.25rem;
	}

	h1 {
		margin: 0 0 0.35rem;
		font-size: 1.5rem;
		font-weight: 500;
	}

	.intro {
		margin: 0;
		max-width: var(--chora-prose);
	}

	.preamble {
		margin: 0 0 1.75rem;
		max-width: var(--chora-prose);
		font-size: 1.05rem;
	}

	.facts {
		display: grid;
		grid-template-columns: 10rem 1fr;
		gap: 0.4rem 1rem;
		margin: 0 0 2rem;
		max-width: 28rem;
		font-family: var(--chora-font-ui);
		font-size: 0.95rem;
	}

	.facts div {
		display: contents;
	}

	dt {
		margin: 0;
		color: var(--chora-text-muted);
	}

	dd {
		margin: 0;
		font-variant-numeric: tabular-nums;
	}

	h2 {
		margin: 0 0 0.6rem;
		font-size: 1rem;
		font-family: var(--chora-font-ui);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--chora-text-muted);
	}

	table {
		width: 100%;
		max-width: 36rem;
		border-collapse: collapse;
		font-family: var(--chora-font-ui);
		font-size: 0.9rem;
		font-variant-numeric: tabular-nums;
	}

	th,
	td {
		text-align: left;
		padding: 0.45rem 0.6rem 0.45rem 0;
		border-bottom: 1px solid var(--chora-border);
	}

	th {
		color: var(--chora-text-muted);
		font-weight: 600;
	}

	.source {
		margin: 1.75rem 0 0;
		font-family: var(--chora-font-ui);
		font-size: 0.85rem;
	}

	a {
		color: inherit;
	}
</style>
