import './styles/global.css';
import { mount, unmount } from 'svelte';
import App from './App.svelte';

export interface ChoraMountOptions {
	target: HTMLElement;
}

export function mountChora({ target }: ChoraMountOptions) {
	const component = mount(App, { target });
	return {
		unmount() {
			try {
				unmount(component);
			} catch {
				/* already torn down */
			}
		},
	};
}

export default mountChora;

function autoMount() {
	const target =
		document.getElementById('chora-root') ?? document.getElementById('app');
	if (target) {
		mountChora({ target });
	}
}

if (typeof document !== 'undefined') {
	autoMount();
}
