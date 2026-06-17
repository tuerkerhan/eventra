<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type EventApi, type EventTypeApi, type SalonApi, type NotificationApi } from '$lib/api';

	let events = $state<EventApi[]>([]);
	let eventTypes = $state<EventTypeApi[]>([]);
	let salon = $state<SalonApi | null>(null);
	let notifications = $state<NotificationApi[]>([]);

	let homeTab = $state<'genel' | 'mail'>('genel');

	const today = new Date();

	onMount(async () => {
		try {
			const [evs, types, s, notifs] = await Promise.all([
				api.get<EventApi[]>('/events'),
				api.get<EventTypeApi[]>('/events/types'),
				api.get<SalonApi>('/settings/salon'),
				api.get<NotificationApi[]>('/notifications?limit=20')
			]);
			events = evs;
			eventTypes = types;
			salon = s;
			notifications = notifs;
		} catch {}
	});

	const NOTIF_LABELS: Record<string, { icon: string; color: string }> = {
		payment_claimed: { icon: '💸', color: '#f59e0b' },
		payment_confirmed: { icon: '✓', color: '#16a34a' },
		email_sent: { icon: '✉️', color: '#2563eb' },
		email_failed: { icon: '⚠', color: '#dc2626' }
	};

	function formatRelative(dateStr: string) {
		const d = new Date(dateStr);
		const diffMin = Math.round((Date.now() - d.getTime()) / 60000);
		if (diffMin < 1) return 'şimdi';
		if (diffMin < 60) return `${diffMin} dk önce`;
		const diffH = Math.round(diffMin / 60);
		if (diffH < 24) return `${diffH} saat önce`;
		return d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
	}

	async function markNotificationRead(id: string) {
		notifications = notifications.map(n => n.id === id ? { ...n, is_read: true } : n);
		try { await api.post(`/notifications/${id}/read`, {}); } catch {}
	}

	async function deleteNotification(id: string) {
		const previous = notifications;
		notifications = notifications.filter(n => n.id !== id);
		try {
			await api.del(`/notifications/${id}`);
		} catch {
			notifications = previous;
		}
	}

	// Müşteriye mail gönder
	let mailAppointmentNo = $state('');
	let mailSubject = $state('');
	let mailBody = $state('');
	let mailSending = $state(false);
	let mailResult = $state<{ ok: boolean; detail: string } | null>(null);

	async function sendCustomerMail() {
		if (!mailAppointmentNo || !mailSubject || !mailBody) return;
		mailSending = true;
		mailResult = null;
		try {
			const res = await api.post<{ ok: boolean; detail: string }>('/events/send-mail', {
				appointment_no: Number(mailAppointmentNo),
				subject: mailSubject,
				body: mailBody
			});
			mailResult = res;
			if (res.ok) {
				mailAppointmentNo = ''; mailSubject = ''; mailBody = '';
			}
		} catch (e) {
			mailResult = { ok: false, detail: e instanceof Error ? e.message : 'Gönderilemedi' };
		} finally {
			mailSending = false;
		}
	}

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
			<h1>{salon?.name ?? 'Eventra'}</h1>
			<p>Gelir, tahsilat ve yaklaşan davetleri tek ekranda gör.</p>
		</div>
		<a class="dashboard-link" href="/dashboard">Dashboard</a>
	</div>

	<div class="home-tab-bar">
		<button class="home-tab-btn" class:active={homeTab === 'genel'} type="button" onclick={() => (homeTab = 'genel')}>Genel</button>
		<button class="home-tab-btn" class:active={homeTab === 'mail'} type="button" onclick={() => (homeTab = 'mail')}>Mail Gönder</button>
	</div>

	{#if homeTab === 'genel'}
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

	<div class="content-grid three">
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

		<section class="panel">
			<div class="panel-head">
				<div>
					<h2>Bildirimler</h2>
					<p>Ödeme ve mail bildirimleri.</p>
				</div>
			</div>

			<div class="notif-list">
				{#each notifications as n}
					{@const meta = NOTIF_LABELS[n.type] ?? { icon: '🔔', color: '#64748b' }}
					<div
						class="notif-row"
						class:unread={!n.is_read}
						style="--ncolor:{meta.color}"
						role="button"
						tabindex="0"
						onclick={() => markNotificationRead(n.id)}
						onkeydown={(e) => {
							if (e.key === 'Enter' || e.key === ' ') {
								e.preventDefault();
								markNotificationRead(n.id);
							}
						}}
					>
						<span class="notif-icon">{meta.icon}</span>
						<div class="notif-main">
							<strong>{n.title}</strong>
							<span>{n.message}</span>
						</div>
						<div class="notif-actions">
							<small>{formatRelative(n.created_at)}</small>
							<button
								class="notif-delete"
								type="button"
								title="Bildirimi sil"
								aria-label="Bildirimi sil"
								onclick={(e) => {
									e.stopPropagation();
									deleteNotification(n.id);
								}}
							>
								Sil
							</button>
						</div>
					</div>
				{:else}
					<p class="empty">Henüz bildirim yok.</p>
				{/each}
			</div>
		</section>
	</div>
	{:else}
	<div class="content-grid single">
		<section class="panel">
			<div class="panel-head">
				<div>
					<h2>Müşteriye Mail Gönder</h2>
					<p>Randevu numarasıyla müşteriye mail at, kayıt mailini sen de al.</p>
				</div>
			</div>

			<form class="mail-form" onsubmit={(e) => { e.preventDefault(); sendCustomerMail(); }}>
				<label><span>Randevu No</span><input type="number" placeholder="#12" bind:value={mailAppointmentNo} required /></label>
				<label><span>Konu</span><input placeholder="Davetinizle ilgili bilgi" bind:value={mailSubject} required /></label>
				<label class="full"><span>Mesaj</span><textarea rows="5" placeholder="Mesajınızı yazın…" bind:value={mailBody} required></textarea></label>
				<div class="form-actions">
					<button class="save-btn" type="submit" disabled={mailSending}>
						{mailSending ? 'Gönderiliyor…' : 'Mail Gönder'}
					</button>
					{#if mailResult}
						<span class="mail-result" class:ok={mailResult.ok} class:fail={!mailResult.ok}>
							{mailResult.ok ? '✓ Mail gönderildi' : `✗ Hata: ${mailResult.detail}`}
						</span>
					{/if}
				</div>
			</form>
		</section>
	</div>
	{/if}
</section>

<style>
	.home-shell { max-width: 1480px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.25rem; }
	.page-heading { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }
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
	.content-grid.three { grid-template-columns: 1.1fr 0.7fr 0.9fr; }
	.content-grid.single { grid-template-columns: 1fr; }
	.home-tab-bar { display: flex; gap: 0.5rem; }
	.home-tab-btn { padding: 0.6rem 1.1rem; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); color: var(--text); font-weight: 800; font-size: 0.86rem; cursor: pointer; }
	.home-tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
	.notif-list { display: flex; flex-direction: column; gap: 0.6rem; max-height: 420px; overflow-y: auto; }
	.notif-row { display: grid; grid-template-columns: auto 1fr auto; align-items: start; gap: 0.6rem; padding: 0.7rem; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-strong); cursor: pointer; }
	.notif-row.unread { border-color: color-mix(in srgb, var(--ncolor) 50%, var(--line)); background: color-mix(in srgb, var(--ncolor) 6%, var(--surface-strong)); }
	.notif-icon { font-size: 1.1rem; }
	.notif-main { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
	.notif-main strong { font-size: 0.84rem; }
	.notif-main span { color: var(--muted); font-size: 0.78rem; }
	.notif-actions { display: flex; flex-direction: column; align-items: flex-end; gap: 0.35rem; }
	.notif-row small { color: var(--muted); white-space: nowrap; font-size: 0.72rem; }
	.notif-delete { border: 1px solid color-mix(in srgb, #dc2626 35%, var(--line)); border-radius: 8px; background: color-mix(in srgb, #dc2626 7%, var(--surface)); color: #dc2626; font-size: 0.72rem; font-weight: 900; line-height: 1; padding: 0.4rem 0.5rem; cursor: pointer; }
	.notif-delete:hover { background: color-mix(in srgb, #dc2626 14%, var(--surface)); }
	.mail-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.85rem; }
	.mail-form label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; font-size: 0.82rem; }
	.mail-form label.full { grid-column: 1 / -1; }
	.mail-form input, .mail-form textarea { padding: 0.65rem 0.75rem; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); color: var(--text); font: inherit; }
	.mail-form .form-actions { grid-column: 1 / -1; display: flex; align-items: center; gap: 0.85rem; }
	.save-btn { padding: 0.7rem 1.2rem; border: 0; border-radius: 8px; background: var(--accent); color: #fff; font-weight: 900; cursor: pointer; }
	.save-btn:disabled { opacity: 0.6; cursor: not-allowed; }
	.mail-result { font-weight: 800; font-size: 0.85rem; }
	.mail-result.ok { color: #16a34a; }
	.mail-result.fail { color: #dc2626; }
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
	@media (max-width: 1000px) { .summary-grid, .content-grid, .content-grid.three { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
	@media (max-width: 700px) {
		.page-heading, .panel-head { flex-direction: column; align-items: stretch; }
		.summary-grid, .content-grid, .content-grid.three { grid-template-columns: 1fr; }
		.event-row { grid-template-columns: 56px 1fr; }
		.payment-pill { grid-column: 2; width: fit-content; }
		.mail-form { grid-template-columns: 1fr; }
	}
</style>
