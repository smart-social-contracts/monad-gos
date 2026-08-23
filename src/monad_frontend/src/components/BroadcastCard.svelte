<script lang="ts">
	import type { BroadcastMessage } from '../lib/types';
	import LoginPrompt from './LoginPrompt.svelte';

	let {
		message,
		onreply,
		needsAuth = false,
		onlogin,
	}: {
		message: BroadcastMessage;
		onreply?: (broadcastId: string) => void;
		needsAuth?: boolean;
		onlogin?: () => void | Promise<void>;
	} = $props();

	let replyPrompt = $state(false);

	function formatTime(ts: number): string {
		return new Date(ts * 1000).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
		});
	}

	function handleReply() {
		if (needsAuth) {
			replyPrompt = true;
			return;
		}
		replyPrompt = false;
		onreply?.(message.id);
	}
</script>

<article class="bubble">
	<header>
		<span class="kind">Monad</span>
		<time class="monad-gos-muted" datetime={new Date(message.created_at * 1000).toISOString()}>
			{formatTime(message.created_at)}
		</time>
	</header>
	<p class="body">{message.body}</p>
	<footer>
		<button type="button" class="reply-link" onclick={handleReply}>Reply</button>
		{#if replyPrompt}
			<LoginPrompt message="Sign in to reply." onlogin={onlogin} />
		{/if}
	</footer>
</article>

<style>
	.bubble {
		align-self: flex-start;
		max-width: 100%;
		padding: 0.75rem 0.9rem;
		border-radius: calc(var(--monad-gos-radius) + 4px);
		background: var(--monad-gos-surface);
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 0.75rem;
		margin-bottom: 0.4rem;
		font-family: var(--monad-gos-font-ui);
		font-size: 0.7rem;
	}

	.kind {
		font-weight: 600;
		color: var(--monad-gos-executive);
	}

	.body {
		margin: 0;
		font-size: 1rem;
		line-height: 1.55;
	}

	footer {
		margin-top: 0.5rem;
	}

	.reply-link {
		border: none;
		background: transparent;
		padding: 0;
		font-family: var(--monad-gos-font-ui);
		font-size: 0.75rem;
		color: var(--monad-gos-text-muted);
		text-decoration: underline;
		text-underline-offset: 0.15em;
	}

	.reply-link:hover {
		color: var(--monad-gos-text);
	}
</style>
