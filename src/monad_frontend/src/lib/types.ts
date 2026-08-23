export type EpochPhase = 'converse' | 'sealed' | 'deliberate' | 'ratify' | 'execute';
export type ThreadVisibility = 'private' | 'public';
export type View = 'broadcast' | 'thread' | 'voting' | 'threads' | 'inputs' | 'settings' | 'realm';

export interface Treasury {
	name: string;
	balance: number;
	created_at: number;
	updated_at: number;
}

export interface BudgetLine {
	name: string;
	share_bps: number;
	allocated: number;
	spent: number;
	available: number;
}

export interface CodexMeta {
	version: string;
	source_url: string;
	commit: string;
	preamble: string;
}

export interface RealmState {
	treasury: Treasury;
	lines: BudgetLine[];
	membership_due: number;
	alignment: AlignmentCoefficient;
	epoch_id: string;
	codex: CodexMeta;
}

export type McpTokenScope = 'read' | 'full';

export interface McpTokenMeta {
	id: number;
	label: string;
	scope: McpTokenScope;
	created_at: string;
	expires_at?: string | null;
	last_used_at?: string | null;
}

export interface McpTokenCreated extends McpTokenMeta {
	token: string;
}

export interface ReplyInputs {
	message_id: string;
	thread_id: string;
	broadcast_id: string;
	kind: string;
	model: string;
	engine: string;
	engine_host: string;
	prompt: string;
	temperature: string;
	num_predict: number;
	seed: string;
	json_mode: boolean;
	created_at: number;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'error';

export interface EpochStatus {
	epoch_id: string;
	phase: EpochPhase;
	seal_at: number;
	seconds_until_seal: number;
}

export interface BroadcastMessage {
	id: string;
	author: string;
	body: string;
	epoch: string;
	created_at: number;
}

export interface ThreadSummary {
	id: string;
	title: string;
	participant_count: number;
	visibility: ThreadVisibility;
	last_activity_at: number;
	epoch: string;
}

export interface BroadcastFeed {
	broadcasts: BroadcastMessage[];
	public_threads: ThreadSummary[];
}

export interface ThreadMessage {
	id: string;
	thread_id: string;
	author: string;
	body: string;
	created_at: number;
}

export interface Thread extends ThreadSummary {
	broadcast_id?: string;
	messages: ThreadMessage[];
	created_at: number;
	updated_at: number;
}

export interface AlignmentCoefficient {
	coefficient: number;
	citizens_current: number;
	citizens_total: number;
	membership_due: number;
	as_of: number;
}

export interface AlignmentTrendPoint {
	epoch: string;
	coefficient: number;
	as_of: number;
}

export interface AlignmentData extends AlignmentCoefficient {
	trend: AlignmentTrendPoint[];
}

export interface ProposalView {
	id: string;
	title: string;
	description: string;
	status: string;
	votes_yes: number;
	votes_no: number;
	votes_abstain: number;
	justification: string;
	cost: string;
	who_loses: string;
	thread_ids: string[];
	voting_deadline?: string;
}

export interface SetupPersonality {
	voice: string;
	stance: string;
	principles: string[];
	description: string;
}

export interface SetupToken {
	mode: string;
	token_id: string;
	symbol: string;
	canister_id: string;
}

export interface SetupDraft {
	step: string;
	personality: SetupPersonality;
	token: SetupToken;
	logo_data_url: string;
}

export interface SetupState {
	entered: boolean;
	completed: boolean;
	is_caller_authorized: boolean;
	creator: string;
	registry_canister_id: string;
	completed_at: number;
	draft: SetupDraft;
	personality: SetupPersonality;
	token: SetupToken;
	logo_data_url: string;
}

export type SetupStep = 'welcome' | 'personality' | 'token' | 'branding' | 'launch';
