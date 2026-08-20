<script lang="ts">
	let {
		placeholder = 'Write to the Monad…',
		submitLabel = 'Send',
		disabled = false,
		fieldId = 'chora-composer',
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
		class="chora-textarea"
		placeholder={placeholder}
		bind:value={text}
		disabled={disabled || sending}
		rows="3"
	></textarea>
	<div class="actions">
		<button type="submit" class="chora-btn chora-btn-primary" disabled={disabled || sending || !text.trim()}>
			{sending ? 'Sending…' : submitLabel}
		</button>
	</div>
</form>

<style>
	.composer {
		margin-top: 1.5rem;
	}

	.actions {
		margin-top: 0.5rem;
		display: flex;
		justify-content: flex-end;
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
