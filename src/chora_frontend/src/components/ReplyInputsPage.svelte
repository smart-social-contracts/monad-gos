<script lang="ts">
	import type { ReplyInputs } from '../lib/types';

	let {
		inputs = null,
		missing = false,
		onback,
	}: {
		inputs?: ReplyInputs | null;
		missing?: boolean;
		onback?: () => void;
	} = $props();

	function formatTime(ts: number): string {
		if (!ts) return '—';
		return new Date(ts * 1000).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
		});
	}
</script>

<section class="inputs-page" aria-label="Inputs for reproducibility">
	<button type="button" class="chora-btn chora-btn-ghost back" onclick={() => onback?.()}>
		← Back
	</button>
	<header class="section-header">
		<h1>Inputs for reproducibility</h1>
		<p class="chora-muted intro">
			These are the exact inputs the Monad used for this reply. Because of how language models
			and hardware work, a rerun is unlikely to match word for word. It should be
			semantically similar.
		</p>
	</header>

	{#if missing}
		<p class="chora-muted">No inputs were recorded for this reply.</p>
	{:else if inputs}
		<dl class="meta">
			<div>
				<dt>Message</dt>
				<dd>{inputs.message_id}</dd>
			</div>
			<div>
				<dt>Thread</dt>
				<dd>{inputs.thread_id || '—'}</dd>
			</div>
			<div>
				<dt>Recorded</dt>
				<dd>{formatTime(inputs.created_at)}</dd>
			</div>
			<div>
				<dt>Engine</dt>
				<dd>{inputs.engine} · {inputs.model}</dd>
			</div>
			<div>
				<dt>Host</dt>
				<dd>{inputs.engine_host || '—'}</dd>
			</div>
			<div>
				<dt>Temperature</dt>
				<dd>{inputs.temperature || 'unset'}</dd>
			</div>
			<div>
				<dt>Max tokens</dt>
				<dd>{inputs.num_predict}</dd>
			</div>
			<div>
				<dt>Seed</dt>
				<dd>{inputs.seed || 'unset'}</dd>
			</div>
		</dl>

		<h2>Prompt</h2>
		<pre class="prompt">{inputs.prompt}</pre>
	{/if}
</section>

<style>
	.section-header {
		margin-bottom: 1.75rem;
	}

	.back {
		margin-bottom: 0.75rem;
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

	h2 {
		margin: 2rem 0 0.5rem;
		font-size: 1rem;
		font-family: var(--chora-font-ui);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--chora-text-muted);
	}

	.meta {
		display: grid;
		grid-template-columns: 8rem 1fr;
		gap: 0.45rem 1rem;
		margin: 0;
		max-width: 40rem;
		font-family: var(--chora-font-ui);
		font-size: 0.9rem;
	}

	.meta div {
		display: contents;
	}

	dt {
		margin: 0;
		color: var(--chora-text-muted);
	}

	dd {
		margin: 0;
	}

	.prompt {
		margin: 0;
		padding: 1rem 0;
		white-space: pre-wrap;
		word-break: break-word;
		font-family: var(--chora-font);
		font-size: 0.95rem;
		line-height: 1.5;
		max-width: var(--chora-prose);
	}
</style>
