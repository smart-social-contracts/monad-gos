<script lang="ts">
	import type {
		AlignmentData,
		BroadcastMessage,
		ConnectionStatus,
		EpochStatus,
		ProposalView,
		ThreadMessage,
		ThreadSummary,
		View,
	} from './lib/types';
	import {
		alignmentCoefficient,
		castVote,
		checkConnection,
		getEpochStatus,
		isMockMode,
		listProposals,
		listThreads,
		readBroadcast,
		readThread,
		replyToBroadcast,
		replyToThread,
		resetActors,
		submitWish,
		monadPrincipal,
		waitForNewMessage,
	} from './chora_api.js';
	import {
		formatPrincipalShort,
		getPrincipalText,
		initAuth,
		isAnonymous,
		login,
		logout,
	} from './lib/auth.js';
	import AppHeader from './components/AppHeader.svelte';
	import EpochStatusLine from './components/EpochStatusLine.svelte';
	import AlignmentCoefficient from './components/AlignmentCoefficient.svelte';
	import Broadcast from './components/Broadcast.svelte';
	import ThreadView from './components/ThreadView.svelte';
	import VotingArea from './components/VotingArea.svelte';
	import ThreadsList from './components/ThreadsList.svelte';
	import MessageComposer from './components/MessageComposer.svelte';
	import LoginPrompt from './components/LoginPrompt.svelte';

	const MONAD_ERROR =
		'The Monad could not be reached. Check your connection, or try again later.';

	let view = $state<View>('broadcast');
	let loading = $state(true);
	let error = $state<string | null>(null);
	let monadError = $state<string | null>(null);
	let connectionStatus = $state<ConnectionStatus>('connecting');

	let epochStatus = $state<EpochStatus | null>(null);
	let alignment = $state<AlignmentData | null>(null);
	let broadcasts = $state<BroadcastMessage[]>([]);
	let publicThreads = $state<ThreadSummary[]>([]);
	let allThreads = $state<ThreadSummary[]>([]);
	let proposals = $state<ProposalView[]>([]);

	let activeThreadId = $state<string | null>(null);
	let activeThread = $state<ThreadSummary | null>(null);
	let activeMessages = $state<ThreadMessage[]>([]);

	let replyBroadcastId = $state<string | null>(null);
	let replyPrompt = $state(false);
	let awaitingMonad = $state(false);
	const monadAuthor = monadPrincipal();

	let isLoggedIn = $state(isMockMode());
	let principalShort = $state(isMockMode() ? 'citizen-mock' : '');

	const needsAuth = $derived(!isMockMode() && !isLoggedIn);

	function refreshAuthState() {
		isLoggedIn = !isAnonymous();
		principalShort = isLoggedIn ? formatPrincipalShort(getPrincipalText()) : '';
	}

	async function handleLogin() {
		try {
			await login();
			resetActors();
			refreshAuthState();
			replyPrompt = false;
			await loadCore();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Sign in failed';
		}
	}

	async function handleLogout() {
		await logout();
		resetActors();
		refreshAuthState();
	}

	async function loadCore() {
		loading = true;
		error = null;
		monadError = null;
		try {
			const [epoch, align, broadcast, proposalList, threadList] = await Promise.all([
				getEpochStatus(),
				alignmentCoefficient(),
				readBroadcast(),
				listProposals(),
				listThreads(),
			]);
			epochStatus = epoch;
			alignment = align;
			broadcasts = broadcast.broadcasts;
			publicThreads = broadcast.public_threads;
			proposals = proposalList;
			allThreads = threadList.threads;
			connectionStatus = 'connected';
		} catch (e) {
			const message = e instanceof Error ? e.message : 'Failed to load Chora';
			error = message;
			monadError = MONAD_ERROR;
			connectionStatus = 'error';
		} finally {
			loading = false;
		}
	}

	async function bootstrap() {
		connectionStatus = 'connecting';
		if (!isMockMode()) {
			await initAuth();
			refreshAuthState();
		}

		const conn = await checkConnection();
		if (!conn.ok) {
			connectionStatus = 'error';
			monadError = MONAD_ERROR;
			error = conn.error ?? MONAD_ERROR;
			loading = false;
			return;
		}

		connectionStatus = 'connected';
		await loadCore();
	}

	async function openThread(threadId: string) {
		replyBroadcastId = null;
		try {
			const data = await readThread(threadId);
			if (!data.thread) {
				throw new Error('Thread not found');
			}
			activeThreadId = threadId;
			activeThread = data.thread;
			activeMessages = data.messages;
			view = 'thread';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load thread';
		}
	}

	function startReplyToBroadcast(broadcastId: string) {
		replyBroadcastId = broadcastId;
		view = 'broadcast';
	}

	async function submitBroadcastReply(body: string) {
		if (!replyBroadcastId) return;
		const { thread_id } = await replyToBroadcast(replyBroadcastId, body);
		const now = Math.floor(Date.now() / 1000);
		replyBroadcastId = null;
		replyPrompt = false;
		activeThreadId = thread_id;
		activeThread = {
			id: thread_id,
			title: body.length > 48 ? `${body.slice(0, 48)}…` : body,
			visibility: 'private',
			participant_count: 1,
			epoch: epochStatus?.epoch_id ?? '0',
			last_activity_at: now,
		};
		activeMessages = [
			{
				id: `local-${now}`,
				thread_id,
				author: getPrincipalText(),
				body,
				created_at: now,
			},
		];
		view = 'thread';
		try {
			const data = await readThread(thread_id);
			if (data.thread) {
				activeThread = data.thread;
				activeMessages = data.messages;
			}
		} catch {
			/* keep the message you just sent on screen */
		}
		try {
			const threadList = await listThreads();
			allThreads = threadList.threads;
		} catch {
			/* list refresh is best-effort */
		}
		awaitingMonad = true;
		try {
			const latest = await waitForNewMessage(thread_id, activeMessages.length);
			if (latest?.thread) {
				activeThread = latest.thread;
				activeMessages = latest.messages;
			}
		} finally {
			awaitingMonad = false;
		}
	}

	async function handleBroadcastReply(body: string) {
		if (needsAuth) {
			replyPrompt = true;
			return;
		}
		try {
			await submitBroadcastReply(body);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Reply failed';
			throw e;
		}
	}

	async function submitThreadReply(body: string) {
		if (!activeThreadId) return;
		await replyToThread(activeThreadId, body);
		const data = await readThread(activeThreadId);
		activeThread = data.thread;
		activeMessages = data.messages;
		awaitingMonad = true;
		try {
			const latest = await waitForNewMessage(activeThreadId, activeMessages.length);
			if (latest?.thread) {
				activeThread = latest.thread;
				activeMessages = latest.messages;
			}
		} finally {
			awaitingMonad = false;
		}
	}

	async function handleWish(body: string) {
		if (!epochStatus) {
			throw new Error('Epoch status is not available.');
		}
		return submitWish('governance', body, epochStatus.epoch_id);
	}

	async function handleVote(proposalId: string, choice: 'yes' | 'no' | 'abstain') {
		await castVote(proposalId, choice);
		proposals = await listProposals();
	}

	function goBroadcast() {
		view = 'broadcast';
		activeThreadId = null;
		replyBroadcastId = null;
	}

	function goProposals() {
		view = 'voting';
		replyBroadcastId = null;
	}

	function goThreads() {
		view = 'threads';
		replyBroadcastId = null;
		activeThreadId = null;
	}

	$effect(() => {
		bootstrap();
		const interval = setInterval(async () => {
			try {
				epochStatus = await getEpochStatus();
				alignment = await alignmentCoefficient();
			} catch {
				/* background refresh — ignore */
			}
		}, 60000);
		return () => clearInterval(interval);
	});
</script>

<div class="chora-app">
	<AppHeader
		connectionStatus={connectionStatus}
		isLoggedIn={isLoggedIn}
		principalShort={principalShort}
		onlogin={handleLogin}
		onlogout={handleLogout}
	/>

	{#if epochStatus}
		<EpochStatusLine
			epochId={epochStatus.epoch_id}
			phase={epochStatus.phase}
			countdownSeconds={epochStatus.seconds_until_seal}
		/>
	{/if}

	<div class="shell">
		<nav class="nav" aria-label="Chora sections">
			<button
				type="button"
				class="nav-btn"
				class:active={view === 'broadcast'}
				onclick={goBroadcast}
			>
				Broadcast
			</button>
			<button
				type="button"
				class="nav-btn"
				class:active={view === 'voting'}
				onclick={goProposals}
			>
				Proposals
			</button>
			<button
				type="button"
				class="nav-btn"
				class:active={view === 'threads'}
				onclick={goThreads}
			>
				Threads
			</button>
			{#if isMockMode()}
				<span class="mock-badge chora-muted">Mock data</span>
			{/if}
		</nav>

		<div class="layout">
			<main class="main">
				{#if loading}
					<p class="chora-muted">Loading Chora…</p>
				{:else if error && connectionStatus === 'error'}
					<p class="error">{error}</p>
					<button type="button" class="chora-btn" onclick={bootstrap}>Retry</button>
				{:else if view === 'broadcast'}
					{#if error}
						<p class="error">{error}</p>
					{/if}
					<Broadcast
						broadcasts={broadcasts}
						publicThreads={publicThreads}
						monadError={monadError}
						needsAuth={needsAuth}
						onreply={startReplyToBroadcast}
						onopenthread={openThread}
						onsubmitwish={handleWish}
						onlogin={handleLogin}
					/>
					{#if replyBroadcastId}
						<div class="reply-panel">
							<h2 class="reply-title">Your reply</h2>
							<p class="chora-muted">This opens a private thread with the Monad.</p>
							<MessageComposer
								placeholder="Write your response…"
								submitLabel="Open thread"
								fieldId="chora-reply-composer"
								onsubmit={handleBroadcastReply}
							/>
							{#if replyPrompt}
								<LoginPrompt message="Sign in to reply." onlogin={handleLogin} />
							{/if}
						</div>
					{/if}
				{:else if view === 'thread'}
					<ThreadView
						thread={activeThread}
						messages={activeMessages}
						needsAuth={needsAuth}
						monadAuthor={monadAuthor}
						awaitingMonad={awaitingMonad}
						onback={goBroadcast}
						onreply={submitThreadReply}
						onlogin={handleLogin}
					/>
				{:else if view === 'threads'}
					<ThreadsList threads={allThreads} onopenthread={openThread} />
				{:else}
					<VotingArea
						proposals={proposals}
						needsAuth={needsAuth}
						onopenthread={openThread}
						onvote={handleVote}
						onlogin={handleLogin}
					/>
				{/if}
			</main>

			<aside class="sidebar">
				<AlignmentCoefficient data={alignment} />
			</aside>
		</div>
	</div>

	<footer class="footer chora-muted">
		Chora · a GGG-compliant GOS · the Monad proposes, the citizens ratify
	</footer>
</div>

<style>
	.chora-app {
		min-height: 100vh;
	}

	.shell {
		max-width: 72rem;
		margin: 0 auto;
		padding: 1.5rem 1.25rem 2rem;
	}

	.nav {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 2rem;
		font-family: var(--chora-font-ui);
	}

	.nav-btn {
		padding: 0.4rem 0.85rem;
		border: 1px solid transparent;
		border-radius: var(--chora-radius);
		background: transparent;
		font-size: 0.9rem;
		color: var(--chora-text-muted);
	}

	.nav-btn:hover {
		background: var(--chora-accent-soft);
		color: var(--chora-text);
	}

	.nav-btn.active {
		background: var(--chora-surface);
		border-color: var(--chora-border);
		color: var(--chora-text);
	}

	.mock-badge {
		margin-left: auto;
		font-size: 0.75rem;
	}

	.layout {
		display: grid;
		grid-template-columns: 1fr 14rem;
		gap: 2.5rem;
		align-items: start;
	}

	.main {
		min-width: 0;
	}

	.sidebar {
		position: sticky;
		top: 1rem;
	}

	.reply-panel {
		margin-top: 2rem;
		padding-top: 2rem;
		border-top: 1px solid var(--chora-border);
		max-width: var(--chora-prose);
	}

	.reply-title {
		margin: 0 0 0.25rem;
		font-size: 1rem;
		font-family: var(--chora-font-ui);
		font-weight: 600;
	}

	.error {
		color: var(--chora-no);
		margin-bottom: 0.75rem;
	}

	.footer {
		text-align: center;
		padding: 2rem 1.25rem 2.5rem;
		font-family: var(--chora-font-ui);
		font-size: 0.75rem;
		border-top: 1px solid var(--chora-border);
	}

	@media (max-width: 768px) {
		.layout {
			grid-template-columns: 1fr;
		}

		.sidebar {
			order: -1;
			position: static;
		}
	}
</style>
