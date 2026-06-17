<script lang="ts">
	import { onMount } from 'svelte';

	const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

	interface Ticket {
		id: string;
		title: string;
		urgency: string;
		description: string;
		status: string;
		created_at: string;
		salon_name?: string;
	}

	let tickets = $state<Ticket[]>([]);
	let loading = $state(true);
	let filterStatus = $state<'all' | 'open' | 'closed'>('open');

	const headers = () => ({
		'Content-Type': 'application/json',
		Authorization: `Bearer ${localStorage.getItem('admin_token')}`
	});

	const load = async () => {
		loading = true;
		const r = await fetch(`${API}/admin/tickets`, { headers: headers() });
		if (r.ok) tickets = await r.json();
		loading = false;
	};

	const updateStatus = async (id: string, status: string) => {
		const r = await fetch(`${API}/admin/tickets/${id}`, {
			method: 'PATCH', headers: headers(), body: JSON.stringify({ status })
		});
		if (r.ok) {
			const updated = await r.json();
			tickets = tickets.map(t => t.id === id ? updated : t);
		}
	};

	const filtered = $derived(
		filterStatus === 'all' ? tickets : tickets.filter(t => t.status === filterStatus)
	);

	const urgencyLabel = (u: string) => ({ low: 'Düşük', normal: 'Normal', high: 'Yüksek', critical: 'Kritik' }[u] ?? u);
	const formatDate = (d: string) => new Date(d).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

	onMount(load);
</script>

<div class="shell">
	<div class="page-head">
		<div><p class="eyebrow">Admin</p><h1>Destek Talepleri</h1></div>
		<div class="filter-row">
			{#each ['all', 'open', 'closed'] as s}
				<button class="filter-btn" class:active={filterStatus === s} type="button" onclick={() => (filterStatus = s as 'all' | 'open' | 'closed')}>
					{s === 'all' ? 'Tümü' : s === 'open' ? 'Açık' : 'Kapalı'}
				</button>
			{/each}
		</div>
	</div>

	{#if loading}
		<p class="muted">Yükleniyor…</p>
	{:else if filtered.length === 0}
		<p class="muted empty">Gösterilecek talep yok.</p>
	{:else}
		<div class="ticket-grid">
			{#each filtered as t (t.id)}
				<div class="ticket-card" data-status={t.status}>
					<div class="ticket-top">
						<div class="ticket-salon">{t.salon_name ?? ''}</div>
						<span class="urgency-badge" data-urgency={t.urgency}>{urgencyLabel(t.urgency)}</span>
						<span class="status-badge" data-status={t.status}>{t.status === 'open' ? 'Açık' : 'Kapalı'}</span>
					</div>
					<h3 class="ticket-title">{t.title}</h3>
					<p class="ticket-desc">{t.description}</p>
					<div class="ticket-footer">
						<span class="ticket-date">{formatDate(t.created_at)}</span>
						{#if t.status === 'open'}
							<button class="close-btn" type="button" onclick={() => updateStatus(t.id, 'closed')}>Kapat</button>
						{:else}
							<button class="reopen-btn" type="button" onclick={() => updateStatus(t.id, 'open')}>Yeniden Aç</button>
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
	h1, h2, h3, p { margin: 0; }
	h1 { font-size: clamp(1.6rem, 3vw, 2.4rem); font-weight: 900; }
	.eyebrow { margin-bottom: 0.25rem; color: #c59b31; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase; }
	.muted { color: #64748b; font-size: 0.88rem; }
	.empty { text-align: center; padding: 3rem; }

	.filter-row { display: flex; gap: 0.4rem; }
	.filter-btn { padding: 0.5rem 0.9rem; border: 1px solid rgba(226,232,240,0.15); border-radius: 7px; background: transparent; color: #64748b; font-weight: 800; font-size: 0.83rem; cursor: pointer; }
	.filter-btn.active { border-color: #c59b31; background: rgba(197,155,49,0.1); color: #c59b31; }

	.ticket-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1rem; }

	.ticket-card { background: #172033; border: 1px solid rgba(226,232,240,0.1); border-radius: 10px; padding: 1.25rem; display: flex; flex-direction: column; gap: 0.65rem; }
	.ticket-card[data-status="closed"] { opacity: 0.6; }

	.ticket-top { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
	.ticket-salon { flex: 1; font-size: 0.78rem; font-weight: 900; color: #c59b31; }
	.ticket-title { font-size: 0.95rem; font-weight: 900; }
	.ticket-desc { font-size: 0.83rem; color: #94a3b8; line-height: 1.5; }
	.ticket-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 0.25rem; }
	.ticket-date { font-size: 0.75rem; color: #475569; }

	.urgency-badge { font-size: 0.7rem; font-weight: 900; padding: 0.18rem 0.5rem; border-radius: 99px; border: 1px solid rgba(226,232,240,0.15); }
	.urgency-badge[data-urgency="low"] { color: #64748b; }
	.urgency-badge[data-urgency="normal"] { color: #2563eb; background: rgba(37,99,235,0.08); border-color: rgba(37,99,235,0.2); }
	.urgency-badge[data-urgency="high"] { color: #d97706; background: rgba(217,119,6,0.08); border-color: rgba(217,119,6,0.2); }
	.urgency-badge[data-urgency="critical"] { color: #dc2626; background: rgba(220,38,38,0.08); border-color: rgba(220,38,38,0.2); }

	.status-badge { font-size: 0.7rem; font-weight: 900; padding: 0.18rem 0.5rem; border-radius: 99px; }
	.status-badge[data-status="open"] { background: rgba(22,163,74,0.12); color: #16a34a; border: 1px solid rgba(22,163,74,0.25); }
	.status-badge[data-status="closed"] { background: rgba(226,232,240,0.08); color: #64748b; border: 1px solid rgba(226,232,240,0.12); }

	.close-btn { border: 1px solid rgba(239,68,68,0.25); border-radius: 7px; padding: 0.35rem 0.75rem; background: rgba(239,68,68,0.08); color: #fca5a5; font-weight: 900; font-size: 0.78rem; cursor: pointer; }
	.reopen-btn { border: 1px solid rgba(37,99,235,0.25); border-radius: 7px; padding: 0.35rem 0.75rem; background: rgba(37,99,235,0.08); color: #93c5fd; font-weight: 900; font-size: 0.78rem; cursor: pointer; }
</style>
