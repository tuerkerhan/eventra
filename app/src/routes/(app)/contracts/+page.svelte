<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type EventApi, type SalonApi, getToken } from '$lib/api';

	const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

	interface ContractTemplate {
		id: string;
		name: string;
		original_filename: string;
		file_type: 'docx' | 'odt';
		created_at: string;
	}

	// ─── State ────────────────────────────────────────────────────────────────
	let events = $state<EventApi[]>([]);
	let salon = $state<SalonApi | null>(null);
	let templates = $state<ContractTemplate[]>([]);
	let loading = $state(true);

	let activeTab = $state<'templates' | 'generate'>('templates');
	let selectedTemplateId = $state<string | null>(null);
	let selectedEventId = $state<string | null>(null);

	// Upload form
	let uploadFile = $state<File | null>(null);
	let uploadName = $state('');
	let uploading = $state(false);
	let uploadError = $state('');

	// Generate
	let generating = $state(false);
	let genError = $state('');
	let genSuccess = $state('');

	const selectedTemplate = $derived(templates.find(t => t.id === selectedTemplateId) ?? null);
	const selectedEvent = $derived(events.find(e => e.id === selectedEventId) ?? null);

	onMount(async () => {
		try {
			const [evs, s] = await Promise.all([
				api.get<EventApi[]>('/events'),
				api.get<SalonApi>('/settings/salon')
			]);
			events = evs;
			salon = s;
			await loadTemplates();
		} catch {}
		loading = false;
	});

	async function loadTemplates() {
		templates = await api.get<ContractTemplate[]>('/contracts/templates');
	}

	// ─── Upload ───────────────────────────────────────────────────────────────
	function onFileChange(e: Event) {
		uploadError = '';
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		const ext = file.name.split('.').pop()?.toLowerCase();
		if (ext !== 'docx' && ext !== 'odt') {
			uploadError = 'Yalnızca .docx ve .odt dosyaları desteklenir.';
			uploadFile = null;
			return;
		}
		uploadFile = file;
		if (!uploadName.trim()) uploadName = file.name.replace(/\.[^.]+$/, '');
	}

	async function uploadTemplate() {
		if (!uploadFile) return;
		uploading = true;
		uploadError = '';
		try {
			const form = new FormData();
			form.append('file', uploadFile);
			form.append('name', uploadName.trim() || uploadFile.name);
			const res = await fetch(`${API}/contracts/templates/upload?name=${encodeURIComponent(uploadName.trim())}`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${getToken()}` },
				body: form
			});
			if (!res.ok) {
				const d = await res.json().catch(() => ({}));
				uploadError = d.detail ?? 'Yükleme başarısız';
			} else {
				uploadFile = null;
				uploadName = '';
				await loadTemplates();
			}
		} catch {
			uploadError = 'Sunucuya bağlanılamadı';
		} finally {
			uploading = false;
		}
	}

	async function deleteTemplate(id: string, name: string) {
		if (!confirm(`"${name}" şablonu silinsin mi?`)) return;
		await api.del(`/contracts/templates/${id}`);
		await loadTemplates();
		if (selectedTemplateId === id) selectedTemplateId = null;
	}

	// ─── Generate ─────────────────────────────────────────────────────────────
	async function generateContract() {
		if (!selectedEventId || !selectedTemplateId) return;
		generating = true;
		genError = '';
		genSuccess = '';
		try {
			const res = await fetch(
				`${API}/contracts/generate/${selectedEventId}?template_id=${selectedTemplateId}`,
				{ headers: { Authorization: `Bearer ${getToken()}` } }
			);
			if (!res.ok) {
				const d = await res.json().catch(() => ({}));
				genError = d.detail ?? 'Sözleşme oluşturulamadı';
				return;
			}
			const blob = await res.blob();
			const url = URL.createObjectURL(blob);
			const disp = res.headers.get('Content-Disposition') ?? '';
			const match = disp.match(/filename="([^"]+)"/);
			const filename = match ? match[1] : `sozlesme.${selectedTemplate?.file_type}`;
			const a = document.createElement('a');
			a.href = url;
			a.download = filename;
			a.click();
			URL.revokeObjectURL(url);
			genSuccess = `"${filename}" indirildi.`;
		} catch {
			genError = 'Sunucuya bağlanılamadı';
		} finally {
			generating = false;
		}
	}

	// ─── Helpers ──────────────────────────────────────────────────────────────
	const fmtDate = (s: string) => s ? new Date(s + 'T00:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
	const fmtMoney = (v: number) => `₺${Math.round(v).toLocaleString('tr-TR')}`;
	const fileIcon = (t: string) => t === 'docx' ? '📝' : '📄';

	const PLACEHOLDERS = [
		{ key: '%baslik%',            label: 'Etkinlik başlığı' },
		{ key: '%isim%',              label: 'Müşteri adı soyadı' },
		{ key: '%gelin_damat%',       label: 'Gelin & Damat' },
		{ key: '%tc_no%',             label: 'T.C. / Vergi No' },
		{ key: '%telefon%',           label: 'Telefon' },
		{ key: '%tarih%',             label: 'Etkinlik tarihi' },
		{ key: '%sozlesme_tarihi%',   label: 'Sözleşme tarihi' },
		{ key: '%baslama_saati%',     label: 'Başlama saati' },
		{ key: '%bitis_saati%',       label: 'Bitiş saati' },
		{ key: '%tip%',               label: 'Etkinlik tipi' },
		{ key: '%rezervasyon_durumu%',label: 'Rezervasyon durumu' },
		{ key: '%davetli_sayisi%',    label: 'Davetli sayısı' },
		{ key: '%adres%',             label: 'Adres' },
		{ key: '%bolge%',             label: 'Bölge' },
		{ key: '%toplam_ucret%',      label: 'Toplam ücret' },
		{ key: '%kapora%',            label: 'Kapora' },
		{ key: '%odenen%',            label: 'Ödenen toplam' },
		{ key: '%kalan%',             label: 'Kalan ücret' },
		{ key: '%sozlesme_no%',       label: 'Sözleşme no (otomatik)' },
		{ key: '%personel%',          label: 'Personel' },
		{ key: '%notlar%',            label: 'Notlar' },
		{ key: '%salon_adi%',         label: 'Salon adı' },
		{ key: '%salon_adresi%',      label: 'Salon adresi' },
		{ key: '%kdv_orani%',         label: 'KDV oranı' },
	];

	function copyPh(key: string) {
		navigator.clipboard.writeText(key).catch(() => {});
	}
</script>

<section class="page-shell">
	<div class="page-heading">
		<div>
			<p class="eyebrow">Sözleşmeler</p>
			<h1>Word & ODT Sözleşme Sistemi</h1>
			<p class="sub">Şablonuna placeholder yaz, sistem müşteriye özel doldurur ve indirir.</p>
		</div>
		<div class="tab-bar">
			<button class:active={activeTab === 'templates'} onclick={() => (activeTab = 'templates')} type="button">Şablonlar</button>
			<button class:active={activeTab === 'generate'}  onclick={() => (activeTab = 'generate')}  type="button">Sözleşme Oluştur</button>
		</div>
	</div>

	{#if activeTab === 'templates'}
	<!-- ── Şablon yönetimi ──────────────────────────────────────────────── -->
	<div class="two-col">

		<!-- Sol: Yükleme + Liste -->
		<div class="col-left">

			<!-- Upload -->
			<div class="panel upload-panel">
				<h2>Şablon Yükle</h2>
				<p class="hint">Word (.docx) veya LibreOffice (.odt) dosyana placeholder etiketlerini yaz, yükle.</p>

				<label class="file-drop" class:has-file={!!uploadFile}>
					<input type="file" accept=".docx,.odt" onchange={onFileChange} class="file-input" />
					{#if uploadFile}
						<span class="file-icon">{fileIcon(uploadFile.name.split('.').pop() ?? '')}</span>
						<span class="file-name">{uploadFile.name}</span>
						<span class="file-size">{(uploadFile.size / 1024).toFixed(0)} KB</span>
					{:else}
						<span class="drop-icon">📁</span>
						<span class="drop-text">Tıkla veya sürükle</span>
						<span class="drop-hint">.docx · .odt</span>
					{/if}
				</label>

				{#if uploadFile}
					<label class="field-label">
						<span>Şablon Adı</span>
						<input bind:value={uploadName} placeholder="Örn: Düğün Sözleşmesi" />
					</label>
				{/if}

				{#if uploadError}<p class="error-msg">{uploadError}</p>{/if}

				<button class="primary-btn" type="button" onclick={uploadTemplate} disabled={!uploadFile || uploading}>
					{uploading ? 'Yükleniyor…' : 'Şablonu Yükle'}
				</button>
			</div>

			<!-- Template list -->
			<div class="panel">
				<h2>Yüklü Şablonlar <span class="count">{templates.length}</span></h2>
				{#if templates.length === 0}
					<p class="empty">Henüz şablon yok.</p>
				{:else}
					<div class="tmpl-list">
						{#each templates as t}
							<div class="tmpl-row" class:selected={selectedTemplateId === t.id}>
								<button class="tmpl-btn" type="button" onclick={() => (selectedTemplateId = selectedTemplateId === t.id ? null : t.id)}>
									<span class="tmpl-icon">{fileIcon(t.file_type)}</span>
									<div class="tmpl-info">
										<strong>{t.name}</strong>
										<span>{t.original_filename} · {new Date(t.created_at).toLocaleDateString('tr-TR')}</span>
									</div>
									<span class="ext-badge {t.file_type}">.{t.file_type}</span>
								</button>
								<button class="del-btn" type="button" onclick={() => deleteTemplate(t.id, t.name)} title="Sil">✕</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Sağ: Placeholder referans -->
		<div class="col-right panel ph-panel">
			<h2>Placeholder Referansı</h2>
			<p class="hint">Bu etiketleri Word/ODT şablonuna birebir yaz. Sözleşme oluşturulurken sistem otomatik doldurur. Tıkla → kopyala.</p>

			<div class="ph-grid">
				{#each PLACEHOLDERS as ph}
					<button class="ph-chip" type="button" onclick={() => copyPh(ph.key)} title="Kopyala">
						<code>{ph.key}</code>
						<span>{ph.label}</span>
					</button>
				{/each}
			</div>

			<div class="ph-note">
				<strong>Nasıl çalışır?</strong>
				<ol>
					<li>Word veya LibreOffice'te sözleşme şablonunu oluştur.</li>
					<li>Müşteriye özel alanların yerine yukarıdaki etiketleri yaz.<br><em>Örn: "Sayın <code>%isim%</code>,"</em></li>
					<li>Dosyayı <code>.docx</code> veya <code>.odt</code> olarak kaydet.</li>
					<li>Sol panelden yükle, ardından "Sözleşme Oluştur" sekmesinden indir.</li>
				</ol>
			</div>
		</div>
	</div>

	{:else}
	<!-- ── Sözleşme oluştur ─────────────────────────────────────────────── -->
	<div class="generate-layout">

		<!-- Sidebar -->
		<aside class="gen-sidebar">
			<div class="panel">
				<h2>1 — Davet Seç</h2>
				{#if loading}
					<p class="hint">Yükleniyor…</p>
				{:else if events.length === 0}
					<p class="empty">Henüz etkinlik yok.</p>
				{:else}
					<div class="event-list">
						{#each events as ev}
							<button class="ev-item" class:selected={selectedEventId === ev.id}
								type="button" onclick={() => (selectedEventId = ev.id)}>
								<strong>{ev.title}</strong>
								<span>{ev.event_date} · {ev.guest_count} kişi</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<div class="panel">
				<h2>2 — Şablon Seç</h2>
				{#if templates.length === 0}
					<p class="empty">Önce "Şablonlar" sekmesinden bir dosya yükleyin.</p>
				{:else}
					<div class="event-list">
						{#each templates as t}
							<button class="ev-item" class:selected={selectedTemplateId === t.id}
								type="button" onclick={() => (selectedTemplateId = t.id)}>
								<strong>{fileIcon(t.file_type)} {t.name}</strong>
								<span>.{t.file_type} · {new Date(t.created_at).toLocaleDateString('tr-TR')}</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<button class="gen-btn" type="button"
				onclick={generateContract}
				disabled={!selectedEventId || !selectedTemplateId || generating}>
				{generating ? 'Oluşturuluyor…' : '⬇ Sözleşme Oluştur & İndir'}
			</button>

			{#if genError}<p class="error-msg">{genError}</p>{/if}
			{#if genSuccess}<p class="success-msg">✓ {genSuccess}</p>{/if}
		</aside>

		<!-- Preview panel -->
		<div class="panel preview-panel">
			{#if selectedEvent && selectedTemplate}
				<div class="preview-head">
					<div>
						<h2>{selectedEvent.title}</h2>
						<p>{fmtDate(selectedEvent.event_date)} · {selectedEvent.guest_count} kişi</p>
					</div>
					<div class="preview-tmpl">
						<span>{fileIcon(selectedTemplate.file_type)}</span>
						<span>{selectedTemplate.name}</span>
						<span class="ext-badge {selectedTemplate.file_type}">.{selectedTemplate.file_type}</span>
					</div>
				</div>

				<div class="event-detail-grid">
					<div class="detail-row"><span>Müşteri</span><strong>{selectedEvent.full_name || '—'}</strong></div>
					<div class="detail-row"><span>Gelin & Damat</span><strong>{selectedEvent.bride_groom || '—'}</strong></div>
					<div class="detail-row"><span>T.C. No</span><strong>{selectedEvent.tc_no || '—'}</strong></div>
					<div class="detail-row"><span>Telefon</span><strong>{selectedEvent.mobile_phone || selectedEvent.phone || '—'}</strong></div>
					<div class="detail-row"><span>Saat</span><strong>{selectedEvent.start_time} – {selectedEvent.end_time}</strong></div>
					<div class="detail-row"><span>Rezervasyon</span><strong>{selectedEvent.reservation_status}</strong></div>
					<div class="detail-row"><span>Toplam Ücret</span><strong>{fmtMoney(selectedEvent.total_fee)}</strong></div>
					<div class="detail-row"><span>Kapora</span><strong>{fmtMoney(selectedEvent.kapora_amount)}</strong></div>
					<div class="detail-row"><span>Ödenen</span><strong>{fmtMoney(selectedEvent.total_paid)}</strong></div>
					<div class="detail-row"><span>Kalan</span><strong style="color:#dc2626">{fmtMoney(selectedEvent.total_fee - selectedEvent.total_paid)}</strong></div>
					{#if selectedEvent.address}
					<div class="detail-row full"><span>Adres</span><strong>{selectedEvent.address}</strong></div>
					{/if}
					{#if selectedEvent.note}
					<div class="detail-row full"><span>Not</span><strong>{selectedEvent.note}</strong></div>
					{/if}
				</div>

				<div class="gen-info">
					<p>Sözleşme No: <code>{salon?.contract_prefix ?? 'EVT'}-{selectedEvent.id.slice(0,8).toUpperCase()}</code></p>
					<p>Şablon dosyasındaki tüm <code>%placeholder%</code> alanları yukarıdaki verilerle doldurulacak.</p>
				</div>

				<button class="gen-btn-inline" type="button" onclick={generateContract} disabled={generating}>
					{generating ? 'Oluşturuluyor…' : `⬇ ${selectedTemplate.name} olarak indir (.${selectedTemplate.file_type})`}
				</button>

				{#if genError}<p class="error-msg">{genError}</p>{/if}
				{#if genSuccess}<p class="success-msg">✓ {genSuccess}</p>{/if}
			{:else}
				<div class="preview-empty">
					<div class="preview-empty-icon">📋</div>
					<h3>Sol taraftan davet ve şablon seçin</h3>
					<p>Seçim yaptıktan sonra burada etkinlik detayları görünür ve sözleşme indirilir.</p>
				</div>
			{/if}
		</div>
	</div>
	{/if}
</section>

<style>
	.page-shell { max-width: 1480px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.1rem; }
	.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
	h1, h2, h3, p { margin: 0; }
	h1 { font-size: clamp(1.6rem, 3vw, 2.6rem); }
	h2 { font-size: 1rem; font-weight: 900; }
	.eyebrow { margin-bottom: 0.25rem; color: var(--accent); font-size: 0.78rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; }
	.sub, .hint { color: var(--muted); font-size: 0.83rem; margin-top: 0.15rem; }

	.tab-bar { display: flex; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 0.3rem; gap: 0.25rem; }
	.tab-bar button { border: none; border-radius: 6px; padding: 0.6rem 1.1rem; background: transparent; color: var(--muted); font: inherit; font-weight: 800; cursor: pointer; }
	.tab-bar .active { background: var(--accent); color: #fff; }

	/* Layout */
	.two-col { display: grid; grid-template-columns: 360px 1fr; gap: 1rem; align-items: start; }
	.col-left { display: flex; flex-direction: column; gap: 1rem; }
	.col-right { flex: 1; }
	.generate-layout { display: grid; grid-template-columns: 300px 1fr; gap: 1rem; align-items: start; }
	.gen-sidebar { display: flex; flex-direction: column; gap: 1rem; }

	/* Panel */
	.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 1.1rem; display: flex; flex-direction: column; gap: 0.85rem; box-shadow: 0 10px 28px rgba(0,0,0,0.1); }

	/* Upload */
	.upload-panel { gap: 0.9rem; }
	.file-drop { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.4rem; min-height: 120px; border: 2px dashed var(--line); border-radius: 10px; cursor: pointer; padding: 1.25rem; background: var(--surface-strong); transition: border-color 0.15s; position: relative; }
	.file-drop:hover { border-color: color-mix(in srgb, var(--accent) 50%, transparent); }
	.file-drop.has-file { border-color: var(--accent); background: var(--accent-soft); }
	.file-input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
	.drop-icon, .file-icon { font-size: 2rem; }
	.drop-text { font-weight: 800; font-size: 0.92rem; }
	.drop-hint, .file-size { font-size: 0.76rem; color: var(--muted); }
	.file-name { font-weight: 800; font-size: 0.88rem; color: var(--accent); }

	/* Template list */
	.count { font-size: 0.78rem; color: var(--muted); margin-left: 0.35rem; }
	.tmpl-list { display: flex; flex-direction: column; gap: 0.45rem; }
	.tmpl-row { display: flex; align-items: center; gap: 0.35rem; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-strong); transition: border-color 0.15s; overflow: hidden; }
	.tmpl-row.selected { border-color: var(--accent); }
	.tmpl-btn { flex: 1; display: flex; align-items: center; gap: 0.65rem; padding: 0.7rem 0.85rem; background: transparent; border: none; color: var(--text); font: inherit; cursor: pointer; text-align: left; }
	.tmpl-icon { font-size: 1.2rem; flex-shrink: 0; }
	.tmpl-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 0.1rem; }
	.tmpl-info strong { font-size: 0.88rem; font-weight: 800; }
	.tmpl-info span { font-size: 0.72rem; color: var(--muted); }
	.ext-badge { font-size: 0.68rem; font-weight: 900; padding: 0.15rem 0.4rem; border-radius: 4px; text-transform: uppercase; }
	.ext-badge.docx { background: rgba(37,99,235,0.12); color: #2563eb; }
	.ext-badge.odt { background: rgba(5,150,105,0.12); color: #059669; }
	.del-btn { padding: 0.7rem 0.75rem; background: transparent; border: none; color: var(--muted); cursor: pointer; font-size: 0.82rem; flex-shrink: 0; }
	.del-btn:hover { color: #dc2626; }

	/* Placeholder panel */
	.ph-panel { gap: 1rem; }
	.ph-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.4rem; }
	.ph-chip { display: flex; flex-direction: column; gap: 0.15rem; padding: 0.5rem 0.7rem; border: 1px solid var(--line); border-radius: 7px; background: var(--surface-strong); color: var(--text); cursor: pointer; text-align: left; font: inherit; transition: all 0.15s; }
	.ph-chip:hover { border-color: color-mix(in srgb, var(--accent) 50%, transparent); background: var(--accent-soft); }
	.ph-chip code { font-family: 'Courier New', monospace; font-size: 0.77rem; color: var(--accent); font-weight: 700; }
	.ph-chip span { font-size: 0.72rem; color: var(--muted); }
	.ph-note { background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; padding: 1rem; font-size: 0.82rem; color: var(--muted); line-height: 1.65; }
	.ph-note strong { color: var(--text); display: block; margin-bottom: 0.5rem; }
	.ph-note ol { margin: 0; padding-left: 1.2rem; display: flex; flex-direction: column; gap: 0.35rem; }
	.ph-note code { font-family: 'Courier New', monospace; color: var(--accent); }

	/* Generate */
	.event-list { display: flex; flex-direction: column; gap: 0.4rem; max-height: 260px; overflow-y: auto; }
	.ev-item { border: 1px solid var(--line); border-radius: 7px; padding: 0.6rem 0.8rem; background: var(--surface-strong); color: var(--text); font: inherit; text-align: left; cursor: pointer; display: flex; flex-direction: column; gap: 0.12rem; transition: all 0.15s; }
	.ev-item strong { font-size: 0.88rem; font-weight: 800; }
	.ev-item span { font-size: 0.73rem; color: var(--muted); }
	.ev-item.selected { border-color: var(--accent); background: var(--accent-soft); }

	.gen-btn { width: 100%; border: none; border-radius: 9px; padding: 0.9rem; background: var(--accent); color: #fff; font: inherit; font-weight: 900; font-size: 0.95rem; cursor: pointer; }
	.gen-btn:disabled { opacity: 0.5; cursor: not-allowed; }
	.gen-btn-inline { border: none; border-radius: 9px; padding: 0.85rem 1.25rem; background: var(--accent); color: #fff; font: inherit; font-weight: 900; font-size: 0.92rem; cursor: pointer; align-self: flex-start; }
	.gen-btn-inline:disabled { opacity: 0.5; cursor: not-allowed; }

	/* Preview */
	.preview-panel { min-height: 400px; }
	.preview-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
	.preview-head h2 { font-size: 1.15rem; }
	.preview-head p { color: var(--muted); font-size: 0.82rem; margin-top: 0.15rem; }
	.preview-tmpl { display: flex; align-items: center; gap: 0.4rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 7px; padding: 0.4rem 0.75rem; font-size: 0.82rem; font-weight: 800; flex-shrink: 0; }
	.event-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
	.detail-row { display: flex; flex-direction: column; gap: 0.15rem; padding: 0.65rem 0.85rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 7px; }
	.detail-row.full { grid-column: 1 / -1; }
	.detail-row span { font-size: 0.73rem; color: var(--muted); font-weight: 800; }
	.detail-row strong { font-size: 0.9rem; }
	.gen-info { background: var(--accent-soft); border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent); border-radius: 8px; padding: 0.85rem 1rem; font-size: 0.82rem; display: flex; flex-direction: column; gap: 0.3rem; color: var(--muted); }
	.gen-info code { font-family: 'Courier New', monospace; color: var(--accent); font-weight: 700; }
	.preview-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; min-height: 320px; gap: 0.75rem; text-align: center; color: var(--muted); }
	.preview-empty-icon { font-size: 3rem; }
	.preview-empty h3 { color: var(--text); font-size: 1.05rem; margin: 0; }

	/* Shared */
	.field-label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; font-size: 0.84rem; }
	.field-label span { color: var(--muted); }
	input { width: 100%; min-height: 38px; border: 1px solid var(--line); border-radius: 7px; padding: 0.5rem 0.7rem; background: var(--surface-strong); color: var(--text); font: inherit; }
	.primary-btn { border: none; border-radius: 8px; padding: 0.7rem 1.1rem; background: var(--accent); color: #fff; font: inherit; font-weight: 900; font-size: 0.88rem; cursor: pointer; }
	.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }
	.error-msg { color: #dc2626; font-size: 0.82rem; font-weight: 700; background: rgba(220,38,38,0.08); border: 1px solid rgba(220,38,38,0.2); border-radius: 7px; padding: 0.6rem 0.85rem; }
	.success-msg { color: #16a34a; font-size: 0.82rem; font-weight: 700; background: rgba(22,163,74,0.08); border: 1px solid rgba(22,163,74,0.2); border-radius: 7px; padding: 0.6rem 0.85rem; }
	.empty { color: var(--muted); font-size: 0.84rem; text-align: center; padding: 1rem 0; }

	@media (max-width: 1100px) { .two-col, .generate-layout { grid-template-columns: 1fr; } }
	@media (max-width: 720px) { .page-heading { flex-direction: column; align-items: stretch; } .event-detail-grid { grid-template-columns: 1fr; } }
</style>
