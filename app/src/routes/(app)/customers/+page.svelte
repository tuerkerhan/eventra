<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type EventApi, type EventTypeApi } from '$lib/api';

	let searchQuery = $state('');
	let filterField = $state('all');
	let sortBy = $state<'date' | 'name' | 'type'>('date');
	let events = $state<EventApi[]>([]);
	let eventTypes = $state<EventTypeApi[]>([]);
	let loadError = $state('');

	onMount(async () => {
		try {
			const [evs, types] = await Promise.all([
				api.get<EventApi[]>('/events'),
				api.get<EventTypeApi[]>('/events/types')
			]);
			events = evs;
			eventTypes = types;
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'Yükleme hatası';
		}
	});

	const typeColor = (typeId: string | null) => eventTypes.find(t => t.id === typeId)?.color ?? '#64748b';
	const typeName = (typeId: string | null) => eventTypes.find(t => t.id === typeId)?.name ?? '—';

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
</script>

<section class="page-shell">
	<div class="page-heading">
		<div>
			<p class="eyebrow">Randevular</p>
			<h1>Davet Listesi</h1>
		</div>
		<a href="/calendar" class="new-btn">+ Yeni Davet</a>
	</div>

	{#if loadError}
		<div class="error-bar">{loadError}</div>
	{/if}

	<div class="toolbar">
		<input class="search" type="search" placeholder="Ara…" bind:value={searchQuery} />
		<select bind:value={filterField}>
			<option value="all">Tüm alanlar</option>
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
					<tr>
						<td>
							<a href="/calendar?event={ev.id}" class="date-link">
								<strong>{formatDate(ev.event_date)}</strong>
								<span>{ev.start_time} – {ev.end_time}</span>
							</a>
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
								{#if ev.bride_groom}<span>{ev.bride_groom}</span>{/if}
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
					<tr><td colspan="11" class="empty">Kayıt bulunamadı.</td></tr>
				{/if}
			</tbody>
		</table>
	</div>
</section>

<style>
	.page-shell { max-width: 1720px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }
	h1, p { margin: 0; }
	.eyebrow { margin-bottom: 0.25rem; color: var(--accent); font-size: 0.78rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; }
	.page-heading { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }
	.new-btn { padding: 0.75rem 1.25rem; background: var(--accent); color: #fff; border-radius: 8px; text-decoration: none; font-weight: 900; white-space: nowrap; }
	.error-bar { padding: 0.75rem 1rem; background: color-mix(in srgb, #ef4444 12%, transparent); border: 1px solid #ef4444; border-radius: 8px; color: #ef4444; font-weight: 800; font-size: 0.85rem; }
	.toolbar { display: flex; align-items: center; gap: 0.65rem; padding: 0.65rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; flex-wrap: wrap; }
	input, select { min-height: 36px; border: 1px solid var(--line); border-radius: 7px; padding: 0.4rem 0.65rem; background: var(--surface-strong); color: var(--text); font: inherit; }
	.search { flex: 1; min-width: 160px; }
	.count { margin-left: auto; font-size: 0.82rem; color: var(--muted); font-weight: 800; }
	.table-wrap { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; overflow-x: auto; }
	table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
	th { padding: 0.65rem 0.85rem; text-align: left; font-size: 0.72rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); border-bottom: 1px solid var(--line); white-space: nowrap; }
	td { padding: 0.75rem 0.85rem; border-bottom: 1px solid color-mix(in srgb, var(--line) 60%, transparent); vertical-align: middle; }
	tr:last-child td { border-bottom: 0; }
	tr:hover td { background: color-mix(in srgb, var(--accent) 4%, transparent); }
	.date-link { display: flex; flex-direction: column; gap: 0.15rem; color: var(--text); text-decoration: none; }
	.date-link strong { font-size: 0.88rem; }
	.date-link span { font-size: 0.75rem; color: var(--muted); }
	.type-pill { display: inline-flex; padding: 0.28rem 0.55rem; border-radius: 5px; font-size: 0.75rem; font-weight: 900; background: color-mix(in srgb, var(--c) 18%, transparent); color: var(--c); border: 1px solid color-mix(in srgb, var(--c) 30%, transparent); }
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
	.muted { color: var(--muted); font-size: 0.82rem; }
	.empty { text-align: center; color: var(--muted); padding: 2rem; font-style: italic; }
</style>
