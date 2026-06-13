<script lang="ts">
	interface Template {
		id: string;
		name: string;
		body: string;
	}

	interface MockEvent {
		id: string;
		title: string;
		date: string;
		fullName: string;
		brideGroom: string;
		start: string;
		end: string;
		type: string;
		guestCount: number;
		total: number;
		kapora: number;
		paid: number;
		address: string;
		region: string;
		mobilePhone: string;
		tcNo: string;
		staff: string;
		note: string;
		contractDate: string;
		reservationStatus: string;
	}

	// Örnek şablonlar
	let templates = $state<Template[]>([
		{
			id: 't1',
			name: 'Standart Düğün Sözleşmesi',
			body: `DAVET VE ORGANİZASYON SÖZLEŞMESİ
Sözleşme No: %sozlesme_no%
Sözleşme Tarihi: %sozlesme_tarihi%

MÜŞTERİ BİLGİLERİ
Ad Soyad       : %isim%
Gelin & Damat  : %gelin_damat%
T.C. Kimlik No : %tc_no%
Telefon        : %telefon%
Bölge          : %bolge%
Adres          : %adres%

ETKİNLİK BİLGİLERİ
Tarihi         : %tarih%
Saati          : %baslama_saati% – %bitis_saati%
Niteliği       : %tip%
Durum          : %rezervasyon_durumu%
Davetli Sayısı : %davetli_sayisi% kişi

ÜCRET BİLGİLERİ
Toplam Ücret   : %toplam_ucret%
Kapora         : %kapora%
Ödenen         : %odenen%
Kalan          : %kalan%

PERSONEL        : %personel%

NOTLAR
%notlar%

Taraflar yukarıdaki koşulları kabul etmiştir.

Salon Yetkilisi: ___________________    Müşteri: ___________________`
		}
	]);

	// Mock events (gerçek uygulamada API'dan gelir)
	const mockEvents: MockEvent[] = [
		{
			id: '2962', title: 'Ayşe & Ahmet', date: '2026-06-18', contractDate: '2026-06-08',
			fullName: 'Ayşe Yılmaz', brideGroom: 'Ayşe Yılmaz & Ahmet Demir',
			start: '19:00', end: '23:30', type: 'Düğün', guestCount: 420,
			total: 150000, kapora: 25000, paid: 25000,
			address: 'İnci Davet Salonu, İstanbul', region: 'Üsküdar',
			mobilePhone: '0532 000 00 00', tcNo: '12345678910',
			staff: 'Elif, Mert, Can',
			note: 'Menü B, ekstra fotoğrafçı ve sahne ışığı istendi.',
			reservationStatus: 'Kesin Rezervasyon'
		},
		{
			id: '2963', title: 'Burcu & Cem', date: '2026-06-25', contractDate: '2026-06-10',
			fullName: 'Burcu Kaya', brideGroom: 'Burcu Kaya & Cem Arslan',
			start: '20:00', end: '00:00', type: 'Nişan', guestCount: 180,
			total: 85000, kapora: 15000, paid: 50000,
			address: 'İnci Davet Teras Salonu', region: 'Kadıköy',
			mobilePhone: '0544 111 22 33', tcNo: '',
			staff: 'Mert, Seda', note: 'Pasta dışarıdan gelecek.',
			reservationStatus: 'Kesin Rezervasyon'
		},
		{
			id: '2964', title: 'Derya & Emre', date: '2026-07-02', contractDate: '2026-06-12',
			fullName: 'Derya Aksoy', brideGroom: 'Derya Aksoy & Emre Çelik',
			start: '14:00', end: '18:00', type: 'Kına', guestCount: 140,
			total: 60000, kapora: 10000, paid: 60000,
			address: 'İnci Davet Salon 2', region: 'Ataşehir',
			mobilePhone: '0555 222 33 44', tcNo: '',
			staff: 'Seda, Can', note: 'Kına tahtı ve giriş müziği hazır.',
			reservationStatus: 'Kesin Rezervasyon'
		}
	];

	// UI state
	let activeTab = $state<'templates' | 'generate'>('templates');
	let selectedTemplateId = $state<string | null>(null);
	let selectedEventId = $state<string | null>(null);
	let preview = $state('');
	let editingTemplate = $state<Template | null>(null);
	let newName = $state('');
	let newBody = $state('');
	let showNewForm = $state(false);
	let uploadError = $state('');

	const formatMoney = (v: number) => `₺${Math.round(v).toLocaleString('tr-TR')}`;
	const formatDate = (d: string) => {
		if (!d) return '';
		try { return new Date(d + 'T00:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }); }
		catch { return d; }
	};

	const PLACEHOLDERS: { key: string; label: string; example: string }[] = [
		{ key: '%isim%',             label: 'Müşteri adı soyadı',  example: 'Ayşe Yılmaz' },
		{ key: '%gelin_damat%',      label: 'Gelin & Damat',       example: 'Ayşe Yılmaz & Ahmet Demir' },
		{ key: '%tc_no%',            label: 'T.C. / Vergi No',     example: '12345678910' },
		{ key: '%telefon%',          label: 'Telefon',             example: '0532 000 00 00' },
		{ key: '%tarih%',            label: 'Etkinlik tarihi',     example: '18 Haziran 2026' },
		{ key: '%baslama_saati%',    label: 'Başlama saati',       example: '19:00' },
		{ key: '%bitis_saati%',      label: 'Bitiş saati',         example: '23:30' },
		{ key: '%tip%',              label: 'Etkinlik tipi',       example: 'Düğün' },
		{ key: '%rezervasyon_durumu%', label: 'Rezervasyon durumu', example: 'Kesin Rezervasyon' },
		{ key: '%davetli_sayisi%',   label: 'Davetli sayısı',      example: '420' },
		{ key: '%adres%',            label: 'Adres',               example: 'İnci Davet Salonu' },
		{ key: '%bolge%',            label: 'Bölge',               example: 'Üsküdar' },
		{ key: '%toplam_ucret%',     label: 'Toplam ücret',        example: '₺150.000' },
		{ key: '%kapora%',           label: 'Kapora',              example: '₺25.000' },
		{ key: '%odenen%',           label: 'Ödenen toplam',       example: '₺25.000' },
		{ key: '%kalan%',            label: 'Kalan ücret',         example: '₺125.000' },
		{ key: '%sozlesme_no%',      label: 'Sözleşme no',         example: '2962' },
		{ key: '%sozlesme_tarihi%',  label: 'Sözleşme tarihi',     example: '8 Haziran 2026' },
		{ key: '%personel%',         label: 'Personel',            example: 'Elif, Mert' },
		{ key: '%notlar%',           label: 'Notlar',              example: 'Menü B istendi.' },
		{ key: '%gelin_damat%',      label: 'Gelin & Damat',       example: 'Ad & Ad' }
	];

	const fillTemplate = (body: string, ev: MockEvent): string => {
		const map: Record<string, string> = {
			'%isim%':               ev.fullName,
			'%gelin_damat%':        ev.brideGroom,
			'%tc_no%':              ev.tcNo,
			'%telefon%':            ev.mobilePhone,
			'%tarih%':              formatDate(ev.date),
			'%baslama_saati%':      ev.start,
			'%bitis_saati%':        ev.end,
			'%tip%':                ev.type,
			'%rezervasyon_durumu%': ev.reservationStatus,
			'%davetli_sayisi%':     String(ev.guestCount),
			'%adres%':              ev.address,
			'%bolge%':              ev.region,
			'%toplam_ucret%':       formatMoney(ev.total),
			'%kapora%':             formatMoney(ev.kapora),
			'%odened%':             formatMoney(ev.paid),
			'%odenen%':             formatMoney(ev.paid),
			'%kalan%':              formatMoney(ev.total - ev.paid),
			'%sozlesme_no%':        ev.id,
			'%sozlesme_tarihi%':    formatDate(ev.contractDate),
			'%personel%':           ev.staff,
			'%notlar%':             ev.note || '—'
		};
		return Object.entries(map).reduce((text, [ph, val]) => text.replaceAll(ph, val), body);
	};

	const generatePreview = () => {
		const tmpl = templates.find(t => t.id === selectedTemplateId);
		const ev = mockEvents.find(e => e.id === selectedEventId);
		if (!tmpl || !ev) { preview = ''; return; }
		preview = fillTemplate(tmpl.body, ev);
	};

	$effect(() => { generatePreview(); });

	const downloadContract = () => {
		if (!preview) return;
		const ev = mockEvents.find(e => e.id === selectedEventId);
		const tmpl = templates.find(t => t.id === selectedTemplateId);
		const blob = new Blob([preview], { type: 'text/plain;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `sozlesme_${ev?.id ?? 'draft'}_${tmpl?.name ?? 'sözleşme'}.txt`.replace(/\s+/g, '_');
		a.click();
		URL.revokeObjectURL(url);
	};

	const addTemplate = () => {
		if (!newName.trim() || !newBody.trim()) return;
		templates = [...templates, { id: String(Math.random()).slice(2), name: newName.trim(), body: newBody.trim() }];
		newName = '';
		newBody = '';
		showNewForm = false;
	};

	const deleteTemplate = (id: string) => {
		if (!confirm('Bu şablonu silmek istediğinizden emin misiniz?')) return;
		templates = templates.filter(t => t.id !== id);
		if (selectedTemplateId === id) selectedTemplateId = null;
	};

	const startEdit = (tmpl: Template) => {
		editingTemplate = { ...tmpl };
	};

	const saveEdit = () => {
		if (!editingTemplate) return;
		templates = templates.map(t => t.id === editingTemplate!.id ? { ...editingTemplate! } : t);
		editingTemplate = null;
	};

	const handleFileUpload = (e: Event) => {
		uploadError = '';
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		if (!file.name.endsWith('.txt') && !file.name.endsWith('.md')) {
			uploadError = 'Yalnızca .txt veya .md dosyaları desteklenir. (.docx için önce metni kopyalayın)';
			return;
		}
		const reader = new FileReader();
		reader.onload = (ev) => {
			newBody = ev.target?.result as string ?? '';
			newName = file.name.replace(/\.[^.]+$/, '');
		};
		reader.readAsText(file, 'UTF-8');
	};

	const copyPlaceholder = (key: string) => {
		navigator.clipboard.writeText(key).catch(() => {});
	};
</script>

<section class="page-shell">
	<div class="page-heading">
		<div>
			<p class="eyebrow">Sözleşmeler</p>
			<h1>Şablon & Sözleşme Oluşturucu</h1>
		</div>
		<div class="tab-switch">
			<button class:active={activeTab === 'templates'} type="button" onclick={() => (activeTab = 'templates')}>Şablonlar</button>
			<button class:active={activeTab === 'generate'}  type="button" onclick={() => (activeTab = 'generate')}>Sözleşme Oluştur</button>
		</div>
	</div>

	{#if activeTab === 'templates'}
		<!-- ── Şablon yönetimi ─────────────────────────────────── -->
		<div class="templates-layout">
			<div class="template-list-col">
				<div class="col-head">
					<h2>Şablonlarım</h2>
					<button class="sm-btn" type="button" onclick={() => (showNewForm = !showNewForm)}>
						{showNewForm ? '✕ Kapat' : '+ Yeni Şablon'}
					</button>
				</div>

				{#if showNewForm}
					<div class="new-template-form">
						<label>
							<span>Şablon Adı</span>
							<input bind:value={newName} placeholder="Örn: Düğün Sözleşmesi" />
						</label>
						<label>
							<span>Dosya Yükle (.txt)</span>
							<input type="file" accept=".txt,.md" onchange={handleFileUpload} />
						</label>
						{#if uploadError}<p class="upload-error">{uploadError}</p>{/if}
						<label>
							<span>veya Şablon Metni Yapıştır <small>(placeholder: %isim%, %tarih% …)</small></span>
							<textarea rows="10" bind:value={newBody} placeholder="Sayın %isim%,&#10;%tarih% tarihinde…"></textarea>
						</label>
						<div class="form-actions">
							<button class="primary-btn" type="button" onclick={addTemplate} disabled={!newName.trim() || !newBody.trim()}>Kaydet</button>
							<button class="ghost-btn" type="button" onclick={() => (showNewForm = false)}>İptal</button>
						</div>
					</div>
				{/if}

				<div class="template-cards">
					{#each templates as tmpl}
						<div class="template-card" class:selected={selectedTemplateId === tmpl.id}>
							<button class="tmpl-name-btn" type="button" onclick={() => (selectedTemplateId = tmpl.id === selectedTemplateId ? null : tmpl.id)}>
								<span class="tmpl-icon">📄</span>
								<span>{tmpl.name}</span>
							</button>
							<div class="tmpl-actions">
								<button class="icon-btn" type="button" onclick={() => startEdit(tmpl)} title="Düzenle">✏️</button>
								<button class="icon-btn danger" type="button" onclick={() => deleteTemplate(tmpl.id)} title="Sil">🗑</button>
							</div>
						</div>
					{/each}
					{#if templates.length === 0}
						<p class="empty-msg">Henüz şablon yok. "Yeni Şablon" ile ekleyin.</p>
					{/if}
				</div>
			</div>

			<div class="template-detail-col">
				{#if editingTemplate}
					<div class="panel">
						<div class="col-head">
							<h2>Şablonu Düzenle</h2>
							<div style="display:flex;gap:0.5rem">
								<button class="primary-btn" type="button" onclick={saveEdit}>Kaydet</button>
								<button class="ghost-btn" type="button" onclick={() => (editingTemplate = null)}>İptal</button>
							</div>
						</div>
						<label><span>Ad</span><input bind:value={editingTemplate.name} /></label>
						<label><span>Şablon Metni</span><textarea rows="22" bind:value={editingTemplate.body}></textarea></label>
					</div>
				{:else if selectedTemplateId}
					{@const tmpl = templates.find(t => t.id === selectedTemplateId)!}
					<div class="panel">
						<div class="col-head">
							<h2>{tmpl.name}</h2>
							<button class="sm-btn" type="button" onclick={() => startEdit(tmpl)}>✏️ Düzenle</button>
						</div>
						<pre class="template-preview">{tmpl.body}</pre>
					</div>
				{:else}
					<div class="panel placeholder-panel">
						<h2>Placeholder Listesi</h2>
						<p class="sub">Şablon metnine bu etiketleri yaz, sistem otomatik doldurur. Tıkla → kopyala.</p>
						<div class="ph-grid">
							{#each PLACEHOLDERS as ph}
								<button class="ph-chip" type="button" onclick={() => copyPlaceholder(ph.key)} title="Kopyala: {ph.key}">
									<code>{ph.key}</code>
									<span>{ph.label}</span>
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>

	{:else}
		<!-- ── Sözleşme oluşturucu ─────────────────────────────── -->
		<div class="generate-layout">
			<aside class="generate-sidebar">
				<div class="panel">
					<h2>1 — Davet Seç</h2>
					<div class="event-list">
						{#each mockEvents as ev}
							<button
								class="event-item"
								class:selected={selectedEventId === ev.id}
								type="button"
								onclick={() => (selectedEventId = ev.id)}
							>
								<strong>{ev.title}</strong>
								<span>{ev.date} · {ev.type}</span>
							</button>
						{/each}
					</div>
				</div>

				<div class="panel">
					<h2>2 — Şablon Seç</h2>
					<div class="event-list">
						{#each templates as tmpl}
							<button
								class="event-item"
								class:selected={selectedTemplateId === tmpl.id}
								type="button"
								onclick={() => (selectedTemplateId = tmpl.id)}
							>
								<strong>{tmpl.name}</strong>
							</button>
						{/each}
						{#if templates.length === 0}
							<p class="empty-msg">Önce "Şablonlar" sekmesinden şablon ekleyin.</p>
						{/if}
					</div>
				</div>

				<button
					class="download-btn"
					type="button"
					onclick={downloadContract}
					disabled={!preview}
				>
					⬇ Sözleşmeyi İndir (.txt)
				</button>
			</aside>

			<div class="preview-col panel">
				<div class="col-head">
					<h2>Önizleme</h2>
					{#if preview}
						<button class="sm-btn" type="button" onclick={downloadContract}>⬇ İndir</button>
					{/if}
				</div>
				{#if preview}
					<pre class="contract-preview">{preview}</pre>
				{:else}
					<div class="preview-empty">
						<p>Davet ve şablon seçince sözleşme burada görünür.</p>
						<p class="sub">Doldurulmuş alanlar otomatik yerleşir, ardından indirebilirsiniz.</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</section>

<style>
	.page-shell { max-width: 1480px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }
	.page-heading { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
	h1, h2, p { margin: 0; }
	h1 { font-size: clamp(1.6rem, 3vw, 2.6rem); }
	h2 { font-size: 1rem; font-weight: 900; }

	.eyebrow { margin-bottom: 0.25rem; color: var(--accent); font-size: 0.78rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; }

	.tab-switch { display: flex; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 0.3rem; gap: 0.25rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
	.tab-switch button { border: 0; border-radius: 6px; padding: 0.6rem 1.1rem; background: transparent; color: var(--muted); font: inherit; font-weight: 800; cursor: pointer; }
	.tab-switch .active { background: var(--accent); color: #fff; }

	/* Templates tab */
	.templates-layout { display: grid; grid-template-columns: 320px 1fr; gap: 1rem; align-items: start; }
	.template-list-col { display: flex; flex-direction: column; gap: 0.85rem; }

	.col-head { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-bottom: 0.15rem; }

	.sm-btn { border: 1px solid var(--line); border-radius: 7px; padding: 0.5rem 0.85rem; background: var(--surface-strong); color: var(--text); font: inherit; font-weight: 800; font-size: 0.82rem; cursor: pointer; white-space: nowrap; }
	.sm-btn:hover { border-color: color-mix(in srgb, var(--accent) 45%, transparent); }

	.primary-btn { border: 0; border-radius: 7px; padding: 0.65rem 1.1rem; background: var(--accent); color: #fff; font: inherit; font-weight: 900; cursor: pointer; }
	.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }
	.ghost-btn { border: 1px solid var(--line); border-radius: 7px; padding: 0.65rem 1rem; background: transparent; color: var(--muted); font: inherit; font-weight: 800; cursor: pointer; }

	.new-template-form { display: flex; flex-direction: column; gap: 0.75rem; padding: 1rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
	.form-actions { display: flex; gap: 0.5rem; }

	.template-cards { display: flex; flex-direction: column; gap: 0.5rem; }
	.template-card { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.75rem 0.85rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; transition: border-color 0.15s; }
	.template-card.selected { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 8%, var(--surface)); }
	.tmpl-name-btn { flex: 1; display: flex; align-items: center; gap: 0.5rem; border: 0; background: transparent; color: var(--text); font: inherit; font-weight: 800; font-size: 0.9rem; cursor: pointer; text-align: left; }
	.tmpl-icon { font-size: 1rem; }
	.tmpl-actions { display: flex; gap: 0.25rem; }
	.icon-btn { border: 0; background: transparent; cursor: pointer; font-size: 0.9rem; padding: 0.25rem 0.35rem; border-radius: 5px; opacity: 0.7; }
	.icon-btn:hover { opacity: 1; background: var(--surface-strong); }
	.icon-btn.danger:hover { background: color-mix(in srgb, #ef4444 12%, transparent); }

	.empty-msg { color: var(--muted); font-size: 0.85rem; text-align: center; padding: 1.5rem 0; }

	.template-detail-col { display: flex; flex-direction: column; }
	.panel { display: flex; flex-direction: column; gap: 0.85rem; padding: 1rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 18px 38px rgba(0,0,0,0.12); }

	.template-preview { font-family: 'Courier New', monospace; font-size: 0.82rem; line-height: 1.65; color: var(--text); background: var(--surface-strong); border: 1px solid var(--line); border-radius: 7px; padding: 1rem; white-space: pre-wrap; word-break: break-word; max-height: 560px; overflow-y: auto; margin: 0; }

	.placeholder-panel { gap: 1rem; }
	.sub { color: var(--muted); font-size: 0.82rem; }
	.ph-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.5rem; }
	.ph-chip { display: flex; flex-direction: column; gap: 0.2rem; padding: 0.55rem 0.75rem; border: 1px solid var(--line); border-radius: 7px; background: var(--surface-strong); color: var(--text); cursor: pointer; text-align: left; font: inherit; transition: all 0.15s; }
	.ph-chip:hover { border-color: color-mix(in srgb, var(--accent) 50%, transparent); background: color-mix(in srgb, var(--accent) 8%, var(--surface-strong)); }
	.ph-chip code { font-family: 'Courier New', monospace; font-size: 0.8rem; color: var(--accent); font-weight: 700; }
	.ph-chip span { font-size: 0.76rem; color: var(--muted); }

	/* Generate tab */
	.generate-layout { display: grid; grid-template-columns: 280px 1fr; gap: 1rem; align-items: start; }
	.generate-sidebar { display: flex; flex-direction: column; gap: 1rem; }

	.event-list { display: flex; flex-direction: column; gap: 0.45rem; }
	.event-item { border: 1px solid var(--line); border-radius: 7px; padding: 0.65rem 0.85rem; background: var(--surface-strong); color: var(--text); font: inherit; text-align: left; cursor: pointer; display: flex; flex-direction: column; gap: 0.15rem; transition: all 0.15s; }
	.event-item strong { font-size: 0.9rem; font-weight: 800; }
	.event-item span { font-size: 0.76rem; color: var(--muted); }
	.event-item.selected { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, var(--surface-strong)); }

	.download-btn { border: 0; border-radius: 8px; padding: 0.85rem; background: var(--accent); color: #fff; font: inherit; font-weight: 900; font-size: 0.95rem; cursor: pointer; }
	.download-btn:disabled { opacity: 0.45; cursor: not-allowed; }

	.preview-col { min-height: 400px; }
	.contract-preview { font-family: 'Courier New', monospace; font-size: 0.8rem; line-height: 1.7; color: var(--text); background: var(--surface-strong); border: 1px solid var(--line); border-radius: 7px; padding: 1.25rem; white-space: pre-wrap; word-break: break-word; max-height: 640px; overflow-y: auto; margin: 0; }

	.preview-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; min-height: 280px; gap: 0.5rem; text-align: center; color: var(--muted); }
	.preview-empty .sub { font-size: 0.82rem; }

	/* Labels & inputs */
	label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; font-size: 0.85rem; }
	label span { color: var(--muted); }
	label small { color: var(--muted); font-weight: 400; }
	input, select, textarea { width: 100%; min-height: 38px; border: 1px solid var(--line); border-radius: 7px; padding: 0.55rem 0.65rem; background: var(--surface-strong); color: var(--text); font: inherit; }
	input[type=file] { min-height: auto; padding: 0.4rem 0; cursor: pointer; }
	textarea { resize: vertical; }

	.upload-error { color: #ef4444; font-size: 0.82rem; margin: 0; }

	@media (max-width: 1100px) { .templates-layout, .generate-layout { grid-template-columns: 1fr; } }
	@media (max-width: 720px) { .page-heading { flex-direction: column; align-items: stretch; } }
</style>
