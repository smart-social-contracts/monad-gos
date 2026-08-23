<script lang="ts">
	import type { ProposalView } from '../lib/types';
	import LoginPrompt from './LoginPrompt.svelte';

	let {
		proposal,
		onopenthread,
		onvote,
		needsAuth = false,
		onlogin,
		voting = false,
	}: {
		proposal: ProposalView;
		onopenthread?: (threadId: string) => void;
		onvote?: (proposalId: string, choice: 'yes' | 'no' | 'abstain') => void | Promise<void>;
		needsAuth?: boolean;
		onlogin?: () => void | Promise<void>;
		voting?: boolean;
	} = $props();

	let casting = $state(false);
	let votePrompt = $state(false);

	async function vote(choice: 'yes' | 'no' | 'abstain') {
		if (casting || voting) return;
		if (needsAuth) {
			votePrompt = true;
			return;
		}
		votePrompt = false;
		casting = true;
		try {
			await onvote?.(proposal.id, choice);
		} finally {
			casting = false;
		}
	}
</script>

<article class="proposal-card">
	<header>
		<h2>{proposal.title}</h2>
		<span class="status monad-gos-muted">{proposal.status}</span>
	</header>

	<p class="description">{proposal.description}</p>

	<dl class="details">
		<div>
			<dt>Justification</dt>
			<dd>{proposal.justification}</dd>
		</div>
		{#if proposal.cost}
			<div>
				<dt>Cost</dt>
				<dd>{proposal.cost}</dd>
			</div>
		{/if}
		{#if proposal.who_loses}
			<div>
				<dt>Who loses</dt>
				<dd>{proposal.who_loses}</dd>
			</div>
		{/if}
		{#if proposal.voting_deadline}
			<div>
				<dt>Deadline</dt>
				<dd>{proposal.voting_deadline}</dd>
			</div>
		{/if}
	</dl>

	{#if proposal.thread_ids.length > 0}
		<div class="threads">
			<span class="monad-gos-muted label">Motivated by</span>
			{#each proposal.thread_ids as threadId (threadId)}
				<button type="button" class="monad-gos-btn monad-gos-btn-ghost thread-btn" onclick={() => onopenthread?.(threadId)}>
					Read thread
				</button>
			{/each}
		</div>
	{/if}

	<div class="tally monad-gos-muted">
		Yes {proposal.votes_yes} · No {proposal.votes_no} · Abstain {proposal.votes_abstain}
	</div>

	{#if proposal.status === 'voting'}
		<div class="ballot" aria-label="Cast your vote">
			<button type="button" class="monad-gos-btn monad-gos-btn-yes" disabled={casting || voting} onclick={() => vote('yes')}>
				Yes
			</button>
			<button type="button" class="monad-gos-btn monad-gos-btn-no" disabled={casting || voting} onclick={() => vote('no')}>
				No
			</button>
			<button type="button" class="monad-gos-btn" disabled={casting || voting} onclick={() => vote('abstain')}>
				Abstain
			</button>
		</div>
		{#if votePrompt}
			<LoginPrompt message="Sign in to vote." onlogin={onlogin} />
		{/if}
	{/if}
</article>

<style>
	.proposal-card {
		padding: 1.5rem 0;
		border-bottom: 1px solid var(--monad-gos-border);
		max-width: var(--monad-gos-prose);
	}

	.proposal-card:last-child {
		border-bottom: none;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 1rem;
		margin-bottom: 0.75rem;
	}

	h2 {
		margin: 0;
		font-size: 1.2rem;
		font-weight: 500;
	}

	.status {
		font-family: var(--monad-gos-font-ui);
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.description {
		margin: 0 0 1rem;
	}

	.details {
		margin: 0 0 1rem;
		font-family: var(--monad-gos-font-ui);
		font-size: 0.9rem;
	}

	.details div {
		margin-bottom: 0.65rem;
	}

	dt {
		font-weight: 600;
		color: var(--monad-gos-text-muted);
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	dd {
		margin: 0.15rem 0 0;
	}

	.threads {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-bottom: 0.75rem;
	}

	.label {
		font-size: 0.8rem;
	}

	.thread-btn {
		font-size: 0.8rem;
	}

	.tally {
		font-size: 0.85rem;
		margin-bottom: 0.75rem;
	}

	.ballot {
		display: flex;
		gap: 0.5rem;
		padding-top: 0.5rem;
		border-top: 1px solid var(--monad-gos-border);
	}
</style>
