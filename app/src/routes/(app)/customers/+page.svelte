<script lang="ts">
	import { onMount } from 'svelte';
	import { api, PORTAL_URL, type EventApi, type EventTypeApi, type VenueLayoutApi, type PortalFormSubmissionApi } from '$lib/api';

	let searchQuery = $state('');
	let filterField = $state('all');
	let sortBy = $state<'date' | 'name' | 'type'>('date');
	let events = $state<EventApi[]>([]);
	let eventTypes = $state<EventTypeApi[]>([]);
	let layouts = $state<VenueLayoutApi[]>([]);
	let loadError = $state('');

	let selectedEventId = $state<string | null>(null);
	let submissions = $state<PortalFormSubmissionApi[]>([]);
	let submissionsLoading = $state(false);

	onMount(async () => {
		try {
			const [evs, types, lyts] = await Promise.all([
				api.get<EventApi[]>('/events'),
				api.get<EventTypeApi[]>('/events/types'),
				api.get<VenueLayoutApi[]>('/venue/layouts')
			]);
			events = evs;
			eventTypes = types;
			layouts = lyts;
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'Yükleme hatası';
		}
	});

	const typeColor = (typeId: string | null) => eventTypes.find(t => t.id === typeId)?.color ?? '#64748b';
	const typeName = (typeId: string | null) => eventTypes.find(t => t.id === typeId)?.name ?? '—';
	const layoutName = (layoutId: string) => layouts.find(l => l.id === layoutId)?.name ?? layoutId;

	const payBadge = (ev: EventApi) => {
		if (ev.payment_complete) return { label: '₺ Tamamlandı', cls: 'badge-green' };
		if (ev.total_paid > 0) return { label: '₺ Kısmi', cls: 'badge-blue' };
		return { label: '₺ Bekliyor', cls: 'badge-amber' };
	};

	const formatMoney = (v: number) => `₺${Math.round(v).toLocaleString('tr-TR')}`;
	const formatDate = (d: string) => {
		try { return new Date(d + 'T00:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }); }
		catch { return d; }
	};
	const formatDateTime = (s: string) => {
		try { return new Date(s).toLocaleString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
		catch { return s; }
	};

	const filteredEvents = $derived(() => {
		let list = [...events];
		if (searchQuery.trim()) {
			const q = searchQuery.toLocaleLowerCase('tr-TR');
			list = list.filter((ev) => {
				if (filterField === 'all' || filterField === 'title')
					if (ev.title.toLocaleLowerCase('tr-TR').includes(q)) return true;
				if (filterField === 'all' || filterField === 'name')
					if (ev.full_name.toLocaleLowerCase('tr-TR').includes(q)) return true;
				if (filterField === 'all' || filterField === 'phone')
					if (ev.mobile_phone.includes(searchQuery)) return true;
				if (filterField === 'all' || filterField === 'type') {
					const tn = typeName(ev.type_id);
					if (tn.toLocaleLowerCase('tr-TR').includes(q)) return true;
				}
				if (filterField === 'all' || filterField === 'appt_no') {
					if (ev.appointment_no && String(ev.appointment_no).includes(searchQuery.trim())) return true;
				}
				return false;
			});
		}
		list.sort((a, b) => {
			if (sortBy === 'date') return a.event_date.localeCompare(b.event_date);
			if (sortBy === 'name') return a.full_name.localeCompare(b.full_name, 'tr-TR');
			return typeName(a.type_id).localeCompare(typeName(b.type_id), 'tr-TR');
		});
		return list;
	});

	const selectedEvent = $derived(events.find(e => e.id === selectedEventId) ?? null);

	async function openDetail(ev: EventApi) {
		selectedEventId = ev.id;
		submissions = [];
		if (ev.portal_token && ev.portal_enabled) {
			submissionsLoading = true;
			try {
				submissions = await api.get<PortalFormSubmissionApi[]>(`/events/${ev.id}/portal-submissions`);
			} catch { /* silent */ }
			finally { submissionsLoading = false; }
		}
	}

	function closeDetail() {
		selectedEventId = null;
		submissions = [];
	}
</script>

<section class="page-shell">
	<div class="page-heading">
		<div>
			<h1>Davet Listesi</h1>
		</div>
		<a href="/calendar" class="new-btn">+ Yeni Davet</a>
	</div>

	{#if loadError}
		<div class="error-bar">{loadError}</div>
	{/if}

	<div class="main-layout" class:has-detail={!!selectedEvent}>
		<div class="list-side">
			<div class="toolbar">
				<input class="search" type="search" placeholder="Ara…" bind:value={searchQuery} />
				<select bind:value={filterField}>
					<option value="all">Tüm alanlar</option>
					<option value="appt_no">Randevu No</option>
					<option value="title">Başlık</option>
					<option value="name">İsim</option>
					<option value="phone">Telefon</option>
					<option value="type">Tip</option>
				</select>
				<select bind:value={sortBy}>
					<option value="date">Tarihe göre</option>
					<option value="name">İsme göre</option>
					<option value="type">Tipe göre</option>
				</select>
				<span class="count">{filteredEvents().length} davet</span>
			</div>

			<div class="table-wrap">
				<table>
					<thead>
						<tr>
							<th>#</th>
							<th>Tarih & Saat</th>
							<th>Tip</th>
							<th>Durum</th>
							<th>Ad Soyad / Gelin&Damat</th>
							<th>Telefon</th>
							<th>Davetli</th>
							<th>Toplam</th>
							<th>Alınan</th>
							<th>Kalan</th>
							<th>Ödeme</th>
							<th>Portal</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredEvents() as ev}
							<tr
								class:selected={selectedEventId === ev.id}
								role="button"
								tabindex="0"
								onclick={() => openDetail(ev)}
								onkeydown={(e) => e.key === 'Enter' && openDetail(ev)}
							>
								<td>
									{#if ev.appointment_no}
										<span class="appt-no">#{ev.appointment_no}</span>
									{:else}
										<span class="muted">—</span>
									{/if}
								</td>
								<td>
									<div class="date-cell">
										<strong>{formatDate(ev.event_date)}</strong>
										<span>{ev.start_time} – {ev.end_time}</span>
									</div>
								</td>
								<td>
									<span class="type-pill" style="--c:{typeColor(ev.type_id)}">{typeName(ev.type_id)}</span>
								</td>
								<td>
									<span class="status-pill" class:kesin={ev.reservation_status === 'Kesin Rezervasyon'}>
										{ev.reservation_status}
									</span>
								</td>
								<td>
									<div class="name-cell">
										<strong>{ev.full_name || ev.title}</strong>
										{#if ev.portal_title && ev.portal_title !== 'Davetiniz'}
											<span class="portal-title-tag">{ev.portal_title}</span>
										{:else if ev.bride_groom}
											<span>{ev.bride_groom}</span>
										{/if}
									</div>
								</td>
								<td>{ev.mobile_phone || ev.phone || '—'}</td>
								<td class="num">{ev.guest_count || '—'}</td>
								<td class="num">{ev.total_fee ? formatMoney(ev.total_fee) : '—'}</td>
								<td class="num">{ev.total_paid ? formatMoney(ev.total_paid) : '—'}</td>
								<td class="num">{ev.total_fee ? formatMoney(ev.total_fee - ev.total_paid) : '—'}</td>
								<td><span class="pay-badge {payBadge(ev).cls}">{payBadge(ev).label}</span></td>
								<td>
									{#if ev.portal_enabled && ev.portal_token}
										<span class="portal-pill">Aktif</span>
									{:else}
										<span class="muted">—</span>
									{/if}
								</td>
							</tr>
						{/each}
						{#if filteredEvents().length === 0}
							<tr><td colspan="12" class="empty">Kayıt bulunamadı.</td></tr>
						{/if}
					</tbody>
				</table>
			</div>
		</div>

		{#if selectedEvent}
			<aside class="detail-panel">
				<div class="detail-header">
					<div>
						<p class="detail-eyebrow">Davet Detayı</p>
						<h2>{selectedEvent.full_name || selectedEvent.title}</h2>
					</div>
					<button class="close-btn" type="button" onclick={closeDetail}>✕</button>
				</div>

				<!-- Basic info -->
				<div class="detail-section">
					<h3>Genel Bilgiler</h3>
					<div class="info-grid">
						{#if selectedEvent.appointment_no}
							<div class="info-row"><span>Randevu No</span><strong class="appt-no-lg">#{selectedEvent.appointment_no}</strong></div>
						{/if}
						<div class="info-row"><span>Tarih</span><strong>{formatDate(selectedEvent.event_date)}</strong></div>
						<div class="info-row"><span>Saat</span><strong>{selectedEvent.start_time} – {selectedEvent.end_time}</strong></div>
						{#if selectedEvent.portal_title && selectedEvent.portal_title !== 'Davetiniz'}
							<div class="info-row"><span>Portal Başlığı</span><strong>{selectedEvent.portal_title}</strong></div>
						{/if}
						{#if selectedEvent.bride_groom}
							<div class="info-row"><span>Gelin & Damat</span><strong>{selectedEvent.bride_groom}</strong></div>
						{/if}
						{#if selectedEvent.type_id}
							<div class="info-row"><span>Tip</span>
								<span class="type-pill sm" style="--c:{typeColor(selectedEvent.type_id)}">{typeName(selectedEvent.type_id)}</span>
							</div>
						{/if}
						<div class="info-row"><span>Durum</span>
							<span class="status-pill" class:kesin={selectedEvent.reservation_status === 'Kesin Rezervasyon'}>{selectedEvent.reservation_status}</span>
						</div>
						{#if selectedEvent.mobile_phone || selectedEvent.phone}
							<div class="info-row"><span>Telefon</span><strong>{selectedEvent.mobile_phone || selectedEvent.phone}</strong></div>
						{/if}
						{#if selectedEvent.tc_no}
							<div class="info-row"><span>TC No</span><strong>{selectedEvent.tc_no}</strong></div>
						{/if}
						{#if selectedEvent.region}
							<div class="info-row"><span>Bölge</span><strong>{selectedEvent.region}</strong></div>
						{/if}
						{#if selectedEvent.guest_count}
							<div class="info-row"><span>Davetli Sayısı</span><strong>{selectedEvent.guest_count}</strong></div>
						{/if}
						{#if selectedEvent.staff}
							<div class="info-row"><span>Personel</span><strong>{selectedEvent.staff}</strong></div>
						{/if}
					</div>
				</div>

				<!-- Payment info -->
				{#if selectedEvent.total_fee > 0}
					<div class="detail-section">
						<h3>Ödeme</h3>
						<div class="info-grid">
							<div class="info-row"><span>Toplam Ücret</span><strong class="money">{formatMoney(selectedEvent.total_fee)}</strong></div>
							<div class="info-row"><span>Alınan</span><strong class="money good">{formatMoney(selectedEvent.total_paid)}</strong></div>
							<div class="info-row"><span>Kalan</span><strong class="money {selectedEvent.total_fee - selectedEvent.total_paid > 0 ? 'warn' : 'good'}">{formatMoney(selectedEvent.total_fee - selectedEvent.total_paid)}</strong></div>
							{#if selectedEvent.kapora_amount}
								<div class="info-row"><span>Kapora</span><strong class="money">{formatMoney(selectedEvent.kapora_amount)}</strong></div>
							{/if}
							<div class="info-row"><span>Durum</span>
								<span class="pay-badge {payBadge(selectedEvent).cls}">{payBadge(selectedEvent).label}</span>
							</div>
						</div>
					</div>
				{/if}

				<!-- Custom fields (Ek Alanlar) -->
				{#if selectedEvent.custom_fields.length > 0}
					<div class="detail-section">
						<h3>Ek Alanlar</h3>
						<div class="info-grid">
							{#each selectedEvent.custom_fields as cf}
								{#if cf.value}
									<div class="info-row"><span>{cf.label}</span><strong>{cf.value}</strong></div>
								{/if}
							{/each}
						</div>
					</div>
				{/if}

				<!-- Reserved layouts -->
				{#if selectedEvent.reserved_layout_ids.length > 0}
					<div class="detail-section">
						<h3>Rezerve Salonlar</h3>
						<div class="layout-chips">
							{#each selectedEvent.reserved_layout_ids as lid}
								<span class="layout-chip">{layoutName(lid)}</span>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Portal info -->
				<div class="detail-section">
					<h3>Portal</h3>
					{#if selectedEvent.portal_enabled && selectedEvent.portal_token}
						<div class="info-grid">
							<div class="info-row"><span>Durum</span><span class="portal-pill">Aktif</span></div>
						</div>
						<a href="{PORTAL_URL}/{selectedEvent.portal_token}" target="_blank" class="portal-link">
							Portal linkini aç ↗
						</a>
					{:else}
						<p class="empty-hint">Bu davet için portal aktif değil.</p>
					{/if}
				</div>

				<!-- Portal form submissions -->
				{#if selectedEvent.portal_enabled && selectedEvent.portal_token}
					<div class="detail-section">
						<h3>Portal Form Gönderileri</h3>
						{#if submissionsLoading}
							<p class="loading-hint">Yükleniyor…</p>
						{:else if submissions.length === 0}
							<p class="empty-hint">Henüz form gönderisi yok.</p>
						{:else}
							<div class="submissions-list">
								{#each submissions as sub}
									<div class="submission-card">
										<div class="submission-meta">{formatDateTime(sub.submitted_at)}</div>
										<div class="submission-data">
											{#each Object.entries(sub.data) as [key, val]}
												<div class="submission-row">
													<span>{key}</span>
													<strong>{String(val)}</strong>
												</div>
											{/each}
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				{/if}

				<!-- Note -->
				{#if selectedEvent.note}
					<div class="detail-section">
						<h3>Notlar</h3>
						<p class="note-text">{selectedEvent.note}</p>
					</div>
				{/if}

				<div class="detail-footer">
					<a href="/calendar?event={selectedEvent.id}" class="edit-btn">Takvimde Düzenle</a>
				</div>
			</aside>
		{/if}
	</div>
</section>

<style>
	.page-shell { max-width: 1920px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }
	h1, h2, p { margin: 0; }
	.page-heading { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }
	.new-btn { padding: 0.75rem 1.25rem; background: var(--accent); color: #fff; border-radius: 8px; text-decoration: none; font-weight: 900; white-space: nowrap; }
	.error-bar { padding: 0.75rem 1rem; background: color-mix(in srgb, #ef4444 12%, transparent); border: 1px solid #ef4444; border-radius: 8px; color: #ef4444; font-weight: 800; font-size: 0.85rem; }

	.main-layout { display: grid; grid-template-columns: 1fr; gap: 1rem; }
	.main-layout.has-detail { grid-template-columns: 1fr 380px; }

	.list-side { display: flex; flex-direction: column; gap: 0.75rem; min-width: 0; }
	.toolbar { display: flex; align-items: center; gap: 0.65rem; padding: 0.65rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; flex-wrap: wrap; }
	input, select { min-height: 36px; border: 1px solid var(--line); border-radius: 7px; padding: 0.4rem 0.65rem; background: var(--surface-strong); color: var(--text); font: inherit; }
	.search { flex: 1; min-width: 160px; }
	.count { margin-left: auto; font-size: 0.82rem; color: var(--muted); font-weight: 800; }
	.table-wrap { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; overflow-x: auto; }
	table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
	th { padding: 0.65rem 0.85rem; text-align: left; font-size: 0.72rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); border-bottom: 1px solid var(--line); white-space: nowrap; }
	td { padding: 0.75rem 0.85rem; border-bottom: 1px solid color-mix(in srgb, var(--line) 60%, transparent); vertical-align: middle; }
	tr:last-child td { border-bottom: 0; }
	tr[role="button"] { cursor: pointer; }
	tr[role="button"]:hover td, tr.selected td { background: color-mix(in srgb, var(--accent) 6%, transparent); }
	tr.selected td { background: color-mix(in srgb, var(--accent) 10%, transparent); }

	.date-cell { display: flex; flex-direction: column; gap: 0.15rem; }
	.date-cell strong { font-size: 0.88rem; }
	.date-cell span { font-size: 0.75rem; color: var(--muted); }
	.type-pill { display: inline-flex; padding: 0.28rem 0.55rem; border-radius: 5px; font-size: 0.75rem; font-weight: 900; background: color-mix(in srgb, var(--c) 18%, transparent); color: var(--c); border: 1px solid color-mix(in srgb, var(--c) 30%, transparent); }
	.type-pill.sm { font-size: 0.72rem; padding: 0.2rem 0.45rem; }
	.status-pill { display: inline-flex; padding: 0.28rem 0.55rem; border-radius: 5px; font-size: 0.74rem; font-weight: 900; background: color-mix(in srgb, #f59e0b 14%, transparent); color: #f59e0b; }
	.status-pill.kesin { background: color-mix(in srgb, #16a34a 14%, transparent); color: #16a34a; }
	.name-cell { display: flex; flex-direction: column; gap: 0.15rem; }
	.name-cell strong { font-size: 0.88rem; }
	.name-cell span { font-size: 0.75rem; color: var(--muted); }
	.num { text-align: right; font-variant-numeric: tabular-nums; font-weight: 800; }
	.pay-badge { display: inline-flex; padding: 0.28rem 0.55rem; border-radius: 5px; font-size: 0.74rem; font-weight: 900; }
	.badge-green { background: color-mix(in srgb, #16a34a 14%, transparent); color: #16a34a; }
	.badge-blue { background: color-mix(in srgb, #2563eb 14%, transparent); color: #2563eb; }
	.badge-amber { background: color-mix(in srgb, #f59e0b 14%, transparent); color: #f59e0b; }
	.portal-pill { display: inline-flex; padding: 0.28rem 0.55rem; border-radius: 5px; font-size: 0.74rem; font-weight: 900; background: color-mix(in srgb, #2563eb 14%, transparent); color: #2563eb; }
	.portal-title-tag { font-size: 0.75rem; color: var(--accent); font-style: italic; }
	.muted { color: var(--muted); font-size: 0.82rem; }
	.appt-no { font-size: 0.78rem; font-weight: 900; color: var(--accent); background: var(--accent-soft); padding: 0.15rem 0.45rem; border-radius: 5px; white-space: nowrap; }
	.appt-no-lg { color: var(--accent); font-size: 0.92rem; }
	.empty { text-align: center; color: var(--muted); padding: 2rem; font-style: italic; }

	/* Detail panel */
	.detail-panel {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 10px;
		display: flex;
		flex-direction: column;
		gap: 0;
		overflow-y: auto;
		max-height: calc(100vh - 220px);
		position: sticky;
		top: 1rem;
		align-self: start;
	}

	.detail-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.5rem;
		padding: 1rem 1.1rem 0.75rem;
		border-bottom: 1px solid var(--line);
		position: sticky;
		top: 0;
		background: var(--surface);
		z-index: 1;
	}
	.detail-eyebrow { color: var(--accent); font-size: 0.72rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.2rem; }
	.detail-header h2 { font-size: 1.05rem; font-weight: 900; margin: 0; }
	.close-btn { background: var(--surface-strong); border: 1px solid var(--line); border-radius: 6px; padding: 0.3rem 0.6rem; cursor: pointer; color: var(--muted); font-size: 0.9rem; flex-shrink: 0; }
	.close-btn:hover { color: var(--text); }

	.detail-section {
		padding: 0.85rem 1.1rem;
		border-bottom: 1px solid color-mix(in srgb, var(--line) 60%, transparent);
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}
	.detail-section:last-of-type { border-bottom: 0; }
	.detail-section h3 { font-size: 0.8rem; font-weight: 900; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin: 0; }

	.info-grid { display: flex; flex-direction: column; gap: 0.45rem; }
	.info-row { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; font-size: 0.84rem; }
	.info-row span:first-child { color: var(--muted); font-weight: 700; flex-shrink: 0; }
	.info-row strong { font-weight: 900; text-align: right; }
	.money { font-variant-numeric: tabular-nums; }
	.good { color: #16a34a; }
	.warn { color: #f59e0b; }

	.layout-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
	.layout-chip { padding: 0.25rem 0.6rem; background: var(--accent-soft); border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent); border-radius: 5px; font-size: 0.78rem; font-weight: 800; color: var(--accent); }

	.portal-link { display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.82rem; font-weight: 800; color: var(--accent); text-decoration: none; border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent); border-radius: 6px; padding: 0.4rem 0.75rem; background: var(--accent-soft); }
	.portal-link:hover { background: color-mix(in srgb, var(--accent) 20%, transparent); }

	.submissions-list { display: flex; flex-direction: column; gap: 0.6rem; }
	.submission-card { background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; padding: 0.65rem 0.85rem; display: flex; flex-direction: column; gap: 0.5rem; }
	.submission-meta { font-size: 0.74rem; color: var(--muted); font-weight: 800; }
	.submission-data { display: flex; flex-direction: column; gap: 0.3rem; }
	.submission-row { display: flex; justify-content: space-between; gap: 0.5rem; font-size: 0.82rem; }
	.submission-row span { color: var(--muted); font-weight: 700; }
	.submission-row strong { font-weight: 900; text-align: right; }

	.note-text { font-size: 0.84rem; color: var(--muted); line-height: 1.5; white-space: pre-wrap; }
	.empty-hint { color: var(--muted); font-size: 0.82rem; font-style: italic; margin: 0; }
	.loading-hint { color: var(--muted); font-size: 0.82rem; margin: 0; }

	.detail-footer { padding: 0.85rem 1.1rem; border-top: 1px solid var(--line); }
	.edit-btn { display: inline-flex; padding: 0.6rem 1rem; background: var(--accent); color: #fff; border-radius: 7px; text-decoration: none; font-weight: 900; font-size: 0.84rem; }

	@media (max-width: 1100px) {
		.main-layout.has-detail { grid-template-columns: 1fr; }
		.detail-panel { position: static; max-height: none; }
	}
</style>
