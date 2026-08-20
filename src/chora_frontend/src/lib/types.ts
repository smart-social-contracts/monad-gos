export type EpochPhase = 'converse' | 'sealed' | 'deliberate' | 'ratify' | 'execute';
export type ThreadVisibility = 'private' | 'public';
export type View = 'broadcast' | 'thread' | 'voting' | 'threads';

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
