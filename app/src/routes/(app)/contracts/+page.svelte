<script lang="ts">
	import { onMount } from 'svelte';
	import { api, getToken } from '$lib/api';

	const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

	interface ContractTemplate {
		id: string;
		name: string;
		original_filename: string;
		file_type: 'docx' | 'odt';
		created_at: string;
	}

	interface EventFormFieldDef {
		key: string;
		label: string;
		placeholder_tag: string;
		is_builtin: boolean;
	}

	// ─── State ────────────────────────────────────────────────────────────────
	let templates = $state<ContractTemplate[]>([]);
	let fieldDefs = $state<EventFormFieldDef[]>([]);
	let selectedTemplateId = $state<string | null>(null);

	// Upload form
	let uploadFile = $state<File | null>(null);
	let uploadName = $state('');
	let uploading = $state(false);
	let uploadError = $state('');

	onMount(async () => {
		await Promise.all([loadTemplates(), loadFieldDefs()]).catch(() => {});
	});

	async function loadTemplates() {
		templates = await api.get<ContractTemplate[]>('/contracts/templates');
	}

	async function loadFieldDefs() {
		fieldDefs = await api.get<EventFormFieldDef[]>('/event-form-fields');
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

	// ─── Helpers ──────────────────────────────────────────────────────────────
	const fileIcon = (t: string) => t === 'docx' ? '📝' : '📄';

	const BASE_PLACEHOLDERS = [
		{ key: '%randevu_no%',        label: 'Randevu no' },
		{ key: '%isim%',              label: 'Müşteri adı soyadı' },
		{ key: '%tc_no%',             label: 'T.C. / Vergi No' },
		{ key: '%telefon%',           label: 'Telefon' },
		{ key: '%email%',             label: 'E-posta' },
		{ key: '%adres%',             label: 'Adres' },
		{ key: '%tarih%',             label: 'Etkinlik tarihi' },
		{ key: '%baslama_saati%',     label: 'Başlama saati' },
		{ key: '%bitis_saati%',       label: 'Bitiş saati' },
		{ key: '%tip%',               label: 'Organizasyon tipi' },
		{ key: '%davetli_sayisi%',    label: 'Davetli sayısı' },
		{ key: '%toplam_ucret%',      label: 'Toplam ücret' },
		{ key: '%kapora%',            label: 'Kapora' },
		{ key: '%kalan%',             label: 'Kalan ücret' },
		{ key: '%notlar%',            label: 'Form notu' },
		{ key: '%salon_adi%',         label: 'Salon adı' },
	];

	const CUSTOM_PLACEHOLDERS = $derived(
		fieldDefs
			.filter((field) => !field.is_builtin)
			.map((field) => ({
				key: field.placeholder_tag || `%${field.key}%`,
				label: field.label
			}))
	);

	const PLACEHOLDERS = $derived([...BASE_PLACEHOLDERS, ...CUSTOM_PLACEHOLDERS]);

	function copyPh(key: string) {
		navigator.clipboard.writeText(key).catch(() => {});
	}
</script>

<section class="page-shell">
	<div class="page-heading">
		<div>
			<p class="sub">Şablonuna placeholder yaz, sistem müşteriye özel doldurur ve indirir.</p>
		</div>
	</div>

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
					<li>Sol panelden yükle, ardından randevu detayındaki sözleşme bölümünden indir.</li>
				</ol>
			</div>
		</div>
	</div>
</section>

<style>
	.page-shell { max-width: 1480px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.1rem; }
	.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
	h2, p { margin: 0; }
	h2 { font-size: 1rem; font-weight: 900; }
	.eyebrow { margin-bottom: 0.25rem; color: var(--accent); font-size: 0.78rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; }
	.sub, .hint { color: var(--muted); font-size: 0.83rem; margin-top: 0.15rem; }

	/* Layout */
	.two-col { display: grid; grid-template-columns: 360px 1fr; gap: 1rem; align-items: start; }
	.col-left { display: flex; flex-direction: column; gap: 1rem; }
	.col-right { flex: 1; }

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

	/* Shared */
	.field-label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; font-size: 0.84rem; }
	.field-label span { color: var(--muted); }
	input { width: 100%; min-height: 38px; border: 1px solid var(--line); border-radius: 7px; padding: 0.5rem 0.7rem; background: var(--surface-strong); color: var(--text); font: inherit; }
	.primary-btn { border: none; border-radius: 8px; padding: 0.7rem 1.1rem; background: var(--accent); color: #fff; font: inherit; font-weight: 900; font-size: 0.88rem; cursor: pointer; }
	.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }
	.error-msg { color: #dc2626; font-size: 0.82rem; font-weight: 700; background: rgba(220,38,38,0.08); border: 1px solid rgba(220,38,38,0.2); border-radius: 7px; padding: 0.6rem 0.85rem; }
	.empty { color: var(--muted); font-size: 0.84rem; text-align: center; padding: 1rem 0; }

	@media (max-width: 1100px) { .two-col { grid-template-columns: 1fr; } }
	@media (max-width: 720px) { .page-heading { flex-direction: column; align-items: stretch; } }
</style>
