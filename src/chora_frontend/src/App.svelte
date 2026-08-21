<script lang="ts">
	import type {
		BroadcastMessage,
		ConnectionStatus,
		EpochStatus,
		ProposalView,
		RealmState,
		ReplyInputs,
		SetupState,
		ThreadMessage,
		ThreadSummary,
		View,
	} from './lib/types';
	import {
		castVote,
		checkConnection,
		configureChoraRuntime,
		getEpochStatus,
		getRealmLogo,
		getSetupState,
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
		getReplyInputs,
		getRealmState,
	} from './chora_api.js';
	import {
		formatPrincipalShort,
		getPrincipalText,
		initAuth,
		isAnonymous,
		login,
		logout,
	} from './lib/auth.js';
	import {
		initPortalBridge,
		isEmbeddedInPortal,
		portalUiReady,
		waitForPortalConfig,
	} from './lib/portal-bridge.ts';
	import AppHeader from './components/AppHeader.svelte';
	import EpochStatusLine from './components/EpochStatusLine.svelte';
	import Broadcast from './components/Broadcast.svelte';
	import ThreadView from './components/ThreadView.svelte';
	import VotingArea from './components/VotingArea.svelte';
	import ThreadsList from './components/ThreadsList.svelte';
	import MessageComposer from './components/MessageComposer.svelte';
	import LoginPrompt from './components/LoginPrompt.svelte';
	import ReplyInputsPage from './components/ReplyInputsPage.svelte';
	import RealmDashboard from './components/RealmDashboard.svelte';
	import Settings from './components/Settings.svelte';
	import SetupWizard from './components/SetupWizard.svelte';

	const MONAD_ERROR =
		'The Monad could not be reached. Check your connection, or try again later.';

	let view = $state<View>('broadcast');
	let loading = $state(true);
	let error = $state<string | null>(null);
	let monadError = $state<string | null>(null);
	let connectionStatus = $state<ConnectionStatus>('connecting');

	let epochStatus = $state<EpochStatus | null>(null);
	let broadcasts = $state<BroadcastMessage[]>([]);
	let publicThreads = $state<ThreadSummary[]>([]);
	let allThreads = $state<ThreadSummary[]>([]);
	let proposals = $state<ProposalView[]>([]);
	let realmState = $state<RealmState | null>(null);
	let setupState = $state<SetupState | null>(null);
	let setupActive = $state(false);
	let realmLogo = $state('');

	let activeThreadId = $state<string | null>(null);
	let activeThread = $state<ThreadSummary | null>(null);
	let activeMessages = $state<ThreadMessage[]>([]);

	let replyBroadcastId = $state<string | null>(null);
	let replyPrompt = $state(false);
	let awaitingMonad = $state(false);
	let activeInputsId = $state<string | null>(null);
	let activeInputs = $state<ReplyInputs | null>(null);
	let inputsMissing = $state(false);

	let wishPrompt = $state(false);
	let wishConfirmation = $state<string | null>(null);
	let wishError = $state<string | null>(null);
	let threadReplyPrompt = $state(false);

	const monadAuthor = monadPrincipal();

	let isLoggedIn = $state(isMockMode());
	let principalShort = $state(isMockMode() ? 'citizen-mock' : '');

	const needsAuth = $derived(!isMockMode() && !isLoggedIn);
	const showComposer = $derived(view === 'broadcast' || view === 'thread');
	const composerPlaceholder = $derived(
		view === 'thread'
			? 'Continue the conversation…'
			: replyBroadcastId
				? 'Write a reply… · opens a thread'
				: 'Write a wish…',
	);
	const composerSubmitLabel = $derived(
		view === 'thread' ? 'Send' : replyBroadcastId ? 'Open thread' : 'Send',
	);
	const composerFieldId = $derived(
		view === 'thread'
			? 'chora-thread-composer'
			: replyBroadcastId
				? 'chora-reply-composer'
				: 'chora-wish-composer',
	);

	function refreshAuthState() {
		isLoggedIn = !isAnonymous();
		principalShort = isLoggedIn ? formatPrincipalShort(getPrincipalText()) : '';
	}

	function cancelReply() {
		replyBroadcastId = null;
		replyPrompt = false;
	}

	async function handleLogin() {
		try {
			await login();
			resetActors();
			refreshAuthState();
			replyPrompt = false;
			wishPrompt = false;
			threadReplyPrompt = false;
			if (setupActive) {
				try {
					setupState = await getSetupState();
				} catch (e) {
					error = e instanceof Error ? e.message : 'Failed to read setup state';
				}
			} else {
				await loadCore();
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Sign in failed';
		}
	}

	async function handleLogout() {
		await logout();
		resetActors();
		refreshAuthState();
		if (view === 'settings') {
			view = 'broadcast';
		}
	}

	async function loadRealmLogo() {
		try {
			const logo = await getRealmLogo();
			if (logo) {
				realmLogo = logo;
				return;
			}
		} catch {
			/* logo query is optional */
		}
		if (setupState?.logo_data_url) {
			realmLogo = setupState.logo_data_url;
		}
	}

	async function handleSetupComplete() {
		setupActive = false;
		try {
			setupState = await getSetupState();
		} catch {
			/* best-effort refresh */
		}
		await loadCore();
		await loadRealmLogo();
		if (isEmbeddedInPortal()) {
			portalUiReady();
		}
	}

	async function loadCore() {
		loading = true;
		error = null;
		monadError = null;
		try {
			const [epoch, broadcast, proposalList, threadList, realm] = await Promise.all([
				getEpochStatus(),
				readBroadcast(),
				listProposals(),
				listThreads(),
				getRealmState(),
			]);
			epochStatus = epoch;
			broadcasts = broadcast.broadcasts;
			publicThreads = broadcast.public_threads;
			proposals = proposalList;
			allThreads = threadList.threads;
			realmState = realm;
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

		if (isEmbeddedInPortal()) {
			const config = await waitForPortalConfig({ timeoutMs: 30_000 });
			if (!config?.backendCanisterId) {
				connectionStatus = 'error';
				monadError = MONAD_ERROR;
				error = 'Portal configuration not received';
				loading = false;
				return;
			}
			configureChoraRuntime({ canisterId: config.backendCanisterId });
		}

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

		try {
			setupState = await getSetupState();
			if (setupState.entered && !setupState.completed) {
				setupActive = true;
				loading = false;
				if (isEmbeddedInPortal()) {
					portalUiReady();
				}
				return;
			}
		} catch (e) {
			const message = e instanceof Error ? e.message : 'Failed to read setup state';
			error = message;
			monadError = MONAD_ERROR;
			connectionStatus = 'error';
			loading = false;
			return;
		}

		await loadCore();
		await loadRealmLogo();
		if (isEmbeddedInPortal()) {
			portalUiReady();
		}
		await applyInputsHash();
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

	async function handleThreadReply(body: string) {
		if (needsAuth) {
			threadReplyPrompt = true;
			return;
		}
		threadReplyPrompt = false;
		try {
			await submitThreadReply(body);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Reply failed';
			throw e;
		}
	}

	async function handleWish(body: string) {
		if (!epochStatus) {
			throw new Error('Epoch status is not available.');
		}
		wishPrompt = false;
		wishError = null;
		const result = await submitWish('governance', body, epochStatus.epoch_id);
		const wishId =
			result && typeof result === 'object' && 'wish_id' in result
				? String((result as { wish_id: string }).wish_id)
				: undefined;
		wishConfirmation = wishId
			? `Wish sealed (${wishId}). The Monad will read it when this epoch ends.`
			: 'Wish sealed. The Monad will read it when this epoch ends.';
	}

	async function handleComposerSubmit(body: string) {
		if (view === 'thread') {
			await handleThreadReply(body);
			return;
		}
		if (replyBroadcastId) {
			await handleBroadcastReply(body);
			return;
		}
		if (needsAuth) {
			wishPrompt = true;
			return;
		}
		try {
			await handleWish(body);
		} catch (e) {
			wishConfirmation = null;
			wishError = e instanceof Error ? e.message : 'Your wish could not be sent.';
		}
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

	function goRealm() {
		view = 'realm';
		replyBroadcastId = null;
	}

	function goSettings() {
		view = 'settings';
		replyBroadcastId = null;
		activeThreadId = null;
	}

	async function openInputs(messageId: string) {
		activeInputsId = messageId;
		view = 'inputs';
		const target = `#inputs/${messageId}`;
		if (location.hash !== target) {
			location.hash = `inputs/${messageId}`;
		}
		try {
			activeInputs = await getReplyInputs(messageId);
			inputsMissing = !activeInputs;
		} catch {
			activeInputs = null;
			inputsMissing = true;
		}
	}

	async function applyInputsHash() {
		const match = location.hash.match(/^#inputs\/(.+)$/);
		if (match?.[1]) {
			await openInputs(match[1]);
		}
	}

	function closeInputs() {
		if (location.hash.startsWith('#inputs/')) {
			history.replaceState(null, '', `${location.pathname}${location.search}`);
		}
		if (activeThreadId) {
			view = 'thread';
		} else {
			view = 'broadcast';
		}
	}

	$effect(() => {
		let disposeBridge = () => {};
		if (isEmbeddedInPortal()) {
			disposeBridge = initPortalBridge();
		}

		const onPortalAuth = async () => {
			resetActors();
			refreshAuthState();
			if (setupActive) {
				try {
					setupState = await getSetupState();
				} catch {
					/* keep current setup gate */
				}
			} else {
				await loadCore();
			}
		};
		window.addEventListener('portal:auth', onPortalAuth);
		window.addEventListener('hashchange', applyInputsHash);

		bootstrap();

		const interval = setInterval(async () => {
			if (setupActive) return;
			try {
				epochStatus = await getEpochStatus();
			} catch {
				/* background refresh — ignore */
			}
		}, 60000);

		return () => {
			disposeBridge();
			window.removeEventListener('portal:auth', onPortalAuth);
			window.removeEventListener('hashchange', applyInputsHash);
			clearInterval(interval);
		};
	});
</script>

<div class="chora-app">
	{#if setupActive}
		<div class="setup-shell">
			{#if loading}
				<p class="chora-muted">Loading setup…</p>
			{:else if needsAuth}
				<section class="setup-gate chora-prose">
					<h1>Founding this realm</h1>
					<p class="chora-muted">Sign in as the founder to continue setup.</p>
					<LoginPrompt message="Sign in to continue setup." onlogin={handleLogin} />
				</section>
			{:else if setupState?.is_caller_authorized}
				<SetupWizard draft={setupState.draft} oncomplete={handleSetupComplete} />
			{:else}
				<section class="setup-gate chora-prose">
					<p>This realm is being set up and is not yet open.</p>
				</section>
			{/if}
		</div>
	{:else}
		<div class="chat-shell">
			<div class="chat-column">
				<div class="floating-chrome" aria-label="Chora navigation">
					<AppHeader
						connectionStatus={connectionStatus}
						isLoggedIn={isLoggedIn}
						principalShort={principalShort}
						logoSrc={realmLogo}
						onlogin={handleLogin}
						onlogout={handleLogout}
						onsettings={goSettings}
					/>

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
						<button
							type="button"
							class="nav-btn"
							class:active={view === 'realm'}
							onclick={goRealm}
						>
							Realm
						</button>
						{#if isMockMode() && !isEmbeddedInPortal()}
							<span class="mock-badge chora-muted">Mock</span>
						{/if}
					</nav>

					{#if epochStatus}
						<EpochStatusLine
							epochId={epochStatus.epoch_id}
							phase={epochStatus.phase}
							countdownSeconds={epochStatus.seconds_until_seal}
						/>
					{/if}
				</div>

				<main class="chat-scroll">
					<div class="chat-content">
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
								onlogin={handleLogin}
							/>
						{:else if view === 'thread'}
							<ThreadView
								thread={activeThread}
								messages={activeMessages}
								monadAuthor={monadAuthor}
								awaitingMonad={awaitingMonad}
								onback={goBroadcast}
								onopeninputs={openInputs}
							/>
						{:else if view === 'inputs'}
							<ReplyInputsPage
								inputs={activeInputs}
								missing={inputsMissing}
								onback={closeInputs}
							/>
						{:else if view === 'threads'}
							<ThreadsList threads={allThreads} onopenthread={openThread} />
						{:else if view === 'realm'}
							<RealmDashboard data={realmState} logoSrc={realmLogo} />
						{:else if view === 'settings'}
							<Settings needsAuth={needsAuth} onlogin={handleLogin} />
						{:else}
							<VotingArea
								proposals={proposals}
								needsAuth={needsAuth}
								onopenthread={openThread}
								onvote={handleVote}
								onlogin={handleLogin}
							/>
						{/if}
					</div>
				</main>

				{#if showComposer}
					<div class="composer-dock">
						{#if view === 'broadcast' && replyBroadcastId}
							<div class="composer-meta">
								<span class="chora-muted">Replying · opens a private thread</span>
								<button type="button" class="cancel-reply" onclick={cancelReply}>Cancel</button>
							</div>
						{/if}
						{#if view === 'broadcast' && wishConfirmation}
							<p class="composer-status" role="status" aria-live="polite">{wishConfirmation}</p>
						{/if}
						{#if view === 'broadcast' && wishError}
							<p class="composer-error" role="alert">{wishError}</p>
						{/if}
						<MessageComposer
							placeholder={composerPlaceholder}
							submitLabel={composerSubmitLabel}
							fieldId={composerFieldId}
							onsubmit={handleComposerSubmit}
						/>
						{#if view === 'broadcast' && (wishPrompt || replyPrompt)}
							<LoginPrompt
								message={replyBroadcastId ? 'Sign in to reply.' : 'Sign in to send a wish.'}
								onlogin={handleLogin}
							/>
						{/if}
						{#if view === 'thread' && threadReplyPrompt}
							<LoginPrompt message="Sign in to reply." onlogin={handleLogin} />
						{/if}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.chora-app {
		height: 100dvh;
		overflow: hidden;
		background: var(--chora-bg);
	}

	.setup-shell {
		max-width: 42rem;
		margin: 0 auto;
		padding: 2rem 1.25rem;
		height: 100%;
		overflow-y: auto;
	}

	.setup-gate h1 {
		margin: 0 0 0.75rem;
		font-size: 1.5rem;
		font-weight: 500;
	}

	.setup-gate p {
		margin: 0;
	}

	.chat-shell {
		height: 100%;
		display: flex;
		justify-content: center;
	}

	.chat-column {
		position: relative;
		display: flex;
		flex-direction: column;
		width: 100%;
		max-width: var(--chora-prose);
		height: 100%;
	}

	.floating-chrome {
		position: absolute;
		top: 0.75rem;
		left: 0.75rem;
		right: 0.75rem;
		z-index: 10;
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
		grid-template-areas: 'brand nav auth';
		align-items: center;
		gap: 0.5rem 0.75rem;
		padding: 0.45rem 0.65rem;
		border: 1px solid color-mix(in srgb, var(--chora-border) 80%, transparent);
		border-radius: 999px;
		background: color-mix(in srgb, var(--chora-surface) 88%, transparent);
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		font-family: var(--chora-font-ui);
	}

	.nav {
		grid-area: nav;
		display: flex;
		align-items: center;
		gap: 0.15rem;
		justify-self: center;
	}

	.nav-btn {
		padding: 0.28rem 0.55rem;
		border: 1px solid transparent;
		border-radius: 999px;
		background: transparent;
		font-size: 0.72rem;
		color: var(--chora-text-muted);
		white-space: nowrap;
	}

	.nav-btn:hover {
		background: color-mix(in srgb, var(--chora-accent-soft) 70%, transparent);
		color: var(--chora-text);
	}

	.nav-btn.active {
		background: var(--chora-surface);
		border-color: var(--chora-border);
		color: var(--chora-text);
	}

	.mock-badge {
		margin-left: 0.25rem;
		font-size: 0.6rem;
	}

	.floating-chrome :global(.epoch-chip) {
		position: absolute;
		top: calc(100% + 0.35rem);
		right: 0;
	}

	.chat-scroll {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		padding: 6.25rem 0.75rem 0;
		scrollbar-gutter: stable;
	}

	.chat-content {
		padding-bottom: 1rem;
	}

	.composer-dock {
		flex-shrink: 0;
		padding: 0.5rem 0.75rem 0.85rem;
		background: linear-gradient(to top, var(--chora-bg) 75%, transparent);
	}

	.composer-meta {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		margin-bottom: 0.35rem;
		font-size: 0.75rem;
	}

	.cancel-reply {
		border: none;
		background: transparent;
		padding: 0;
		font-family: var(--chora-font-ui);
		font-size: 0.75rem;
		color: var(--chora-text-muted);
		text-decoration: underline;
		text-underline-offset: 0.15em;
	}

	.cancel-reply:hover {
		color: var(--chora-text);
	}

	.composer-status {
		margin: 0 0 0.35rem;
		font-family: var(--chora-font-ui);
		font-size: 0.8rem;
		color: var(--chora-text);
	}

	.composer-error {
		margin: 0 0 0.35rem;
		font-family: var(--chora-font-ui);
		font-size: 0.8rem;
		color: var(--chora-no);
	}

	.error {
		color: var(--chora-no);
		margin-bottom: 0.75rem;
	}

	@media (max-width: 640px) {
		.floating-chrome {
			grid-template-columns: 1fr 1fr;
			grid-template-areas:
				'brand auth'
				'nav nav';
			border-radius: calc(var(--chora-radius) + 4px);
			padding: 0.5rem 0.6rem;
		}

		.nav {
			justify-self: stretch;
			justify-content: center;
			flex-wrap: wrap;
		}

		.chat-scroll {
			padding-top: 7.5rem;
		}
	}
</style>
