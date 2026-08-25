/** Landing composer and thread-open helpers. Talking lives in threads. */

export const MONAD_REPLY_MISSING =
	'The Monad did not reply. The executive may be down — try again later.';

export function latestPrivateThread(threads) {
	if (!Array.isArray(threads) || threads.length === 0) return null;
	let best = null;
	for (const thread of threads) {
		if (!thread?.id || thread.visibility !== 'private') continue;
		if (!best || Number(thread.last_activity_at) >= Number(best.last_activity_at)) {
			best = thread;
		}
	}
	return best;
}

export function latestBroadcastId(broadcasts) {
	if (!Array.isArray(broadcasts) || broadcasts.length === 0) return null;
	let latest = broadcasts[0];
	for (const item of broadcasts) {
		if (Number(item.created_at) >= Number(latest.created_at)) {
			latest = item;
		}
	}
	return latest?.id || null;
}

/**
 * Decide how the Broadcast composer starts or continues a 1:1 thread.
 * Reply-to-a-broadcast always opens a new private thread for that post.
 * Otherwise continue the latest private thread, or open one from the latest
 * broadcast, or start a direct thread if the backend supports it.
 */
export function resolveLandingConversation(replyBroadcastId, threads, broadcasts) {
	if (replyBroadcastId) {
		return { action: 'open-from-broadcast', broadcastId: replyBroadcastId };
	}
	const existing = latestPrivateThread(threads);
	if (existing) {
		return { action: 'continue-thread', threadId: existing.id };
	}
	const broadcastId = latestBroadcastId(broadcasts);
	if (broadcastId) {
		return { action: 'open-from-broadcast', broadcastId };
	}
	return { action: 'start-direct' };
}

export function hasReplyAfter(messages, afterCount) {
	return (messages?.length ?? 0) > afterCount;
}

export function threadIdFromEvent(event) {
	const target = event?.target;
	if (!target || typeof target.closest !== 'function') return null;
	const row = target.closest('[data-thread-id]');
	return row?.getAttribute?.('data-thread-id') || null;
}

export function createThreadOpenHandler(onopenthread, debounceMs = 500) {
	let lastId = null;
	let lastAt = 0;
	return function handleThreadOpenEvent(event) {
		const id = threadIdFromEvent(event);
		if (!id) return false;
		const now = Date.now();
		if (id === lastId && now - lastAt < debounceMs) {
			return true;
		}
		lastId = id;
		lastAt = now;
		onopenthread?.(id);
		return true;
	};
}
