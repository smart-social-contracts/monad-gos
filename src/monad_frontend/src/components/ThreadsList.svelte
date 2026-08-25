<script lang="ts">
	import type { ThreadSummary } from '../lib/types';
	import { createThreadOpenHandler } from '../lib/conversation.js';

	let {
		threads = [],
		onopenthread,
	}: {
		threads?: ThreadSummary[];
		onopenthread?: (threadId: string) => void;
	} = $props();

	const openFromEvent = createThreadOpenHandler((threadId) => onopenthread?.(threadId));
</script>

<section class="threads-list" aria-label="Threads">
	<header class="section-header">
		<h1>Threads</h1>
		<p class="monad-gos-muted intro">
			Public and private conversations with the Monad and fellow citizens.
		</p>
	</header>

	{#if threads.length === 0}
		<p class="monad-gos-muted">No threads yet.</p>
	{:else}
		<ul>
			{#each threads as thread (thread.id)}
				<li>
					<button
						type="button"
						class="thread-link"
						data-thread-id={thread.id}
						onclick={openFromEvent}
					>
						<span class="title">{thread.title}</span>
						<span class="monad-gos-muted meta">
							{thread.participant_count} participants · {thread.visibility}
						</span>
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</section>

<style>
	.section-header {
		margin-bottom: 2rem;
	}

	h1 {
		margin: 0 0 0.35rem;
		font-size: 1.5rem;
		font-weight: 500;
	}

	.intro {
		margin: 0;
		max-width: var(--monad-gos-prose);
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
		max-width: var(--monad-gos-prose);
	}

	.thread-link {
		display: block;
		width: 100%;
		text-align: left;
		padding: 0.75rem 0;
		border: none;
		border-bottom: 1px solid var(--monad-gos-border);
		background: transparent;
		font-family: var(--monad-gos-font);
		font-size: 1rem;
		color: inherit;
		touch-action: manipulation;
	}

	@media (hover: hover) and (pointer: fine) {
		.thread-link:hover {
			background: var(--monad-gos-accent-soft);
		}
	}

	.title {
		display: block;
		font-weight: 500;
	}

	.meta {
		font-size: 0.8rem;
	}
</style>
