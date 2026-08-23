import './styles/global.css';
import { mount, unmount } from 'svelte';
import App from './App.svelte';

export interface MonadGosMountOptions {
	target: HTMLElement;
}

export function mountMonadGos({ target }: MonadGosMountOptions) {
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

export default mountMonadGos;

function autoMount() {
	const target =
		document.getElementById('monad-gos-root') ?? document.getElementById('app');
	if (target) {
		mountMonadGos({ target });
	}
}

if (typeof document !== 'undefined') {
	autoMount();
}
