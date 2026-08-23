<script lang="ts">
	import type { ProposalView } from '../lib/types';
	import ProposalCard from './ProposalCard.svelte';

	let {
		proposals = [],
		needsAuth = false,
		onopenthread,
		onvote,
		onlogin,
	}: {
		proposals?: ProposalView[];
		needsAuth?: boolean;
		onopenthread?: (threadId: string) => void;
		onvote?: (proposalId: string, choice: 'yes' | 'no' | 'abstain') => void | Promise<void>;
		onlogin?: () => void | Promise<void>;
	} = $props();
</script>

<section class="voting-area" aria-label="Proposals">
	<header class="section-header">
		<h1>Proposals</h1>
		<p class="monad-gos-muted intro">
			Ratification is separate from conversation. Read the deliberation, then decide.
		</p>
	</header>

	{#if proposals.length === 0}
		<p class="monad-gos-muted">No proposals open for voting.</p>
	{:else}
		{#each proposals as proposal (proposal.id)}
			<ProposalCard
				proposal={proposal}
				needsAuth={needsAuth}
				onopenthread={onopenthread}
				onvote={onvote}
				onlogin={onlogin}
			/>
		{/each}
	{/if}
</section>

<style>
	.section-header {
		margin-bottom: 2rem;
		max-width: var(--monad-gos-prose);
	}

	h1 {
		margin: 0 0 0.35rem;
		font-size: 1.5rem;
		font-weight: 500;
	}

	.intro {
		margin: 0;
	}
</style>
