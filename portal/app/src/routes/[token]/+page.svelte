<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

	interface FormField {
		id: string;
		key: string;
		label: string;
		field_type: string;
		options: string[];
		is_required: boolean;
		sort_order: number;
	}

	interface LayoutInfo {
		id: string;
		name: string;
	}

	interface PortalInfo {
		salon_name: string;
		event_date: string;
		start_time: string;
		end_time: string;
		bride_groom: string;
		guest_count: number;
		event_type_name: string;
		seating_enabled: boolean;
		portal_layout_permission: boolean;
		reserved_layouts: LayoutInfo[];
		form_fields: FormField[];
	}

	const token = $derived($page.params.token);

	let info = $state<PortalInfo | null>(null);
	let error = $state('');
	let loading = $state(true);
	let formData = $state<Record<string, string>>({});
	let submitting = $state(false);
	let submitted = $state(false);

	onMount(async () => {
		try {
			const res = await fetch(`${API}/portal/${token}`);
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				error = (err as { detail?: string }).detail || 'Portal bulunamadı';
				return;
			}
			info = await res.json();
			if (info) {
				const initial: Record<string, string> = {};
				for (const f of info.form_fields) initial[f.key] = '';
				formData = initial;
			}
		} catch {
			error = 'Sunucuya bağlanılamadı';
		} finally {
			loading = false;
		}
	});

	function formatDate(d: string) {
		if (!d) return '—';
		try { return new Date(d + 'T00:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }); }
		catch { return d; }
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		submitting = true;
		try {
			const res = await fetch(`${API}/portal/${token}/form`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ data: formData })
			});
			if (!res.ok) throw new Error('Gönderme başarısız');
			submitted = true;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Hata oluştu';
		} finally {
			submitting = false;
		}
	}

	function goToSeating(layoutId: string) {
		goto(`/${token}/seating?layout=${layoutId}`);
	}
</script>

<svelte:head>
	<title>{info?.salon_name ?? 'Müşteri Portali'} — Eventra</title>
</svelte:head>

<div class="portal-shell">
	<header class="portal-header">
		<div class="logo-area">
			<span class="logo-text">✦ Eventra</span>
			{#if info}<span class="salon-name">{info.salon_name}</span>{/if}
		</div>
	</header>

	<main class="portal-main">
		{#if loading}
			<div class="state-card">
				<div class="spinner"></div>
				<p>Yükleniyor…</p>
			</div>

		{:else if error}
			<div class="state-card error-card">
				<div class="error-icon">✕</div>
				<h2>Portal Bulunamadı</h2>
				<p>{error}</p>
			</div>

		{:else if submitted}
			<div class="state-card success-card">
				<div class="success-icon">✓</div>
				<h2>Teşekkürler!</h2>
				<p>Organizasyon bilgileriniz başarıyla iletildi. Salon ile iletişime geçeceğiz.</p>
				{#if info?.portal_layout_permission && info.reserved_layouts.length > 0}
					<div class="seating-prompt">
						<p>Salon düzeninizi de ayarlayabilirsiniz:</p>
						<div class="layout-buttons">
							{#each info.reserved_layouts as layout}
								<button onclick={() => goToSeating(layout.id)} class="seating-btn">
									{layout.name} — Misafir Yerleşimi →
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>

		{:else if info}
			<div class="event-card">
				<div class="event-badge">{info.event_type_name || 'Davet'}</div>
				<h1>{info.bride_groom || 'Davetiniz'}</h1>
				<div class="event-meta">
					<span>📅 {formatDate(info.event_date)}</span>
					<span>🕐 {info.start_time} – {info.end_time}</span>
					{#if info.guest_count > 0}<span>👥 {info.guest_count} davetli</span>{/if}
				</div>
			</div>

			{#if info.form_fields.length > 0}
				<form class="portal-form" onsubmit={handleSubmit}>
					<div class="form-header">
						<h2>Organizasyon Detayları</h2>
						<p>Lütfen aşağıdaki bilgileri doldurun.</p>
					</div>

					<div class="form-fields">
						{#each info.form_fields as field}
							<div class="field-group">
								<label for="field_{field.key}">
									{field.label}
									{#if field.is_required}<span class="required">*</span>{/if}
								</label>

								{#if field.field_type === 'textarea'}
									<textarea
										id="field_{field.key}"
										bind:value={formData[field.key]}
										rows="4"
										required={field.is_required}
									></textarea>
								{:else if field.field_type === 'select'}
									<select
										id="field_{field.key}"
										bind:value={formData[field.key]}
										required={field.is_required}
									>
										<option value="">— Seçin —</option>
										{#each field.options as opt}
											<option value={opt}>{opt}</option>
										{/each}
									</select>
								{:else if field.field_type === 'checkbox'}
									<label class="checkbox-label">
										<input
											type="checkbox"
											id="field_{field.key}"
											checked={formData[field.key] === 'true'}
											onchange={(e) => (formData[field.key] = String(e.currentTarget.checked))}
										/>
										<span>{field.label}</span>
									</label>
								{:else if field.field_type === 'range'}
									<div class="range-wrap">
										<input
											type="range"
											id="field_{field.key}"
											min="0"
											max="100"
											bind:value={formData[field.key]}
										/>
										<span class="range-val">{formData[field.key] || '0'}</span>
									</div>
								{:else}
									<input
										type={field.field_type}
										id="field_{field.key}"
										bind:value={formData[field.key]}
										required={field.is_required}
									/>
								{/if}
							</div>
						{/each}
					</div>

					<button type="submit" class="submit-btn" disabled={submitting}>
						{submitting ? 'Gönderiliyor…' : 'Gönder'}
					</button>
				</form>
			{:else}
				<div class="no-form-card">
					<p>Bu portal için organizasyon formu henüz hazırlanmamış.</p>
				</div>
			{/if}

			{#if info.portal_layout_permission && info.reserved_layouts.length > 0}
				<div class="seating-section">
					<h2>Salon Düzeni</h2>
					<p>Misafirleriniz için masa ve koltuk düzenini oluşturabilirsiniz.</p>
					<div class="layout-buttons">
						{#each info.reserved_layouts as layout}
							<button onclick={() => goToSeating(layout.id)} class="seating-btn">
								{layout.name} — Misafir Yerleşimini Düzenle →
							</button>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</main>

	<footer class="portal-footer">
		<p>Bu portal <strong>Eventra</strong> tarafından oluşturulmuştur.</p>
	</footer>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
		background: #0f172a;
		color: #f1f5f9;
	}
	:global(*) { box-sizing: border-box; }

	.portal-shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
	}

	.portal-header {
		display: flex;
		align-items: center;
		padding: 1rem 2rem;
		border-bottom: 1px solid rgba(255,255,255,0.08);
		background: rgba(255,255,255,0.04);
		backdrop-filter: blur(8px);
	}

	.logo-area { display: flex; flex-direction: column; gap: 0.1rem; }
	.logo-text { font-size: 1.1rem; font-weight: 900; color: #c59b31; letter-spacing: 0.05em; }
	.salon-name { font-size: 0.78rem; color: rgba(255,255,255,0.5); }

	.portal-main {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.5rem;
		padding: 2rem 1rem 3rem;
		max-width: 680px;
		margin: 0 auto;
		width: 100%;
	}

	.state-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		padding: 3rem;
		background: rgba(255,255,255,0.06);
		border: 1px solid rgba(255,255,255,0.12);
		border-radius: 16px;
		text-align: center;
		width: 100%;
	}

	.error-card { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.08); }
	.success-card { border-color: rgba(22,163,74,0.3); background: rgba(22,163,74,0.08); }
	.error-icon { font-size: 2.5rem; color: #ef4444; }
	.success-icon { font-size: 2.5rem; color: #16a34a; }

	.spinner {
		width: 40px; height: 40px;
		border: 3px solid rgba(255,255,255,0.1);
		border-top-color: #c59b31;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin { to { transform: rotate(360deg); } }

	.event-card {
		width: 100%;
		padding: 2rem;
		background: rgba(197,155,49,0.08);
		border: 1px solid rgba(197,155,49,0.25);
		border-radius: 16px;
		text-align: center;
	}

	.event-badge {
		display: inline-block;
		padding: 0.35rem 0.85rem;
		background: rgba(197,155,49,0.2);
		border: 1px solid rgba(197,155,49,0.4);
		border-radius: 999px;
		font-size: 0.78rem;
		font-weight: 900;
		color: #c59b31;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.75rem;
	}

	.event-card h1 {
		font-size: clamp(1.8rem, 4vw, 2.5rem);
		font-weight: 900;
		margin: 0 0 1rem;
		color: #f1f5f9;
	}

	.event-meta {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 1rem;
		color: rgba(255,255,255,0.65);
		font-size: 0.9rem;
	}

	.portal-form, .seating-section {
		width: 100%;
		background: rgba(255,255,255,0.05);
		border: 1px solid rgba(255,255,255,0.1);
		border-radius: 16px;
		overflow: hidden;
	}

	.form-header { padding: 1.5rem 1.5rem 0; }
	.form-header h2 { font-size: 1.2rem; font-weight: 900; margin: 0 0 0.35rem; color: #f1f5f9; }
	.form-header p { color: rgba(255,255,255,0.5); font-size: 0.88rem; margin: 0; }

	.form-fields { display: flex; flex-direction: column; gap: 1.25rem; padding: 1.5rem; }

	.field-group { display: flex; flex-direction: column; gap: 0.5rem; }
	.field-group > label { font-size: 0.88rem; font-weight: 700; color: rgba(255,255,255,0.8); }
	.required { color: #ef4444; margin-left: 0.2rem; }

	input[type="text"], input[type="number"], input[type="date"], input[type="email"], textarea, select {
		width: 100%; min-height: 44px;
		background: rgba(255,255,255,0.07);
		border: 1px solid rgba(255,255,255,0.15);
		border-radius: 10px;
		padding: 0.65rem 0.85rem;
		color: #f1f5f9; font: inherit; font-size: 0.95rem;
		transition: border-color 0.2s;
	}
	input:focus, textarea:focus, select:focus { outline: none; border-color: rgba(197,155,49,0.6); background: rgba(255,255,255,0.1); }
	textarea { resize: vertical; min-height: 100px; }
	select option { background: #1e293b; color: #f1f5f9; }

	.checkbox-label { display: flex; align-items: center; gap: 0.65rem; cursor: pointer; font-size: 0.9rem; color: rgba(255,255,255,0.8); }
	.checkbox-label input { width: 18px; height: 18px; min-height: auto; accent-color: #c59b31; cursor: pointer; }

	.range-wrap { display: flex; align-items: center; gap: 1rem; }
	.range-wrap input { flex: 1; min-height: auto; padding: 0; accent-color: #c59b31; }
	.range-val { font-weight: 700; color: #c59b31; min-width: 32px; text-align: right; }

	.submit-btn {
		display: block; width: calc(100% - 3rem); margin: 0 1.5rem 1.5rem;
		padding: 1rem; background: linear-gradient(135deg, #c59b31, #a07a20); color: #0f172a;
		border: none; border-radius: 10px; font: inherit; font-size: 1rem; font-weight: 900;
		cursor: pointer; letter-spacing: 0.05em; transition: all 0.2s;
	}
	.submit-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(197,155,49,0.3); }
	.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

	.seating-section { padding: 1.5rem; }
	.seating-section h2 { font-size: 1.1rem; font-weight: 900; margin: 0 0 0.35rem; }
	.seating-section p { color: rgba(255,255,255,0.55); font-size: 0.88rem; margin: 0 0 1rem; }

	.layout-buttons { display: flex; flex-direction: column; gap: 0.65rem; margin-top: 1rem; }

	.seating-btn {
		padding: 0.85rem 1.25rem;
		background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15);
		border-radius: 10px; color: #f1f5f9; font: inherit; font-weight: 800; font-size: 0.92rem;
		cursor: pointer; text-align: left; transition: all 0.15s;
	}
	.seating-btn:hover { background: rgba(197,155,49,0.12); border-color: rgba(197,155,49,0.35); }

	.seating-prompt { margin-top: 1.5rem; }
	.seating-prompt p { color: rgba(255,255,255,0.65); font-size: 0.9rem; margin: 0 0 0.75rem; }

	.no-form-card { width: 100%; padding: 1.5rem; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; text-align: center; color: rgba(255,255,255,0.5); font-size: 0.9rem; }

	.portal-footer { padding: 1.5rem; text-align: center; border-top: 1px solid rgba(255,255,255,0.06); color: rgba(255,255,255,0.3); font-size: 0.82rem; }

	@media (max-width: 640px) {
		.portal-header { padding: 0.85rem 1rem; }
		.portal-main { padding: 1.25rem 0.85rem 2rem; }
	}
</style>
