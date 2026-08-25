import { render } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import ThreadView from './ThreadView.svelte';

describe('ThreadView reply status', () => {
	it('shows a visible error when the executive does not reply', () => {
		const { getByRole } = render(ThreadView, {
			props: {
				thread: {
					id: 'thread-1',
					title: 'Direct',
					visibility: 'private',
					participant_count: 2,
					last_activity_at: 1,
					epoch: '0',
				},
				messages: [
					{
						id: 'm1',
						thread_id: 'thread-1',
						author: 'citizen',
						body: 'Hello',
						created_at: 1,
					},
				],
				awaitingMonad: false,
				error: 'The Monad did not reply. The executive may be down — try again later.',
			},
		});

		expect(getByRole('alert').textContent).toMatch(/executive may be down/i);
	});
});
