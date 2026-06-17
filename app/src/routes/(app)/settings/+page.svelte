<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type SalonApi, type EventTypeApi, type OrgTypeFieldApi, type EventFormFieldDefApi, type EventTypeFieldDefApi, type CustomerFormTypeApi, type CustomerFormTypeFieldApi, type VenueLayoutApi } from '$lib/api';

	type FieldType = 'text' | 'number' | 'date' | 'time' | 'textarea' | 'select' | 'checkbox';
	const FIELD_TYPE_LABELS: Record<FieldType, string> = {
		text: 'Metin', number: 'Sayı', date: 'Tarih', time: 'Saat',
		textarea: 'Uzun Metin', select: 'Seçenek', checkbox: 'Onay Kutusu'
	};

	const PLACEHOLDER_OPTIONS = [
		'%randevu_no%','%isim%','%tc_no%','%telefon%','%email%','%adres%','%tarih%',
		'%baslama_saati%','%bitis_saati%','%tip%','%davetli_sayisi%',
		'%toplam_ucret%','%kapora%','%kalan%','%notlar%','%salon_adi%'
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

	// Event types
	let eventTypes = $state<EventTypeApi[]>([]);
	let newTypeName = $state('');
	let newTypeColor = $state('#64748b');

	// Salonlar (oda) — max 3, sadece isim değiştirme
	let venueLayouts = $state<VenueLayoutApi[]>([]);
	let savingSalonId = $state('');

	// Event form field defs (Genel Form Alanı)
	let formFieldDefs = $state<EventFormFieldDefApi[]>([]);
	let newEfLabel = $state('');
	let newEfType = $state<FieldType>('text');
	let newEfTag = $state('');
	let newEfOptions = $state('');

	// Etkinlik Form Alanı (per event type)
	let selectedEtypeId = $state('');
	let etypeFields = $state<EventTypeFieldDefApi[]>([]);
	let newEtfLabel = $state('');
	let newEtfType = $state<FieldType>('text');
	let newEtfOptions = $state('');

	const selectedFormType = $derived(customerFormTypes.find(t => t.id === selectedFormTypeId) ?? null);

	onMount(async () => {
		try {
			const [s, cfTypes, ffdefs, etypes, layouts] = await Promise.all([
				api.get<SalonApi>('/settings/salon'),
				api.get<CustomerFormTypeApi[]>('/customer-forms/types'),
				api.get<EventFormFieldDefApi[]>('/event-form-fields'),
				api.get<EventTypeApi[]>('/events/types'),
				api.get<VenueLayoutApi[]>('/venue/layouts')
			]);
			salon = { ...s };
			customerFormTypes = cfTypes;
			formFieldDefs = ffdefs;
			eventTypes = etypes;
			venueLayouts = layouts;
			if (cfTypes.length > 0) {
				selectedFormTypeId = cfTypes[0].id;
				await loadFormTypeFields(cfTypes[0].id);
			}
			if (etypes.length > 0) {
				selectedEtypeId = etypes[0].id;
				await loadEtypeFields(etypes[0].id);
			}
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'Yükleme hatası';
		}
	});

	async function loadEtypeFields(typeId: string) {
		etypeFields = await api.get<EventTypeFieldDefApi[]>(`/event-type-fields?type_id=${typeId}`);
	}

	async function selectEtype(id: string) {
		selectedEtypeId = id;
		await loadEtypeFields(id);
	}

	async function addEtypeField() {
		const label = newEtfLabel.trim();
		if (!label || !selectedEtypeId) return;
		const slug = label.toLocaleLowerCase('tr-TR').replaceAll(' ', '_').replace(/[^a-z0-9_]/gi, '');
		const options = newEtfOptions.split(',').map(s => s.trim()).filter(Boolean);
		const f = await api.post<EventTypeFieldDefApi>('/event-type-fields', {
			event_type_id: selectedEtypeId,
			key: slug || `field_${etypeFields.length + 1}`,
			label, field_type: newEtfType, options, sort_order: etypeFields.length
		});
		etypeFields = [...etypeFields, f];
		newEtfLabel = ''; newEtfOptions = '';
	}

	async function deleteEtypeField(id: string) {
		await api.del(`/event-type-fields/${id}`);
		etypeFields = etypeFields.filter(f => f.id !== id);
	}

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
				vat_rate: salon.vat_rate,
				reminder_days: salon.reminder_days,
				payment_bank_name: salon.payment_bank_name,
				payment_iban: salon.payment_iban,
				payment_account_holder: salon.payment_account_holder,
				payment_description: salon.payment_description,
				smtp_host: salon.smtp_host,
				smtp_port: salon.smtp_port,
				smtp_username: salon.smtp_username,
				smtp_password: salon.smtp_password,
				smtp_from_email: salon.smtp_from_email,
				smtp_use_tls: salon.smtp_use_tls,
				notification_email: salon.notification_email
			});
			salon = { ...updated };
			saved = true;
			setTimeout(() => (saved = false), 2500);
		} finally {
			saving = false;
		}
	}

	// SMTP test
	let smtpTesting = $state(false);
	let smtpTestResult = $state<{ ok: boolean; detail: string } | null>(null);

	async function testSmtp() {
		if (!salon) return;
		smtpTesting = true;
		smtpTestResult = null;
		try {
			const result = await api.post<{ ok: boolean; detail: string }>('/settings/smtp-test', {
				to_email: salon.notification_email || undefined,
				smtp_host: salon.smtp_host,
				smtp_port: salon.smtp_port,
				smtp_username: salon.smtp_username,
				smtp_password: salon.smtp_password,
				smtp_from_email: salon.smtp_from_email,
				smtp_use_tls: salon.smtp_use_tls
			});
			smtpTestResult = result;
		} catch (e) {
			smtpTestResult = { ok: false, detail: e instanceof Error ? e.message : 'Test başarısız' };
		} finally {
			smtpTesting = false;
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

	async function addEventType() {
		const name = newTypeName.trim();
		if (!name) return;
		const t = await api.post<EventTypeApi>('/events/types', { name, color: newTypeColor });
		eventTypes = [...eventTypes, t];
		newTypeName = '';
		newTypeColor = '#64748b';
	}

	async function updateEventTypeColor(id: string, color: string) {
		const t = eventTypes.find(e => e.id === id);
		if (!t) return;
		const updated = await api.put<EventTypeApi>(`/events/types/${id}`, { name: t.name, color });
		eventTypes = eventTypes.map(e => e.id === id ? updated : e);
	}

	async function deleteEventType(id: string) {
		if (!confirm('Bu etkinlik tipini sil?')) return;
		await api.del(`/events/types/${id}`);
		eventTypes = eventTypes.filter(e => e.id !== id);
	}

	async function renameSalon(layout: VenueLayoutApi) {
		savingSalonId = layout.id;
		try {
			const updated = await api.put<VenueLayoutApi>(`/venue/layouts/${layout.id}`, {
				name: layout.name,
				canvas_width: layout.canvas_width,
				canvas_height: layout.canvas_height,
				stage: layout.stage,
				walls: layout.walls,
				tables: layout.tables
			});
			venueLayouts = venueLayouts.map(l => l.id === updated.id ? updated : l);
		} finally {
			savingSalonId = '';
		}
	}

	type SettingsTab = 'genel' | 'odeme' | 'etkinlik-tipleri' | 'musteri-formu' | 'etkinlik-formu' | 'salonlar';
	let activeTab = $state<SettingsTab>('genel');
	const TABS: { id: SettingsTab; label: string }[] = [
		{ id: 'genel',          label: 'Genel' },
		{ id: 'salonlar',       label: 'Salonlar' },
		{ id: 'odeme',          label: 'Ödeme & Mail' },
		{ id: 'etkinlik-tipleri', label: 'Etkinlik Tipleri' },
		{ id: 'musteri-formu',  label: 'Müşteri Formu' },
		{ id: 'etkinlik-formu', label: 'Randevu Kayıt Formu' },
	];
</script>

<section class="page-shell">
	<div class="page-heading">
		<div>
			<h1>Salon Ayarları</h1>
		</div>
	</div>

	{#if loadError}
		<div class="error-bar">{loadError}</div>
	{/if}

	{#if salon}
		<div class="tab-bar">
			{#each TABS as tab}
				<button
					class="tab-btn"
					class:active={activeTab === tab.id}
					type="button"
					onclick={() => (activeTab = tab.id)}
				>{tab.label}</button>
			{/each}
		</div>

		<div class="tab-body">

			<!-- ── GENEL ── -->
			{#if activeTab === 'genel'}
				<div class="form-section">
					<div class="section-header"><h2>Salon Bilgileri</h2></div>
					<div class="form-grid">
						<label class="full"><span>Salon Adı</span><input value={salon.name} readonly /></label>
						<label class="full"><span>Adres</span><textarea rows="2" readonly>{salon.address}</textarea></label>
						<label><span>Sözleşme No Prefix</span><input value={salon.contract_prefix} readonly /></label>
						<label><span>Para Birimi</span><input value={salon.currency} readonly /></label>
						<label><span>KDV Oranı (%)</span><input type="number" bind:value={salon.vat_rate} /></label>
						<label><span>Hatırlatma Günü</span><input type="number" bind:value={salon.reminder_days} /></label>
					</div>
					<div class="form-actions">
						<button class="save-btn" onclick={saveSalon} disabled={saving}>
							{saving ? 'Kaydediliyor…' : saved ? '✓ Kaydedildi' : 'Kaydet'}
						</button>
					</div>
				</div>

			<!-- ── SALONLAR ── -->
			{:else if activeTab === 'salonlar'}
				<div class="form-section">
					<div class="section-header">
						<h2>Salonlar</h2>
						<p class="hint">Sistem en fazla 3 salon (oda) destekler. Her salonun kendi takvimi vardır; isimlerini buradan değiştirebilirsin.</p>
					</div>
					<div class="form-grid">
						{#each venueLayouts as layout (layout.id)}
							<label><span>Salon Adı</span>
								<input bind:value={layout.name} placeholder="Örn: Salon A" />
							</label>
							<div class="form-actions">
								<button class="save-btn" onclick={() => renameSalon(layout)} disabled={savingSalonId === layout.id}>
									{savingSalonId === layout.id ? 'Kaydediliyor…' : 'Kaydet'}
								</button>
							</div>
						{/each}
					</div>
				</div>

			<!-- ── ÖDEME & SMS ── -->
			{:else if activeTab === 'odeme'}
				<div class="form-section">
					<div class="section-header">
						<h2>Ödeme Bilgileri</h2>
						<p class="hint">Müşteri portalinde gösterilecek banka / havale bilgileri.</p>
					</div>
					<div class="form-grid">
						<label><span>Banka Adı</span><input placeholder="Örn: Ziraat Bankası" bind:value={salon.payment_bank_name} /></label>
						<label><span>Hesap Sahibi</span><input placeholder="Ad Soyad veya Firma Adı" bind:value={salon.payment_account_holder} /></label>
						<label class="full"><span>IBAN</span><input placeholder="TR00 0000 0000 0000 0000 0000 00" bind:value={salon.payment_iban} /></label>
						<label class="full"><span>Açıklama Şablonu</span>
							<textarea rows="2" placeholder="Örn: Randevu No: {"{randevu_id}"} için ödeme" bind:value={salon.payment_description}></textarea>
							<small class="opt-hint">{'{randevu_id}'} ve {'{isim}'} yerine otomatik doldurulur</small>
						</label>
					</div>
				</div>

				<div class="form-section">
					<div class="section-header">
						<h2>Mail (SMTP) Ayarları</h2>
						<p class="hint">Müşteri ödeme bildirdiğinde veya müşteriye mail gönderildiğinde bu hesap kullanılır.</p>
					</div>
					<div class="form-grid">
						<label><span>SMTP Sunucu</span><input placeholder="smtp.gmail.com" bind:value={salon.smtp_host} /></label>
						<label><span>Port</span><input type="number" placeholder="587" bind:value={salon.smtp_port} /></label>
						<label><span>Kullanıcı Adı (gönderme maili)</span><input placeholder="ornek@gmail.com" bind:value={salon.smtp_username} /></label>
						<label><span>Şifre</span><input type="password" bind:value={salon.smtp_password} /></label>
						<label><span>Gönderen Mail (From)</span><input placeholder="ornek@gmail.com" bind:value={salon.smtp_from_email} /></label>
						<label class="checkbox-inline-row"><input type="checkbox" bind:checked={salon.smtp_use_tls} /> TLS kullan</label>
						<label class="full"><span>Bildirim Maili</span>
							<input placeholder="kendi@mailiniz.com" bind:value={salon.notification_email} />
							<small class="opt-hint">Ödeme bildirimleri ve mail gönderim sonuçları bu adrese gider.</small>
						</label>
					</div>
					<div class="form-actions">
						<button class="save-btn" type="button" onclick={testSmtp} disabled={smtpTesting}>
							{smtpTesting ? 'Gönderiliyor…' : 'Test Mail Gönder'}
						</button>
						{#if smtpTestResult}
							<span class="smtp-test-result" class:ok={smtpTestResult.ok} class:fail={!smtpTestResult.ok}>
								{smtpTestResult.ok ? '✓ Test maili gönderildi' : `✗ Hata: ${smtpTestResult.detail}`}
							</span>
						{/if}
					</div>
				</div>

				<div class="form-actions">
					<button class="save-btn" onclick={saveSalon} disabled={saving}>
						{saving ? 'Kaydediliyor…' : saved ? '✓ Kaydedildi' : 'Kaydet'}
					</button>
				</div>

			<!-- ── ETKİNLİK TİPLERİ ── -->
			{:else if activeTab === 'etkinlik-tipleri'}
				<div class="form-section">
					<div class="section-header">
						<h2>Etkinlik Tipleri</h2>
						<p class="hint">Takvimde gösterilecek organizasyon tiplerini ve renklerini tanımla.</p>
					</div>

					{#if eventTypes.length === 0}
						<p class="empty-hint">Henüz etkinlik tipi eklenmemiş.</p>
					{:else}
						<div class="field-list">
							{#each eventTypes as t}
								<div class="field-row">
									<div class="type-color-dot" style="background:{t.color}"></div>
									<div class="field-info"><strong>{t.name}</strong></div>
									<input type="color" value={t.color} class="type-color-input" title="Rengi değiştir"
										onchange={(e) => updateEventTypeColor(t.id, e.currentTarget.value)} />
									<button class="del-btn" onclick={() => deleteEventType(t.id)}>Sil</button>
								</div>
							{/each}
						</div>
					{/if}

					<div class="add-row">
						<input placeholder="Yeni tip adı (örn: Düğün)" bind:value={newTypeName} onkeydown={(e) => e.key === 'Enter' && addEventType()} />
						<input type="color" bind:value={newTypeColor} class="type-color-input" title="Renk seç" />
						<button class="add-inline-btn" onclick={addEventType}>Ekle</button>
					</div>
				</div>

			<!-- ── MÜŞTERİ FORMU ── -->
			{:else if activeTab === 'musteri-formu'}
				<div class="form-section">
					<div class="section-header">
						<h2>Müşteri Formu</h2>
						<p class="hint">Portalde müşteriye gösterilecek form tipleri. Takvim etkinlik tiplerinden bağımsızdır.</p>
					</div>

					<div class="type-chips">
						{#each customerFormTypes as t}
							<button
								class="type-chip"
								class:active={selectedFormTypeId === t.id}
								onclick={() => selectFormType(t.id)}
							>
								{t.name}
								<span class="chip-del" role="button" tabindex="0"
									onclick={(e) => { e.stopPropagation(); deleteFormType(t.id); }}
									onkeydown={(e) => e.key === 'Enter' && deleteFormType(t.id)}>×</span>
							</button>
						{/each}
					</div>

					<div class="add-row">
						<input placeholder="Yeni form tipi (örn: Düğün, Nişan)" bind:value={newFormTypeName} onkeydown={(e) => e.key === 'Enter' && addFormType()} />
						<button class="add-inline-btn" onclick={addFormType}>Ekle</button>
					</div>

					{#if selectedFormType}
						<div class="subsection">
							<h3>{selectedFormType.name} — Alanlar</h3>

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
				</div>

			<!-- ── RANDEVU KAYIT FORMU ── -->
			{:else if activeTab === 'etkinlik-formu'}
				<div class="form-section">
					<div class="section-header">
						<h2>Genel Form Alanı</h2>
						<p class="hint">Tüm randevularda ortak olan alanlar. Yerleşik alanları gizleyebilir, yeni alanlar ekleyip sözleşme etiketiyle ilişkilendirebilirsin.</p>
					</div>

					<div class="subsection">
						<h3>Yerleşik Alanlar</h3>
						<div class="field-list">
							{#each formFieldDefs.filter(f => f.is_builtin) as f}
								<div class="field-row">
									<div class="field-info">
										<strong>{f.label}</strong>
										{#if f.placeholder_tag}<code class="ph-tag">{f.placeholder_tag}</code>{/if}
									</div>
									<button class="vis-btn" class:hidden={!f.is_visible} type="button"
										onclick={() => toggleFieldVisibility(f)} title={f.is_visible ? 'Gizle' : 'Göster'}
									>{f.is_visible ? '👁' : '🚫'}</button>
								</div>
							{/each}
						</div>
					</div>

					<div class="subsection">
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
										<button class="vis-btn" class:hidden={!f.is_visible} type="button"
											onclick={() => toggleFieldVisibility(f)} title={f.is_visible ? 'Gizle' : 'Göster'}
										>{f.is_visible ? '👁' : '🚫'}</button>
										<button class="del-btn" type="button" onclick={() => deleteEventFormField(f.id)}>Sil</button>
									</div>
								{/each}
							</div>
						{/if}

						<div class="field-add-form">
							<label><span>Alan Adı</span><input placeholder="Örn: Ek Bilgi" bind:value={newEfLabel} /></label>
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
							<label class="full"><span>Sözleşme Etiketi <span class="opt-hint">(opsiyonel)</span></span>
								<input bind:value={newEfTag} placeholder="%ozel_alan%" list="ph-list" />
								<datalist id="ph-list">
									{#each PLACEHOLDER_OPTIONS as ph}<option value={ph}>{ph}</option>{/each}
								</datalist>
							</label>
							<button class="add-field-btn" type="button" onclick={addEventFormField}>Alan Ekle</button>
						</div>
					</div>

					<div class="section-header">
						<h2>Etkinlik Form Alanı</h2>
						<p class="hint">Bir etkinlik tipi seç, sadece o tipte görünecek özel alanları yönet (örn. Düğün → Gelin ve Damat).</p>
					</div>
					<div class="etype-chip-row">
						{#each eventTypes as t}
							<button type="button" class="etype-chip" class:active={selectedEtypeId === t.id}
								style="--c:{t.color}" onclick={() => selectEtype(t.id)}>{t.name}</button>
						{/each}
					</div>

					<div class="subsection">
						{#if etypeFields.length === 0}
							<p class="empty-hint">Bu etkinlik tipi için henüz özel alan eklenmemiş.</p>
						{:else}
							<div class="field-list">
								{#each etypeFields as f}
									<div class="field-row">
										<div class="field-info">
											<strong>{f.label}</strong>
											<span>{FIELD_TYPE_LABELS[f.field_type as FieldType] ?? f.field_type}</span>
										</div>
										<button class="del-btn" type="button" onclick={() => deleteEtypeField(f.id)}>Sil</button>
									</div>
								{/each}
							</div>
						{/if}

						<div class="field-add-form">
							<label><span>Alan Adı</span><input placeholder="Örn: Gelin ve Damat" bind:value={newEtfLabel} /></label>
							<label><span>Tip</span>
								<select bind:value={newEtfType}>
									{#each Object.entries(FIELD_TYPE_LABELS) as [val, lbl]}
										<option value={val}>{lbl}</option>
									{/each}
								</select>
							</label>
							{#if newEtfType === 'select'}
								<label class="full"><span>Seçenekler (virgülle ayır)</span><input placeholder="Seçenek 1, Seçenek 2" bind:value={newEtfOptions} /></label>
							{/if}
							<button class="add-field-btn" type="button" onclick={addEtypeField} disabled={!selectedEtypeId}>Alan Ekle</button>
						</div>
					</div>
				</div>
			{/if}

		</div>
	{:else if !loadError}
		<div class="loading">Yükleniyor…</div>
	{/if}
</section>

<style>
	/* ── Layout ── */
	.page-shell { max-width: 860px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }
	h1, h2, h3, p { margin: 0; }

	/* ── Tab bar ── */
	.tab-bar { display: flex; gap: 0.25rem; border-bottom: 2px solid var(--line); padding-bottom: 0; overflow-x: auto; }
	.tab-btn { padding: 0.6rem 1.1rem; border: 0; background: transparent; color: var(--muted); font: inherit; font-weight: 700; font-size: 0.88rem; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.15s; white-space: nowrap; border-radius: 6px 6px 0 0; }
	.tab-btn:hover { color: var(--text); background: var(--surface-strong); }
	.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); background: color-mix(in srgb, var(--accent) 6%, transparent); }

	/* ── Tab body ── */
	.tab-body { display: flex; flex-direction: column; gap: 1.25rem; }

	/* ── Form sections ── */
	.form-section { display: flex; flex-direction: column; gap: 0.85rem; padding: 1.25rem; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
	.section-header { display: flex; flex-direction: column; gap: 0.2rem; }
	h2 { font-size: 1rem; color: var(--accent); }
	h3 { font-size: 0.9rem; font-weight: 900; color: var(--muted); }
	.hint { color: var(--muted); font-size: 0.82rem; }

	/* ── Form grid ── */
	.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
	.form-grid .full { grid-column: 1 / -1; }
	.form-actions { padding-top: 0.25rem; }
	label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; }
	label span { color: var(--muted); font-size: 0.82rem; }
	input, select, textarea { width: 100%; min-height: 38px; border: 1px solid var(--line); border-radius: 7px; padding: 0.55rem 0.65rem; background: var(--surface-strong); color: var(--text); font: inherit; }
	textarea { resize: vertical; }

	/* ── Buttons ── */
	.save-btn { padding: 0.7rem 1.4rem; background: var(--accent); color: #fff; border: 0; border-radius: 8px; font-weight: 900; cursor: pointer; }
	.save-btn:disabled { opacity: 0.7; cursor: not-allowed; }
	.add-inline-btn { border: 0; border-radius: 7px; padding: 0.55rem 1rem; background: var(--accent); color: #fff; font-weight: 900; cursor: pointer; white-space: nowrap; font: inherit; }
	.add-field-btn { grid-column: 1 / -1; padding: 0.65rem; background: var(--accent); color: #fff; border: 0; border-radius: 7px; font-weight: 900; cursor: pointer; font: inherit; }

	/* ── Field add form ── */
	.field-add-form { display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; padding: 0.85rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; margin-top: 0.25rem; }
	.field-add-form .full { grid-column: 1 / -1; }

	/* ── Etkinlik tipi chip seçici ── */
	.etype-chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.5rem 0 1rem; }
	.etype-chip { padding: 0.4rem 0.85rem; border-radius: 999px; border: 1px solid color-mix(in srgb, var(--c) 40%, transparent); background: color-mix(in srgb, var(--c) 14%, var(--surface)); color: var(--text); font-weight: 800; font-size: 0.82rem; cursor: pointer; }
	.etype-chip.active { background: var(--c); color: #fff; }

	/* ── Field list ── */
	.field-list { display: flex; flex-direction: column; gap: 0.5rem; }
	.field-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; }
	.field-info { flex: 1; display: flex; flex-direction: column; gap: 0.15rem; }
	.field-info strong { font-size: 0.88rem; }
	.field-info span { font-size: 0.76rem; color: var(--muted); }
	.field-info small { font-size: 0.72rem; color: var(--muted); }

	/* ── Misc controls ── */
	.check-label { flex-direction: row !important; align-items: center; gap: 0.4rem; color: var(--muted); font-size: 0.82rem; }
	.check-label input { width: auto; min-height: auto; accent-color: var(--accent); }
	.del-btn { padding: 0.4rem 0.65rem; border: 1px solid var(--line); border-radius: 6px; background: transparent; color: var(--danger); font-weight: 900; font-size: 0.76rem; cursor: pointer; white-space: nowrap; }
	.vis-btn { padding: 0.35rem 0.6rem; border: 1px solid var(--line); border-radius: 6px; background: transparent; cursor: pointer; font-size: 0.92rem; transition: opacity 0.15s; }
	.vis-btn.hidden { opacity: 0.35; }
	.opt-hint { font-weight: 400; color: var(--muted); font-size: 0.75rem; }
	.checkbox-inline-row { flex-direction: row !important; align-items: center; gap: 0.5rem; }
	.checkbox-inline-row input { width: auto; min-height: auto; accent-color: var(--accent); }
	.smtp-test-result { font-weight: 800; font-size: 0.85rem; }
	.smtp-test-result.ok { color: #16a34a; }
	.smtp-test-result.fail { color: var(--danger); }
	.ph-tag { font-family: 'Courier New', monospace; font-size: 0.7rem; color: var(--accent); background: var(--accent-soft); padding: 0.1rem 0.35rem; border-radius: 4px; }
	.empty-hint { color: var(--muted); font-size: 0.82rem; font-style: italic; }
	.error-bar { padding: 0.85rem 1rem; background: color-mix(in srgb, var(--danger) 12%, transparent); border: 1px solid var(--danger); border-radius: 8px; color: var(--danger); font-weight: 800; }
	.loading { color: var(--muted); padding: 2rem; text-align: center; }

	/* ── Subsection divider ── */
	.subsection { display: flex; flex-direction: column; gap: 0.65rem; padding-top: 0.85rem; border-top: 1px solid var(--line); }

	/* ── Add row (inline input + button) ── */
	.add-row { display: flex; gap: 0.5rem; align-items: center; }
	.add-row input { flex: 1; }

	/* ── Type chips (customer form types) ── */
	.type-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
	.type-chip { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.45rem 0.8rem; border: 1px solid var(--line); border-radius: 20px; background: var(--surface-strong); color: var(--text); font-weight: 700; font-size: 0.82rem; cursor: pointer; transition: all 0.15s; font: inherit; }
	.type-chip:hover, .type-chip.active { border-color: var(--accent); background: var(--accent-soft); color: var(--accent); }
	.chip-del { color: var(--muted); font-size: 1rem; line-height: 1; cursor: pointer; }
	.chip-del:hover { color: var(--danger); }

	/* ── Event type colors ── */
	.type-color-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.15); }
	.type-color-input { width: 32px; height: 32px; min-height: 32px; border: 0; padding: 0; background: transparent; cursor: pointer; border-radius: 6px; flex-shrink: 0; }

	@media (max-width: 640px) { .form-grid { grid-template-columns: 1fr; } .form-grid .full { grid-column: 1; } }
</style>
