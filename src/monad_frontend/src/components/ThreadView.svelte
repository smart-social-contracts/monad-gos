<script lang="ts">
	import type { ThreadMessage, ThreadSummary } from '../lib/types';
	import ThreadMessageView from './ThreadMessage.svelte';

	let {
		thread,
		messages = [],
		onback,
		monadAuthor = '',
		awaitingMonad = false,
		error = null,
		onopeninputs,
	}: {
		thread: ThreadSummary | null;
		messages?: ThreadMessage[];
		onback?: () => void;
		monadAuthor?: string;
		awaitingMonad?: boolean;
		error?: string | null;
		onopeninputs?: (messageId: string) => void;
	} = $props();
</script>

<section class="thread-view" aria-label="Conversation thread">
	{#if thread}
		<header class="thread-header">
			<button type="button" class="back-link" onclick={() => onback?.()}>← Back</button>
			<p class="thread-title">{thread.title}</p>
			<p class="monad-gos-muted meta">
				{thread.visibility === 'private' ? 'Private' : 'Public'} · {thread.participant_count} participants
			</p>
		</header>

		<div class="messages">
			{#each messages as message (message.id)}
				<ThreadMessageView
					message={message}
					monadAuthor={monadAuthor}
					onopeninputs={onopeninputs}
				/>
			{/each}
		</div>
		{#if awaitingMonad}
			<p class="monad-gos-muted considering" role="status" aria-live="polite">
				The Monad is considering…
			</p>
		{/if}
		{#if error}
			<p class="reply-error" role="alert">{error}</p>
		{/if}
	{:else}
		<button type="button" class="back-link" onclick={() => onback?.()}>← Back</button>
		<p class="monad-gos-muted">Thread not found.</p>
	{/if}
</section>

<style>
	.thread-view {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}

	.thread-header {
		margin-bottom: 0.25rem;
	}

	.back-link {
		border: none;
		background: transparent;
		padding: 0;
		margin-bottom: 0.35rem;
		font-family: var(--monad-gos-font-ui);
		font-size: 0.75rem;
		color: var(--monad-gos-text-muted);
		text-decoration: underline;
		text-underline-offset: 0.15em;
	}

	.back-link:hover {
		color: var(--monad-gos-text);
	}

	.thread-title {
		margin: 0;
		font-size: 1rem;
		font-weight: 500;
	}

	.meta {
		margin: 0.2rem 0 0;
		font-size: 0.75rem;
	}

	.messages {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}

	.considering {
		margin: 0;
		font-family: var(--monad-gos-font-ui);
		font-style: italic;
		font-size: 0.85rem;
	}

	.reply-error {
		margin: 0;
		font-family: var(--monad-gos-font-ui);
		font-size: 0.85rem;
		color: var(--monad-gos-no);
	}
</style>
