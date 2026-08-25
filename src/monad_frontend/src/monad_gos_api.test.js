import { afterEach, describe, expect, it } from 'vitest';
import { MONAD_AUTHOR, resetMockThreads } from './lib/mock_data.js';
import {
	MONAD_REPLY_MISSING,
	readThread,
	replyToBroadcast,
	replyToThread,
	startThread,
	waitForNewMessage,
} from './monad_gos_api.js';

afterEach(() => {
	resetMockThreads();
});

describe('mock Monad reply path', () => {
	it('adds a visible Monad reply when sending in a thread', async () => {
		const before = await readThread('thread-1');
		const priorCount = before.messages.length;

		await replyToThread('thread-1', 'Can you lower the membership due?');

		const after = await readThread('thread-1');
		expect(after.messages.length).toBeGreaterThan(priorCount + 1);
		const newest = after.messages[after.messages.length - 1];
		expect(newest.author).toBe(MONAD_AUTHOR);
		expect(newest.body).toMatch(/not waiting for the seal/i);
	});

	it('opens a broadcast reply thread that already contains the Monad answer', async () => {
		const { thread_id } = await replyToBroadcast('broadcast-1', 'I want to talk now.');
		const data = await readThread(thread_id);
		expect(data.messages[0].body).toBe('I want to talk now.');
		expect(data.messages.some((message) => message.author === MONAD_AUTHOR)).toBe(true);
	});

	it('starts a direct thread without a broadcast and includes a Monad reply', async () => {
		const { thread_id } = await startThread('Hello Monad');
		const data = await readThread(thread_id);
		expect(data.thread.visibility).toBe('private');
		expect(data.messages.some((message) => message.author === MONAD_AUTHOR)).toBe(true);
	});

	it('waitForNewMessage returns immediately when the Monad reply is already present', async () => {
		const before = await readThread('thread-1');
		await replyToThread('thread-1', 'Please answer.');
		const latest = await waitForNewMessage('thread-1', before.messages.length + 1, 200, 20);
		expect(latest.messages.some((message) => message.author === MONAD_AUTHOR)).toBe(true);
	});

	it('surfaces a real error when no Monad reply arrives', async () => {
		const data = await readThread('thread-1');
		await expect(waitForNewMessage('thread-1', data.messages.length, 40, 10)).rejects.toThrow(
			MONAD_REPLY_MISSING,
		);
	});
});
