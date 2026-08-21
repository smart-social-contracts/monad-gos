<script lang="ts">
	import type { ThreadMessage } from '../lib/types';

	let {
		message,
		monadAuthor = '',
		onopeninputs,
	}: {
		message: ThreadMessage;
		monadAuthor?: string;
		onopeninputs?: (messageId: string) => void;
	} = $props();

	const isMonad = $derived(
		monadAuthor ? message.author === monadAuthor : message.author.includes('aaaaa-aa'),
	);
	const isSystem = $derived(message.author === 'system');

	function formatTime(ts: number): string {
		return new Date(ts * 1000).toLocaleString(undefined, {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
		});
	}
</script>

<article class="bubble" class:monad={isMonad} class:system={isSystem} class:self={!isMonad && !isSystem}>
	<header>
		<span class="author">{isMonad ? 'Monad' : isSystem ? 'System' : 'You'}</span>
		<time class="chora-muted" datetime={new Date(message.created_at * 1000).toISOString()}>
			{formatTime(message.created_at)}
		</time>
	</header>
	<p>{message.body}</p>
	{#if isMonad}
		<p class="repro">
			<button type="button" class="repro-link" onclick={() => onopeninputs?.(message.id)}>
				Inputs
			</button>
		</p>
	{/if}
</article>

<style>
	.bubble {
		align-self: flex-start;
		max-width: 92%;
		padding: 0.75rem 0.9rem;
		border-radius: calc(var(--chora-radius) + 4px);
		background: var(--chora-surface);
	}

	.bubble.self {
		align-self: flex-end;
		background: color-mix(in srgb, var(--chora-accent-soft) 55%, var(--chora-surface));
	}

	.bubble header {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 0.75rem;
		margin-bottom: 0.35rem;
		font-family: var(--chora-font-ui);
		font-size: 0.7rem;
	}

	.author {
		font-weight: 600;
	}

	.bubble p {
		margin: 0;
		font-size: 0.95rem;
		line-height: 1.55;
	}

	.bubble.monad .author {
		color: var(--chora-monad);
	}

	.bubble.system {
		opacity: 0.7;
		font-size: 0.9rem;
	}

	.repro {
		margin: 0.45rem 0 0;
	}

	.repro-link {
		border: none;
		background: transparent;
		padding: 0;
		font-family: var(--chora-font-ui);
		font-size: 0.75rem;
		color: var(--chora-text-muted);
		text-decoration: underline;
		text-underline-offset: 0.15em;
	}

	.repro-link:hover {
		color: var(--chora-text);
	}
</style>
