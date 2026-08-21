<script lang="ts">
	import { untrack } from 'svelte';
	import type { SetupDraft, SetupStep } from '../lib/types';
	import { completeSetup, saveSetupDraft } from '../chora_api.js';

	let {
		draft,
		oncomplete,
	}: {
		draft: SetupDraft;
		oncomplete?: () => void | Promise<void>;
	} = $props();

	const STEPS: SetupStep[] = ['welcome', 'personality', 'token', 'branding', 'launch'];

	const STEP_LABELS: Record<SetupStep, string> = {
		welcome: 'Welcome',
		personality: 'Personality',
		token: 'Token',
		branding: 'Branding',
		launch: 'Launch',
	};

	const VOICES = [
		{ id: 'austere', label: 'Austere' },
		{ id: 'warm', label: 'Warm' },
		{ id: 'playful', label: 'Playful' },
	];

	const STANCES = [
		{ id: 'preserve', label: 'Preserve' },
		{ id: 'balance', label: 'Balance' },
		{ id: 'experiment', label: 'Experiment' },
	];

	const PRINCIPLES = [
		{ id: 'treasury_honesty', label: 'Treasury honesty' },
		{ id: 'exit_is_voice', label: 'Exit is voice' },
		{ id: 'propose_never_write', label: 'Propose, never write' },
		{ id: 'short_replies', label: 'Short replies' },
		{ id: 'cite_codex', label: 'Cite the Codex' },
		{ id: 'no_private_deals', label: 'No private deals' },
		{ id: 'maximize_alignment', label: 'Maximize alignment' },
		{ id: 'plain_language', label: 'Plain language' },
	];

	const SHARED_TOKENS = [
		{
			id: 'ICP',
			symbol: 'ICP',
			label: 'ICP',
			canister: 'ryjl3-tyaaa-aaaaa-aaaba-cai',
		},
		{
			id: 'ckBTC',
			symbol: 'ckBTC',
			label: 'ckBTC',
			canister: 'mxzaz-hqaaa-aaaar-qaada-cai',
		},
		{
			id: 'ckUSDC',
			symbol: 'ckUSDC',
			label: 'ckUSDC',
			canister: 'xevnm-gaaaa-aaaar-qafnq-cai',
		},
	];

	const RANDOM_DESCRIPTIONS = [
		'A steady steward of the treasury, plain in speech and careful with proposals.',
		'Warm but disciplined — short replies, open books, and alignment above all.',
		'Playful in tone yet serious about exit, honesty, and the Codex.',
		'An austere Monad: cite the Codex, propose never write, no side deals.',
	];

	const seed = untrack(() => ({
		step: (draft.step as SetupStep) || 'welcome',
		voice: draft.personality.voice,
		stance: draft.personality.stance,
		principles: [...draft.personality.principles],
		description: draft.personality.description,
		tokenMode: draft.token.mode || 'none',
		tokenId: draft.token.token_id,
		tokenSymbol: draft.token.symbol,
		tokenCanisterId: draft.token.canister_id,
		logoDataUrl: draft.logo_data_url,
	}));

	let step = $state<SetupStep>(seed.step);
	let voice = $state(seed.voice);
	let stance = $state(seed.stance);
	let principles = $state<string[]>(seed.principles);
	let description = $state(seed.description);
	let tokenMode = $state(seed.tokenMode);
	let tokenId = $state(seed.tokenId);
	let tokenSymbol = $state(seed.tokenSymbol);
	let tokenCanisterId = $state(seed.tokenCanisterId);
	let logoDataUrl = $state(seed.logoDataUrl);

	let stepError = $state<string | null>(null);
	let saveError = $state<string | null>(null);
	let saving = $state(false);
	let launching = $state(false);
	let opening = $state(false);

	let descriptionDebounce: ReturnType<typeof setTimeout> | null = null;

	const stepIndex = $derived(STEPS.indexOf(step));
	const stepNumber = $derived(stepIndex + 1);

	const voiceLabel = $derived(VOICES.find((v) => v.id === voice)?.label ?? voice);
	const stanceLabel = $derived(STANCES.find((s) => s.id === stance)?.label ?? stance);
	const principleLabels = $derived(
		principles.map((id) => PRINCIPLES.find((p) => p.id === id)?.label ?? id),
	);

	const tokenSummary = $derived.by(() => {
		if (tokenMode === 'none') return 'None — dues and credits only';
		if (tokenMode === 'shared') {
			const shared = SHARED_TOKENS.find((t) => t.id === tokenId || t.canister === tokenCanisterId);
			return shared ? `${shared.label} (${shared.symbol})` : 'Shared token';
		}
		if (tokenMode === 'custom') {
			return tokenSymbol
				? `${tokenSymbol}${tokenCanisterId ? ` · ${tokenCanisterId}` : ''}`
				: 'Custom token';
		}
		return tokenMode;
	});

	function buildDraft(nextStep: SetupStep = step): SetupDraft {
		return {
			step: nextStep,
			personality: {
				voice,
				stance,
				principles: [...principles],
				description,
			},
			token: {
				mode: tokenMode,
				token_id: tokenId,
				symbol: tokenSymbol,
				canister_id: tokenCanisterId,
			},
			logo_data_url: logoDataUrl,
		};
	}

	async function persistDraft(nextStep: SetupStep = step) {
		saving = true;
		saveError = null;
		try {
			await saveSetupDraft(buildDraft(nextStep));
		} catch (e) {
			saveError = e instanceof Error ? e.message : 'Could not save draft';
			throw e;
		} finally {
			saving = false;
		}
	}

	function scheduleDescriptionSave() {
		if (descriptionDebounce) clearTimeout(descriptionDebounce);
		descriptionDebounce = setTimeout(() => {
			persistDraft().catch(() => {
				/* saveError already set */
			});
		}, 400);
	}

	function togglePrinciple(id: string) {
		if (principles.includes(id)) {
			principles = principles.filter((p) => p !== id);
		} else {
			principles = [...principles, id];
		}
	}

	function selectVoice(id: string) {
		voice = id;
	}

	function selectStance(id: string) {
		stance = id;
	}

	function selectTokenMode(mode: string) {
		tokenMode = mode;
		if (mode === 'none') {
			tokenId = '';
			tokenSymbol = '';
			tokenCanisterId = '';
		}
	}

	function selectSharedToken(id: string, symbol: string, canister: string) {
		tokenMode = 'shared';
		tokenId = id;
		tokenSymbol = symbol;
		tokenCanisterId = canister;
	}

	function randomizePersonality() {
		voice = VOICES[Math.floor(Math.random() * VOICES.length)].id;
		stance = STANCES[Math.floor(Math.random() * STANCES.length)].id;
		const count = 2 + Math.floor(Math.random() * 3);
		const shuffled = [...PRINCIPLES].sort(() => Math.random() - 0.5);
		principles = shuffled.slice(0, count).map((p) => p.id);
		description = RANDOM_DESCRIPTIONS[Math.floor(Math.random() * RANDOM_DESCRIPTIONS.length)];
		persistDraft().catch(() => {
			/* saveError already set */
		});
	}

	function validateStep(): string | null {
		if (step === 'personality') {
			if (!voice) return 'Choose a voice for the Monad.';
			if (!stance) return 'Choose a stance for the Monad.';
		}
		if (step === 'token' && tokenMode === 'custom' && !tokenCanisterId.trim()) {
			return 'Enter a canister id for a custom token.';
		}
		return null;
	}

	async function goNext() {
		stepError = validateStep();
		if (stepError) return;
		const next = STEPS[stepIndex + 1];
		if (!next) return;
		try {
			await persistDraft(next);
			step = next;
			stepError = null;
		} catch {
			/* saveError shown */
		}
	}

	async function goBack() {
		const prev = STEPS[stepIndex - 1];
		if (!prev) return;
		try {
			await persistDraft(prev);
			step = prev;
			stepError = null;
		} catch {
			/* saveError shown */
		}
	}

	async function handleLogoChange(event: Event) {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		const reader = new FileReader();
		reader.onload = () => {
			logoDataUrl = typeof reader.result === 'string' ? reader.result : '';
			persistDraft().catch(() => {
				/* saveError already set */
			});
		};
		reader.readAsDataURL(file);
	}

	function clearLogo() {
		logoDataUrl = '';
		persistDraft().catch(() => {
			/* saveError already set */
		});
	}

	async function handleLaunch() {
		stepError = null;
		launching = true;
		saveError = null;
		try {
			await persistDraft('launch');
			await completeSetup();
			opening = true;
			await oncomplete?.();
		} catch (e) {
			saveError = e instanceof Error ? e.message : 'Launch failed';
			opening = false;
		} finally {
			launching = false;
		}
	}

	$effect(() => {
		return () => {
			if (descriptionDebounce) clearTimeout(descriptionDebounce);
		};
	});
</script>

<section class="wizard chora-prose" aria-label="Realm setup">
	<header class="wizard-header">
		<p class="eyebrow chora-muted">
			Step {stepNumber} of {STEPS.length} · {STEP_LABELS[step]}
		</p>
		<h1>Founding this Chora realm</h1>
	</header>

	{#if opening}
		<p class="opening">Opening the realm…</p>
	{:else if step === 'welcome'}
		<div class="step-body">
			<p>
				You are founding a new Chora realm. The Monad proposes; citizens ratify.
			</p>
			<p class="chora-muted">
				Alignment is the share of citizens current on membership dues — the
				live measure of who stands with the realm.
			</p>
		</div>
	{:else if step === 'personality'}
		<div class="step-body">
			<p class="chora-muted intro">
				Shape how the Monad speaks and decides. No marketplace — just your
				principles.
			</p>

			<fieldset class="field-group">
				<legend>Voice</legend>
				<div class="chip-row">
					{#each VOICES as option (option.id)}
						<button
							type="button"
							class="chip"
							class:selected={voice === option.id}
							aria-pressed={voice === option.id}
							onclick={() => selectVoice(option.id)}
						>
							{option.label}
						</button>
					{/each}
				</div>
			</fieldset>

			<fieldset class="field-group">
				<legend>Stance</legend>
				<div class="chip-row">
					{#each STANCES as option (option.id)}
						<button
							type="button"
							class="chip"
							class:selected={stance === option.id}
							aria-pressed={stance === option.id}
							onclick={() => selectStance(option.id)}
						>
							{option.label}
						</button>
					{/each}
				</div>
			</fieldset>

			<fieldset class="field-group">
				<legend>Principles</legend>
				<div class="chip-row">
					{#each PRINCIPLES as option (option.id)}
						<button
							type="button"
							class="chip"
							class:selected={principles.includes(option.id)}
							aria-pressed={principles.includes(option.id)}
							onclick={() => togglePrinciple(option.id)}
						>
							{option.label}
						</button>
					{/each}
				</div>
			</fieldset>

			<label class="field-group" for="monad-description">
				<span class="label">Describe the Monad</span>
				<textarea
					id="monad-description"
					class="chora-textarea"
					rows="4"
					placeholder="Optional — how should the Monad carry itself?"
					bind:value={description}
					oninput={scheduleDescriptionSave}
				></textarea>
			</label>

			<button type="button" class="chora-btn" onclick={randomizePersonality}>
				Random
			</button>
		</div>
	{:else if step === 'token'}
		<div class="step-body">
			<p class="chora-muted intro">
				Optional. This realm runs on dues and credits by default.
			</p>

			<fieldset class="field-group">
				<legend>Token</legend>
				<div class="choice-list">
					<label class="choice">
						<input
							type="radio"
							name="token-mode"
							value="none"
							checked={tokenMode === 'none'}
							onchange={() => selectTokenMode('none')}
						/>
						<span>None — dues and credits only</span>
					</label>

					{#each SHARED_TOKENS as shared (shared.id)}
						<label class="choice">
							<input
								type="radio"
								name="token-mode"
								value={shared.id}
								checked={tokenMode === 'shared' && tokenId === shared.id}
								onchange={() => selectSharedToken(shared.id, shared.symbol, shared.canister)}
							/>
							<span>{shared.label}</span>
						</label>
					{/each}

					<label class="choice">
						<input
							type="radio"
							name="token-mode"
							value="custom"
							checked={tokenMode === 'custom'}
							onchange={() => selectTokenMode('custom')}
						/>
						<span>Custom token</span>
					</label>
				</div>
			</fieldset>

			{#if tokenMode === 'custom'}
				<label class="field-group" for="token-canister">
					<span class="label">Canister id</span>
					<input
						id="token-canister"
						class="chora-input"
						type="text"
						placeholder="aaaaa-aa"
						bind:value={tokenCanisterId}
					/>
				</label>
				<label class="field-group" for="token-symbol">
					<span class="label">Symbol</span>
					<input
						id="token-symbol"
						class="chora-input"
						type="text"
						placeholder="TKN"
						bind:value={tokenSymbol}
					/>
				</label>
			{/if}
		</div>
	{:else if step === 'branding'}
		<div class="step-body">
			<p class="chora-muted intro">Optional logo for this realm.</p>

			<label class="field-group" for="realm-logo">
				<span class="label">Logo</span>
				<input id="realm-logo" type="file" accept="image/*" onchange={handleLogoChange} />
			</label>

			{#if logoDataUrl}
				<div class="logo-preview">
					<img src={logoDataUrl} alt="Realm logo preview" />
					<button type="button" class="chora-btn chora-btn-ghost" onclick={clearLogo}>
						Clear
					</button>
				</div>
			{/if}
		</div>
	{:else if step === 'launch'}
		<div class="step-body">
			<p class="chora-muted intro">Review your choices, then open the realm.</p>

			<dl class="summary">
				<div>
					<dt>Voice</dt>
					<dd>{voiceLabel || '—'}</dd>
				</div>
				<div>
					<dt>Stance</dt>
					<dd>{stanceLabel || '—'}</dd>
				</div>
				<div>
					<dt>Principles</dt>
					<dd>
						{#if principleLabels.length}
							{principleLabels.join(', ')}
						{:else}
							None selected
						{/if}
					</dd>
				</div>
				<div>
					<dt>Description</dt>
					<dd>{description.trim() || '—'}</dd>
				</div>
				<div>
					<dt>Token</dt>
					<dd>{tokenSummary}</dd>
				</div>
				<div>
					<dt>Logo</dt>
					<dd>{logoDataUrl ? 'Included' : 'None'}</dd>
				</div>
			</dl>
		</div>
	{/if}

	{#if stepError}
		<p class="error">{stepError}</p>
	{/if}
	{#if saveError}
		<p class="error">{saveError}</p>
	{/if}

	{#if !opening}
		<footer class="wizard-footer">
			{#if stepIndex > 0}
				<button type="button" class="chora-btn chora-btn-ghost" disabled={saving || launching} onclick={goBack}>
					Back
				</button>
			{/if}

			<div class="footer-end">
				{#if saving}
					<span class="chora-muted save-hint">Saving…</span>
				{/if}

				{#if step === 'launch'}
					<button
						type="button"
						class="chora-btn chora-btn-primary"
						disabled={launching}
						onclick={handleLaunch}
					>
						{launching ? 'Launching…' : 'Launch realm'}
					</button>
				{:else}
					<button type="button" class="chora-btn chora-btn-primary" disabled={saving} onclick={goNext}>
						Next
					</button>
				{/if}
			</div>
		</footer>
	{/if}
</section>

<style>
	.wizard {
		margin: 0 auto;
		padding: 0.5rem 0 2rem;
	}

	.wizard-header {
		margin-bottom: 1.5rem;
	}

	.eyebrow {
		margin: 0 0 0.35rem;
		font-family: var(--chora-font-ui);
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	h1 {
		margin: 0;
		font-size: 1.6rem;
		font-weight: 500;
	}

	.step-body {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.intro {
		margin: 0;
	}

	.field-group {
		margin: 0;
		padding: 0;
		border: 0;
	}

	legend,
	.label {
		display: block;
		margin-bottom: 0.5rem;
		font-family: var(--chora-font-ui);
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--chora-text-muted);
	}

	.chip-row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.45rem;
	}

	.chip {
		padding: 0.35rem 0.7rem;
		border: 1px solid var(--chora-border);
		border-radius: var(--chora-radius);
		background: var(--chora-surface);
		font-family: var(--chora-font-ui);
		font-size: 0.85rem;
		color: var(--chora-text);
	}

	.chip:hover {
		background: var(--chora-accent-soft);
	}

	.chip.selected {
		background: var(--chora-accent-soft);
		border-color: var(--chora-accent);
		color: var(--chora-text);
	}

	.choice-list {
		display: flex;
		flex-direction: column;
		gap: 0.55rem;
		font-family: var(--chora-font-ui);
		font-size: 0.95rem;
	}

	.choice {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.logo-preview {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.logo-preview img {
		width: 4rem;
		height: 4rem;
		object-fit: contain;
		border: 1px solid var(--chora-border);
		border-radius: var(--chora-radius);
		background: var(--chora-surface);
	}

	.summary {
		display: grid;
		grid-template-columns: 8.5rem 1fr;
		gap: 0.55rem 1rem;
		margin: 0;
		font-family: var(--chora-font-ui);
		font-size: 0.95rem;
	}

	.summary div {
		display: contents;
	}

	dt {
		margin: 0;
		color: var(--chora-text-muted);
	}

	dd {
		margin: 0;
	}

	.opening {
		margin: 2rem 0;
		font-family: var(--chora-font-ui);
		color: var(--chora-text-muted);
	}

	.error {
		margin: 1rem 0 0;
		color: var(--chora-no);
		font-family: var(--chora-font-ui);
		font-size: 0.9rem;
	}

	.wizard-footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 1px solid var(--chora-border);
	}

	.footer-end {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-left: auto;
	}

	.save-hint {
		font-size: 0.8rem;
	}
</style>
