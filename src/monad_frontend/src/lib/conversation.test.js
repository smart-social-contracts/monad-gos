import { describe, expect, it, vi } from 'vitest';
import {
	createThreadOpenHandler,
	hasReplyAfter,
	latestBroadcastId,
	latestPrivateThread,
	MONAD_REPLY_MISSING,
	resolveLandingConversation,
	threadIdFromEvent,
} from './conversation.js';

const privateRecent = {
	id: 'thread-private-2',
	visibility: 'private',
	last_activity_at: 200,
};
const privateOlder = {
	id: 'thread-private-1',
	visibility: 'private',
	last_activity_at: 100,
};
const publicThread = {
	id: 'thread-public',
	visibility: 'public',
	last_activity_at: 300,
};

describe('resolveLandingConversation', () => {
	it('opens a new thread when Replying to a broadcast', () => {
		expect(
			resolveLandingConversation('broadcast-2', [privateRecent], [{ id: 'broadcast-1', created_at: 1 }]),
		).toEqual({ action: 'open-from-broadcast', broadcastId: 'broadcast-2' });
	});

	it('continues the latest private thread from the landing composer', () => {
		expect(resolveLandingConversation(null, [privateOlder, publicThread, privateRecent], [])).toEqual({
			action: 'continue-thread',
			threadId: 'thread-private-2',
		});
	});

	it('opens a thread from the latest broadcast when no private thread exists', () => {
		expect(
			resolveLandingConversation(null, [publicThread], [
				{ id: 'broadcast-1', created_at: 10 },
				{ id: 'broadcast-3', created_at: 30 },
				{ id: 'broadcast-2', created_at: 20 },
			]),
		).toEqual({ action: 'open-from-broadcast', broadcastId: 'broadcast-3' });
	});

	it('starts a direct thread when there is no broadcast to reply to', () => {
		expect(resolveLandingConversation(null, [], [])).toEqual({ action: 'start-direct' });
	});

	it('never seals a wish from the landing composer', () => {
		for (const decision of [
			resolveLandingConversation('broadcast-1', [], [{ id: 'broadcast-1', created_at: 1 }]),
			resolveLandingConversation(null, [privateRecent], []),
			resolveLandingConversation(null, [], [{ id: 'broadcast-1', created_at: 1 }]),
			resolveLandingConversation(null, [], []),
		]) {
			expect(decision.action).not.toMatch(/wish/i);
		}
	});
});

describe('thread open events', () => {
	it('reads the thread id from a nested tap target', () => {
		const button = document.createElement('button');
		button.setAttribute('data-thread-id', 'thread-1');
		const title = document.createElement('span');
		title.textContent = 'Membership due';
		button.appendChild(title);
		expect(threadIdFromEvent({ target: title })).toBe('thread-1');
	});

	it('opens on the first click and ignores a ghost second click', () => {
		const onopenthread = vi.fn();
		const handle = createThreadOpenHandler(onopenthread, 500);
		const button = document.createElement('button');
		button.setAttribute('data-thread-id', 'thread-9');
		handle({ target: button });
		handle({ target: button });
		expect(onopenthread).toHaveBeenCalledTimes(1);
		expect(onopenthread).toHaveBeenCalledWith('thread-9');
	});
});

describe('reply detection', () => {
	it('treats a longer message list as a visible reply', () => {
		expect(hasReplyAfter([{ id: 'a' }, { id: 'b' }], 1)).toBe(true);
		expect(hasReplyAfter([{ id: 'a' }], 1)).toBe(false);
	});

	it('exports a visible executive-down error', () => {
		expect(MONAD_REPLY_MISSING).toMatch(/executive may be down/i);
	});
});

describe('latest helpers', () => {
	it('ignores public threads when finding a continuable conversation', () => {
		expect(latestPrivateThread([publicThread])).toBeNull();
		expect(latestPrivateThread([publicThread, privateOlder])?.id).toBe('thread-private-1');
	});

	it('picks the newest broadcast', () => {
		expect(
			latestBroadcastId([
				{ id: 'old', created_at: 1 },
				{ id: 'new', created_at: 9 },
			]),
		).toBe('new');
	});
});
