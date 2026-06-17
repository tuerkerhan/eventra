<script lang="ts">
	import { onMount } from 'svelte';

	const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

	interface AdminSettings {
		smtp_host: string;
		smtp_port: number;
		smtp_username: string;
		smtp_password: string;
		smtp_from_email: string;
		smtp_use_tls: boolean;
		support_phone: string;
		booking_link: string;
		shared_support_email: string;
	}

	let settings = $state<AdminSettings>({
		smtp_host: '', smtp_port: 587, smtp_username: '', smtp_password: '',
		smtp_from_email: '', smtp_use_tls: true,
		support_phone: '', booking_link: '', shared_support_email: ''
	});
	let saving = $state(false);
	let saved = $state(false);
	let testEmail = $state('');
	let testing = $state(false);
	let testResult = $state<{ ok: boolean; detail?: string } | null>(null);
	let loadError = $state('');

	const headers = () => ({
		'Content-Type': 'application/json',
		Authorization: `Bearer ${localStorage.getItem('admin_token')}`
	});

	onMount(async () => {
		try {
			const r = await fetch(`${API}/admin/settings`, { headers: headers() });
			if (r.ok) settings = await r.json();
		} catch (e) {
			loadError = 'Yükleme hatası';
		}
	});

	async function save() {
		saving = true;
		try {
			const r = await fetch(`${API}/admin/settings`, {
				method: 'PATCH',
				headers: headers(),
				body: JSON.stringify(settings)
			});
			if (r.ok) { settings = await r.json(); saved = true; setTimeout(() => saved = false, 2500); }
		} finally { saving = false; }
	}

	async function sendTestMail() {
		if (!testEmail) return;
		testing = true;
		testResult = null;
		try {
			const r = await fetch(`${API}/admin/settings/test-mail`, {
				method: 'POST',
				headers: headers(),
				body: JSON.stringify({ to_email: testEmail })
			});
			testResult = r.ok ? { ok: true } : { ok: false, detail: (await r.json()).detail };
		} catch (e) {
			testResult = { ok: false, detail: 'Bağlantı hatası' };
		} finally { testing = false; }
	}
</script>

<div class="shell">
	<div class="page-head">
		<div><p class="eyebrow">Admin</p><h1>Ayarlar</h1></div>
	</div>

	{#if loadError}
		<div class="error-bar">{loadError}</div>
	{/if}

	<div class="grid">
		<div class="panel">
			<h2>Admin SMTP Ayarları</h2>
			<p class="hint">Müşterilere gönderilecek broadcast mailleri ve ticket bildirimleri bu SMTP üzerinden gider.</p>
			<form class="form" onsubmit={(e) => { e.preventDefault(); save(); }}>
				<label><span>SMTP Host</span><input bind:value={settings.smtp_host} placeholder="smtp.example.com" /></label>
				<label><span>Port</span><input type="number" bind:value={settings.smtp_port} /></label>
				<label><span>Kullanıcı Adı</span><input bind:value={settings.smtp_username} /></label>
				<label><span>Şifre</span><input type="password" bind:value={settings.smtp_password} /></label>
				<label class="full"><span>Gönderici E-posta</span><input bind:value={settings.smtp_from_email} placeholder="noreply@eventra.com" /></label>
				<label class="full"><span>Ortak Destek E-postası</span><input type="email" bind:value={settings.shared_support_email} placeholder="destek@sirket.com" /></label>
				<label class="check-label">
					<input type="checkbox" bind:checked={settings.smtp_use_tls} />
					STARTTLS kullan
				</label>
				<button class="save-btn" type="submit" disabled={saving}>{saving ? 'Kaydediliyor…' : saved ? '✓ Kaydedildi' : 'Kaydet'}</button>
			</form>

			<div class="test-row">
				<input bind:value={testEmail} placeholder="test@example.com" type="email" />
				<button class="test-btn" type="button" onclick={sendTestMail} disabled={testing}>
					{testing ? 'Gönderiliyor…' : 'Test Maili Gönder'}
				</button>
			</div>
			{#if testResult}
				<p class="test-result" class:ok={testResult.ok} class:fail={!testResult.ok}>
					{testResult.ok ? '✓ Mail gönderildi' : `✗ Hata: ${testResult.detail}`}
				</p>
			{/if}
		</div>

		<div class="panel">
			<h2>Destek Bilgileri</h2>
			<p class="hint">Müşterilere Teknik Destek sekmesinde gösterilecek bilgiler.</p>
			<div class="form">
				<label><span>Destek Telefonu</span><input bind:value={settings.support_phone} placeholder="+90 500 000 00 00" /></label>
				<label class="full"><span>Randevu Linki (Proton Takvim vb.)</span><input bind:value={settings.booking_link} placeholder="https://cal.proton.me/..." /></label>
			</div>
			<div class="form-actions">
				<button class="save-btn" type="button" onclick={save} disabled={saving}>{saving ? 'Kaydediliyor…' : saved ? '✓ Kaydedildi' : 'Kaydet'}</button>
			</div>
		</div>
	</div>
</div>

<style>
	.shell { display: flex; flex-direction: column; gap: 1.5rem; }
	.page-head { display: flex; align-items: flex-end; justify-content: space-between; }
	h1, h2, p { margin: 0; }
	h1 { font-size: clamp(1.6rem, 3vw, 2.4rem); font-weight: 900; }
	h2 { font-size: 1.05rem; font-weight: 900; margin-bottom: 0.5rem; }
	.eyebrow { margin-bottom: 0.25rem; color: #c59b31; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase; }
	.hint { color: #64748b; font-size: 0.83rem; margin-bottom: 0.85rem; }

	.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; align-items: start; }
	.panel { background: #172033; border: 1px solid rgba(226,232,240,0.1); border-radius: 10px; padding: 1.5rem; }

	.form { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
	.form .full { grid-column: 1 / -1; }
	.form-actions { margin-top: 0.85rem; }

	label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; font-size: 0.85rem; color: #94a3b8; }
	input { width: 100%; min-height: 40px; border: 1px solid rgba(226,232,240,0.15); border-radius: 8px; padding: 0.55rem 0.75rem; background: #101827; color: #f8fafc; font: inherit; }

	.check-label { flex-direction: row !important; align-items: center; gap: 0.4rem; color: #94a3b8; font-size: 0.85rem; }
	.check-label input { width: auto; min-height: auto; }

	.save-btn { padding: 0.7rem 1.4rem; background: #c59b31; color: #fff; border: 0; border-radius: 8px; font-weight: 900; cursor: pointer; }
	.save-btn:disabled { opacity: 0.7; cursor: not-allowed; }

	.test-row { display: flex; gap: 0.65rem; margin-top: 1rem; }
	.test-row input { flex: 1; }
	.test-btn { border: 1px solid rgba(197,155,49,0.35); border-radius: 8px; padding: 0.55rem 0.85rem; background: rgba(197,155,49,0.1); color: #c59b31; font-weight: 900; font-size: 0.85rem; cursor: pointer; white-space: nowrap; }

	.test-result { margin-top: 0.5rem; font-weight: 800; font-size: 0.85rem; }
	.test-result.ok { color: #16a34a; }
	.test-result.fail { color: #ef4444; }

	.error-bar { padding: 0.85rem 1rem; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25); border-radius: 8px; color: #fca5a5; font-weight: 800; }

	@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } .form { grid-template-columns: 1fr; } }
</style>
