/**
 * Monad GOS backend client — GGG canister (ggg.did v0.2.0) plus Monad GOS admin extensions.
 *
 * Mock mode: VITE_MONAD_GOS_MOCK=true, or no canister ID when not portal-embedded.
 * Query calls use an anonymous agent; updates use the Internet Identity session.
 */
import { HttpAgent, Actor } from '@dfinity/agent';
import { IDL } from '@dfinity/candid';
import { getIdentity } from './lib/auth.js';
import { isEmbeddedInPortal } from './lib/portal-bridge.ts';
import { hasReplyAfter, MONAD_REPLY_MISSING } from './lib/conversation.js';
import { envForcesMock, inferCanisterIdFromHost } from './lib/runtime.js';
import {
	mockAlignment,
	mockBroadcast,
	mockEpochStatus,
	mockProposals,
	mockReplyInputs,
	mockThreads,
	MONAD_AUTHOR,
} from './lib/mock_data.js';

/** @type {string | null} */
let runtimeCanisterId = null;
/** @type {string | null} */
let runtimeHost = null;

export function configureMonadGosRuntime({ canisterId, host } = {}) {
	runtimeCanisterId = canisterId || null;
	runtimeHost = host || null;
	resetActors();
}

export function getCanisterId() {
	return runtimeCanisterId || inferCanisterIdFromHost() || '';
}

function getHost() {
	if (runtimeHost) return runtimeHost;
	if (typeof window !== 'undefined') {
		const { hostname } = window.location;
		if (
			isEmbeddedInPortal() &&
			(hostname.endsWith('.icp0.io') || hostname.endsWith('gos.earth'))
		) {
			return 'https://icp0.io';
		}
	}
	return import.meta.env.VITE_IC_HOST || 'http://127.0.0.1:4943';
}

export function isMockMode() {
	if (envForcesMock()) return true;
	if (isEmbeddedInPortal()) return false;
	return !getCanisterId();
}

const gggError = IDL.Variant({
	not_found: IDL.Null,
	unauthorized: IDL.Null,
	invalid_input: IDL.Text,
	conflict: IDL.Text,
	forbidden: IDL.Text,
});

/** GGG service IDL — slim scope used by the frontend. */
const gggIdlFactory = ({ IDL }) => {
	const ProposalStatus = IDL.Variant({
		pending_vote: IDL.Null,
		voting: IDL.Null,
		approved: IDL.Null,
		rejected: IDL.Null,
		no_quorum: IDL.Null,
		expired: IDL.Null,
	});
	const VoteChoice = IDL.Variant({
		yes: IDL.Null,
		no: IDL.Null,
		abstain: IDL.Null,
	});
	const ThreadVisibility = IDL.Text;
	const EpochPhase = IDL.Variant({
		converse: IDL.Null,
		sealed: IDL.Null,
		deliberate: IDL.Null,
		ratify: IDL.Null,
		execute: IDL.Null,
	});
	const AlignmentCoefficient = IDL.Record({
		coefficient: IDL.Float64,
		citizens_total: IDL.Nat,
		citizens_current: IDL.Nat,
		membership_due: IDL.Nat,
		as_of: IDL.Nat64,
	});
	const AlignmentTrendPoint = IDL.Record({
		epoch: IDL.Text,
		coefficient: IDL.Float64,
		as_of: IDL.Nat64,
	});
	const BroadcastMessage = IDL.Record({
		id: IDL.Text,
		author: IDL.Text,
		body: IDL.Text,
		epoch: IDL.Text,
		created_at: IDL.Nat64,
	});
	const ThreadSummary = IDL.Record({
		id: IDL.Text,
		title: IDL.Text,
		participant_count: IDL.Nat,
		visibility: ThreadVisibility,
		last_activity_at: IDL.Nat64,
		epoch: IDL.Text,
	});
	const BroadcastFeed = IDL.Record({
		broadcasts: IDL.Vec(BroadcastMessage),
		public_threads: IDL.Vec(ThreadSummary),
	});
	const ThreadMessage = IDL.Record({
		id: IDL.Text,
		thread_id: IDL.Text,
		author: IDL.Text,
		body: IDL.Text,
		created_at: IDL.Nat64,
	});
	const Thread = IDL.Record({
		id: IDL.Text,
		title: IDL.Text,
		visibility: ThreadVisibility,
		participant_count: IDL.Nat,
		epoch: IDL.Text,
		broadcast_id: IDL.Opt(IDL.Text),
		messages: IDL.Vec(ThreadMessage),
		created_at: IDL.Nat64,
		updated_at: IDL.Nat64,
	});
	const EpochStatus = IDL.Record({
		epoch_id: IDL.Text,
		phase: EpochPhase,
		seal_at: IDL.Nat64,
		seconds_until_seal: IDL.Nat,
	});
	const Proposal = IDL.Record({
		id: IDL.Text,
		title: IDL.Text,
		description: IDL.Text,
		code_url: IDL.Text,
		code_checksum: IDL.Text,
		proposer: IDL.Text,
		status: ProposalStatus,
		voting_deadline: IDL.Opt(IDL.Text),
		votes_yes: IDL.Nat,
		votes_no: IDL.Nat,
		votes_abstain: IDL.Nat,
		total_voters: IDL.Nat,
		required_threshold: IDL.Float64,
		org_scope: IDL.Text,
		metadata: IDL.Text,
		created_at: IDL.Nat64,
		updated_at: IDL.Nat64,
	});
	const ProposalFilter = IDL.Record({
		status: IDL.Opt(ProposalStatus),
		org_scope: IDL.Opt(IDL.Text),
		limit: IDL.Nat,
		offset: IDL.Nat,
	});
	const CastVoteInput = IDL.Record({
		proposal_id: IDL.Text,
		choice: VoteChoice,
		metadata: IDL.Text,
	});
	const SubmitWishInput = IDL.Record({
		domain: IDL.Text,
		ciphertext: IDL.Text,
		epoch: IDL.Text,
		assistant_id: IDL.Text,
	});
	const Result_VoteId = IDL.Variant({ ok: IDL.Text, err: gggError });
	const Result_WishId = IDL.Variant({ ok: IDL.Text, err: gggError });
	const Result = IDL.Variant({ ok: IDL.Null, err: gggError });
	const Result_ThreadId = IDL.Variant({ ok: IDL.Text, err: gggError });
	const Result_ThreadMessageId = IDL.Variant({ ok: IDL.Text, err: gggError });
	const Result_Text = IDL.Variant({ ok: IDL.Text, err: gggError });
	const Treasury = IDL.Record({
		name: IDL.Text,
		balance: IDL.Nat,
		created_at: IDL.Nat64,
		updated_at: IDL.Nat64,
	});
	const BudgetLine = IDL.Record({
		name: IDL.Text,
		share_bps: IDL.Nat,
		allocated: IDL.Nat,
		spent: IDL.Nat,
		available: IDL.Nat,
	});
	const CodexMeta = IDL.Record({
		version: IDL.Text,
		source_url: IDL.Text,
		commit: IDL.Text,
		preamble: IDL.Text,
	});
	const RealmState = IDL.Record({
		treasury: Treasury,
		lines: IDL.Vec(BudgetLine),
		membership_due: IDL.Nat,
		alignment: AlignmentCoefficient,
		epoch_id: IDL.Text,
		codex: CodexMeta,
	});
	const ReplyInputs = IDL.Record({
		message_id: IDL.Text,
		thread_id: IDL.Text,
		broadcast_id: IDL.Text,
		kind: IDL.Text,
		model: IDL.Text,
		engine: IDL.Text,
		engine_host: IDL.Text,
		prompt: IDL.Text,
		temperature: IDL.Text,
		num_predict: IDL.Nat,
		seed: IDL.Text,
		json_mode: IDL.Bool,
		created_at: IDL.Nat64,
		receipt_hash: IDL.Text,
	});
	const SetupPersonality = IDL.Record({
		voice: IDL.Text,
		stance: IDL.Text,
		principles: IDL.Vec(IDL.Text),
		description: IDL.Text,
	});
	const SetupToken = IDL.Record({
		mode: IDL.Text,
		token_id: IDL.Text,
		symbol: IDL.Text,
		canister_id: IDL.Text,
	});
	const SetupDraft = IDL.Record({
		step: IDL.Text,
		personality: SetupPersonality,
		token: SetupToken,
		logo_data_url: IDL.Text,
	});
	const SetupState = IDL.Record({
		entered: IDL.Bool,
		completed: IDL.Bool,
		is_caller_authorized: IDL.Bool,
		creator: IDL.Text,
		registry_canister_id: IDL.Text,
		completed_at: IDL.Nat64,
		draft: SetupDraft,
		personality: SetupPersonality,
		token: SetupToken,
		logo_data_url: IDL.Text,
	});

	return IDL.Service({
		ggg_version: IDL.Func([], [IDL.Text], ['query']),
		alignment_coefficient: IDL.Func([], [AlignmentCoefficient], ['query']),
		alignment_trend: IDL.Func([], [IDL.Vec(AlignmentTrendPoint)], ['query']),
		get_epoch_status: IDL.Func([], [EpochStatus], ['query']),
		read_broadcast: IDL.Func([], [BroadcastFeed], ['query']),
		list_threads: IDL.Func([], [IDL.Vec(ThreadSummary)], ['query']),
		read_thread: IDL.Func([IDL.Text], [IDL.Opt(Thread)], ['query']),
		submit_wish: IDL.Func([SubmitWishInput], [Result_WishId], []),
		reply_to_broadcast: IDL.Func([IDL.Text, IDL.Text], [Result_ThreadId], []),
		start_thread: IDL.Func([IDL.Text], [Result_ThreadId], []),
		reply_to_thread: IDL.Func([IDL.Text, IDL.Text], [Result_ThreadMessageId], []),
		list_proposals: IDL.Func([ProposalFilter], [IDL.Vec(Proposal)], ['query']),
		cast_vote: IDL.Func([CastVoteInput], [Result_VoteId], []),
		get_reply_inputs: IDL.Func([IDL.Text], [IDL.Opt(ReplyInputs)], ['query']),
		create_mcp_pairing: IDL.Func([], [Result_Text], []),
		verify_mcp_pairing: IDL.Func([IDL.Text], [IDL.Opt(IDL.Text)], ['query']),
		get_treasury: IDL.Func([IDL.Text], [IDL.Opt(Treasury)], ['query']),
		get_realm_state: IDL.Func([], [RealmState], ['query']),
		get_setup_state: IDL.Func([], [SetupState], ['query']),
		save_setup_draft: IDL.Func([SetupDraft], [Result], []),
		complete_setup: IDL.Func([], [Result], []),
		get_realm_logo: IDL.Func([], [IDL.Text], ['query']),
	});
};

/** @type {Promise<import('@dfinity/agent').ActorSubclass | null> | null} */
let queryActorPromise = null;
/** @type {Promise<import('@dfinity/agent').ActorSubclass | null> | null} */
let updateActorPromise = null;
/** @type {string | null} */
let queryIdentityKey = null;
/** @type {string | null} */
let updateIdentityKey = null;

export function resetActors() {
	queryActorPromise = null;
	updateActorPromise = null;
	queryIdentityKey = null;
	updateIdentityKey = null;
}

async function createAgent(identity) {
	const host = getHost();
	const agent = new HttpAgent({
		host,
		identity,
		verifyQuerySignatures: false,
	});
	// fetchRootKey is only for local replica — never on mainnet
	if (host.includes('127.0.0.1') || host.includes('localhost')) {
		await agent.fetchRootKey();
	}
	return agent;
}

function identityKey() {
	const identity = getIdentity();
	return identity?.getPrincipal().toText() ?? 'anonymous';
}

async function getQueryActor() {
	if (isMockMode()) return null;
	const identity = getIdentity();
	const principalKey = identityKey();
	if (!queryActorPromise || queryIdentityKey !== principalKey) {
		queryIdentityKey = principalKey;
		queryActorPromise = (async () => {
			const agent = await createAgent(identity);
			return Actor.createActor(gggIdlFactory, {
				agent,
				canisterId: getCanisterId(),
			});
		})();
	}
	return queryActorPromise;
}

async function getUpdateActor() {
	if (isMockMode()) return null;
	const identity = getIdentity();
	const principalKey = identity?.getPrincipal().toText() ?? 'anonymous';
	if (!updateActorPromise || updateIdentityKey !== principalKey) {
		updateIdentityKey = principalKey;
		updateActorPromise = (async () => {
			const agent = await createAgent(identity);
			return Actor.createActor(gggIdlFactory, {
				agent,
				canisterId: getCanisterId(),
			});
		})();
	}
	return updateActorPromise;
}

/** Lightweight health check — anonymous ggg_version query. */
export async function checkConnection() {
	if (isMockMode()) return { ok: true, version: 'mock' };
	try {
		const actor = await getQueryActor();
		const version = await actor.ggg_version();
		return { ok: true, version };
	} catch (e) {
		return {
			ok: false,
			error: e instanceof Error ? e.message : 'Connection failed',
		};
	}
}

function variantKey(value) {
	if (!value) return '';
	const keys = Object.keys(value);
	return keys[0] || '';
}

function mapThreadSummary(t) {
	return {
		id: t.id,
		title: t.title,
		participant_count: Number(t.participant_count),
		visibility: t.visibility,
		last_activity_at: Number(t.last_activity_at),
		epoch: t.epoch,
	};
}

function mapThreadMessage(m) {
	return {
		id: m.id,
		thread_id: m.thread_id,
		author: m.author,
		body: m.body,
		created_at: Number(m.created_at),
	};
}

function mapThread(t) {
	return {
		id: t.id,
		title: t.title,
		participant_count: Number(t.participant_count),
		visibility: t.visibility,
		epoch: t.epoch,
		last_activity_at: Number(t.updated_at),
		broadcast_id: t.broadcast_id?.[0],
		messages: t.messages.map(mapThreadMessage),
		created_at: Number(t.created_at),
		updated_at: Number(t.updated_at),
	};
}

function mapBroadcastMessage(b) {
	return {
		id: b.id,
		author: b.author,
		body: b.body,
		epoch: b.epoch,
		created_at: Number(b.created_at),
	};
}

function parseProposalMetadata(metadata) {
	const costMatch = metadata.match(/^cost:(.+)$/m);
	const justificationMatch = metadata.match(/^justification:(.+)$/m);
	const whoLosesMatch = metadata.match(/^who_loses:(.+)$/m);
	const threadIds = [...metadata.matchAll(/^thread_id:(.+)$/gm)].map((m) => m[1].trim());
	return {
		cost: costMatch?.[1]?.trim() || '',
		justification: justificationMatch?.[1]?.trim() || '',
		who_loses: whoLosesMatch?.[1]?.trim() || '',
		thread_ids: threadIds,
	};
}

function mapProposal(p) {
	const meta = parseProposalMetadata(p.metadata);
	return {
		id: p.id,
		title: p.title,
		description: p.description,
		status: variantKey(p.status),
		votes_yes: Number(p.votes_yes),
		votes_no: Number(p.votes_no),
		votes_abstain: Number(p.votes_abstain),
		justification: meta.justification || p.description,
		cost: meta.cost || '',
		who_loses: meta.who_loses || '',
		thread_ids: meta.thread_ids,
		voting_deadline: p.voting_deadline?.[0] || undefined,
	};
}

function delay(ms = 80) {
	return new Promise((r) => setTimeout(r, ms));
}

/** @returns {Promise<import('./lib/mock_data.js').EpochStatus>} */
export async function getEpochStatus() {
	if (isMockMode()) {
		await delay();
		const now = Math.floor(Date.now() / 1000);
		return {
			...mockEpochStatus,
			seconds_until_seal: Math.max(0, mockEpochStatus.seal_at - now),
		};
	}
	const actor = await getQueryActor();
	const raw = await actor.get_epoch_status();
	return {
		epoch_id: raw.epoch_id,
		phase: variantKey(raw.phase),
		seal_at: Number(raw.seal_at),
		seconds_until_seal: Number(raw.seconds_until_seal),
	};
}

function mapRealmState(raw) {
	return {
		treasury: {
			name: raw.treasury.name,
			balance: Number(raw.treasury.balance),
			created_at: Number(raw.treasury.created_at),
			updated_at: Number(raw.treasury.updated_at),
		},
		lines: raw.lines.map((line) => ({
			name: line.name,
			share_bps: Number(line.share_bps),
			allocated: Number(line.allocated),
			spent: Number(line.spent),
			available: Number(line.available),
		})),
		membership_due: Number(raw.membership_due),
		alignment: {
			coefficient: raw.alignment.coefficient,
			citizens_current: Number(raw.alignment.citizens_current),
			citizens_total: Number(raw.alignment.citizens_total),
			membership_due: Number(raw.alignment.membership_due),
			as_of: Number(raw.alignment.as_of),
		},
		epoch_id: raw.epoch_id,
		codex: {
			version: raw.codex.version,
			source_url: raw.codex.source_url,
			commit: raw.codex.commit,
			preamble: raw.codex.preamble,
		},
	};
}

export async function getRealmState() {
	if (isMockMode()) {
		await delay();
		return {
			treasury: { name: 'monad-gos', balance: 0, created_at: 0, updated_at: 0 },
			lines: [
				{ name: 'reserve', share_bps: 5000, allocated: 0, spent: 0, available: 0 },
				{ name: 'commons', share_bps: 3000, allocated: 0, spent: 0, available: 0 },
				{ name: 'operations', share_bps: 2000, allocated: 0, spent: 0, available: 0 },
			],
			membership_due: 12,
			alignment: structuredClone(mockAlignment),
			epoch_id: '0',
			codex: {
				version: '0.1.0',
				source_url: 'https://github.com/smart-social-contracts/monad-gos/blob/main/src/monad_backend/codex/codex.mo',
				commit: '',
				preamble: 'The Monad holds no purse of its own.',
			},
		};
	}
	const actor = await getQueryActor();
	return mapRealmState(await actor.get_realm_state());
}

/** @returns {Promise<import('./lib/mock_data.js').BroadcastFeed>} */
export async function readBroadcast() {
	if (isMockMode()) {
		await delay();
		return structuredClone(mockBroadcast);
	}
	const actor = await getQueryActor();
	const raw = await actor.read_broadcast();
	return {
		broadcasts: raw.broadcasts.map(mapBroadcastMessage),
		public_threads: raw.public_threads.map(mapThreadSummary),
	};
}

/** @returns {Promise<{ threads: import('./lib/mock_data.js').ThreadSummary[] }>} */
export async function listThreads() {
	if (isMockMode()) {
		await delay();
		return { threads: Object.values(mockThreads).map((t) => mapThreadSummary(t)) };
	}
	const actor = await getQueryActor();
	const raw = await actor.list_threads();
	return { threads: raw.map(mapThreadSummary) };
}

export function monadPrincipal() {
	return import.meta.env.VITE_MONAD_PRINCIPAL || '';
}

export { MONAD_REPLY_MISSING };

export async function waitForNewMessage(threadId, previousCount, timeoutMs = 45000, intervalMs = 2000) {
	const started = Date.now();
	const immediate = await readThread(threadId);
	if (hasReplyAfter(immediate.messages, previousCount)) {
		return immediate;
	}
	while (Date.now() - started < timeoutMs) {
		await new Promise((resolve) => setTimeout(resolve, intervalMs));
		const data = await readThread(threadId);
		if (hasReplyAfter(data.messages, previousCount)) {
			return data;
		}
	}
	throw new Error(MONAD_REPLY_MISSING);
}

function mapReplyInputs(inputs) {
	if (!inputs) return null;
	return {
		message_id: inputs.message_id,
		thread_id: inputs.thread_id,
		broadcast_id: inputs.broadcast_id,
		kind: inputs.kind,
		model: inputs.model,
		engine: inputs.engine,
		engine_host: inputs.engine_host,
		prompt: inputs.prompt,
		temperature: inputs.temperature,
		num_predict: Number(inputs.num_predict),
		seed: inputs.seed,
		json_mode: Boolean(inputs.json_mode),
		created_at: Number(inputs.created_at),
		receipt_hash: inputs.receipt_hash || '',
	};
}

export async function getReplyInputs(messageId) {
	if (isMockMode()) {
		await delay();
		return mapReplyInputs(mockReplyInputs[messageId] ?? null);
	}
	const actor = await getQueryActor();
	const raw = await actor.get_reply_inputs(messageId);
	return mapReplyInputs(raw[0]);
}

export async function readThread(threadId) {
	if (isMockMode()) {
		await delay();
		const entry = mockThreads[threadId];
		if (!entry) throw new Error(`Thread not found: ${threadId}`);
		const mapped = mapThread(entry);
		return {
			thread: mapped,
			messages: mapped.messages,
		};
	}
	const actor = await getQueryActor();
	const raw = await actor.read_thread(threadId);
	const thread = raw[0];
	if (!thread) throw new Error(`Thread not found: ${threadId}`);
	const mapped = mapThread(thread);
	return { thread: mapped, messages: mapped.messages };
}

/** @returns {Promise<import('./lib/mock_data.js').AlignmentData>} */
export async function alignmentCoefficient() {
	if (isMockMode()) {
		await delay();
		return structuredClone(mockAlignment);
	}
	const actor = await getQueryActor();
	const [snapshot, trend] = await Promise.all([
		actor.alignment_coefficient(),
		actor.alignment_trend(),
	]);
	return {
		coefficient: snapshot.coefficient,
		citizens_current: Number(snapshot.citizens_current),
		citizens_total: Number(snapshot.citizens_total),
		membership_due: Number(snapshot.membership_due),
		as_of: Number(snapshot.as_of),
		trend: trend.map((point) => ({
			epoch: point.epoch,
			coefficient: point.coefficient,
			as_of: Number(point.as_of),
		})),
	};
}

/** @returns {Promise<import('./lib/mock_data.js').ProposalView[]>} */
export async function listProposals() {
	if (isMockMode()) {
		await delay();
		return structuredClone(mockProposals);
	}
	const actor = await getQueryActor();
	const raw = await actor.list_proposals({
		status: [{ voting: null }],
		org_scope: [],
		limit: 50,
		offset: 0,
	});
	return raw.map(mapProposal);
}

/**
 * @param {string} domain
 * @param {string} body
 * @param {string} epoch
 */
export async function submitWish(domain, body, epoch) {
	if (isMockMode()) {
		await delay();
		return { wish_id: `wish-mock-${Date.now()}` };
	}
	const actor = await getUpdateActor();
	const result = await actor.submit_wish({
		domain,
		ciphertext: body,
		epoch,
		assistant_id: '',
	});
	if ('err' in result) {
		throw new Error(`submit_wish failed: ${JSON.stringify(result.err)}`);
	}
	return { wish_id: result.ok };
}

/**
 * @param {string} proposalId
 * @param {'yes' | 'no' | 'abstain'} choice
 */
export async function castVote(proposalId, choice) {
	if (isMockMode()) {
		await delay();
		const proposal = mockProposals.find((p) => p.id === proposalId);
		if (!proposal) throw new Error('Proposal not found');
		if (choice === 'yes') proposal.votes_yes += 1;
		else if (choice === 'no') proposal.votes_no += 1;
		else proposal.votes_abstain += 1;
		return { vote_id: `vote-mock-${Date.now()}` };
	}
	const actor = await getUpdateActor();
	const result = await actor.cast_vote({
		proposal_id: proposalId,
		choice: { [choice]: null },
		metadata: '',
	});
	if ('err' in result) {
		throw new Error(`cast_vote failed: ${JSON.stringify(result.err)}`);
	}
	return { vote_id: result.ok };
}

function mockThreadTitle(body) {
	return body.length > 48 ? `${body.slice(0, 48)}…` : body;
}

function appendMockCitizenMessage(entry, body) {
	const now = Math.floor(Date.now() / 1000);
	const message = {
		id: `msg-mock-${now}-${entry.messages.length}`,
		thread_id: entry.id,
		author: 'citizen-mock',
		body,
		created_at: now,
	};
	entry.messages.push(message);
	entry.updated_at = now;
	entry.last_activity_at = now;
	entry.participant_count = Math.max(entry.participant_count, 1);
	return message;
}

function appendMockMonadReply(entry, citizenBody) {
	const now = Math.floor(Date.now() / 1000);
	const excerpt = citizenBody.trim().slice(0, 72);
	const message = {
		id: `msg-mock-${now}-${entry.messages.length}`,
		thread_id: entry.id,
		author: MONAD_AUTHOR,
		body: excerpt
			? `I hear you. I am answering in this thread now — not waiting for the seal: ${excerpt}`
			: 'I hear you. I am answering in this thread now — not waiting for the seal.',
		created_at: now,
	};
	entry.messages.push(message);
	entry.updated_at = now;
	entry.last_activity_at = now;
	entry.participant_count = Math.max(entry.participant_count, 2);
	mockReplyInputs[message.id] = {
		message_id: message.id,
		thread_id: entry.id,
		broadcast_id: entry.broadcast_id || '',
		kind: 'thread',
		model: 'mock',
		engine: 'mock',
		engine_host: 'local',
		prompt: `You are the Monad of this Monad GOS realm.\n\nConversation so far:\nCitizen: ${citizenBody}\n\nMonad:`,
		temperature: '0',
		num_predict: 0,
		seed: '0',
		json_mode: false,
		created_at: now,
		receipt_hash: `sha256:mock-${message.id}`,
	};
	return message;
}

function createMockPrivateThread(body, broadcastId) {
	const threadId = `thread-private-${Date.now()}`;
	const now = Math.floor(Date.now() / 1000);
	const entry = {
		id: threadId,
		title: mockThreadTitle(body),
		visibility: 'private',
		participant_count: 1,
		epoch: mockEpochStatus.epoch_id,
		broadcast_id: broadcastId,
		created_at: now,
		updated_at: now,
		last_activity_at: now,
		messages: [],
	};
	appendMockCitizenMessage(entry, body);
	appendMockMonadReply(entry, body);
	mockThreads[threadId] = entry;
	return threadId;
}

/**
 * @param {string} broadcastId
 * @param {string} body
 */
export async function replyToBroadcast(broadcastId, body) {
	if (isMockMode()) {
		await delay();
		return { thread_id: createMockPrivateThread(body, broadcastId) };
	}
	const actor = await getUpdateActor();
	const result = await actor.reply_to_broadcast(broadcastId, body);
	if ('err' in result) {
		throw new Error(`reply_to_broadcast failed: ${JSON.stringify(result.err)}`);
	}
	return { thread_id: result.ok };
}

/**
 * Start a private citizen↔Monad thread without tying it to a broadcast.
 * @param {string} body
 */
export async function startThread(body) {
	if (isMockMode()) {
		await delay();
		return { thread_id: createMockPrivateThread(body) };
	}
	const actor = await getUpdateActor();
	if (typeof actor.start_thread !== 'function') {
		throw new Error('Direct threads are not available on this backend yet.');
	}
	const result = await actor.start_thread(body);
	if ('err' in result) {
		throw new Error(`start_thread failed: ${JSON.stringify(result.err)}`);
	}
	return { thread_id: result.ok };
}

/**
 * @param {string} threadId
 * @param {string} body
 */
export async function replyToThread(threadId, body) {
	if (isMockMode()) {
		await delay();
		const entry = mockThreads[threadId];
		if (!entry) throw new Error('Thread not found');
		const citizen = appendMockCitizenMessage(entry, body);
		appendMockMonadReply(entry, body);
		return { message_id: citizen.id };
	}
	const actor = await getUpdateActor();
	const result = await actor.reply_to_thread(threadId, body);
	if ('err' in result) {
		throw new Error(`reply_to_thread failed: ${JSON.stringify(result.err)}`);
	}
	return { message_id: result.ok };
}

export async function createMcpPairing() {
	if (isMockMode()) {
		await delay();
		return 'mcp_mock_pairing';
	}
	const actor = await getUpdateActor();
	const result = await actor.create_mcp_pairing();
	if ('err' in result) {
		throw new Error(`create_mcp_pairing failed: ${JSON.stringify(result.err)}`);
	}
	return result.ok;
}

export function getConfig() {
	return {
		mock: isMockMode(),
		canisterId: getCanisterId(),
		host: getHost(),
	};
}

function emptySetupDraft() {
	return {
		step: 'welcome',
		personality: {
			voice: '',
			stance: '',
			principles: [],
			description: '',
		},
		token: {
			mode: 'none',
			token_id: '',
			symbol: '',
			canister_id: '',
		},
		logo_data_url: '',
	};
}

function mapSetupPersonality(raw) {
	return {
		voice: raw.voice,
		stance: raw.stance,
		principles: [...raw.principles],
		description: raw.description,
	};
}

function mapSetupToken(raw) {
	return {
		mode: raw.mode,
		token_id: raw.token_id,
		symbol: raw.symbol,
		canister_id: raw.canister_id,
	};
}

function mapSetupDraft(raw) {
	return {
		step: raw.step,
		personality: mapSetupPersonality(raw.personality),
		token: mapSetupToken(raw.token),
		logo_data_url: raw.logo_data_url,
	};
}

function mapSetupState(raw) {
	return {
		entered: Boolean(raw.entered),
		completed: Boolean(raw.completed),
		is_caller_authorized: Boolean(raw.is_caller_authorized),
		creator: raw.creator,
		registry_canister_id: raw.registry_canister_id,
		completed_at: Number(raw.completed_at),
		draft: mapSetupDraft(raw.draft),
		personality: mapSetupPersonality(raw.personality),
		token: mapSetupToken(raw.token),
		logo_data_url: raw.logo_data_url,
	};
}

function toSetupDraftRaw(draft) {
	return {
		step: draft.step,
		personality: {
			voice: draft.personality.voice,
			stance: draft.personality.stance,
			principles: draft.personality.principles,
			description: draft.personality.description,
		},
		token: {
			mode: draft.token.mode,
			token_id: draft.token.token_id,
			symbol: draft.token.symbol,
			canister_id: draft.token.canister_id,
		},
		logo_data_url: draft.logo_data_url,
	};
}

/** @returns {Promise<import('./lib/types.ts').SetupState>} */
export async function getSetupState() {
	if (isMockMode()) {
		await delay();
		const draft = emptySetupDraft();
		return {
			entered: false,
			completed: true,
			is_caller_authorized: true,
			creator: '',
			registry_canister_id: '',
			completed_at: 0,
			draft,
			personality: draft.personality,
			token: draft.token,
			logo_data_url: '',
		};
	}
	const actor = await getQueryActor();
	return mapSetupState(await actor.get_setup_state());
}

/** @param {import('./lib/types.ts').SetupDraft} draft */
export async function saveSetupDraft(draft) {
	if (isMockMode()) return;
	const actor = await getUpdateActor();
	const result = await actor.save_setup_draft(toSetupDraftRaw(draft));
	if ('err' in result) {
		throw new Error(`save_setup_draft failed: ${JSON.stringify(result.err)}`);
	}
}

export async function completeSetup() {
	if (isMockMode()) return;
	const actor = await getUpdateActor();
	const result = await actor.complete_setup();
	if ('err' in result) {
		throw new Error(`complete_setup failed: ${JSON.stringify(result.err)}`);
	}
}

export async function getRealmLogo() {
	if (isMockMode()) {
		await delay();
		return '';
	}
	const actor = await getQueryActor();
	return await actor.get_realm_logo();
}
