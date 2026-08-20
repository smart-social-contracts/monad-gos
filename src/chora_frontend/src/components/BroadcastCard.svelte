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

<article class="broadcast-card">
	<header>
		<span class="kind">Monad</span>
		<time class="chora-muted" datetime={new Date(message.created_at * 1000).toISOString()}>
			{formatTime(message.created_at)}
		</time>
	</header>
	<p class="body">{message.body}</p>
	<footer>
		<button type="button" class="chora-btn" onclick={handleReply}>
			Reply — opens a thread
		</button>
		{#if replyPrompt}
			<LoginPrompt message="Sign in to reply." onlogin={onlogin} />
		{/if}
	</footer>
</article>

<style>
	.broadcast-card {
		padding: 1.5rem 0;
		border-bottom: 1px solid var(--chora-border);
	}

	.broadcast-card:last-child {
		border-bottom: none;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 1rem;
		margin-bottom: 0.75rem;
		font-family: var(--chora-font-ui);
		font-size: 0.8rem;
	}

	.kind {
		font-weight: 600;
		color: var(--chora-monad);
	}

	.body {
		margin: 0;
		font-size: 1.05rem;
	}

	footer {
		margin-top: 1rem;
	}
</style>
