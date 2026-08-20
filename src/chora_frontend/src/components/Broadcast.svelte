<script lang="ts">
	import type { BroadcastMessage, ThreadSummary } from '../lib/types';
	import BroadcastCard from './BroadcastCard.svelte';
	import MessageComposer from './MessageComposer.svelte';
	import LoginPrompt from './LoginPrompt.svelte';

	let {
		broadcasts = [],
		publicThreads = [],
		monadError = null,
		needsAuth = false,
		wishDomain = 'governance',
		onreply,
		onopenthread,
		onsubmitwish,
		onlogin,
	}: {
		broadcasts?: BroadcastMessage[];
		publicThreads?: ThreadSummary[];
		monadError?: string | null;
		needsAuth?: boolean;
		wishDomain?: string;
		onreply?: (broadcastId: string) => void;
		onopenthread?: (threadId: string) => void;
		onsubmitwish?: (body: string) => void | Promise<{ wish_id?: string } | void>;
		onlogin?: () => void | Promise<void>;
	} = $props();

	let wishPrompt = $state(false);
	let wishConfirmation = $state<string | null>(null);
	let wishError = $state<string | null>(null);

	function showWishConfirmation(wishId?: string) {
		wishError = null;
		wishConfirmation = wishId
			? `Wish sealed (${wishId}). The Monad will read it when this epoch ends.`
			: 'Wish sealed. The Monad will read it when this epoch ends.';
	}

	async function handleWish(body: string) {
		if (needsAuth) {
			wishPrompt = true;
			return;
		}
		wishPrompt = false;
		wishError = null;
		try {
			const result = await onsubmitwish?.(body);
			const wishId =
				result && typeof result === 'object' && 'wish_id' in result
					? String((result as { wish_id: string }).wish_id)
					: undefined;
			showWishConfirmation(wishId);
		} catch (e) {
			wishConfirmation = null;
			wishError = e instanceof Error ? e.message : 'Your wish could not be sent.';
		}
	}
</script>

<section class="broadcast" aria-label="Monad broadcast">
	<header class="section-header">
		<h1>The Monad speaks</h1>
		<p class="chora-muted intro">
			The realm’s voice to all citizens. Read, respond, and speak your wish before the seal.
		</p>
	</header>

	{#if monadError}
		<p class="monad-error">{monadError}</p>
	{/if}

	<div class="wish-panel">
		<h2 class="wish-title">Your wish</h2>
		<p class="chora-muted wish-hint">
			Speak to the Monad before the epoch seals. Domain: {wishDomain}. Wishes stay sealed — they will not appear in this feed.
		</p>
		<MessageComposer
			placeholder="What should the realm hear this epoch?"
			submitLabel="Send wish"
			fieldId="chora-wish-composer"
			onsubmit={handleWish}
		/>
		{#if wishConfirmation}
			<p class="wish-confirmation" role="status" aria-live="polite">
				{wishConfirmation}
			</p>
		{/if}
		{#if wishError}
			<p class="monad-error wish-error" role="alert">{wishError}</p>
		{/if}
		{#if wishPrompt}
			<LoginPrompt message="Sign in to send a wish." onlogin={onlogin} />
		{/if}
	</div>

	<div class="feed chora-prose">
		{#if broadcasts.length === 0}
			<p class="chora-muted empty">No broadcasts yet.</p>
			<p class="chora-muted empty-hint">
				The Monad will address the realm when the first epoch opens.
			</p>
		{:else}
			{#each broadcasts as message (message.id)}
				<BroadcastCard message={message} onreply={onreply} needsAuth={needsAuth} onlogin={onlogin} />
			{/each}
		{/if}
	</div>

	{#if publicThreads.length > 0}
		<aside class="public-threads">
			<h2>Public threads</h2>
			<ul>
				{#each publicThreads as thread (thread.id)}
					<li>
						<button type="button" class="thread-link" onclick={() => onopenthread?.(thread.id)}>
							<span class="title">{thread.title}</span>
							<span class="chora-muted meta">
								{thread.participant_count} participants · {thread.visibility}
							</span>
						</button>
					</li>
				{/each}
			</ul>
		</aside>
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
		max-width: var(--chora-prose);
	}

	.monad-error {
		color: var(--chora-no);
		margin: 0 0 1.5rem;
		max-width: var(--chora-prose);
		font-family: var(--chora-font-ui);
		font-size: 0.9rem;
	}

	.empty {
		margin: 0;
	}

	.empty-hint {
		margin: 0.35rem 0 0;
	}

	.public-threads {
		margin-top: 3rem;
		padding-top: 2rem;
		border-top: 1px solid var(--chora-border);
		max-width: var(--chora-prose);
	}

	h2 {
		margin: 0 0 1rem;
		font-size: 1rem;
		font-family: var(--chora-font-ui);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--chora-text-muted);
	}

	ul {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.thread-link {
		display: block;
		width: 100%;
		text-align: left;
		padding: 0.75rem 0;
		border: none;
		border-bottom: 1px solid var(--chora-border);
		background: transparent;
		font-family: var(--chora-font);
		font-size: 1rem;
		color: inherit;
	}

	.thread-link:hover {
		background: var(--chora-accent-soft);
	}

	.title {
		display: block;
		font-weight: 500;
	}

	.meta {
		font-size: 0.8rem;
	}

	.wish-panel {
		margin: 0 0 2.5rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid var(--chora-border);
		max-width: var(--chora-prose);
	}

	.wish-title {
		margin: 0 0 0.25rem;
		font-size: 1rem;
		font-family: var(--chora-font-ui);
		font-weight: 600;
	}

	.wish-hint {
		margin: 0 0 0.5rem;
		font-size: 0.85rem;
	}

	.wish-confirmation {
		margin: 0.75rem 0 0;
		font-family: var(--chora-font-ui);
		font-size: 0.95rem;
		color: var(--chora-text);
		font-weight: 500;
	}

	.wish-error {
		margin: 0.5rem 0 0;
	}
</style>
