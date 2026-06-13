<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type EventApi, type EventTypeApi, type SalonApi } from '$lib/api';

	let events = $state<EventApi[]>([]);
	let eventTypes = $state<EventTypeApi[]>([]);
	let salon = $state<SalonApi | null>(null);

	const today = new Date();

	onMount(async () => {
		try {
			const [evs, types, s] = await Promise.all([
				api.get<EventApi[]>('/events'),
				api.get<EventTypeApi[]>('/events/types'),
				api.get<SalonApi>('/settings/salon')
			]);
			events = evs;
			eventTypes = types;
			salon = s;
		} catch {}
	});

	const typeName = (typeId: string | null) => eventTypes.find(t => t.id === typeId)?.name ?? '—';
	const formatMoney = (value: number) => `₺${value.toLocaleString('tr-TR')}`;

	const upcomingEvents = $derived(
		events
			.filter(e => new Date(e.event_date + 'T00:00:00') >= today)
			.sort((a, b) => a.event_date.localeCompare(b.event_date))
			.slice(0, 5)
	);

	const thisMonth = today.toISOString().slice(0, 7);
	const monthEvents = $derived(events.filter(e => e.event_date.startsWith(thisMonth)));
	const monthRevenue = $derived(monthEvents.reduce((s, e) => s + e.total_fee, 0));
	const monthPaid = $derived(monthEvents.reduce((s, e) => s + e.total_paid, 0));
	const remaining = $derived(monthRevenue - monthPaid);

	const paymentStatus = (ev: EventApi) => {
		if (ev.payment_complete) return { label: 'Tamamlandı', color: '#16a34a' };
		if (ev.total_paid > 0) return { label: 'Kısmi ödeme', color: '#2563eb' };
		if (ev.kapora_paid) return { label: 'Kapora alındı', color: '#f59e0b' };
		return { label: 'Bekliyor', color: '#dc2626' };
	};

	const getDaysLeft = (dateStr: string) => {
		const target = new Date(dateStr + 'T00:00:00');
		return Math.ceil((target.getTime() - today.getTime()) / 86400000);
	};

	const totalPaidAll = $derived(events.reduce((s, e) => s + (e.payment_complete ? e.total_fee : e.total_paid), 0));
	const totalPartial = $derived(events.reduce((s, e) => s + (!e.payment_complete && e.total_paid > 0 ? e.total_paid : 0), 0));
	const totalPending = $derived(events.reduce((s, e) => s + (e.total_fee - e.total_paid), 0));
</script>

<section class="home-shell">
	<div class="page-heading">
		<div>
			<p class="eyebrow">Ana Sayfa</p>
			<h1>{salon?.name ?? 'Eventra'}</h1>
			<p>Gelir, tahsilat ve yaklaşan davetleri tek ekranda gör.</p>
		</div>
		<a class="dashboard-link" href="/dashboard">Dashboard</a>
	</div>

	<div class="summary-grid">
		<div class="metric-card strong">
			<span>{today.toLocaleDateString('tr-TR', { month: 'long' })} ciro</span>
			<strong>{formatMoney(monthRevenue)}</strong>
			<small>{monthEvents.length} davet bu ay</small>
		</div>
		<div class="metric-card">
			<span>Tahsil edilen</span>
			<strong>{formatMoney(monthPaid)}</strong>
			<small>{formatMoney(remaining)} bekleyen ödeme</small>
		</div>
		<div class="metric-card">
			<span>Toplam davet</span>
			<strong>{events.length}</strong>
			<small>{events.filter(e => e.portal_enabled).length} aktif portal</small>
		</div>
		<div class="metric-card">
			<span>Yaklaşan davet</span>
			<strong>{upcomingEvents.length}</strong>
			<small>{upcomingEvents[0] ? `En yakın davete ${getDaysLeft(upcomingEvents[0].event_date)} gün kaldı` : 'Yaklaşan davet yok'}</small>
		</div>
	</div>

	<div class="content-grid">
		<section class="panel">
			<div class="panel-head">
				<div>
					<h2>Yaklaşan Davetler</h2>
					<p>Takvimden tam görünümü açabilirsin.</p>
				</div>
				<a href="/calendar">Takvim</a>
			</div>

			<div class="event-list">
				{#each upcomingEvents as event}
					{@const ps = paymentStatus(event)}
					<a class="event-row" href="/calendar">
						<div class="date-box">
							<strong>{new Date(event.event_date + 'T00:00:00').toLocaleDateString('tr-TR', { day: '2-digit' })}</strong>
							<span>{new Date(event.event_date + 'T00:00:00').toLocaleDateString('tr-TR', { month: 'short' })}</span>
						</div>
						<div class="event-main">
							<strong>{event.title}{event.bride_groom ? ` · ${event.bride_groom}` : ''}</strong>
							<span>{typeName(event.type_id)} · {event.start_time} · {event.guest_count} kişi</span>
						</div>
						<div class="payment-pill" style="--status:{ps.color}">
							{ps.label}
						</div>
					</a>
				{:else}
					<p class="empty">Henüz davet yok. <a href="/calendar">Takvimden davet ekle.</a></p>
				{/each}
			</div>
		</section>

		<section class="panel">
			<div class="panel-head">
				<div>
					<h2>Nakit Akışı</h2>
					<p>Tahsilat ve bekleyen ödemeler.</p>
				</div>
			</div>

			<div class="cash-bars">
				<div>
					<span>Tamamlanan ödemeler</span>
					<div class="bar"><i style="width: {monthRevenue > 0 ? Math.round(totalPaidAll / Math.max(monthRevenue + totalPending, 1) * 100) : 0}%"></i></div>
					<strong>{formatMoney(totalPaidAll)}</strong>
				</div>
				<div>
					<span>Kısmi ödemeler</span>
					<div class="bar blue"><i style="width: {monthRevenue > 0 ? Math.round(totalPartial / Math.max(monthRevenue + totalPending, 1) * 100) : 0}%"></i></div>
					<strong>{formatMoney(totalPartial)}</strong>
				</div>
				<div>
					<span>Bekleyen tahsilat</span>
					<div class="bar red"><i style="width: {monthRevenue > 0 ? Math.round(totalPending / Math.max(monthRevenue + totalPending, 1) * 100) : 0}%"></i></div>
					<strong>{formatMoney(totalPending)}</strong>
				</div>
			</div>
		</section>
	</div>
</section>

<style>
	.home-shell { max-width: 1480px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.25rem; }
	.page-heading { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }
	.eyebrow { margin: 0 0 0.25rem; color: var(--accent); font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; font-size: 0.78rem; }
	h1, h2, p { margin: 0; }
	h1 { font-size: clamp(1.8rem, 3.4vw, 3rem); }
	.page-heading p, .panel-head p, .metric-card small, .event-main span, .cash-bars span { color: var(--muted); }
	.dashboard-link, .panel-head a { color: #ffffff; background: var(--accent); border-radius: 8px; padding: 0.8rem 1rem; text-decoration: none; font-weight: 900; white-space: nowrap; }
	.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1rem; }
	.metric-card, .panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 18px 38px rgba(0, 0, 0, 0.12); }
	.metric-card { display: flex; flex-direction: column; gap: 0.45rem; padding: 1.1rem; }
	.metric-card span { color: var(--muted); font-weight: 800; font-size: 0.88rem; }
	.metric-card strong { font-size: clamp(1.45rem, 2.6vw, 2.15rem); }
	.metric-card.strong { background: linear-gradient(135deg, var(--accent-soft), var(--surface)); }
	.content-grid { display: grid; grid-template-columns: 1.35fr 0.8fr; gap: 1rem; }
	.panel { padding: 1rem; }
	.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
	.panel h2 { font-size: 1.15rem; margin-bottom: 0.2rem; }
	.event-list, .cash-bars { display: flex; flex-direction: column; gap: 0.75rem; }
	.event-row { display: grid; grid-template-columns: 62px 1fr auto; align-items: center; gap: 0.85rem; padding: 0.85rem; border: 1px solid var(--line); border-radius: 8px; color: var(--text); text-decoration: none; background: var(--surface-strong); }
	.date-box { display: grid; place-items: center; min-height: 58px; border-radius: 8px; background: var(--accent-soft); color: var(--accent); }
	.date-box strong { font-size: 1.25rem; line-height: 1; }
	.date-box span { font-size: 0.72rem; text-transform: uppercase; }
	.event-main { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
	.payment-pill { color: var(--status); background: color-mix(in srgb, var(--status) 12%, transparent); border: 1px solid color-mix(in srgb, var(--status) 30%, transparent); border-radius: 999px; padding: 0.45rem 0.65rem; font-weight: 900; font-size: 0.78rem; white-space: nowrap; }
	.cash-bars > div { display: grid; grid-template-columns: 1fr; gap: 0.45rem; padding: 0.85rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; }
	.cash-bars strong { font-size: 1.1rem; }
	.bar { height: 10px; border-radius: 999px; background: var(--muted-surface); overflow: hidden; }
	.bar i { display: block; height: 100%; background: #16a34a; border-radius: inherit; }
	.bar.blue i { background: #2563eb; }
	.bar.red i { background: #dc2626; }
	.empty { color: var(--muted); font-size: 0.88rem; font-style: italic; text-align: center; padding: 1rem; }
	.empty a { color: var(--accent); }
	@media (max-width: 1000px) { .summary-grid, .content-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
	@media (max-width: 700px) {
		.page-heading, .panel-head { flex-direction: column; align-items: stretch; }
		.summary-grid, .content-grid { grid-template-columns: 1fr; }
		.event-row { grid-template-columns: 56px 1fr; }
		.payment-pill { grid-column: 2; width: fit-content; }
	}
</style>
