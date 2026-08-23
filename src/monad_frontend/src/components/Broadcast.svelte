<script lang="ts">
	import type { BroadcastMessage, ThreadSummary } from '../lib/types';
	import BroadcastCard from './BroadcastCard.svelte';

	let {
		broadcasts = [],
		publicThreads = [],
		monadError = null,
		needsAuth = false,
		onreply,
		onopenthread,
		onlogin,
	}: {
		broadcasts?: BroadcastMessage[];
		publicThreads?: ThreadSummary[];
		monadError?: string | null;
		needsAuth?: boolean;
		onreply?: (broadcastId: string) => void;
		onopenthread?: (threadId: string) => void;
		onlogin?: () => void | Promise<void>;
	} = $props();
</script>

<section class="broadcast" aria-label="Monad broadcast">
	{#if monadError}
		<p class="monad-error">{monadError}</p>
	{/if}

	<div class="feed">
		{#if broadcasts.length === 0}
			<p class="monad-gos-muted empty">No broadcasts yet.</p>
		{:else}
			{#each broadcasts as message (message.id)}
				<BroadcastCard message={message} onreply={onreply} needsAuth={needsAuth} onlogin={onlogin} />
			{/each}
		{/if}
	</div>

	{#if publicThreads.length > 0}
		<aside class="public-threads">
			<ul>
				{#each publicThreads as thread (thread.id)}
					<li>
						<button type="button" class="thread-link" onclick={() => onopenthread?.(thread.id)}>
							{thread.title}
							<span class="monad-gos-muted meta">
								· {thread.participant_count} participants
							</span>
						</button>
					</li>
				{/each}
			</ul>
		</aside>
	{/if}
</section>

<style>
	.broadcast {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}

	.monad-error {
		color: var(--monad-gos-no);
		margin: 0;
		font-family: var(--monad-gos-font-ui);
		font-size: 0.85rem;
	}

	.feed {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}

	.empty {
		margin: 0;
		text-align: center;
		padding: 2rem 0;
	}

	.public-threads {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid color-mix(in srgb, var(--monad-gos-border) 60%, transparent);
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.thread-link {
		display: inline;
		border: none;
		background: transparent;
		padding: 0;
		font-family: var(--monad-gos-font);
		font-size: 0.875rem;
		color: var(--monad-gos-accent);
		text-align: left;
		text-decoration: underline;
		text-underline-offset: 0.15em;
	}

	.thread-link:hover {
		color: var(--monad-gos-text);
	}

	.meta {
		font-size: 0.8rem;
		text-decoration: none;
	}
</style>
