import { render, fireEvent } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import ThreadsList from './ThreadsList.svelte';

const threads = [
	{
		id: 'thread-1',
		title: 'Membership due — questions',
		participant_count: 3,
		visibility: 'private',
		last_activity_at: 1,
		epoch: '0',
	},
	{
		id: 'thread-2',
		title: 'East quarter water fees',
		participant_count: 4,
		visibility: 'public',
		last_activity_at: 2,
		epoch: '0',
	},
];

describe('ThreadsList tap', () => {
	it('opens the thread on a single click of the row title', async () => {
		const onopenthread = vi.fn();
		const { getByText } = render(ThreadsList, {
			props: { threads, onopenthread },
		});

		await fireEvent.click(getByText('Membership due — questions'));

		expect(onopenthread).toHaveBeenCalledTimes(1);
		expect(onopenthread).toHaveBeenCalledWith('thread-1');
	});

	it('opens from a click on the nested meta line', async () => {
		const onopenthread = vi.fn();
		const { getByText } = render(ThreadsList, {
			props: { threads, onopenthread },
		});

		await fireEvent.click(getByText('4 participants · public'));

		expect(onopenthread).toHaveBeenCalledTimes(1);
		expect(onopenthread).toHaveBeenCalledWith('thread-2');
	});
});
