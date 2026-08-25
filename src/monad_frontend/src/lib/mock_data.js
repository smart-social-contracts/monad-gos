/** @typedef {'converse' | 'sealed' | 'deliberate' | 'ratify' | 'execute'} EpochPhase */
/** @typedef {'private' | 'public'} ThreadVisibility */

/**
 * @typedef {object} EpochStatus
 * @property {string} epoch_id
 * @property {EpochPhase} phase
 * @property {number} seal_at
 * @property {number} seconds_until_seal
 */

/**
 * @typedef {object} BroadcastMessage
 * @property {string} id
 * @property {string} author
 * @property {string} body
 * @property {string} epoch
 * @property {number} created_at
 */

/**
 * @typedef {object} ThreadSummary
 * @property {string} id
 * @property {string} title
 * @property {number} participant_count
 * @property {ThreadVisibility} visibility
 * @property {number} last_activity_at
 * @property {string} epoch
 */

/**
 * @typedef {object} BroadcastFeed
 * @property {BroadcastMessage[]} broadcasts
 * @property {ThreadSummary[]} public_threads
 */

/**
 * @typedef {object} ThreadMessage
 * @property {string} id
 * @property {string} thread_id
 * @property {string} author
 * @property {string} body
 * @property {number} created_at
 */

/**
 * @typedef {object} Thread
 * @property {string} id
 * @property {string} title
 * @property {ThreadVisibility} visibility
 * @property {number} participant_count
 * @property {string} epoch
 * @property {string} [broadcast_id]
 * @property {ThreadMessage[]} messages
 * @property {number} created_at
 * @property {number} updated_at
 */

/**
 * @typedef {object} AlignmentCoefficient
 * @property {number} coefficient
 * @property {number} citizens_current
 * @property {number} citizens_total
 * @property {number} membership_due
 * @property {number} as_of
 */

/**
 * @typedef {object} AlignmentTrendPoint
 * @property {string} epoch
 * @property {number} coefficient
 * @property {number} as_of
 */

/**
 * @typedef {AlignmentCoefficient & { trend: AlignmentTrendPoint[] }} AlignmentData
 */

/**
 * @typedef {object} ProposalView
 * @property {string} id
 * @property {string} title
 * @property {string} description
 * @property {string} status
 * @property {number} votes_yes
 * @property {number} votes_no
 * @property {number} votes_abstain
 * @property {string} justification
 * @property {string} cost
 * @property {string} who_loses
 * @property {string[]} thread_ids
 * @property {string} [voting_deadline]
 */

const NOW = Math.floor(Date.now() / 1000);
const EPOCH_ID = '0';
const MONAD_AUTHOR = 'aaaaa-aa';

/** @type {EpochStatus} */
export const mockEpochStatus = {
	epoch_id: EPOCH_ID,
	phase: 'converse',
	seal_at: NOW + 4 * 3600 + 22 * 60,
	seconds_until_seal: 4 * 3600 + 22 * 60,
};

/** @type {BroadcastFeed} */
export const mockBroadcast = {
	broadcasts: [
		{
			id: 'broadcast-1',
			author: MONAD_AUTHOR,
			body:
				'Citizens, this epoch I have been listening. The treasury holds enough for two modest proposals if we stay aligned. Water fees remain the loudest wish — I hear it in finance and land alike. I will not act until the seal; until then, speak plainly.',
			created_at: NOW - 7200,
			epoch: EPOCH_ID,
		},
		{
			id: 'broadcast-2',
			author: MONAD_AUTHOR,
			body:
				'On the east quarter path: three citizens asked for clarification on the membership due. I set it at 12 credits per month. Paying keeps you current; withholding is a legitimate signal, not exile. I will answer questions in thread.',
			created_at: NOW - 3600,
			epoch: EPOCH_ID,
		},
		{
			id: 'broadcast-3',
			author: MONAD_AUTHOR,
			body:
				'From the last epoch I drafted two proposals on water infrastructure. Voting is open in the voting area. Read the threads first — the deliberation is on the record.',
			created_at: NOW - 1800,
			epoch: EPOCH_ID,
		},
	],
	public_threads: [
		{
			id: 'thread-1',
			title: 'Membership due — questions',
			participant_count: 3,
			visibility: 'public',
			last_activity_at: NOW - 2400,
			epoch: EPOCH_ID,
		},
		{
			id: 'thread-2',
			title: 'East quarter water fees',
			participant_count: 4,
			visibility: 'public',
			last_activity_at: NOW - 5400,
			epoch: EPOCH_ID,
		},
	],
};

/** @type {Record<string, Thread>} */
export const mockThreads = {
	'thread-1': {
		...mockBroadcast.public_threads[0],
		broadcast_id: 'broadcast-2',
		created_at: NOW - 3000,
		updated_at: NOW - 2400,
		messages: [
			{
				id: 'msg-1',
				thread_id: 'thread-1',
				author: 'citizen-1',
				body: 'Why 12 credits? Last epoch it was 10.',
				created_at: NOW - 3000,
			},
			{
				id: 'msg-2',
				thread_id: 'thread-1',
				author: MONAD_AUTHOR,
				body:
					'The treasury forecast for pipe repair is higher. I raised the due modestly so alignment still funds the work without a separate levy. If citizens withhold, I will see it in the coefficient before I spend.',
				created_at: NOW - 2800,
			},
			{
				id: 'msg-3',
				thread_id: 'thread-1',
				author: 'citizen-2',
				body: 'Fair. I can live with 12 if the east path is first.',
				created_at: NOW - 2600,
			},
			{
				id: 'msg-4',
				thread_id: 'thread-1',
				author: MONAD_AUTHOR,
				body: 'East path is first in the draft proposal. The critic argued for west — I weighed both in the sealed record.',
				created_at: NOW - 2500,
			},
			{
				id: 'msg-5',
				thread_id: 'thread-1',
				author: 'system',
				body: 'Thread opened from broadcast.',
				created_at: NOW - 2400,
			},
		],
	},
	'thread-2': {
		...mockBroadcast.public_threads[1],
		created_at: NOW - 6000,
		updated_at: NOW - 5400,
		messages: [
			{
				id: 'msg-w1',
				thread_id: 'thread-2',
				author: 'citizen-3',
				body: 'The east path flooding is worse after last rain. We need metering, not another lecture.',
				created_at: NOW - 6000,
			},
			{
				id: 'msg-w2',
				thread_id: 'thread-2',
				author: MONAD_AUTHOR,
				body:
					'I hear urgency. Metering is in the draft — but someone on the west path loses priority if we only fund east. That tension is why it goes to vote, not decree.',
				created_at: NOW - 5800,
			},
			{
				id: 'msg-w3',
				thread_id: 'thread-2',
				author: 'citizen-4',
				body: 'West can wait one epoch. East is unsafe.',
				created_at: NOW - 5600,
			},
		],
	},
	'thread-private-new': {
		id: 'thread-private-new',
		title: 'Your reply to the Monad',
		visibility: 'private',
		participant_count: 2,
		epoch: EPOCH_ID,
		broadcast_id: 'broadcast-1',
		created_at: NOW - 120,
		updated_at: NOW - 60,
		last_activity_at: NOW - 60,
		messages: [
			{
				id: 'msg-p1',
				thread_id: 'thread-private-new',
				author: 'citizen-5',
				body: 'I want the membership due lowered until east path is fixed.',
				created_at: NOW - 120,
			},
			{
				id: 'msg-p2',
				thread_id: 'thread-private-new',
				author: MONAD_AUTHOR,
				body:
					'Lowering the due would shrink the treasury that pays for the path. I understand the frustration — would a one-month pause for east-quarter residents be enough, or do you want a realm-wide cut?',
				created_at: NOW - 60,
			},
		],
	},
};

/** @type {AlignmentData} */
export const mockAlignment = {
	coefficient: 0.847,
	citizens_current: 847,
	citizens_total: 1000,
	membership_due: 12,
	as_of: NOW,
	trend: [
		{ epoch: '-7', coefficient: 0.812, as_of: NOW - 7 * 86400 },
		{ epoch: '-6', coefficient: 0.821, as_of: NOW - 6 * 86400 },
		{ epoch: '-5', coefficient: 0.828, as_of: NOW - 5 * 86400 },
		{ epoch: '-4', coefficient: 0.835, as_of: NOW - 4 * 86400 },
		{ epoch: '-3', coefficient: 0.839, as_of: NOW - 3 * 86400 },
		{ epoch: '-2', coefficient: 0.843, as_of: NOW - 2 * 86400 },
		{ epoch: '-1', coefficient: 0.845, as_of: NOW - 86400 },
		{ epoch: EPOCH_ID, coefficient: 0.847, as_of: NOW },
	],
};

/** @type {ProposalView[]} */
export const mockProposals = [
	{
		id: 'proposal-1',
		title: 'Meter east quarter water usage',
		description:
			'Install meters on the east path mains and bill usage at 0.4 credits per cubic meter.',
		status: 'voting',
		votes_yes: 412,
		votes_no: 98,
		votes_abstain: 34,
		justification:
			'Sealed wishes and public thread show east flooding and unfair flat fees. Metering ties cost to use.',
		cost: '4,200 credits from treasury',
		who_loses: 'West quarter — deferred priority; flat-fee households pay more if they use heavily',
		thread_ids: ['thread-2'],
		voting_deadline: '2026-08-26T18:00:00Z',
	},
	{
		id: 'proposal-2',
		title: 'Emergency pipe repair fund',
		description: 'Allocate 1,800 credits for immediate east path pipe repair before winter.',
		status: 'voting',
		votes_yes: 501,
		votes_no: 67,
		votes_abstain: 22,
		justification: 'Oracle rainfall data and citizen reports name a burst risk on the east main.',
		cost: '1,800 credits from treasury',
		who_loses: 'Other capital projects this epoch — playground and west lighting slip',
		thread_ids: ['thread-2', 'thread-1'],
		voting_deadline: '2026-08-26T18:00:00Z',
	},
];

/**
 * @typedef {object} ReplyInputs
 * @property {string} message_id
 * @property {string} thread_id
 * @property {string} broadcast_id
 * @property {string} kind
 * @property {string} model
 * @property {string} engine
 * @property {string} engine_host
 * @property {string} prompt
 * @property {string} temperature
 * @property {number} num_predict
 * @property {string} seed
 * @property {boolean} json_mode
 * @property {number} created_at
 * @property {string} receipt_hash
 */

function mockReceipt(partial) {
	return {
		engine: 'mock',
		engine_host: 'local',
		model: 'mock',
		temperature: '0',
		num_predict: 0,
		seed: '0',
		json_mode: false,
		created_at: NOW - 1800,
		...partial,
	};
}

/** @type {Record<string, ReplyInputs>} */
export const mockReplyInputs = {
	'broadcast-1': mockReceipt({
		message_id: 'broadcast-1',
		thread_id: '',
		broadcast_id: 'broadcast-1',
		kind: 'broadcast',
		prompt:
			'Public legislative input. Epoch 0 broadcast. Treasury holds enough for two modest proposals. Water fees remain the loudest wish.',
		receipt_hash: 'sha256:a744b626a3d970578304f4b6735e71f4a1489df7850dc98ad627a0c04eee30df',
		created_at: NOW - 7200,
	}),
	'broadcast-2': mockReceipt({
		message_id: 'broadcast-2',
		thread_id: '',
		broadcast_id: 'broadcast-2',
		kind: 'broadcast',
		prompt:
			'Public legislative input. Membership due is 12 credits per month. Paying keeps you current; withholding is a legitimate signal.',
		receipt_hash: 'sha256:52cd0ea65006be445e82e99e2fae162d047229e417125e6de82f800e0d14c9ec',
		created_at: NOW - 3600,
	}),
	'broadcast-3': mockReceipt({
		message_id: 'broadcast-3',
		thread_id: '',
		broadcast_id: 'broadcast-3',
		kind: 'broadcast',
		prompt:
			'Public legislative input. Two proposals on water infrastructure from the last epoch. Voting is open.',
		receipt_hash: 'sha256:0ed5b8e80890a1f45797089f9db84f2dc16deb5eb431a892ad22d3693a0dac87',
	}),
	'msg-2': mockReceipt({
		message_id: 'msg-2',
		thread_id: 'thread-1',
		broadcast_id: 'broadcast-2',
		kind: 'thread',
		prompt:
			'You are the Monad of this Monad GOS realm.\n\nConversation so far:\nCitizen: Why 12 credits? Last epoch it was 10.\n\nMonad:',
		receipt_hash: 'sha256:af8ab9797d029abe886c0da047c150b84910e98b92bf9f1555081a6d5461a771',
		created_at: NOW - 2800,
	}),
	'msg-4': mockReceipt({
		message_id: 'msg-4',
		thread_id: 'thread-1',
		broadcast_id: 'broadcast-2',
		kind: 'thread',
		prompt:
			'You are the Monad of this Monad GOS realm.\n\nConversation so far:\nCitizen: Why 12 credits? Last epoch it was 10.\nMonad: The treasury forecast for pipe repair is higher.\nCitizen: Fair. I can live with 12 if the east path is first.\n\nMonad:',
		receipt_hash: 'sha256:5e0b6aedaab9aad6bb941daf4e41bc37ec7713a6d17a9604629496b909e80726',
		created_at: NOW - 2500,
	}),
	'msg-w2': mockReceipt({
		message_id: 'msg-w2',
		thread_id: 'thread-2',
		broadcast_id: '',
		kind: 'thread',
		prompt:
			'You are the Monad of this Monad GOS realm.\n\nConversation so far:\nCitizen: The east path flooding is worse after last rain.\n\nMonad:',
		receipt_hash: 'sha256:516a16c1bf7c9f367772c0cf50528c2ac27bd593061b0f4e2cbe9b4e5c975177',
		created_at: NOW - 5800,
	}),
	'msg-p2': mockReceipt({
		message_id: 'msg-p2',
		thread_id: 'thread-private-new',
		broadcast_id: 'broadcast-1',
		kind: 'thread',
		prompt:
			'You are the Monad of this Monad GOS realm.\n\nConversation so far:\nCitizen: I want the membership due lowered until east path is fixed.\n\nMonad:',
		receipt_hash: 'sha256:65acbc793cbbd49e539704a1895dc2af691516c7a5ae3c697a4362f68b79eb7b',
		created_at: NOW - 60,
	}),
};
