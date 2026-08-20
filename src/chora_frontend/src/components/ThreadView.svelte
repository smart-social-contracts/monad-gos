<script lang="ts">
	import type { ThreadMessage, ThreadSummary } from '../lib/types';
	import ThreadMessageView from './ThreadMessage.svelte';
	import MessageComposer from './MessageComposer.svelte';
	import LoginPrompt from './LoginPrompt.svelte';

	let {
		thread,
		messages = [],
		needsAuth = false,
		onback,
		onreply,
		onlogin,
		monadAuthor = '',
		awaitingMonad = false,
	}: {
		thread: ThreadSummary | null;
		messages?: ThreadMessage[];
		needsAuth?: boolean;
		onback?: () => void;
		onreply?: (body: string) => void | Promise<void>;
		onlogin?: () => void | Promise<void>;
		monadAuthor?: string;
		awaitingMonad?: boolean;
	} = $props();

	let replyPrompt = $state(false);

	async function handleReply(body: string) {
		if (needsAuth) {
			replyPrompt = true;
			return;
		}
		replyPrompt = false;
		await onreply?.(body);
	}
</script>

<section class="thread-view" aria-label="Conversation thread">
	{#if thread}
		<header class="thread-header">
			<button type="button" class="chora-btn chora-btn-ghost back" onclick={() => onback?.()}>
				← Back
			</button>
			<div>
				<h1>{thread.title}</h1>
				<p class="chora-muted meta">
					{thread.visibility === 'private' ? 'Private — you and the Monad' : 'Public — citizens and the Monad'}
					· {thread.participant_count} participants
				</p>
			</div>
		</header>

		<div class="messages chora-prose">
			{#each messages as message (message.id)}
				<ThreadMessageView message={message} monadAuthor={monadAuthor} />
			{/each}
		</div>
		{#if awaitingMonad}
			<p class="chora-muted considering" role="status" aria-live="polite">
				The Monad is considering…
			</p>
		{/if}

		<MessageComposer
			placeholder="Continue the conversation…"
			fieldId="chora-thread-composer"
			onsubmit={handleReply}
		/>
		{#if replyPrompt}
			<LoginPrompt message="Sign in to reply." onlogin={onlogin} />
		{/if}
	{:else}
		<button type="button" class="chora-btn chora-btn-ghost back" onclick={() => onback?.()}>
			← Back
		</button>
		<p class="chora-muted">Thread not found.</p>
	{/if}
</section>

<style>
	.thread-header {
		margin-bottom: 1.5rem;
	}

	.back {
		margin-bottom: 0.75rem;
	}

	h1 {
		margin: 0;
		font-size: 1.35rem;
		font-weight: 500;
	}

	.meta {
		margin: 0.25rem 0 0;
		font-size: 0.875rem;
	}

	.messages {
		margin-top: 1rem;
	}

	.considering {
		margin: 0.75rem 0 0;
		font-family: var(--chora-font-ui);
		font-style: italic;
	}
</style>
