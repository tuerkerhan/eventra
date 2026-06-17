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
	interface LayoutInfo { id: string; name: string; }
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
		portal_title: string;
		appointment_no: number | null;
		payment_enabled: boolean;
		payment_bank_name: string;
		payment_iban: string;
		payment_account_holder: string;
		payment_description: string;
		payment_complete: boolean;
		customer_payment_claimed: boolean;
		portal_message: string;
		portal_photos: { name: string; url: string }[];
	}

	const token = $derived($page.params.token);

	let info = $state<PortalInfo | null>(null);
	let error = $state('');
	let loading = $state(true);
	let formData = $state<Record<string, string>>({});
	let submitting = $state(false);
	let submitted = $state(false);
	let submitMessage = $state('');
	let mounted = $state(false);
	let paymentClaiming = $state(false);
	let paymentClaimed = $state(false);

	// Sparkle particles
	const sparkles = Array.from({ length: 22 }, (_, i) => ({
		id: i,
		left: Math.random() * 100,
		delay: Math.random() * 8,
		duration: 6 + Math.random() * 8,
		size: 4 + Math.random() * 6,
		opacity: 0.2 + Math.random() * 0.5,
	}));

	onMount(async () => {
		setTimeout(() => (mounted = true), 80);
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
		try { return new Date(d + 'T00:00:00').toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }); }
		catch { return d; }
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		submitting = true;
		error = '';
		try {
			const res = await fetch(`${API}/portal/${token}/form`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ data: formData })
			});
			if (!res.ok) {
				const detail = await res.json().catch(() => ({}));
				throw new Error((detail as { detail?: string }).detail || 'Gönderme başarısız');
			}
			submitted = true;
			submitMessage = 'Bilgileriniz iletildi.';
			setTimeout(() => { submitMessage = ''; }, 4500);
		} catch (ex) {
			error = ex instanceof Error ? ex.message : 'Hata oluştu';
		} finally {
			submitting = false;
		}
	}

	function goToSeating(layoutId: string) { goto(`/${token}/seating?layout=${layoutId}`); }

	function buildPaymentDescription(info: PortalInfo): string {
		if (!info.payment_description) return '';
		const name = info.bride_groom || info.salon_name || '';
		return info.payment_description
			.replace(/\{randevu_id\}/g, info.appointment_no ? String(info.appointment_no) : '—')
			.replace(/\{isim\}/g, name);
	}

	async function claimPayment() {
		if (paymentClaiming || paymentClaimed) return;
		paymentClaiming = true;
		try {
			await fetch(`${API}/portal/${token}/payment-claimed`, { method: 'POST' });
			paymentClaimed = true;
			if (info) info = { ...info, customer_payment_claimed: true };
		} catch {
			// silent
		} finally {
			paymentClaiming = false;
		}
	}
</script>

<svelte:head>
	<title>{info?.salon_name ?? 'Müşteri Portali'} — Eventra</title>
	<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Cormorant+Garamond:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet" />
</svelte:head>

<!-- Sparkle particles -->
<div class="sparkle-layer" aria-hidden="true">
	{#each sparkles as s}
		<div
			class="sparkle"
			style="
				left:{s.left}%;
				animation-delay:{s.delay}s;
				animation-duration:{s.duration}s;
				width:{s.size}px;
				height:{s.size}px;
				opacity:{s.opacity};
			"
		></div>
	{/each}
</div>

<div class="portal-shell" class:mounted>

	<!-- ── Header ─────────────────────────── -->
	<header class="portal-header">
		<div class="header-inner">
			<div class="brand-block">
				<div class="brand-logo-wrap">
					<img src="/ikon.png" alt="Logo" class="brand-logo" />
					<div class="logo-glow"></div>
				</div>
				<div class="brand-text">
					<img src="/crown-icon.png" alt="" class="header-crown" />
					<img src="/logo-yatay.png" alt="Eventra" class="header-wordmark" />
				</div>
			</div>
			{#if info}
				<div class="salon-chip">
					<span class="salon-chip-dot"></span>
					{info.salon_name}
				</div>
			{/if}
		</div>
	</header>

	<!-- ── Content ────────────────────────── -->
	<main class="portal-main">

		{#if loading}
			<div class="state-card animate-in">
				<div class="spinner-ring"></div>
				<p class="state-text">Yükleniyor…</p>
			</div>

		{:else if error && !info}
			<div class="state-card error-card animate-in">
				<div class="state-icon error-icon">✕</div>
				<h2>Portal Bulunamadı</h2>
				<p>{error}</p>
			</div>

		{:else if info}

			<!-- Event hero card -->
			<div class="event-hero animate-in" style="animation-delay:0.05s">
				<div class="hero-glow-ring"></div>
				<div class="event-badge-row">
					<span class="event-type-badge">{info.event_type_name || 'Özel Davet'}</span>
				</div>
				<div class="crown-float-wrap">
					<img src="/crown-icon.png" alt="" class="crown-float" />
				</div>
				<h1 class="event-name">{info.portal_title || 'Davetiniz'}</h1>
				<div class="event-divider"><span></span><img src="/ikon.png" alt="" class="divider-icon" /><span></span></div>
				<div class="event-meta">
					<div class="meta-item">
						<span class="meta-icon">📅</span>
						<span>{formatDate(info.event_date)}</span>
					</div>
					<div class="meta-sep"></div>
					<div class="meta-item">
						<span class="meta-icon">🕐</span>
						<span>{info.start_time} – {info.end_time}</span>
					</div>
					{#if info.guest_count > 0}
						<div class="meta-sep"></div>
						<div class="meta-item">
							<span class="meta-icon">👥</span>
							<span>{info.guest_count} davetli</span>
						</div>
					{/if}
				</div>
			</div>

			<!-- Message from business -->
			{#if info.portal_message}
				<div class="message-card animate-in" style="animation-delay:0.1s">
					<span class="message-icon">✉️</span>
					<p>{info.portal_message}</p>
				</div>
			{/if}

			<!-- Admin photos -->
			{#if (info.portal_photos ?? []).length > 0}
				<div class="admin-photos-card animate-in" style="animation-delay:0.12s">
					<div class="admin-photos-grid">
						{#each info.portal_photos as photo}
							<a href="{API}{photo.url}" target="_blank" class="admin-photo-thumb">
								<img src="{API}{photo.url}" alt={photo.name} />
							</a>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Form -->
			{#if info.form_fields.length > 0}
				<div class="form-card animate-in" style="animation-delay:0.15s">
					<div class="form-card-header">
						<img src="/crown-icon.png" alt="" class="form-crown" />
						<div>
							<h2 class="form-title">Organizasyon Detayları</h2>
							<p class="form-subtitle">Lütfen aşağıdaki bilgileri eksiksiz doldurun.</p>
						</div>
					</div>

					<form onsubmit={handleSubmit}>
						<div class="form-fields">
							{#each info.form_fields as field}
								<div class="field-group">
									<label for="f_{field.key}">
										{field.label}
										{#if field.is_required}<span class="req">*</span>{/if}
									</label>

									{#if field.field_type === 'textarea'}
										<textarea id="f_{field.key}" bind:value={formData[field.key]} rows="4" required={field.is_required}></textarea>
									{:else if field.field_type === 'select'}
										<select id="f_{field.key}" bind:value={formData[field.key]} required={field.is_required}>
											<option value="">— Seçin —</option>
											{#each field.options as opt}<option value={opt}>{opt}</option>{/each}
										</select>
									{:else if field.field_type === 'checkbox'}
										<label class="check-label">
											<input type="checkbox" id="f_{field.key}" checked={formData[field.key] === 'true'} onchange={(e) => (formData[field.key] = String(e.currentTarget.checked))} />
											<span class="check-box"></span>
											<span>{field.label}</span>
										</label>
									{:else if field.field_type === 'range'}
										<div class="range-wrap">
											<input type="range" id="f_{field.key}" min="0" max="100" bind:value={formData[field.key]} />
											<span class="range-val">{formData[field.key] || '0'}</span>
										</div>
									{:else}
										<input type={field.field_type} id="f_{field.key}" bind:value={formData[field.key]} required={field.is_required} />
									{/if}
								</div>
							{/each}
						</div>

						{#if error}
							<p class="form-error">{error}</p>
						{/if}
						{#if submitMessage}
							<p class="form-success">{submitMessage}</p>
						{/if}

						<div class="submit-wrap">
							<button type="submit" class="submit-btn" disabled={submitting}>
								{#if submitting}
									<span class="btn-spinner"></span> Gönderiliyor…
								{:else}
									<img src="/crown-icon.png" alt="" class="btn-crown" /> {submitted ? 'Tekrar Gönder' : 'Gönder'}
								{/if}
							</button>
						</div>
					</form>
				</div>
			{:else}
				<div class="no-form-card animate-in" style="animation-delay:0.15s">
					<p>Bu portal için organizasyon formu henüz hazırlanmamış.</p>
				</div>
			{/if}

			<!-- Payment section -->
			{#if info.payment_enabled}
				<div class="payment-card animate-in" style="animation-delay:0.2s">
					{#if info.payment_complete}
						<div class="payment-confirmed">
							<div class="confirmed-icon">✓</div>
							<div>
								<strong>Ödemeniz Onaylanmıştır</strong>
								<p>İşletme ödemenizi sisteme işledi. Teşekkürler!</p>
							</div>
						</div>
					{:else}
						<div class="payment-header">
							<span class="payment-icon">🏦</span>
							<div>
								<h2 class="payment-title">Ödeme Bilgileri</h2>
								<p class="payment-subtitle">Havale / EFT ile ödeme yapabilirsiniz.</p>
							</div>
						</div>

						{#if info.appointment_no}
							<div class="payment-appt-no">
								Randevu ID: <strong>#{info.appointment_no}</strong>
							</div>
						{/if}

						<div class="payment-details">
							{#if info.payment_bank_name}
								<div class="payment-row">
									<span>Banka</span>
									<strong>{info.payment_bank_name}</strong>
								</div>
							{/if}
							{#if info.payment_account_holder}
								<div class="payment-row">
									<span>Hesap Sahibi</span>
									<strong>{info.payment_account_holder}</strong>
								</div>
							{/if}
							{#if info.payment_iban}
								<div class="payment-row iban-row">
									<span>IBAN</span>
									<strong class="iban">{info.payment_iban}</strong>
								</div>
							{/if}
							{#if info.payment_description}
								<div class="payment-row">
									<span>Açıklama</span>
									<strong>{buildPaymentDescription(info)}</strong>
								</div>
							{/if}
						</div>

						<div class="payment-claim-section">
							{#if info.customer_payment_claimed || paymentClaimed}
								<div class="claim-sent">
									<span class="claim-check">✓</span>
									Ödeme bildiriminiz iletildi. İşletme onayını bekliyorsunuz.
								</div>
							{:else}
								<p class="claim-hint">Ödemeyi yaptıysanız aşağıdan bildirin, işletme bilgilendirilsin.</p>
								<button class="claim-btn" onclick={claimPayment} disabled={paymentClaiming}>
									{#if paymentClaiming}
										<span class="btn-spinner"></span> Gönderiliyor…
									{:else}
										<span class="claim-btn-icon">✓</span> Ödemeyi Yaptım
									{/if}
								</button>
							{/if}
						</div>
					{/if}
				</div>
			{/if}

		<!-- Seating section -->
			{#if info.portal_layout_permission && info.reserved_layouts.length > 0}
				<div class="seating-card animate-in" style="animation-delay:0.25s">
					<div class="seating-card-icon">🪑</div>
					<h2>Salon Oturma Düzeni</h2>
					<p>Misafirleriniz için masa ve koltuk yerleşimini oluşturabilirsiniz.</p>
					<div class="layout-buttons">
						{#each info.reserved_layouts as layout}
							<button onclick={() => goToSeating(layout.id)} class="seating-btn">
								<span class="seating-btn-icon">🪑</span>
								{layout.name} — Yerleşimi Düzenle
								<span class="seating-btn-arrow">→</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</main>

	<!-- ── Footer ─────────────────────────── -->
	<footer class="portal-footer">
		<img src="/logo-dikey.png" alt="Eventra" class="footer-logo" />
		<p>Bu portal <strong>Eventra</strong> etkinlik yönetim sistemi tarafından oluşturulmuştur.</p>
	</footer>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
		background: #080e1c;
		color: #f1f5f9;
		overflow-x: hidden;
	}
	:global(*) { box-sizing: border-box; }
	:global(input, select, textarea, button) { font: inherit; }

	/* ── Animated background ── */
	.portal-shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background:
			radial-gradient(ellipse 80% 50% at 50% -10%, rgba(197,155,49,0.14) 0%, transparent 60%),
			radial-gradient(ellipse 60% 40% at 80% 100%, rgba(99,102,241,0.1) 0%, transparent 55%),
			radial-gradient(ellipse 50% 50% at 10% 60%, rgba(197,155,49,0.06) 0%, transparent 60%),
			linear-gradient(160deg, #080e1c 0%, #0d1526 40%, #0a1020 100%);
		position: relative;
	}

	/* ── Sparkles ── */
	.sparkle-layer {
		position: fixed;
		inset: 0;
		pointer-events: none;
		z-index: 0;
		overflow: hidden;
	}

	.sparkle {
		position: absolute;
		bottom: -10px;
		border-radius: 50%;
		background: radial-gradient(circle, #f0c040 0%, rgba(197,155,49,0.4) 50%, transparent 70%);
		animation: sparkle-rise linear infinite;
	}

	@keyframes sparkle-rise {
		0%   { transform: translateY(0) scale(1) rotate(0deg); opacity: var(--op, 0.35); }
		50%  { transform: translateY(-45vh) scale(1.3) rotate(180deg); opacity: calc(var(--op, 0.35) * 1.5); }
		100% { transform: translateY(-100vh) scale(0.6) rotate(360deg); opacity: 0; }
	}

	/* ── Entrance animations ── */
	.portal-shell { opacity: 0; transition: opacity 0.4s ease; }
	.portal-shell.mounted { opacity: 1; }

	.animate-in {
		opacity: 0;
		transform: translateY(20px);
		animation: slide-up 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
	}

	@keyframes slide-up {
		to { opacity: 1; transform: translateY(0); }
	}

	/* ── Header ── */
	.portal-header {
		position: relative;
		z-index: 10;
		border-bottom: 1px solid rgba(197,155,49,0.15);
		background: linear-gradient(180deg, rgba(197,155,49,0.06) 0%, transparent 100%);
		backdrop-filter: blur(12px);
	}

	.header-inner {
		max-width: 780px;
		margin: 0 auto;
		padding: 1.1rem 1.5rem;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}

	.brand-block {
		display: flex;
		align-items: center;
		gap: 0.9rem;
	}

	.brand-logo-wrap {
		position: relative;
		width: 52px;
		height: 52px;
		display: grid;
		place-items: center;
		border-radius: 10px;
		background: rgba(197,155,49,0.12);
		border: 1px solid rgba(197,155,49,0.25);
	}

	.brand-logo {
		width: 38px;
		height: 38px;
		object-fit: contain;
		filter: drop-shadow(0 0 12px rgba(197,155,49,0.6));
		animation: logo-pulse 3s ease-in-out infinite;
	}

	@keyframes logo-pulse {
		0%, 100% { filter: drop-shadow(0 0 10px rgba(197,155,49,0.5)); }
		50%       { filter: drop-shadow(0 0 22px rgba(197,155,49,0.9)); }
	}

	.logo-glow {
		position: absolute;
		inset: -4px;
		border-radius: 14px;
		background: radial-gradient(circle, rgba(197,155,49,0.2), transparent 70%);
		animation: glow-pulse 3s ease-in-out infinite;
	}

	@keyframes glow-pulse {
		0%, 100% { opacity: 0.5; }
		50%       { opacity: 1; }
	}

	.brand-text {
		position: relative;
		display: flex;
		align-items: center;
		padding-top: 0.6rem;
	}

	.header-crown {
		position: absolute;
		top: -18px;
		left: 50%;
		transform: translateX(-50%);
		width: 26px;
		height: 26px;
		object-fit: contain;
		filter: drop-shadow(0 0 8px rgba(197,155,49,0.8));
		animation: crown-bob 2.6s ease-in-out infinite;
	}

	@keyframes crown-bob {
		0%, 100% { transform: translateX(-50%) translateY(0); }
		50%       { transform: translateX(-50%) translateY(-3px); }
	}

	.header-wordmark {
		height: 28px;
		object-fit: contain;
		filter: brightness(1.15) drop-shadow(0 1px 6px rgba(197,155,49,0.3));
	}

	.salon-chip {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.4rem 0.9rem;
		border-radius: 999px;
		background: rgba(197,155,49,0.1);
		border: 1px solid rgba(197,155,49,0.25);
		font-size: 0.82rem;
		font-weight: 700;
		color: rgba(240,192,64,0.9);
		white-space: nowrap;
	}

	.salon-chip-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: #c59b31;
		box-shadow: 0 0 6px #c59b31;
		animation: dot-blink 2s ease-in-out infinite;
	}

	@keyframes dot-blink {
		0%, 100% { opacity: 1; }
		50%       { opacity: 0.4; }
	}

	/* ── Main ── */
	.portal-main {
		flex: 1;
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.5rem;
		padding: 2.5rem 1rem 4rem;
		max-width: 680px;
		width: 100%;
		margin: 0 auto;
	}

	/* ── State cards ── */
	.state-card {
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.1rem;
		padding: 3.5rem 2rem;
		background: rgba(255,255,255,0.04);
		border: 1px solid rgba(255,255,255,0.1);
		border-radius: 20px;
		text-align: center;
		backdrop-filter: blur(8px);
	}

	.error-card { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.06); }
	.success-card { border-color: rgba(197,155,49,0.35); background: rgba(197,155,49,0.06); }
	.state-text { color: rgba(255,255,255,0.5); margin: 0; }

	.state-icon {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		font-size: 1.8rem;
		font-weight: 900;
	}

	.error-icon { background: rgba(239,68,68,0.15); color: #ef4444; border: 2px solid rgba(239,68,68,0.3); }
	.success-icon { background: rgba(197,155,49,0.15); color: #c59b31; border: 2px solid rgba(197,155,49,0.4); }

	.success-burst {
		position: relative;
		display: grid;
		place-items: center;
	}

	.success-crown {
		position: absolute;
		top: -28px;
		width: 38px;
		height: 38px;
		object-fit: contain;
		filter: drop-shadow(0 0 10px rgba(197,155,49,0.9));
		animation: crown-bob 2.6s ease-in-out infinite;
	}

	.state-card h2 { margin: 0; font-size: 1.5rem; font-weight: 900; color: #f0c040; }
	.state-card p { margin: 0; color: rgba(255,255,255,0.65); font-size: 0.92rem; line-height: 1.6; }

	/* ── Spinner ── */
	.spinner-ring {
		width: 52px;
		height: 52px;
		border: 3px solid rgba(255,255,255,0.08);
		border-top-color: #c59b31;
		border-right-color: rgba(197,155,49,0.4);
		border-radius: 50%;
		animation: spin 0.75s linear infinite;
	}

	@keyframes spin { to { transform: rotate(360deg); } }

	/* ── Event hero ── */
	.event-hero {
		position: relative;
		width: 100%;
		padding: 2.5rem 2rem 2rem;
		background:
			radial-gradient(ellipse 80% 60% at 50% 0%, rgba(197,155,49,0.18) 0%, transparent 65%),
			rgba(197,155,49,0.05);
		border: 1px solid rgba(197,155,49,0.28);
		border-radius: 20px;
		text-align: center;
		overflow: hidden;
		backdrop-filter: blur(6px);
	}

	.hero-glow-ring {
		position: absolute;
		inset: -1px;
		border-radius: 20px;
		background: transparent;
		border: 1px solid rgba(197,155,49,0.15);
		animation: border-glow 3s ease-in-out infinite;
		pointer-events: none;
	}

	@keyframes border-glow {
		0%, 100% { box-shadow: 0 0 20px rgba(197,155,49,0.1), inset 0 0 20px rgba(197,155,49,0.04); }
		50%       { box-shadow: 0 0 40px rgba(197,155,49,0.22), inset 0 0 30px rgba(197,155,49,0.08); }
	}

	.event-badge-row { margin-bottom: 1rem; }

	.event-type-badge {
		display: inline-block;
		padding: 0.35rem 1.1rem;
		border-radius: 999px;
		background: rgba(197,155,49,0.15);
		border: 1px solid rgba(197,155,49,0.35);
		font-size: 0.72rem;
		font-weight: 900;
		color: #f0c040;
		letter-spacing: 0.1em;
		text-transform: uppercase;
	}

	.crown-float-wrap {
		display: flex;
		justify-content: center;
		margin-bottom: 0.35rem;
	}

	.crown-float {
		width: 44px;
		height: 44px;
		object-fit: contain;
		filter: drop-shadow(0 0 16px rgba(197,155,49,0.85));
		animation: crown-float 3s ease-in-out infinite;
	}

	@keyframes crown-float {
		0%, 100% { transform: translateY(0) rotate(-2deg); }
		50%       { transform: translateY(-6px) rotate(2deg); }
	}

	.event-name {
		font-family: 'Great Vibes', cursive;
		font-size: clamp(2.4rem, 8vw, 3.8rem);
		font-weight: 400;
		color: #f0c040;
		margin: 0 0 1.1rem;
		line-height: 1.1;
		text-shadow: 0 0 40px rgba(197,155,49,0.4);
		animation: name-shimmer 4s ease-in-out infinite;
	}

	@keyframes name-shimmer {
		0%, 100% { text-shadow: 0 0 30px rgba(197,155,49,0.35); }
		50%       { text-shadow: 0 0 60px rgba(240,192,64,0.6), 0 0 100px rgba(197,155,49,0.2); }
	}

	.event-divider {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		justify-content: center;
		margin-bottom: 1.25rem;
	}

	.event-divider span {
		flex: 1;
		max-width: 80px;
		height: 1px;
		background: linear-gradient(90deg, transparent, rgba(197,155,49,0.5));
	}

	.event-divider span:last-child {
		background: linear-gradient(270deg, transparent, rgba(197,155,49,0.5));
	}

	.divider-icon {
		width: 22px;
		height: 22px;
		object-fit: contain;
		filter: drop-shadow(0 0 6px rgba(197,155,49,0.6));
		opacity: 0.85;
	}

	.event-meta {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		align-items: center;
		gap: 0.5rem;
	}

	.meta-item {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		color: rgba(255,255,255,0.7);
		font-size: 0.9rem;
		font-family: 'Cormorant Garamond', serif;
		font-size: 1rem;
	}

	.meta-icon { font-size: 1rem; }

	.meta-sep {
		width: 4px;
		height: 4px;
		border-radius: 50%;
		background: rgba(197,155,49,0.5);
	}

	/* ── Form card ── */
	.form-card {
		width: 100%;
		background: rgba(255,255,255,0.03);
		border: 1px solid rgba(255,255,255,0.1);
		border-radius: 20px;
		overflow: hidden;
		backdrop-filter: blur(8px);
	}

	.form-card-header {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1.75rem 1.75rem 0;
	}

	.form-crown {
		width: 32px;
		height: 32px;
		object-fit: contain;
		flex-shrink: 0;
		margin-top: 0.2rem;
		filter: drop-shadow(0 0 8px rgba(197,155,49,0.6));
		animation: crown-bob 2.6s ease-in-out infinite;
	}

	.form-title { font-size: 1.2rem; font-weight: 900; margin: 0 0 0.3rem; color: #f1f5f9; }
	.form-subtitle { color: rgba(255,255,255,0.45); font-size: 0.86rem; margin: 0; }


	.form-fields { display: flex; flex-direction: column; gap: 1.25rem; padding: 1.5rem 1.75rem; }

	.field-group { display: flex; flex-direction: column; gap: 0.5rem; }
	.field-group > label { font-size: 0.85rem; font-weight: 700; color: rgba(255,255,255,0.75); letter-spacing: 0.01em; }
	.req { color: #f0c040; margin-left: 0.2rem; }

	input[type="text"], input[type="number"], input[type="date"], input[type="email"],
	input[type="tel"], input[type="time"], textarea, select {
		width: 100%;
		min-height: 46px;
		background: rgba(255,255,255,0.06);
		border: 1px solid rgba(255,255,255,0.12);
		border-radius: 12px;
		padding: 0.7rem 1rem;
		color: #f1f5f9;
		font-size: 0.95rem;
		transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
	}

	input:focus, textarea:focus, select:focus {
		outline: none;
		border-color: rgba(197,155,49,0.55);
		background: rgba(255,255,255,0.09);
		box-shadow: 0 0 0 3px rgba(197,155,49,0.1);
	}

	textarea { resize: vertical; min-height: 110px; }
	select option { background: #1e293b; color: #f1f5f9; }

	/* Custom checkbox */
	.check-label { display: flex; align-items: center; gap: 0.75rem; cursor: pointer; font-size: 0.9rem; color: rgba(255,255,255,0.75); }
	.check-label input { display: none; }
	.check-box {
		width: 20px; height: 20px; flex-shrink: 0;
		border: 2px solid rgba(255,255,255,0.2);
		border-radius: 6px;
		background: rgba(255,255,255,0.05);
		transition: all 0.2s;
		position: relative;
	}
	.check-label input:checked ~ .check-box {
		background: #c59b31;
		border-color: #c59b31;
		box-shadow: 0 0 10px rgba(197,155,49,0.4);
	}
	.check-label input:checked ~ .check-box::after {
		content: '✓';
		position: absolute;
		inset: 0;
		display: grid;
		place-items: center;
		font-size: 11px;
		color: #0a1020;
		font-weight: 900;
	}

	.range-wrap { display: flex; align-items: center; gap: 1rem; }
	.range-wrap input { flex: 1; min-height: auto; padding: 0; accent-color: #c59b31; }
	.range-val { font-weight: 800; color: #f0c040; min-width: 32px; text-align: right; font-size: 1rem; }

	.form-error { color: #f87171; font-size: 0.85rem; padding: 0 1.75rem; margin: 0 0 0.5rem; }
	.form-success { color: #4ade80; font-size: 0.85rem; font-weight: 800; padding: 0 1.75rem; margin: 0 0 0.5rem; }

	/* Submit button */
	.submit-wrap { padding: 0 1.75rem 1.75rem; }

	.submit-btn {
		width: 100%;
		padding: 1rem 1.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.6rem;
		background: linear-gradient(135deg, #c59b31 0%, #a07a20 50%, #c59b31 100%);
		background-size: 200% 200%;
		animation: btn-shimmer 3s ease-in-out infinite;
		color: #0a1020;
		border: none;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 900;
		letter-spacing: 0.06em;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
		box-shadow: 0 4px 20px rgba(197,155,49,0.25);
	}

	@keyframes btn-shimmer {
		0%   { background-position: 0% 50%; }
		50%  { background-position: 100% 50%; }
		100% { background-position: 0% 50%; }
	}

	.submit-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 8px 32px rgba(197,155,49,0.4);
	}

	.submit-btn:active:not(:disabled) { transform: translateY(0); }
	.submit-btn:disabled { opacity: 0.55; cursor: not-allowed; animation: none; }

	.btn-crown { width: 20px; height: 20px; object-fit: contain; }
	.btn-spinner {
		width: 18px; height: 18px;
		border: 2px solid rgba(10,16,32,0.2);
		border-top-color: #0a1020;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
		flex-shrink: 0;
	}

	/* ── Seating card ── */
	.seating-card {
		width: 100%;
		padding: 1.75rem;
		background: rgba(255,255,255,0.03);
		border: 1px solid rgba(255,255,255,0.1);
		border-radius: 20px;
		backdrop-filter: blur(8px);
	}

	.seating-card-icon { font-size: 2rem; margin-bottom: 0.75rem; }
	.seating-card h2 { font-size: 1.15rem; font-weight: 900; margin: 0 0 0.35rem; }
	.seating-card p { color: rgba(255,255,255,0.5); font-size: 0.88rem; margin: 0 0 1.25rem; }

	.layout-buttons { display: flex; flex-direction: column; gap: 0.65rem; }

	.seating-btn {
		display: flex;
		align-items: center;
		gap: 0.65rem;
		padding: 0.9rem 1.25rem;
		background: rgba(197,155,49,0.07);
		border: 1px solid rgba(197,155,49,0.2);
		border-radius: 12px;
		color: #f1f5f9;
		font-weight: 800;
		font-size: 0.92rem;
		cursor: pointer;
		text-align: left;
		transition: all 0.18s;
	}

	.seating-btn:hover {
		background: rgba(197,155,49,0.14);
		border-color: rgba(197,155,49,0.4);
		transform: translateX(3px);
	}

	.seating-btn-icon { font-size: 1.1rem; }
	.seating-btn-arrow { margin-left: auto; color: rgba(197,155,49,0.7); transition: transform 0.18s; }
	.seating-btn:hover .seating-btn-arrow { transform: translateX(4px); }

	.seating-prompt { margin-top: 1.5rem; width: 100%; }
	.seating-prompt-label { color: rgba(255,255,255,0.6); font-size: 0.88rem; margin: 0 0 0.85rem; }

	/* ── No form ── */
	.no-form-card {
		width: 100%;
		padding: 2rem;
		background: rgba(255,255,255,0.03);
		border: 1px solid rgba(255,255,255,0.08);
		border-radius: 16px;
		text-align: center;
		color: rgba(255,255,255,0.4);
		font-size: 0.9rem;
	}

	/* ── Payment card ── */
	.payment-card {
		width: 100%;
		background: rgba(255,255,255,0.03);
		border: 1px solid rgba(255,255,255,0.1);
		border-radius: 20px;
		overflow: hidden;
		backdrop-filter: blur(8px);
		padding: 1.75rem;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.payment-confirmed {
		display: flex;
		align-items: center;
		gap: 1.25rem;
	}

	.confirmed-icon {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		background: rgba(22,163,74,0.15);
		border: 2px solid rgba(22,163,74,0.4);
		color: #16a34a;
		font-size: 1.4rem;
		font-weight: 900;
		display: grid;
		place-items: center;
		flex-shrink: 0;
	}

	.payment-confirmed strong { font-size: 1.1rem; color: #4ade80; display: block; margin-bottom: 0.25rem; }
	.payment-confirmed p { margin: 0; color: rgba(255,255,255,0.6); font-size: 0.88rem; }

	.payment-header {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
	}

	.payment-icon { font-size: 2rem; flex-shrink: 0; }
	.payment-title { font-size: 1.15rem; font-weight: 900; margin: 0 0 0.25rem; color: #f1f5f9; }
	.payment-subtitle { color: rgba(255,255,255,0.45); font-size: 0.86rem; margin: 0; }

	.payment-appt-no {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: rgba(197,155,49,0.1);
		border: 1px solid rgba(197,155,49,0.3);
		border-radius: 10px;
		font-size: 0.88rem;
		color: rgba(255,255,255,0.7);
	}

	.payment-appt-no strong { color: #f0c040; font-size: 1rem; }

	.payment-details {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		padding: 1rem;
		background: rgba(255,255,255,0.04);
		border: 1px solid rgba(255,255,255,0.08);
		border-radius: 12px;
	}

	.payment-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		font-size: 0.9rem;
	}

	.payment-row span { color: rgba(255,255,255,0.45); flex-shrink: 0; }
	.payment-row strong { color: #f1f5f9; text-align: right; }

	.iban-row { flex-wrap: wrap; }
	.iban {
		font-family: 'Courier New', monospace;
		font-size: 0.85rem;
		letter-spacing: 0.05em;
		color: #f0c040;
		word-break: break-all;
	}

	.payment-claim-section { padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.07); }
	.claim-hint { color: rgba(255,255,255,0.45); font-size: 0.84rem; margin: 0 0 0.85rem; }

	.claim-btn {
		width: 100%;
		padding: 0.75rem 1.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.65rem;
		background: linear-gradient(135deg, rgba(22,163,74,0.2), rgba(22,163,74,0.08));
		border: 1px solid rgba(22,163,74,0.4);
		color: #4ade80;
		border-radius: 999px;
		font-size: 0.95rem;
		font-weight: 900;
		cursor: pointer;
		transition: all 0.2s;
	}

	.claim-btn-icon {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: rgba(22,163,74,0.25);
		display: inline-flex;
		align-items: center;
		justify-content: center;
		font-size: 0.85rem;
		flex-shrink: 0;
	}

	.admin-photos-card {
		width: 100%;
		padding: 1rem;
		background: rgba(255,255,255,0.03);
		border: 1px solid rgba(255,255,255,0.1);
		border-radius: 16px;
		backdrop-filter: blur(8px);
	}
	.admin-photos-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		gap: 0.6rem;
	}
	.admin-photo-thumb {
		display: block;
		border-radius: 10px;
		overflow: hidden;
		border: 1px solid rgba(197,155,49,0.2);
		aspect-ratio: 1;
	}
	.admin-photo-thumb img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		transition: transform 0.2s;
	}
	.admin-photo-thumb:hover img { transform: scale(1.05); }

	.message-card {
		display: flex;
		gap: 0.75rem;
		align-items: flex-start;
		padding: 1rem 1.25rem;
		background: rgba(255,255,255,0.04);
		border: 1px solid rgba(255,255,255,0.1);
		border-radius: 14px;
	}
	.message-icon { font-size: 1.3rem; flex-shrink: 0; }
	.message-card p { margin: 0; color: rgba(255,255,255,0.82); font-size: 0.92rem; line-height: 1.5; white-space: pre-wrap; }

	.claim-btn:hover:not(:disabled) {
		background: rgba(22,163,74,0.25);
		border-color: rgba(22,163,74,0.65);
		transform: translateY(-1px);
	}

	.claim-btn:disabled { opacity: 0.55; cursor: not-allowed; }

	.claim-sent {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.85rem 1rem;
		background: rgba(22,163,74,0.1);
		border: 1px solid rgba(22,163,74,0.3);
		border-radius: 10px;
		font-size: 0.88rem;
		color: rgba(255,255,255,0.7);
		font-weight: 700;
	}

	.claim-check {
		width: 28px;
		height: 28px;
		border-radius: 50%;
		background: rgba(22,163,74,0.2);
		color: #4ade80;
		display: grid;
		place-items: center;
		font-weight: 900;
		flex-shrink: 0;
	}

	/* ── Footer ── */
	.portal-footer {
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.65rem;
		padding: 2rem 1rem;
		border-top: 1px solid rgba(197,155,49,0.1);
		text-align: center;
		color: rgba(255,255,255,0.25);
		font-size: 0.8rem;
	}

	.footer-logo {
		height: 40px;
		object-fit: contain;
		filter: brightness(0.5) sepia(1) hue-rotate(5deg) saturate(0.8);
		opacity: 0.6;
	}

	.portal-footer strong { color: rgba(197,155,49,0.6); }

	/* ── Responsive ── */
	@media (max-width: 640px) {
		.header-inner { padding: 0.9rem 1rem; }
		.header-wordmark { height: 22px; }
		.brand-logo-wrap { width: 42px; height: 42px; }
		.brand-logo { width: 30px; height: 30px; }
		.portal-main { padding: 1.5rem 0.85rem 3rem; }
		.event-hero, .form-card-header { padding: 1.75rem 1.25rem 1.5rem; }
		.form-fields, .submit-wrap { padding-left: 1.25rem; padding-right: 1.25rem; }
		.salon-chip { display: none; }
	}
</style>
