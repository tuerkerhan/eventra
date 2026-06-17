<script lang="ts">
	import { onMount } from 'svelte';

	const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

	interface AdminNotif {
		id: string;
		type: string;
		title: string;
		message: string;
		is_read: boolean;
		salon_id: string | null;
		ref_id: string | null;
		created_at: string;
	}

	let notifs = $state<AdminNotif[]>([]);
	let loading = $state(true);
	let filterUnread = $state(false);

	const headers = () => ({
		'Content-Type': 'application/json',
		Authorization: `Bearer ${localStorage.getItem('admin_token')}`
	});

	const load = async () => {
		loading = true;
		const r = await fetch(`${API}/admin/notifications`, { headers: headers() });
		if (r.ok) notifs = await r.json();
		loading = false;
	};

	const markRead = async (id: string) => {
		const r = await fetch(`${API}/admin/notifications/${id}/read`, { method: 'POST', headers: headers() });
		if (r.ok) notifs = notifs.map(n => n.id === id ? { ...n, is_read: true } : n);
	};

	const markAllRead = async () => {
		const r = await fetch(`${API}/admin/notifications/read-all`, { method: 'POST', headers: headers() });
		if (r.ok) notifs = notifs.map(n => ({ ...n, is_read: true }));
	};

	const filtered = $derived(filterUnread ? notifs.filter(n => !n.is_read) : notifs);
	const unreadCount = $derived(notifs.filter(n => !n.is_read).length);

	const typeLabel = (t: string) => ({ ticket_new: 'Yeni Talep', admin_broadcast: 'Yayın' }[t] ?? t);
	const formatDate = (d: string) => new Date(d).toLocaleString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });

	onMount(load);
</script>

<div class="shell">
	<div class="page-head">
		<div>
			<p class="eyebrow">Admin</p>
			<h1>Bildirimler {#if unreadCount > 0}<span class="unread-chip">{unreadCount} okunmamış</span>{/if}</h1>
		</div>
		<div class="head-actions">
			<label class="check-label">
				<input type="checkbox" bind:checked={filterUnread} />
				Sadece okunmamışlar
			</label>
			{#if unreadCount > 0}
				<button class="read-all-btn" type="button" onclick={markAllRead}>Tümünü Okundu İşaretle</button>
			{/if}
		</div>
	</div>

	{#if loading}
		<p class="muted">Yükleniyor…</p>
	{:else if filtered.length === 0}
		<p class="muted empty">Bildirim yok.</p>
	{:else}
		<div class="notif-list">
			{#each filtered as n (n.id)}
				<div class="notif-card" class:unread={!n.is_read}>
					<div class="notif-left">
						<span class="type-chip">{typeLabel(n.type)}</span>
						<div class="notif-body">
							<strong>{n.title}</strong>
							<p>{n.message}</p>
						</div>
					</div>
					<div class="notif-right">
						<span class="notif-date">{formatDate(n.created_at)}</span>
						{#if !n.is_read}
							<button class="read-btn" type="button" onclick={() => markRead(n.id)}>Okundu</button>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.shell { display: flex; flex-direction: column; gap: 1.5rem; }
	.page-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
	h1, p { margin: 0; }
	h1 { font-size: clamp(1.6rem, 3vw, 2.4rem); font-weight: 900; display: flex; align-items: center; gap: 0.65rem; flex-wrap: wrap; }
	.eyebrow { margin-bottom: 0.25rem; color: #c59b31; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase; }
	.muted { color: #64748b; font-size: 0.88rem; }
	.empty { padding: 3rem; text-align: center; }

	.unread-chip { font-size: 0.78rem; font-weight: 900; padding: 0.25rem 0.65rem; border-radius: 99px; background: rgba(239,68,68,0.12); color: #fca5a5; border: 1px solid rgba(239,68,68,0.25); }

	.head-actions { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
	.check-label { display: flex; align-items: center; gap: 0.4rem; color: #64748b; font-size: 0.85rem; font-weight: 800; cursor: pointer; }
	.check-label input { accent-color: #c59b31; }
	.read-all-btn { border: 1px solid rgba(197,155,49,0.3); border-radius: 7px; padding: 0.5rem 0.85rem; background: rgba(197,155,49,0.08); color: #c59b31; font-weight: 900; font-size: 0.82rem; cursor: pointer; }

	.notif-list { display: flex; flex-direction: column; gap: 0.5rem; }
	.notif-card { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; padding: 1rem 1.25rem; background: #172033; border: 1px solid rgba(226,232,240,0.08); border-radius: 10px; transition: border-color 0.15s; }
	.notif-card.unread { border-color: rgba(197,155,49,0.2); background: rgba(197,155,49,0.04); }

	.notif-left { display: flex; align-items: flex-start; gap: 0.85rem; flex: 1; }
	.notif-right { display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem; flex-shrink: 0; }

	.type-chip { font-size: 0.68rem; font-weight: 900; padding: 0.2rem 0.5rem; border-radius: 99px; background: rgba(197,155,49,0.12); color: #c59b31; border: 1px solid rgba(197,155,49,0.25); white-space: nowrap; }

	.notif-body { display: flex; flex-direction: column; gap: 0.2rem; }
	.notif-body strong { font-size: 0.9rem; }
	.notif-body p { font-size: 0.82rem; color: #94a3b8; line-height: 1.5; }

	.notif-date { font-size: 0.75rem; color: #475569; white-space: nowrap; }
	.read-btn { border: 1px solid rgba(226,232,240,0.15); border-radius: 6px; padding: 0.3rem 0.65rem; background: transparent; color: #94a3b8; font-weight: 900; font-size: 0.75rem; cursor: pointer; white-space: nowrap; }
</style>
