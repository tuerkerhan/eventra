<script lang="ts">
	import { page } from '$app/stores';

	const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
	const token = $derived($page.params.token);
	const layoutId = $derived($page.url.searchParams.get('layout'));

	interface VenueTable {
		id: string;
		table_no: number;
		shape: string;
		x: number;
		y: number;
		width: number;
		height: number;
		capacity: number;
		label: string;
	}

	interface VenueLayout {
		id: string;
		name: string;
		canvas_width: number;
		canvas_height: number;
		stage: { x: number; y: number; width: number; height: number };
		walls: { x1: number; y1: number; x2: number; y2: number }[];
		tables: VenueTable[];
	}

	interface Seating {
		table_id: string;
		seat_no: number;
		guest_name: string;
	}

	let layout = $state<VenueLayout | null>(null);
	let seatings = $state<Seating[]>([]);
	let loading = $state(true);
	let saving = $state(false);
	let saved = $state(false);
	let editingSeat = $state<{ tableId: string; seatNo: number } | null>(null);
	let guestInput = $state('');
	let guestInputEl: HTMLInputElement | undefined = $state();
	let printMode = $state(false);

	$effect(() => {
		if (editingSeat) {
			setTimeout(() => guestInputEl?.focus(), 0);
		}
	});

	const SEAT_GAP = 22;

	const loadData = async () => {
		if (!token) return;
		loading = true;
		try {
			if (layoutId) {
				// New per-layout endpoints
				const [layoutRes, seatingRes] = await Promise.all([
					fetch(`${API}/portal/${token}/layouts/${layoutId}`),
					fetch(`${API}/portal/${token}/layouts/${layoutId}/seatings`)
				]);
				if (layoutRes.ok) layout = await layoutRes.json();
				if (seatingRes.ok) seatings = await seatingRes.json();
			} else {
				// Legacy: single layout
				const [layoutRes, seatingRes] = await Promise.all([
					fetch(`${API}/portal/${token}/layout`),
					fetch(`${API}/portal/${token}/seatings`)
				]);
				if (layoutRes.ok) layout = await layoutRes.json();
				if (seatingRes.ok) seatings = await seatingRes.json();
			}
		} finally {
			loading = false;
		}
	};

	$effect(() => { if (token) loadData(); });

	const seatPositions = (t: VenueTable) => {
		const cx = t.x + t.width / 2;
		const cy = t.y + t.height / 2;
		const rx = t.width / 2 + SEAT_GAP;
		const ry = t.height / 2 + SEAT_GAP;
		return Array.from({ length: t.capacity }, (_, i) => {
			const angle = (i / t.capacity) * 2 * Math.PI - Math.PI / 2;
			return { x: cx + rx * Math.cos(angle), y: cy + ry * Math.sin(angle), seat: i + 1 };
		});
	};

	const getGuest = (tableId: string, seatNo: number) =>
		seatings.find((s) => s.table_id === tableId && s.seat_no === seatNo)?.guest_name ?? '';

	const openEdit = (tableId: string, seatNo: number) => {
		editingSeat = { tableId, seatNo };
		guestInput = getGuest(tableId, seatNo);
	};

	const saveGuest = () => {
		if (!editingSeat) return;
		const { tableId, seatNo } = editingSeat;
		const existing = seatings.findIndex((s) => s.table_id === tableId && s.seat_no === seatNo);
		if (existing >= 0) {
			if (guestInput.trim()) {
				seatings[existing].guest_name = guestInput.trim();
			} else {
				seatings = seatings.filter((_, i) => i !== existing);
			}
		} else if (guestInput.trim()) {
			seatings = [...seatings, { table_id: tableId, seat_no: seatNo, guest_name: guestInput.trim() }];
		}
		editingSeat = null;
		guestInput = '';
	};

	const saveToServer = async () => {
		saving = true;
		const url = layoutId
			? `${API}/portal/${token}/layouts/${layoutId}/seatings`
			: `${API}/portal/${token}/seatings`;
		const r = await fetch(url, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ seatings })
		});
		saving = false;
		if (r.ok) { saved = true; setTimeout(() => (saved = false), 2500); }
	};

	const printLayout = () => {
		printMode = true;
		setTimeout(() => window.print(), 300);
		setTimeout(() => (printMode = false), 1500);
	};

	// Group seatings by table for the print view
	const tableGroups = () => {
		if (!layout) return [];
		return layout.tables.map((t) => ({
			table: t,
			guests: seatings.filter((s) => s.table_id === t.id && s.guest_name).sort((a, b) => a.seat_no - b.seat_no)
		}));
	};
</script>

<svelte:head>
	<title>Oturma Düzeni</title>
</svelte:head>

<main class="seating-shell" class:print-mode={printMode}>
	<header class="seating-header no-print">
		<a class="back-link" href="/{token}">
			<img src="/ikon.png" alt="" class="back-logo" />
			← Portale Dön
		</a>
		<h1>🪑 Oturma Düzeni</h1>
		<div class="header-actions">
			<button type="button" onclick={saveToServer} disabled={saving} class="save-btn" class:saved>
				{saved ? '✓ Kaydedildi' : saving ? 'Kaydediliyor…' : 'Kaydet'}
			</button>
			<button type="button" onclick={printLayout} class="print-btn">🖨 Yazdır</button>
		</div>
	</header>

	{#if loading}
		<div class="loading">Yükleniyor…</div>
	{:else if !layout}
		<div class="error-box">
			<p>Bu etkinlik için oturma düzeni tanımlanmamış.</p>
			<a href="/{token}">Portale Dön</a>
		</div>
	{:else}
		<div class="canvas-help no-print">
			<span>Bir koltuğa tıklayarak misafir adı girin. Yeşil = atanmış, gri = boş.</span>
		</div>

		<div class="svg-wrap">
			<svg
				width={layout.canvas_width}
				height={layout.canvas_height}
				class="salon-svg"
				role="img"
				aria-label="Salon oturma düzeni"
			>
				<rect width={layout.canvas_width} height={layout.canvas_height} rx="8" fill="#1a2540" />
				{#each Array.from({ length: Math.floor(layout.canvas_width / 40) }, (_, i) => (i + 1) * 40) as gx}
					<line x1={gx} y1="0" x2={gx} y2={layout.canvas_height} stroke="rgba(255,255,255,0.04)" stroke-width="1" />
				{/each}
				{#each Array.from({ length: Math.floor(layout.canvas_height / 40) }, (_, i) => (i + 1) * 40) as gy}
					<line x1="0" y1={gy} x2={layout.canvas_width} y2={gy} stroke="rgba(255,255,255,0.04)" stroke-width="1" />
				{/each}

				{#each layout.walls as w}
					<line x1={w.x1} y1={w.y1} x2={w.x2} y2={w.y2} stroke="#6b7280" stroke-width="6" stroke-linecap="round" />
				{/each}

				<g>
					<rect x={layout.stage.x} y={layout.stage.y} width={layout.stage.width} height={layout.stage.height} rx="6" fill="#1e3a5f" stroke="#3b82f6" stroke-width="2" />
					<text x={layout.stage.x + layout.stage.width / 2} y={layout.stage.y + layout.stage.height / 2 + 5} text-anchor="middle" fill="#93c5fd" font-size="13" font-weight="900" letter-spacing="3">SAHNE</text>
				</g>

				{#each layout.tables as t}
					<rect x={t.x} y={t.y} width={t.width} height={t.height} rx="6" fill="#1e40af" stroke="rgba(59,130,246,0.4)" stroke-width="1.5" />
					<text x={t.x + t.width / 2} y={t.y + t.height / 2 - 7} text-anchor="middle" fill="#fff" font-size="10" font-weight="900">Masa {t.table_no}</text>
					<text x={t.x + t.width / 2} y={t.y + t.height / 2 + 8} text-anchor="middle" fill="rgba(255,255,255,0.45)" font-size="8">{t.capacity} kişi</text>

					{#each seatPositions(t) as sp}
						{@const guest = getGuest(t.id, sp.seat)}
						{@const isAssigned = Boolean(guest)}
						<g
							onclick={() => openEdit(t.id, sp.seat)}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									openEdit(t.id, sp.seat);
								}
							}}
							style="cursor: pointer"
							role="button"
							aria-label="Koltuk {sp.seat}: {guest || 'boş'}"
							tabindex="0"
						>
							<circle cx={sp.x} cy={sp.y} r="13" fill={isAssigned ? '#16a34a' : '#334155'} stroke={isAssigned ? '#4ade80' : '#475569'} stroke-width="1.5" />
							{#if isAssigned}
								<text x={sp.x} y={sp.y + 4} text-anchor="middle" fill="#fff" font-size="7" font-weight="900">{guest.split(' ')[0].slice(0,7)}</text>
							{:else}
								<text x={sp.x} y={sp.y + 4} text-anchor="middle" fill="#64748b" font-size="8">{sp.seat}</text>
							{/if}
						</g>
					{/each}
				{/each}
			</svg>
		</div>

		<!-- Seat edit modal -->
		{#if editingSeat}
			<div class="modal-backdrop" onclick={(e) => {
				if (e.target === e.currentTarget) editingSeat = null;
			}} onkeydown={(e) => {
				if (e.key === 'Escape') editingSeat = null;
			}} role="dialog" aria-modal="true" aria-label="Koltuk düzenle" tabindex="-1">
				<div class="modal" role="document">
					<h3>Koltuk {editingSeat.seatNo} – Misafir</h3>
					<input
						bind:this={guestInputEl}
						type="text"
						placeholder="Misafir adı soyadı"
						bind:value={guestInput}
						onkeydown={(e) => e.key === 'Enter' && saveGuest()}
					/>
					<div class="modal-actions">
						<button type="button" class="modal-save" onclick={saveGuest}>Kaydet</button>
						<button type="button" class="modal-cancel" onclick={() => (editingSeat = null)}>İptal</button>
					</div>
				</div>
			</div>
		{/if}

		<!-- Print view -->
		<section class="print-table-list print-only">
			<h2>Oturma Düzeni – Masa Listesi</h2>
			{#each tableGroups() as { table, guests }}
				{#if guests.length > 0}
					<div class="print-table">
						<h3>Masa {table.table_no} ({table.capacity} kişilik)</h3>
						<ol>
							{#each guests as s}
								<li>{s.seat_no}. {s.guest_name}</li>
							{/each}
						</ol>
					</div>
				{/if}
			{/each}
		</section>
	{/if}
</main>

<style>
	.seating-shell {
		max-width: 1100px; margin: 0 auto; padding: 1.5rem 1rem;
		display: flex; flex-direction: column; gap: 1rem;
		min-height: 100vh;
		background:
			radial-gradient(ellipse 80% 40% at 50% -5%, rgba(197,155,49,0.1) 0%, transparent 60%),
			linear-gradient(160deg, #080e1c 0%, #0d1526 100%);
	}

	.seating-header { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
	h1 { margin: 0; font-size: 1.4rem; flex: 1; }

	.back-link {
		display: flex; align-items: center; gap: 0.5rem;
		color: #c59b31; text-decoration: none; font-weight: 800; white-space: nowrap;
	}
	.back-logo { width: 26px; height: 26px; object-fit: contain; filter: drop-shadow(0 0 6px rgba(197,155,49,0.5)); }
	.header-actions { display: flex; gap: 0.65rem; }

	.save-btn {
		border: 0; border-radius: 8px; padding: 0.65rem 1.1rem;
		background: #c59b31; color: #fff; font-weight: 900; cursor: pointer;
	}
	.save-btn.saved { background: #16a34a; }
	.save-btn:disabled { opacity: 0.6; }

	.print-btn {
		border: 1px solid rgba(226,232,240,0.15); border-radius: 8px; padding: 0.65rem 1.1rem;
		background: rgba(226,232,240,0.08); color: #f8fafc; font-weight: 800; cursor: pointer;
	}

	.canvas-help { font-size: 0.82rem; color: #64748b; text-align: center; }

	.loading { text-align: center; padding: 4rem; color: #64748b; }
	.error-box { text-align: center; padding: 3rem; color: #94a3b8; }

	.svg-wrap { overflow-x: auto; border-radius: 8px; border: 1px solid rgba(226,232,240,0.1); }
	.salon-svg { display: block; max-width: 100%; }

	.modal-backdrop {
		position: fixed; inset: 0; background: rgba(0,0,0,0.65);
		display: flex; align-items: center; justify-content: center; z-index: 100;
	}
	.modal {
		background: #172033; border: 1px solid rgba(226,232,240,0.12); border-radius: 12px;
		padding: 1.75rem; width: min(380px, 92vw); display: flex; flex-direction: column; gap: 1rem;
	}
	.modal h3 { margin: 0; font-size: 1.1rem; }
	.modal input {
		width: 100%; min-height: 42px; border: 1px solid rgba(226,232,240,0.15); border-radius: 8px;
		padding: 0.6rem 0.75rem; background: #101827; color: #f8fafc; font: inherit;
	}
	.modal-actions { display: flex; gap: 0.65rem; }
	.modal-save { flex: 1; border: 0; border-radius: 8px; padding: 0.7rem; background: #c59b31; color: #fff; font-weight: 900; cursor: pointer; }
	.modal-cancel { border: 1px solid rgba(226,232,240,0.15); border-radius: 8px; padding: 0.7rem 1rem; background: transparent; color: #94a3b8; font-weight: 800; cursor: pointer; }

	/* Print styles */
	.print-only { display: none; }

	@media print {
		.no-print { display: none !important; }
		.print-only { display: block; }
		.svg-wrap { display: none; }
		.seating-shell { padding: 0; max-width: 100%; }
		.print-table-list h2 { font-size: 1.3rem; margin-bottom: 1rem; }
		.print-table { break-inside: avoid; margin-bottom: 1.2rem; }
		.print-table h3 { font-size: 1rem; margin: 0 0 0.3rem; }
		.print-table ol { margin: 0; padding-left: 1.2rem; }
		.print-table ol li { font-size: 0.9rem; margin-bottom: 0.15rem; }
	}
</style>
