<script lang="ts">
	let {
		message = 'Sign in to continue.',
		onlogin,
	}: {
		message?: string;
		onlogin?: () => void | Promise<void>;
	} = $props();
</script>

<p class="login-prompt">
	<span class="text monad-gos-muted">{message}</span>
	<button type="button" class="monad-gos-btn monad-gos-btn-ghost" onclick={() => onlogin?.()}>
		Sign in
	</button>
</p>

<style>
	.login-prompt {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin: 0.5rem 0 0;
		font-family: var(--monad-gos-font-ui);
		font-size: 0.85rem;
	}

	.text {
		font-size: 0.85rem;
	}
</style>
