<script lang="ts">
	import type { ThreadMessage } from '../lib/types';

	let { message, monadAuthor = '' }: { message: ThreadMessage; monadAuthor?: string } =
		$props();

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

<article class="message" class:monad={isMonad} class:system={isSystem}>
	<header>
		<span class="author">{isMonad ? 'Monad' : message.author}</span>
		<time class="chora-muted" datetime={new Date(message.created_at * 1000).toISOString()}>
			{formatTime(message.created_at)}
		</time>
	</header>
	<p>{message.body}</p>
</article>

<style>
	.message {
		padding: 1rem 0;
		border-bottom: 1px solid var(--chora-border);
	}

	.message:last-child {
		border-bottom: none;
	}

	.message header {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 1rem;
		margin-bottom: 0.35rem;
		font-family: var(--chora-font-ui);
		font-size: 0.8rem;
	}

	.author {
		font-weight: 600;
	}

	.message p {
		margin: 0;
	}

	.message.monad .author {
		color: var(--chora-monad);
	}

	.message.system {
		opacity: 0.7;
		font-size: 0.9rem;
	}
</style>
