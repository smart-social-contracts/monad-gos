<script lang="ts">
	let {
		placeholder = 'Write to the Monad…',
		submitLabel = 'Send',
		disabled = false,
		fieldId = 'monad-gos-composer',
		onsubmit,
	}: {
		placeholder?: string;
		submitLabel?: string;
		disabled?: boolean;
		fieldId?: string;
		onsubmit?: (body: string) => void | Promise<void>;
	} = $props();

	let text = $state('');
	let sending = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		const body = text.trim();
		if (!body || sending || disabled) return;
		sending = true;
		try {
			await onsubmit?.(body);
			text = '';
		} finally {
			sending = false;
		}
	}
</script>

<form class="composer" onsubmit={handleSubmit}>
	<label class="sr-only" for={fieldId}>Message</label>
	<textarea
		id={fieldId}
		class="composer-input"
		placeholder={placeholder}
		bind:value={text}
		disabled={disabled || sending}
		rows="1"
	></textarea>
	<button
		type="submit"
		class="monad-gos-btn monad-gos-btn-primary composer-send"
		disabled={disabled || sending || !text.trim()}
	>
		{sending ? '…' : submitLabel}
	</button>
</form>

<style>
	.composer {
		display: flex;
		align-items: flex-end;
		gap: 0.5rem;
		margin: 0;
		padding: 0.55rem 0.65rem;
		border: 1px solid var(--monad-gos-border);
		border-radius: calc(var(--monad-gos-radius) + 2px);
		background: var(--monad-gos-surface);
	}

	.composer-input {
		flex: 1;
		min-width: 0;
		min-height: 2.25rem;
		max-height: 6rem;
		padding: 0.45rem 0.5rem;
		border: none;
		border-radius: var(--monad-gos-radius);
		background: transparent;
		font-family: var(--monad-gos-font);
		font-size: 0.95rem;
		line-height: 1.45;
		resize: none;
	}

	.composer-input:focus {
		outline: none;
	}

	.composer-send {
		flex-shrink: 0;
		padding: 0.4rem 0.75rem;
		font-size: 0.8rem;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		border: 0;
	}
</style>
