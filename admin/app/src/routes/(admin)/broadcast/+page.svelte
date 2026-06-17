<script lang="ts">
	import { onMount } from 'svelte';

	const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

	interface Salon {
		id: string;
		name: string;
		company_name: string;
		city: string;
		notification_email: string;
		max_users: number;
	}

	let salons = $state<Salon[]>([]);
	let selectedIds = $state<Set<string>>(new Set());
	let search = $state('');
	let cityFilter = $state('all');
	let subject = $state('');
	let body = $state('');
	let sendEmail = $state(true);
	let sendNotif = $state(true);
	let sending = $state(false);
	let result = $state<{ sent: number; total: number } | null>(null);
	let error = $state('');

	const headers = () => ({
		'Content-Type': 'application/json',
		Authorization: `Bearer ${localStorage.getItem('admin_token')}`
	});

	onMount(async () => {
		const r = await fetch(`${API}/admin/salons`, { headers: headers() });
		if (r.ok) salons = await r.json();
	});

	const hasEmail = (s: Salon) => Boolean(s.notification_email?.trim());

	const visibleSalons = $derived(() => {
		const q = search.trim().toLocaleLowerCase('tr');
		const list = [...salons].sort((a, b) => a.name.localeCompare(b.name, 'tr'));
		return list.filter((s) => {
			const city = cityName(s);
			if (cityFilter !== 'all' && city !== cityFilter) return false;
			if (!q) return true;
			return [s.name, s.company_name, s.notification_email, city]
				.filter(Boolean)
				.some((v) => v.toLocaleLowerCase('tr').includes(q));
		});
	});

	const cityOptions = $derived(() => {
		const counts = new Map<string, number>();
		for (const s of salons) {
			const city = cityName(s);
			counts.set(city, (counts.get(city) ?? 0) + 1);
		}
		return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0], 'tr'));
	});

	const groupedSalons = $derived(() => {
		const groups = new Map<string, Salon[]>();
		for (const s of visibleSalons()) {
			const city = cityName(s);
			if (!groups.has(city)) groups.set(city, []);
			groups.get(city)!.push(s);
		}
		return [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0], 'tr'));
	});

	const categories = $derived(() => {
		const emailReady = salons.filter(hasEmail);
		const emailMissing = salons.filter((s) => !hasEmail(s));
		const multiUser = salons.filter((s) => s.max_users > 1);
		return [
			{
				id: 'all',
				label: 'Tüm müşteriler',
				helper: 'Panel bildirimi veya e-posta için tüm salon hesapları.',
				ids: salons.map((s) => s.id)
			},
			{
				id: 'email',
				label: 'E-posta tanımlı',
				helper: 'Bildirim e-postası kayıtlı müşteriler.',
				ids: emailReady.map((s) => s.id)
			},
			{
				id: 'missing-email',
				label: 'E-postası eksik',
				helper: 'Panel bildirimi gidebilir, e-posta için ayar bekler.',
				ids: emailMissing.map((s) => s.id)
			},
			{
				id: 'team',
				label: 'Ekipli hesaplar',
				helper: 'Birden fazla kullanıcı hakkı olan müşteriler.',
				ids: multiUser.map((s) => s.id)
			}
		];
	});

	const allSelected = $derived(salons.length > 0 && salons.every(s => selectedIds.has(s.id)));
	const selectedSalons = $derived(salons.filter((s) => selectedIds.has(s.id)));
	const selectedEmailCount = $derived(selectedSalons.filter(hasEmail).length);

	function cityName(s: Salon) {
		return s.city?.trim() || 'Şehir belirtilmemiş';
	}

	function toggleAll() {
		if (allSelected) selectedIds = new Set();
		else selectedIds = new Set(salons.map(s => s.id));
	}

	function categoryState(ids: string[]): 'all' | 'some' | 'none' {
		if (ids.length === 0) return 'none';
		const checked = ids.filter((id) => selectedIds.has(id)).length;
		if (checked === ids.length) return 'all';
		if (checked > 0) return 'some';
		return 'none';
	}

	function applyCategory(ids: string[]) {
		selectedIds = new Set(ids);
	}

	function toggleSalon(id: string) {
		const next = new Set(selectedIds);
		if (next.has(id)) next.delete(id); else next.add(id);
		selectedIds = next;
	}

	async function send() {
		if (!subject.trim() || !body.trim()) { error = 'Konu ve içerik zorunludur.'; return; }
		if (!sendEmail && !sendNotif) { error = 'En az bir gönderim türü seçin.'; return; }
		if (selectedIds.size === 0) { error = 'En az bir müşteri veya kategori seçin.'; return; }
		sending = true;
		error = '';
		result = null;
		try {
			const r = await fetch(`${API}/admin/broadcast`, {
				method: 'POST',
				headers: headers(),
				body: JSON.stringify({
					subject: subject.trim(),
					body: body.trim(),
					salon_ids: [...selectedIds],
					send_email: sendEmail,
					send_notification: sendNotif
				})
			});
			if (r.ok) result = await r.json();
			else error = (await r.json()).detail ?? 'Gönderim başarısız';
		} finally { sending = false; }
	}
</script>

<div class="shell">
	<div class="page-head">
		<div><p class="eyebrow">Admin</p><h1>Mesaj Gönder</h1></div>
	</div>

	<div class="layout">
		<!-- Left: Salon selection -->
		<div class="card recipients-card">
			<div class="card-head">
				<div>
					<h2>Alıcılar</h2>
					<p class="card-subtitle">Kategoriyle toplu seç, gerekirse tek tek düzenle.</p>
				</div>
				<label class="select-all">
					<input type="checkbox" checked={allSelected} onchange={toggleAll} />
					<span>Tümünü seç</span>
				</label>
			</div>

			{#if salons.length === 0}
				<p class="empty-msg">Salon bulunamadı.</p>
			{:else}
				<div class="category-grid">
					{#each categories() as category}
						<button
							type="button"
							class="category-card"
							class:active={categoryState(category.ids) === 'all'}
							class:partial={categoryState(category.ids) === 'some'}
							onclick={() => applyCategory(category.ids)}
							disabled={category.ids.length === 0}
						>
							<span class="category-top">
								<strong>{category.label}</strong>
								<em>{category.ids.length}</em>
							</span>
							<span>{category.helper}</span>
						</button>
					{/each}
				</div>

				<div class="search-row">
					<input bind:value={search} placeholder="Salon, firma, şehir veya e-posta ara" />
				</div>

				<div class="city-filter" aria-label="Şehre göre görüntüle">
					<button
						type="button"
						class:active={cityFilter === 'all'}
						onclick={() => (cityFilter = 'all')}
					>
						Tüm şehirler
						<span>{salons.length}</span>
					</button>
					{#each cityOptions() as [city, count]}
						<button
							type="button"
							class:active={cityFilter === city}
							onclick={() => (cityFilter = city)}
						>
							{city}
							<span>{count}</span>
						</button>
					{/each}
				</div>

				<div class="salon-list">
					{#each groupedSalons() as [city, citySalons]}
						<section class="city-group">
							<div class="city-head">
								<strong>{city}</strong>
								<span>{citySalons.length} salon</span>
							</div>
							{#each citySalons as s (s.id)}
								<label class="salon-row" class:sel={selectedIds.has(s.id)}>
									<input
										type="checkbox"
										checked={selectedIds.has(s.id)}
										onchange={() => toggleSalon(s.id)}
									/>
									<span class="salon-copy">
										<span class="salon-name">{s.name}</span>
										<span class="salon-meta">
											{#if s.company_name}{s.company_name}{:else}Firma adı yok{/if}
											<span aria-hidden="true">•</span>
											{#if hasEmail(s)}{s.notification_email}{:else}E-posta eksik{/if}
										</span>
									</span>
								</label>
							{/each}
						</section>
					{:else}
						<p class="empty-msg">Bu görüntüde salon bulunamadı.</p>
					{/each}
				</div>

				<div class="selection-summary">
					<div>
						<strong>{selectedIds.size}</strong>
						<span>müşteri seçili</span>
					</div>
					<div>
						<strong>{selectedEmailCount}</strong>
						<span>e-posta alabilir</span>
					</div>
				</div>

				{#if selectedSalons.length > 0}
					<div class="selected-strip">
						{#each selectedSalons.slice(0, 8) as s (s.id)}
							<button type="button" onclick={() => toggleSalon(s.id)}>{s.name}</button>
						{/each}
						{#if selectedSalons.length > 8}
							<span>+{selectedSalons.length - 8}</span>
						{/if}
					</div>
				{/if}

				<div class="selection-footer">
					{#if selectedIds.size > 0}
						<button class="clear-btn" type="button" onclick={() => (selectedIds = new Set())}>Seçimi temizle</button>
					{:else}
						<span class="sel-hint">Gönderim için kategori veya salon seç.</span>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Right: Message -->
		<div class="card message-card">
			<div class="message-head">
				<h2>Mesaj</h2>
				<span>{selectedIds.size} alıcı</span>
			</div>
			<div class="form">
				<label>
					<span>Konu *</span>
					<input bind:value={subject} placeholder="Duyuru: Yeni özellik" />
				</label>
				<label>
					<span>İçerik *</span>
					<textarea rows="9" bind:value={body} placeholder="Mesajınızı buraya yazın…"></textarea>
				</label>

				<div class="options-row">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={sendEmail} />
						<span>E-posta gönder</span>
					</label>
					<label class="toggle-label">
						<input type="checkbox" bind:checked={sendNotif} />
						<span>Panel bildirimi</span>
					</label>
				</div>

				{#if error}
					<div class="msg-error">{error}</div>
				{/if}
				{#if result}
					<div class="msg-success">
						Gönderildi — {result.total} müşteriye ulaşıldı{result.sent > 0 ? `, ${result.sent} e-posta` : ''}
					</div>
				{/if}

				<button class="send-btn" type="button" onclick={send} disabled={sending}>
					{sending ? 'Gönderiliyor…' : 'Gönder'}
				</button>
			</div>
		</div>
	</div>
</div>

<style>
	.shell { display: flex; flex-direction: column; gap: 1.5rem; }
	.page-head { display: flex; align-items: flex-end; justify-content: space-between; }
	h1, h2, p { margin: 0; }
	h1 { font-size: clamp(1.6rem, 3vw, 2.4rem); font-weight: 900; }
	h2 { font-size: 1.05rem; font-weight: 900; color: #e2e8f0; }
	.eyebrow { margin-bottom: 0.25rem; color: #c59b31; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase; }

	.layout { display: grid; grid-template-columns: minmax(360px, 430px) 1fr; gap: 1.25rem; align-items: start; }
	.card { background: #172033; border: 1px solid rgba(226,232,240,0.1); border-radius: 8px; }
	.recipients-card { display: flex; flex-direction: column; overflow: hidden; }
	.message-card { padding: 1.25rem; }

	.card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; padding: 1rem 1.25rem; border-bottom: 1px solid rgba(226,232,240,0.08); }
	.card-subtitle { margin-top: 0.25rem; color: #64748b; font-size: 0.78rem; font-weight: 700; }
	.select-all { display: flex; flex-direction: row; align-items: center; gap: 0.45rem; cursor: pointer; font-size: 0.82rem; font-weight: 800; color: #94a3b8; white-space: nowrap; }
	.select-all input { accent-color: #c59b31; }

	.category-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; padding: 1rem 1.25rem 0.75rem; }
	.category-card {
		display: flex; flex-direction: column; gap: 0.35rem; min-height: 98px;
		border: 1px solid rgba(226,232,240,0.11); border-radius: 8px; padding: 0.75rem;
		background: #101827; color: #94a3b8; text-align: left; cursor: pointer;
	}
	.category-card:hover { border-color: rgba(197,155,49,0.38); background: rgba(197,155,49,0.07); }
	.category-card.active { border-color: rgba(197,155,49,0.65); background: rgba(197,155,49,0.13); }
	.category-card.partial { border-color: rgba(148,163,184,0.32); }
	.category-card:disabled { opacity: 0.45; cursor: not-allowed; }
	.category-card span:last-child { font-size: 0.74rem; line-height: 1.35; font-weight: 700; }
	.category-top { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
	.category-top strong { color: #e2e8f0; font-size: 0.82rem; }
	.category-top em { min-width: 28px; height: 24px; border-radius: 999px; display: grid; place-items: center; background: rgba(226,232,240,0.08); color: #c59b31; font-style: normal; font-size: 0.75rem; font-weight: 900; }

	.search-row { padding: 0 1.25rem 0.75rem; }

	.city-filter {
		display: flex;
		gap: 0.45rem;
		overflow-x: auto;
		padding: 0 1.25rem 0.8rem;
		scrollbar-width: thin;
	}
	.city-filter button {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		white-space: nowrap;
		border: 1px solid rgba(226,232,240,0.1);
		border-radius: 999px;
		padding: 0.35rem 0.6rem;
		background: rgba(16,24,39,0.7);
		color: #94a3b8;
		font-size: 0.75rem;
		font-weight: 850;
		cursor: pointer;
	}
	.city-filter button:hover,
	.city-filter button.active {
		border-color: rgba(197,155,49,0.42);
		background: rgba(197,155,49,0.1);
		color: #f8fafc;
	}
	.city-filter span {
		min-width: 22px;
		height: 20px;
		border-radius: 999px;
		display: grid;
		place-items: center;
		background: rgba(226,232,240,0.08);
		color: #c59b31;
		font-size: 0.68rem;
	}

	.salon-list { overflow-y: auto; max-height: 360px; padding: 0.15rem 0 0.5rem; border-top: 1px solid rgba(226,232,240,0.08); }
	.empty-msg { padding: 1.5rem 1.25rem; color: #64748b; font-size: 0.88rem; font-weight: 700; }

	.city-group + .city-group { border-top: 1px solid rgba(226,232,240,0.07); }
	.city-head {
		position: sticky;
		top: 0;
		z-index: 1;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.55rem 1.25rem;
		background: #172033;
	}
	.city-head strong {
		color: #c59b31;
		font-size: 0.76rem;
		font-weight: 950;
		text-transform: uppercase;
	}
	.city-head span {
		color: #64748b;
		font-size: 0.72rem;
		font-weight: 850;
	}

	.salon-row {
		display: flex; flex-direction: row; align-items: flex-start; gap: 0.65rem;
		padding: 0.68rem 1.25rem;
		cursor: pointer;
		user-select: none;
		transition: background 0.1s;
	}
	.salon-row:hover { background: rgba(255,255,255,0.03); }
	.salon-row.sel { background: rgba(197,155,49,0.07); }
	.salon-row input { width: auto; min-height: auto; margin-top: 0.12rem; accent-color: #c59b31; flex-shrink: 0; }
	.salon-copy { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
	.salon-name { font-size: 0.88rem; font-weight: 850; color: #cbd5e1; }
	.salon-row.sel .salon-name { color: #f8fafc; }
	.salon-meta { display: flex; align-items: center; gap: 0.35rem; color: #64748b; font-size: 0.74rem; font-weight: 700; overflow-wrap: anywhere; }

	.selection-summary { display: grid; grid-template-columns: repeat(2, 1fr); border-top: 1px solid rgba(226,232,240,0.08); border-bottom: 1px solid rgba(226,232,240,0.08); }
	.selection-summary div { display: flex; flex-direction: column; gap: 0.1rem; padding: 0.85rem 1.25rem; }
	.selection-summary div + div { border-left: 1px solid rgba(226,232,240,0.08); }
	.selection-summary strong { color: #c59b31; font-size: 1.25rem; line-height: 1; }
	.selection-summary span { color: #64748b; font-size: 0.75rem; font-weight: 800; }

	.selected-strip { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; padding: 0.75rem 1.25rem 0; }
	.selected-strip button, .selected-strip span { border: 1px solid rgba(197,155,49,0.28); border-radius: 999px; padding: 0.25rem 0.55rem; background: rgba(197,155,49,0.08); color: #e2e8f0; font-size: 0.73rem; font-weight: 800; }
	.selected-strip button { cursor: pointer; }

	.selection-footer { display: flex; align-items: center; justify-content: flex-end; padding: 0.75rem 1.25rem; min-height: 44px; }
	.sel-hint { margin-right: auto; font-size: 0.78rem; color: #64748b; font-weight: 700; }
	.clear-btn { font-size: 0.78rem; font-weight: 850; color: #94a3b8; background: none; border: none; cursor: pointer; padding: 0; }
	.clear-btn:hover { color: #e2e8f0; }

	.message-head { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
	.message-head span { border-radius: 999px; background: rgba(226,232,240,0.07); color: #94a3b8; padding: 0.25rem 0.65rem; font-size: 0.76rem; font-weight: 900; }
	.form { display: flex; flex-direction: column; gap: 0.85rem; margin-top: 1rem; }
	label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; font-size: 0.85rem; color: #64748b; }
	input, textarea { width: 100%; min-height: 40px; border: 1px solid rgba(226,232,240,0.12); border-radius: 8px; padding: 0.55rem 0.75rem; background: #101827; color: #f8fafc; font: inherit; box-sizing: border-box; }
	input:focus, textarea:focus { outline: none; border-color: rgba(197,155,49,0.4); }
	textarea { min-height: 180px; resize: vertical; }

	.options-row { display: flex; gap: 1.5rem; flex-wrap: wrap; }
	.toggle-label { display: flex; flex-direction: row; align-items: center; gap: 0.45rem; color: #94a3b8; font-size: 0.85rem; cursor: pointer; }
	.toggle-label input { width: auto; min-height: auto; accent-color: #c59b31; }

	.send-btn { padding: 0.8rem 1.6rem; background: #c59b31; color: #fff; border: 0; border-radius: 8px; font-weight: 900; font-size: 0.95rem; cursor: pointer; align-self: flex-start; }
	.send-btn:disabled { opacity: 0.6; cursor: not-allowed; }

	.msg-error { padding: 0.75rem 1rem; border-radius: 8px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25); color: #fca5a5; font-size: 0.85rem; font-weight: 700; }
	.msg-success { padding: 0.75rem 1rem; border-radius: 8px; background: rgba(22,163,74,0.1); border: 1px solid rgba(22,163,74,0.25); color: #86efac; font-size: 0.85rem; font-weight: 700; }

	@media (max-width: 980px) {
		.layout { grid-template-columns: 1fr; }
	}

	@media (max-width: 520px) {
		.category-grid { grid-template-columns: 1fr; }
		.card-head { flex-direction: column; }
		.select-all { align-self: flex-start; }
		.salon-meta { flex-direction: column; align-items: flex-start; gap: 0.1rem; }
		.salon-meta span { display: none; }
	}
</style>
