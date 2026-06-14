<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type SalonApi, type EventTypeApi, type OrgTypeFieldApi, type EventFormFieldDefApi, type CustomerFormTypeApi, type CustomerFormTypeFieldApi } from '$lib/api';

	type FieldType = 'text' | 'number' | 'date' | 'time' | 'textarea' | 'select' | 'checkbox';
	const FIELD_TYPE_LABELS: Record<FieldType, string> = {
		text: 'Metin', number: 'Sayı', date: 'Tarih', time: 'Saat',
		textarea: 'Uzun Metin', select: 'Seçenek', checkbox: 'Onay Kutusu'
	};

	const PLACEHOLDER_OPTIONS = [
		'%baslik%','%isim%','%gelin_damat%','%tc_no%','%telefon%','%tarih%',
		'%sozlesme_tarihi%','%baslama_saati%','%bitis_saati%','%tip%',
		'%rezervasyon_durumu%','%davetli_sayisi%','%adres%','%bolge%',
		'%toplam_ucret%','%kapora%','%odenen%','%kalan%','%sozlesme_no%',
		'%personel%','%notlar%','%salon_adi%','%salon_adresi%','%kdv_orani%'
	];

	// Salon settings
	let salon = $state<SalonApi | null>(null);
	let saving = $state(false);
	let saved = $state(false);
	let loadError = $state('');

	// Customer form types (portal form, no colors — separate from calendar EventType)
	let customerFormTypes = $state<CustomerFormTypeApi[]>([]);
	let selectedFormTypeId = $state('');
	let newFormTypeName = $state('');

	// Customer form type fields
	let formTypeFields = $state<CustomerFormTypeFieldApi[]>([]);
	let newFieldLabel = $state('');
	let newFieldType = $state<FieldType>('text');
	let newFieldOptions = $state('');
	let newFieldRequired = $state(false);

	// Event form field defs
	let formFieldDefs = $state<EventFormFieldDefApi[]>([]);
	let newEfLabel = $state('');
	let newEfType = $state<FieldType>('text');
	let newEfTag = $state('');
	let newEfOptions = $state('');

	const selectedFormType = $derived(customerFormTypes.find(t => t.id === selectedFormTypeId) ?? null);

	onMount(async () => {
		try {
			const [s, cfTypes, ffdefs] = await Promise.all([
				api.get<SalonApi>('/settings/salon'),
				api.get<CustomerFormTypeApi[]>('/customer-forms/types'),
				api.get<EventFormFieldDefApi[]>('/event-form-fields')
			]);
			salon = { ...s };
			customerFormTypes = cfTypes;
			formFieldDefs = ffdefs;
			if (cfTypes.length > 0) {
				selectedFormTypeId = cfTypes[0].id;
				await loadFormTypeFields(cfTypes[0].id);
			}
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'Yükleme hatası';
		}
	});

	async function loadFormTypeFields(typeId: string) {
		formTypeFields = await api.get<CustomerFormTypeFieldApi[]>(`/customer-forms/fields?type_id=${typeId}`);
	}

	async function selectFormType(id: string) {
		selectedFormTypeId = id;
		await loadFormTypeFields(id);
	}

	async function saveSalon() {
		if (!salon) return;
		saving = true;
		try {
			const updated = await api.patch<SalonApi>('/settings/salon', {
				name: salon.name,
				address: salon.address,
				currency: salon.currency,
				vat_rate: salon.vat_rate,
				contract_prefix: salon.contract_prefix,
				reminder_days: salon.reminder_days
			});
			salon = { ...updated };
			saved = true;
			setTimeout(() => (saved = false), 2500);
		} finally {
			saving = false;
		}
	}

	async function addFormType() {
		const name = newFormTypeName.trim();
		if (!name) return;
		const t = await api.post<CustomerFormTypeApi>('/customer-forms/types', { name });
		customerFormTypes = [...customerFormTypes, t];
		newFormTypeName = '';
		await selectFormType(t.id);
	}

	async function deleteFormType(id: string) {
		if (!confirm('Bu form tipini sil?')) return;
		await api.del(`/customer-forms/types/${id}`);
		customerFormTypes = customerFormTypes.filter(t => t.id !== id);
		if (selectedFormTypeId === id) {
			selectedFormTypeId = customerFormTypes[0]?.id ?? '';
			if (selectedFormTypeId) await loadFormTypeFields(selectedFormTypeId);
			else formTypeFields = [];
		}
	}

	async function addFormTypeField() {
		const label = newFieldLabel.trim();
		if (!label || !selectedFormTypeId) return;
		const slug = label.toLocaleLowerCase('tr-TR').replaceAll(' ', '_').replace(/[^a-z0-9_]/gi, '');
		const options = newFieldOptions.split(',').map(s => s.trim()).filter(Boolean);
		const f = await api.post<CustomerFormTypeFieldApi>('/customer-forms/fields', {
			customer_form_type_id: selectedFormTypeId,
			key: slug || `field_${formTypeFields.length + 1}`,
			label,
			field_type: newFieldType,
			options,
			is_required: newFieldRequired,
			sort_order: formTypeFields.length
		});
		formTypeFields = [...formTypeFields, f];
		newFieldLabel = '';
		newFieldOptions = '';
		newFieldRequired = false;
	}

	async function deleteFormTypeField(id: string) {
		await api.del(`/customer-forms/fields/${id}`);
		formTypeFields = formTypeFields.filter(f => f.id !== id);
	}

	// ── Event form field def actions ─────────────────────────────────────────
	async function toggleFieldVisibility(f: EventFormFieldDefApi) {
		const updated = await api.patch<EventFormFieldDefApi>(`/event-form-fields/${f.id}`, { is_visible: !f.is_visible });
		formFieldDefs = formFieldDefs.map(d => d.id === updated.id ? updated : d);
	}

	async function addEventFormField() {
		const label = newEfLabel.trim();
		if (!label) return;
		const slug = label.toLocaleLowerCase('tr-TR').replaceAll(' ', '_').replace(/[^a-z0-9_]/gi, '');
		const options = newEfOptions.split(',').map(s => s.trim()).filter(Boolean);
		const f = await api.post<EventFormFieldDefApi>('/event-form-fields', {
			key: slug || `custom_${formFieldDefs.length}`,
			label,
			field_type: newEfType,
			options,
			placeholder_tag: newEfTag,
			sort_order: formFieldDefs.length
		});
		formFieldDefs = [...formFieldDefs, f];
		newEfLabel = '';
		newEfTag = '';
		newEfOptions = '';
	}

	async function deleteEventFormField(id: string) {
		await api.del(`/event-form-fields/${id}`);
		formFieldDefs = formFieldDefs.filter(f => f.id !== id);
	}
</script>

<section class="page-shell">
	<div class="page-heading">
		<div>
			<p class="eyebrow">Ayarlar</p>
			<h1>Salon ayarları</h1>
		</div>
	</div>

	{#if loadError}
		<div class="error-bar">{loadError}</div>
	{/if}

	{#if salon}
		<div class="settings-grid">
			<section class="panel">
				<h2>Genel Bilgiler</h2>
				<label><span>Salon Adı</span><input bind:value={salon.name} /></label>
				<label><span>Adres</span><textarea rows="3" bind:value={salon.address}></textarea></label>
				<label><span>Para Birimi</span>
					<select bind:value={salon.currency}>
						<option>TRY</option><option>EUR</option><option>USD</option>
					</select>
				</label>
				<h2 style="margin-top:0.5rem">Operasyon</h2>
				<label><span>Hatırlatma Günü</span><input type="number" bind:value={salon.reminder_days} /></label>
				<label><span>KDV Oranı (%)</span><input type="number" bind:value={salon.vat_rate} /></label>
				<label><span>Sözleşme No Prefix</span><input bind:value={salon.contract_prefix} /></label>
				<button class="save-btn" onclick={saveSalon} disabled={saving}>
					{saving ? 'Kaydediliyor…' : saved ? '✓ Kaydedildi' : 'Kaydet'}
				</button>
			</section>

			<section class="panel org-panel">
				<h2>Müşteri Formu</h2>
				<p class="hint">Müşteri portalinde gösterilecek form tiplerini ve alanlarını tanımla. Takvim etkinlik tiplerinden bağımsızdır.</p>

				<div class="type-tabs">
					{#each customerFormTypes as t}
						<div
							class="type-tab no-color"
							class:active={selectedFormTypeId === t.id}
							role="button"
							tabindex="0"
							onclick={() => selectFormType(t.id)}
							onkeydown={(e) => e.key === 'Enter' && selectFormType(t.id)}
						>
							{t.name}
							<button class="del-type" onclick={(e) => { e.stopPropagation(); deleteFormType(t.id); }}>×</button>
						</div>
					{/each}
					{#if customerFormTypes.length === 0}
						<p class="empty-hint">Henüz form tipi eklenmemiş.</p>
					{/if}
				</div>

				<div class="inline-add type-add-nocolor">
					<input placeholder="Yeni form tipi (örn: Düğün, Nişan)" bind:value={newFormTypeName} onkeydown={(e) => e.key === 'Enter' && addFormType()} />
					<button onclick={addFormType}>Ekle</button>
				</div>

				{#if selectedFormType}
					<div class="fields-section">
						<h3>{selectedFormType.name} — Form Alanları</h3>

						{#if formTypeFields.length === 0}
							<p class="empty-hint">Bu form tipi için henüz alan eklenmemiş.</p>
						{:else}
							<div class="field-list">
								{#each formTypeFields as f}
									<div class="field-row">
										<div class="field-info">
											<strong>{f.label}</strong>
											<span>{FIELD_TYPE_LABELS[f.field_type as FieldType] ?? f.field_type}{f.is_required ? ' · Zorunlu' : ''}</span>
											{#if f.options?.length > 0}<small>Seçenekler: {f.options.join(', ')}</small>{/if}
										</div>
										<button class="del-btn" onclick={() => deleteFormTypeField(f.id)}>Sil</button>
									</div>
								{/each}
							</div>
						{/if}

						<div class="field-add-form">
							<label><span>Alan Adı</span><input placeholder="Örn: Masa düzeni tercihi" bind:value={newFieldLabel} onkeydown={(e) => e.key === 'Enter' && addFormTypeField()} /></label>
							<label><span>Tip</span>
								<select bind:value={newFieldType}>
									{#each Object.entries(FIELD_TYPE_LABELS) as [val, lbl]}
										<option value={val}>{lbl}</option>
									{/each}
								</select>
							</label>
							{#if newFieldType === 'select'}
								<label class="full"><span>Seçenekler (virgülle ayır)</span><input placeholder="Seçenek 1, Seçenek 2" bind:value={newFieldOptions} /></label>
							{/if}
							<label class="check-label">
								<input type="checkbox" bind:checked={newFieldRequired} />
								Zorunlu alan
							</label>
							<button class="add-field-btn" onclick={addFormTypeField}>Alan Ekle</button>
						</div>
					</div>
				{/if}
			</section>

			<!-- ── Etkinlik Formu Alanları ──────────────────────────────── -->
			<section class="panel ef-panel">
				<h2>Etkinlik Formu Alanları</h2>
				<p class="hint">Takvim formunda hangi alanların görüneceğini ayarla. Yerleşik alanları gizleyebilir, yeni alanlar ekleyip sözleşme etiketiyle ilişkilendirebilirsin.</p>

				<div class="ef-section">
					<h3>Yerleşik Alanlar</h3>
					<div class="field-list">
						{#each formFieldDefs.filter(f => f.is_builtin) as f}
							<div class="field-row">
								<div class="field-info">
									<strong>{f.label}</strong>
									{#if f.placeholder_tag}<code class="ph-tag">{f.placeholder_tag}</code>{/if}
								</div>
								<button
									class="vis-btn"
									class:hidden={!f.is_visible}
									type="button"
									onclick={() => toggleFieldVisibility(f)}
									title={f.is_visible ? 'Gizle' : 'Göster'}
								>{f.is_visible ? '👁' : '🚫'}</button>
							</div>
						{/each}
					</div>
				</div>

				<div class="ef-section">
					<h3>Özel Alanlar</h3>
					{#if formFieldDefs.filter(f => !f.is_builtin).length === 0}
						<p class="empty-hint">Henüz özel alan eklenmemiş.</p>
					{:else}
						<div class="field-list">
							{#each formFieldDefs.filter(f => !f.is_builtin) as f}
								<div class="field-row">
									<div class="field-info">
										<strong>{f.label}</strong>
										<span>{FIELD_TYPE_LABELS[f.field_type as FieldType] ?? f.field_type}</span>
										{#if f.placeholder_tag}<code class="ph-tag">{f.placeholder_tag}</code>{/if}
									</div>
									<button class="vis-btn" class:hidden={!f.is_visible} type="button" onclick={() => toggleFieldVisibility(f)} title={f.is_visible ? 'Gizle' : 'Göster'}>{f.is_visible ? '👁' : '🚫'}</button>
									<button class="del-btn" type="button" onclick={() => deleteEventFormField(f.id)}>Sil</button>
								</div>
							{/each}
						</div>
					{/if}

					<div class="field-add-form">
						<label><span>Alan Adı</span><input placeholder="Örn: Nota Ek Bilgi" bind:value={newEfLabel} /></label>
						<label><span>Tip</span>
							<select bind:value={newEfType}>
								{#each Object.entries(FIELD_TYPE_LABELS) as [val, lbl]}
									<option value={val}>{lbl}</option>
								{/each}
							</select>
						</label>
						{#if newEfType === 'select'}
							<label class="full"><span>Seçenekler (virgülle ayır)</span><input placeholder="Seçenek 1, Seçenek 2" bind:value={newEfOptions} /></label>
						{/if}
						<label class="full"><span>Sözleşme Etiketi <span class="opt-hint">(opsiyonel — örn: %ozel_alan%)</span></span>
							<input bind:value={newEfTag} placeholder="%ozel_alan%" list="ph-list" />
							<datalist id="ph-list">
								{#each PLACEHOLDER_OPTIONS as ph}<option value={ph}>{ph}</option>{/each}
							</datalist>
						</label>
						<button class="add-field-btn" type="button" onclick={addEventFormField}>Alan Ekle</button>
					</div>
				</div>
			</section>
		</div>
	{:else if !loadError}
		<div class="loading">Yükleniyor…</div>
	{/if}
</section>

<style>
	.page-shell { max-width: 1280px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }
	h1, h2, h3, p { margin: 0; }
	.eyebrow { margin-bottom: 0.25rem; color: var(--accent); font-size: 0.78rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; }
	.settings-grid { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1.4fr) minmax(0,1.4fr); gap: 1rem; align-items: start; }
	.panel { display: flex; flex-direction: column; gap: 0.85rem; padding: 1.2rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 18px 38px rgba(0,0,0,0.12); }
	h2 { font-size: 1rem; color: var(--accent); }
	h3 { font-size: 0.92rem; display: flex; align-items: center; gap: 0.5rem; }
	label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; }
	label span { color: var(--muted); font-size: 0.82rem; }
	input, select, textarea { width: 100%; min-height: 38px; border: 1px solid var(--line); border-radius: 7px; padding: 0.55rem 0.65rem; background: var(--surface-strong); color: var(--text); font: inherit; }
	textarea { resize: vertical; }
	.save-btn { margin-top: 0.5rem; padding: 0.75rem 1.5rem; background: var(--accent); color: #fff; border: 0; border-radius: 8px; font-weight: 900; cursor: pointer; }
	.save-btn:disabled { opacity: 0.7; cursor: not-allowed; }
	.hint { color: var(--muted); font-size: 0.82rem; }
	.type-tabs { display: flex; flex-wrap: wrap; gap: 0.5rem; }
	.type-tab { display: flex; align-items: center; gap: 0.4rem; padding: 0.5rem 0.85rem; border: 1px solid var(--line); border-radius: 7px; background: var(--surface-strong); color: var(--text); font-weight: 800; font-size: 0.82rem; cursor: pointer; transition: all 0.15s; }
	.type-tab:hover, .type-tab.active { border-color: var(--c, var(--accent)); background: color-mix(in srgb, var(--c, var(--accent)) 14%, var(--surface-strong)); }
	.type-tab.no-color:hover, .type-tab.no-color.active { border-color: var(--accent); background: var(--accent-soft); }
	.del-type { margin-left: 0.3rem; background: transparent; border: 0; color: var(--muted); cursor: pointer; font-size: 1rem; line-height: 1; padding: 0; }
	.del-type:hover { color: var(--danger); }
	.inline-add { display: grid; grid-template-columns: 1fr auto auto; gap: 0.5rem; }
	.type-add-nocolor { display: grid; grid-template-columns: 1fr auto; gap: 0.5rem; }
	.type-add-nocolor button { border: 0; border-radius: 7px; padding: 0.55rem 0.85rem; background: var(--accent); color: #fff; font-weight: 900; cursor: pointer; white-space: nowrap; }
	.fields-section { display: flex; flex-direction: column; gap: 0.85rem; padding-top: 0.85rem; border-top: 1px solid var(--line); }
	.field-list { display: flex; flex-direction: column; gap: 0.5rem; }
	.field-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; }
	.field-info { flex: 1; display: flex; flex-direction: column; gap: 0.15rem; }
	.field-info strong { font-size: 0.88rem; }
	.field-info span { font-size: 0.76rem; color: var(--muted); }
	.field-info small { font-size: 0.72rem; color: var(--muted); }
	.del-btn { padding: 0.4rem 0.65rem; border: 1px solid var(--line); border-radius: 6px; background: transparent; color: var(--danger); font-weight: 900; font-size: 0.76rem; cursor: pointer; white-space: nowrap; }
	.field-add-form { display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; padding: 0.85rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; }
	.field-add-form .full { grid-column: 1 / -1; }
	.check-label { flex-direction: row; align-items: center; gap: 0.4rem; color: var(--muted); font-size: 0.82rem; }
	.check-label input { width: auto; min-height: auto; accent-color: var(--accent); }
	.add-field-btn { grid-column: 1 / -1; padding: 0.65rem; background: var(--accent); color: #fff; border: 0; border-radius: 7px; font-weight: 900; cursor: pointer; }
	.empty-hint { color: var(--muted); font-size: 0.82rem; font-style: italic; }
	.error-bar { padding: 0.85rem 1rem; background: color-mix(in srgb, var(--danger) 12%, transparent); border: 1px solid var(--danger); border-radius: 8px; color: var(--danger); font-weight: 800; }
	.loading { color: var(--muted); padding: 2rem; text-align: center; }
	.ef-panel { gap: 1rem; }
	.ef-section { display: flex; flex-direction: column; gap: 0.65rem; padding-top: 0.75rem; border-top: 1px solid var(--line); }
	.ef-section h3 { font-size: 0.85rem; font-weight: 900; color: var(--muted); margin: 0; }
	.opt-hint { font-weight: 400; color: var(--muted); font-size: 0.75rem; }
	.vis-btn { padding: 0.35rem 0.6rem; border: 1px solid var(--line); border-radius: 6px; background: transparent; cursor: pointer; font-size: 0.92rem; transition: opacity 0.15s; }
	.vis-btn.hidden { opacity: 0.35; }
	.ph-tag { font-family: 'Courier New', monospace; font-size: 0.7rem; color: var(--accent); background: var(--accent-soft); padding: 0.1rem 0.35rem; border-radius: 4px; }
	@media (max-width: 1100px) { .settings-grid { grid-template-columns: 1fr 1fr; } }
	@media (max-width: 700px) { .settings-grid { grid-template-columns: 1fr; } }
</style>
