<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type VenueLayoutApi } from '$lib/api';

	type Shape = 'round' | 'rectangle';
	type Tool = 'select' | 'wall';
	type ResizeEdge = 'right' | 'bottom' | 'br' | 'radius' | null;
	type DragTarget = 'table' | 'stage' | 'resize-table' | 'resize-stage' | null;

	interface Table {
		id: string;
		no: number;
		shape: Shape;
		x: number;
		y: number;
		width: number;
		height: number;
		capacity: number;
	}

	interface Wall { id: string; x1: number; y1: number; x2: number; y2: number; }
	interface Stage { x: number; y: number; width: number; height: number; }

	const CW = 900;
	const CH = 600;
	const SEAT_GAP = 22;

	// API state
	let allLayouts = $state<VenueLayoutApi[]>([]);
	let currentLayoutId = $state<string | null>(null);
	let loadError = $state('');
	let saving = $state(false);
	let newLayoutName = $state('');

	// Reactive state
	let tables = $state<Table[]>([]);
	let walls = $state<Wall[]>([]);
	let stage = $state<Stage>({ x: 270, y: 20, width: 360, height: 90 });
	let selectedId = $state<string | null>(null);
	let showSeatsFor = $state<string | null>(null);
	let activeTool = $state<Tool>('select');
	let layoutName = $state('Ana Salon');
	let saved = $state(false);
	let drawingWall = $state<{ x1: number; y1: number } | null>(null);
	let mouseX = $state(0);
	let mouseY = $state(0);
	let stageSelected = $state(false);

	// Non-reactive drag/resize internals
	let svgEl: SVGSVGElement;
	let dragTarget: DragTarget = null;
	let dragId: string | null = null;
	let dragStartX = 0;
	let dragStartY = 0;
	let dragOrigX = 0;
	let dragOrigY = 0;
	let resizeEdge: ResizeEdge = null;
	let resizeOrigW = 0;
	let resizeOrigH = 0;

	const getSVGPoint = (e: PointerEvent) => {
		const rect = svgEl.getBoundingClientRect();
		const scaleX = CW / rect.width;
		const scaleY = CH / rect.height;
		return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY };
	};

	const addTable = (shape: Shape) => {
		const no = tables.length + 1;
		const w = shape === 'round' ? 90 : 140;
		const h = shape === 'round' ? 90 : 80;
		const cap = shape === 'round' ? 8 : 10;
		tables = [...tables, {
			id: String(Math.random()).slice(2),
			no, shape,
			x: 60 + ((no - 1) % 4) * 175,
			y: 160 + Math.floor((no - 1) / 4) * 145,
			width: w, height: h, capacity: cap
		}];
		selectedId = tables[tables.length - 1].id;
		showSeatsFor = null;
	};

	const removeSelected = () => {
		if (!selectedId) return;
		tables = tables.filter((t) => t.id !== selectedId).map((t, i) => ({ ...t, no: i + 1 }));
		selectedId = null;
		showSeatsFor = null;
	};

	const selectedTable = () => tables.find((t) => t.id === selectedId) ?? null;

	const seatPositions = (t: Table) => {
		const cx = t.x + t.width / 2;
		const cy = t.y + t.height / 2;
		const rx = t.width / 2 + SEAT_GAP;
		const ry = t.height / 2 + SEAT_GAP;
		return Array.from({ length: t.capacity }, (_, i) => {
			const angle = (i / t.capacity) * 2 * Math.PI - Math.PI / 2;
			return { x: cx + rx * Math.cos(angle), y: cy + ry * Math.sin(angle), seat: i + 1 };
		});
	};

	const onSvgPointerDown = (e: PointerEvent) => {
		const pt = getSVGPoint(e);
		mouseX = pt.x; mouseY = pt.y;
		if (activeTool === 'wall') drawingWall = { x1: pt.x, y1: pt.y };
	};

	const onSvgPointerMove = (e: PointerEvent) => {
		const pt = getSVGPoint(e);
		mouseX = pt.x; mouseY = pt.y;

		if (dragTarget === 'table' && dragId) {
			const dx = pt.x - dragStartX; const dy = pt.y - dragStartY;
			tables = tables.map((t) => t.id !== dragId ? t : {
				...t,
				x: Math.max(0, Math.min(CW - t.width, dragOrigX + dx)),
				y: Math.max(0, Math.min(CH - t.height, dragOrigY + dy))
			});
		} else if (dragTarget === 'stage') {
			const dx = pt.x - dragStartX; const dy = pt.y - dragStartY;
			stage = { ...stage, x: Math.max(0, Math.min(CW - stage.width, dragOrigX + dx)), y: Math.max(0, Math.min(CH - stage.height, dragOrigY + dy)) };
		} else if (dragTarget === 'resize-table' && dragId && resizeEdge) {
			const dx = pt.x - dragStartX; const dy = pt.y - dragStartY;
			tables = tables.map((t) => {
				if (t.id !== dragId) return t;
				if (resizeEdge === 'right') return { ...t, width: Math.max(60, resizeOrigW + dx) };
				if (resizeEdge === 'bottom') return { ...t, height: Math.max(40, resizeOrigH + dy) };
				if (resizeEdge === 'br') return { ...t, width: Math.max(60, resizeOrigW + dx), height: Math.max(40, resizeOrigH + dy) };
				if (resizeEdge === 'radius') { const d = Math.max(60, resizeOrigW + dx * 2); return { ...t, width: d, height: d }; }
				return t;
			});
		} else if (dragTarget === 'resize-stage' && resizeEdge) {
			const dx = pt.x - dragStartX; const dy = pt.y - dragStartY;
			if (resizeEdge === 'right') stage = { ...stage, width: Math.max(80, resizeOrigW + dx) };
			else if (resizeEdge === 'bottom') stage = { ...stage, height: Math.max(40, resizeOrigH + dy) };
			else if (resizeEdge === 'br') stage = { ...stage, width: Math.max(80, resizeOrigW + dx), height: Math.max(40, resizeOrigH + dy) };
		}
	};

	const onSvgPointerUp = (e: PointerEvent) => {
		if (drawingWall && activeTool === 'wall') {
			const pt = getSVGPoint(e);
			const dx = pt.x - drawingWall.x1; const dy = pt.y - drawingWall.y1;
			if (Math.sqrt(dx * dx + dy * dy) > 10) {
				walls = [...walls, { id: String(Math.random()).slice(2), x1: drawingWall.x1, y1: drawingWall.y1, x2: pt.x, y2: pt.y }];
			}
			drawingWall = null;
		}
		dragTarget = null; dragId = null; resizeEdge = null;
	};

	const onSvgClick = (e: MouseEvent) => {
		const tag = (e.target as SVGElement).tagName;
		if (activeTool === 'select' && (tag === 'svg' || tag === 'rect')) {
			selectedId = null; showSeatsFor = null; stageSelected = false;
		}
	};

	const startTableDrag = (e: PointerEvent, id: string) => {
		if (activeTool !== 'select') return;
		e.stopPropagation();
		const t = tables.find((t) => t.id === id);
		if (!t) return;
		const pt = getSVGPoint(e);
		dragTarget = 'table'; dragId = id;
		dragStartX = pt.x; dragStartY = pt.y;
		dragOrigX = t.x; dragOrigY = t.y;
		selectedId = id;
		(e.currentTarget as SVGElement).setPointerCapture(e.pointerId);
	};

	const clickTable = (e: Event, id: string) => {
		if (activeTool !== 'select') return;
		e.stopPropagation();
		selectedId = id;
		showSeatsFor = showSeatsFor === id ? null : id;
		stageSelected = false;
	};

	const startResize = (e: PointerEvent, id: string, edge: ResizeEdge) => {
		if (activeTool !== 'select') return;
		e.stopPropagation();
		const t = tables.find((t) => t.id === id);
		if (!t) return;
		const pt = getSVGPoint(e);
		dragTarget = 'resize-table'; dragId = id; resizeEdge = edge;
		dragStartX = pt.x; dragStartY = pt.y;
		resizeOrigW = t.width; resizeOrigH = t.height;
		(e.currentTarget as SVGElement).setPointerCapture(e.pointerId);
	};

	const startStageDrag = (e: PointerEvent) => {
		if (activeTool !== 'select') return;
		e.stopPropagation();
		const pt = getSVGPoint(e);
		dragTarget = 'stage';
		dragStartX = pt.x; dragStartY = pt.y;
		dragOrigX = stage.x; dragOrigY = stage.y;
		stageSelected = true; selectedId = null;
		(e.currentTarget as SVGElement).setPointerCapture(e.pointerId);
	};

	const startStageResize = (e: PointerEvent, edge: ResizeEdge) => {
		if (activeTool !== 'select') return;
		e.stopPropagation();
		const pt = getSVGPoint(e);
		dragTarget = 'resize-stage'; resizeEdge = edge;
		dragStartX = pt.x; dragStartY = pt.y;
		resizeOrigW = stage.width; resizeOrigH = stage.height;
		(e.currentTarget as SVGElement).setPointerCapture(e.pointerId);
	};

	onMount(async () => {
		try {
			const lyts = await api.get<VenueLayoutApi[]>('/venue/layouts');
			allLayouts = lyts;
			if (lyts.length > 0) loadLayout(lyts[0]);
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'Yükleme hatası';
		}
	});

	function loadLayout(layout: VenueLayoutApi) {
		currentLayoutId = layout.id;
		layoutName = layout.name;
		stage = { x: layout.stage.x, y: layout.stage.y, width: layout.stage.width, height: layout.stage.height };
		walls = (layout.walls as unknown as Wall[]) ?? [];
		tables = layout.tables.map((t, i) => ({
			id: t.id,
			no: t.table_no,
			shape: (t.shape === 'rectangle' || t.shape === 'long' ? 'rectangle' : 'round') as Shape,
			x: t.x, y: t.y, width: t.width, height: t.height, capacity: t.capacity
		}));
		selectedId = null; showSeatsFor = null; stageSelected = false;
	}

	async function createLayout() {
		const name = newLayoutName.trim() || 'Yeni Salon';
		const layout = await api.post<VenueLayoutApi>('/venue/layouts', {
			name, canvas_width: CW, canvas_height: CH,
			stage: { x: 270, y: 20, width: 360, height: 90 },
			walls: [], tables: []
		});
		allLayouts = [...allLayouts, layout];
		loadLayout(layout);
		newLayoutName = '';
	}

	async function deleteCurrentLayout() {
		if (!currentLayoutId || !confirm('Bu salon düzenini sil?')) return;
		await api.del(`/venue/layouts/${currentLayoutId}`);
		allLayouts = allLayouts.filter(l => l.id !== currentLayoutId);
		if (allLayouts.length > 0) loadLayout(allLayouts[0]);
		else { currentLayoutId = null; tables = []; walls = []; layoutName = 'Ana Salon'; }
	}

	const saveLayout = async () => {
		saving = true;
		try {
			const tableData = tables.map(t => ({
				table_no: t.no,
				shape: t.shape === 'round' ? 'square' : 'rectangle',
				x: t.x, y: t.y, width: t.width, height: t.height,
				capacity: t.capacity, label: ''
			}));
			if (currentLayoutId) {
				const updated = await api.put<VenueLayoutApi>(`/venue/layouts/${currentLayoutId}`, {
					name: layoutName, canvas_width: CW, canvas_height: CH,
					stage: { x: stage.x, y: stage.y, width: stage.width, height: stage.height },
					walls, tables: tableData
				});
				allLayouts = allLayouts.map(l => l.id === updated.id ? updated : l);
			} else {
				const layout = await api.post<VenueLayoutApi>('/venue/layouts', {
					name: layoutName, canvas_width: CW, canvas_height: CH,
					stage: { x: stage.x, y: stage.y, width: stage.width, height: stage.height },
					walls, tables: tableData
				});
				allLayouts = [...allLayouts, layout];
				currentLayoutId = layout.id;
			}
			saved = true; setTimeout(() => (saved = false), 2000);
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Kaydetme hatası');
		} finally {
			saving = false;
		}
	};

	const shapeNames: Record<Shape, string> = { round: 'Yuvarlak Masa', rectangle: 'Dikdörtgen Masa' };

	const gridLines = {
		x: Array.from({ length: Math.floor(CW / 40) }, (_, i) => (i + 1) * 40),
		y: Array.from({ length: Math.floor(CH / 40) }, (_, i) => (i + 1) * 40)
	};

	// Resize handle size
	const RH = 10;
</script>

<section class="page-shell">
	{#if loadError}
		<div class="error-bar">{loadError}</div>
	{/if}

	<div class="page-heading">
		<div class="head-actions">
			<input class="layout-name" bind:value={layoutName} placeholder="Salon adı" />
			<button class="save-btn" class:saved={saved} disabled={saving} type="button" onclick={saveLayout}>
				{saving ? 'Kaydediliyor…' : saved ? '✓ Kaydedildi' : 'Kaydet'}
			</button>
		</div>
	</div>

	<div class="layout-bar">
		{#each allLayouts as layout}
			<button
				class="layout-tab"
				class:active={currentLayoutId === layout.id}
				onclick={() => loadLayout(layout)}
			>{layout.name}</button>
		{/each}
		<div class="new-layout-row">
			<input placeholder="Yeni salon adı" bind:value={newLayoutName} onkeydown={(e) => e.key === 'Enter' && createLayout()} />
			<button onclick={createLayout}>+ Salon Ekle</button>
		</div>
		{#if currentLayoutId}
			<button class="del-layout" onclick={deleteCurrentLayout}>Sil</button>
		{/if}
	</div>

	<div class="designer-wrap">
		<aside class="toolbar">
			<div class="tool-section">
				<p class="tool-label">Araç</p>
				<button class="tool-btn" class:active={activeTool === 'select'} type="button" onclick={() => (activeTool = 'select')}>↖ Seç / Taşı</button>
				<button class="tool-btn" class:active={activeTool === 'wall'} type="button" onclick={() => (activeTool = 'wall')}>━ Duvar Çiz</button>
			</div>

			<div class="tool-section">
				<p class="tool-label">Masa Ekle</p>
				{#each (['round', 'rectangle'] as Shape[]) as shape}
					<button class="add-btn" type="button" onclick={() => addTable(shape)}>
						<span class="shape-prev {shape}"></span>
						{shapeNames[shape]}
					</button>
				{/each}
			</div>

			{#if selectedTable()}
				{@const st = selectedTable()!}
				<div class="tool-section props-panel">
					<p class="tool-label">Masa {st.no} – {shapeNames[st.shape]}</p>
					<label>
						<span>Kişi sayısı</span>
						<input type="number" min="1" max="40" value={st.capacity}
							oninput={(e) => { const t = tables.find(t => t.id === st.id); if (t) t.capacity = Number(e.currentTarget.value); }} />
					</label>
					{#if st.shape === 'round'}
						<label>
							<span>Çap</span>
							<input type="number" min="60" max="300" value={st.width}
								oninput={(e) => { const t = tables.find(t => t.id === st.id); if (t) { const v = Number(e.currentTarget.value); t.width = v; t.height = v; } }} />
						</label>
					{:else}
						<label>
							<span>Genişlik</span>
							<input type="number" min="60" max="400" value={st.width}
								oninput={(e) => { const t = tables.find(t => t.id === st.id); if (t) t.width = Number(e.currentTarget.value); }} />
						</label>
						<label>
							<span>Yükseklik</span>
							<input type="number" min="40" max="300" value={st.height}
								oninput={(e) => { const t = tables.find(t => t.id === st.id); if (t) t.height = Number(e.currentTarget.value); }} />
						</label>
					{/if}
					<p class="props-hint">Tutamaç sürükleyerek de boyutlandırabilirsin</p>
					<button class="remove-btn" type="button" onclick={removeSelected}>Masayı Kaldır</button>
					<button class="seat-btn" type="button" onclick={() => (showSeatsFor = showSeatsFor === selectedId ? null : selectedId)}>
						{showSeatsFor === selectedId ? 'Koltukları Gizle' : 'Koltukları Göster'}
					</button>
				</div>
			{/if}

			{#if stageSelected}
				<div class="tool-section props-panel">
					<p class="tool-label">Sahne</p>
					<label>
						<span>Genişlik</span>
						<input type="number" min="80" max={CW - 20} value={stage.width}
							oninput={(e) => (stage = { ...stage, width: Number(e.currentTarget.value) })} />
					</label>
					<label>
						<span>Yükseklik</span>
						<input type="number" min="40" max={CH / 2} value={stage.height}
							oninput={(e) => (stage = { ...stage, height: Number(e.currentTarget.value) })} />
					</label>
					<p class="props-hint">Tutamaç sürükleyerek de boyutlandırabilirsin</p>
				</div>
			{/if}

			{#if walls.length > 0}
				<div class="tool-section">
					<p class="tool-label">Duvarlar</p>
					{#each walls as w, i}
						<div class="wall-item">
							<span>Duvar {i + 1}</span>
							<button class="icon-btn" type="button" onclick={() => (walls = walls.filter(x => x.id !== w.id))}>✕</button>
						</div>
					{/each}
				</div>
			{/if}

			<div class="tool-section legend">
				<p class="tool-label">Açıklama</p>
				<div class="legend-item"><span class="dot dt"></span>Masa (tıkla → koltuklar)</div>
				<div class="legend-item"><span class="dot ds"></span>Koltuk</div>
				<div class="legend-item"><span class="dot dstage"></span>Sahne</div>
				<div class="legend-item"><span class="lp"></span>Duvar</div>
				<div class="legend-item"><span class="dot rh-legend"></span>Yeniden boyutlandır</div>
			</div>
		</aside>

		<div class="canvas-wrap">
			<svg
				bind:this={svgEl}
				class="salon-svg"
				class:tool-wall={activeTool === 'wall'}
				viewBox="0 0 {CW} {CH}"
				width={CW}
				height={CH}
				onpointerdown={onSvgPointerDown}
				onpointermove={onSvgPointerMove}
				onpointerup={onSvgPointerUp}
				onclick={onSvgClick}
				onkeydown={(e) => {
					if (e.key === 'Enter' || e.key === ' ') e.preventDefault();
				}}
				role="button"
				tabindex="0"
				aria-label="Salon tasarım alanı"
				style="touch-action:none"
			>
				<rect width={CW} height={CH} rx="8" fill="#1a2540" />

				{#each gridLines.x as gx}
					<line x1={gx} y1="0" x2={gx} y2={CH} stroke="rgba(255,255,255,0.04)" stroke-width="1" />
				{/each}
				{#each gridLines.y as gy}
					<line x1="0" y1={gy} x2={CW} y2={gy} stroke="rgba(255,255,255,0.04)" stroke-width="1" />
				{/each}

				{#each walls as w}
					<line x1={w.x1} y1={w.y1} x2={w.x2} y2={w.y2} stroke="#6b7280" stroke-width="6" stroke-linecap="round" />
				{/each}

				{#if drawingWall}
					<line x1={drawingWall.x1} y1={drawingWall.y1} x2={mouseX} y2={mouseY}
						stroke="#c59b31" stroke-width="4" stroke-dasharray="8 4" stroke-linecap="round" opacity="0.7" />
				{/if}

				<!-- Stage -->
				<g onpointerdown={startStageDrag} role="presentation" style="cursor:move">
					<rect x={stage.x} y={stage.y} width={stage.width} height={stage.height}
						rx="6"
						fill={stageSelected ? '#1e4a7f' : '#1e3a5f'}
						stroke={stageSelected ? '#c59b31' : '#3b82f6'}
						stroke-width={stageSelected ? 2.5 : 2}
					/>
					<text x={stage.x + stage.width / 2} y={stage.y + stage.height / 2 - 6}
						text-anchor="middle" fill="#93c5fd" font-size="11" font-weight="900" letter-spacing="3" pointer-events="none">SAHNE</text>
					<text x={stage.x + stage.width / 2} y={stage.y + stage.height / 2 + 12}
						text-anchor="middle" fill="rgba(147,197,253,0.4)" font-size="9" pointer-events="none">sürükle taşı</text>
				</g>
				<!-- Stage resize handles (always visible) -->
				<rect class="rh rh-ew" x={stage.x + stage.width - RH/2} y={stage.y + stage.height/2 - RH/2} width={RH} height={RH}
					role="presentation"
					onpointerdown={(e) => startStageResize(e, 'right')} />
				<rect class="rh rh-ns" x={stage.x + stage.width/2 - RH/2} y={stage.y + stage.height - RH/2} width={RH} height={RH}
					role="presentation"
					onpointerdown={(e) => startStageResize(e, 'bottom')} />
				<rect class="rh rh-nwse" x={stage.x + stage.width - RH/2} y={stage.y + stage.height - RH/2} width={RH} height={RH}
					role="presentation"
					onpointerdown={(e) => startStageResize(e, 'br')} />

				{#each tables as t (t.id)}
					<g
						onpointerdown={(e) => startTableDrag(e, t.id)}
						onclick={(e) => clickTable(e, t.id)}
						onkeydown={(e) => {
							if (e.key === 'Enter' || e.key === ' ') {
								e.preventDefault();
								clickTable(e, t.id);
							}
						}}
						role="presentation"
						style="cursor:{activeTool === 'select' ? 'grab' : 'default'}"
					>
						{#if t.shape === 'round'}
							<circle
								cx={t.x + t.width / 2} cy={t.y + t.height / 2} r={t.width / 2 - 1}
								fill={selectedId === t.id ? '#92400e' : '#1e40af'}
								stroke={selectedId === t.id ? '#c59b31' : 'rgba(59,130,246,0.5)'}
								stroke-width={selectedId === t.id ? 2.5 : 1.5}
							/>
						{:else}
							<rect
								x={t.x} y={t.y} width={t.width} height={t.height} rx="6"
								fill={selectedId === t.id ? '#92400e' : '#1e40af'}
								stroke={selectedId === t.id ? '#c59b31' : 'rgba(59,130,246,0.5)'}
								stroke-width={selectedId === t.id ? 2.5 : 1.5}
							/>
						{/if}
						<text x={t.x + t.width / 2} y={t.y + t.height / 2 - 7}
							text-anchor="middle" fill="#fff" font-size="11" font-weight="900" pointer-events="none">
							{t.no}
						</text>
						<text x={t.x + t.width / 2} y={t.y + t.height / 2 + 9}
							text-anchor="middle" fill="rgba(255,255,255,0.55)" font-size="9" pointer-events="none">
							{t.capacity} kişi
						</text>
					</g>

					{#if showSeatsFor === t.id}
						{#each seatPositions(t) as sp}
							<circle cx={sp.x} cy={sp.y} r="11" fill="#16a34a" opacity="0.85" pointer-events="none" />
							<text x={sp.x} y={sp.y + 4} text-anchor="middle" fill="#fff" font-size="8" font-weight="900" pointer-events="none">{sp.seat}</text>
						{/each}
					{/if}

					<!-- Table resize handles (only when selected) -->
					{#if selectedId === t.id}
						{#if t.shape === 'rectangle'}
							<rect class="rh rh-ew" x={t.x + t.width - RH/2} y={t.y + t.height/2 - RH/2} width={RH} height={RH}
								role="presentation"
								onpointerdown={(e) => startResize(e, t.id, 'right')} />
							<rect class="rh rh-ns" x={t.x + t.width/2 - RH/2} y={t.y + t.height - RH/2} width={RH} height={RH}
								role="presentation"
								onpointerdown={(e) => startResize(e, t.id, 'bottom')} />
							<rect class="rh rh-nwse" x={t.x + t.width - RH/2} y={t.y + t.height - RH/2} width={RH} height={RH}
								role="presentation"
								onpointerdown={(e) => startResize(e, t.id, 'br')} />
						{:else}
							<!-- Round: radius handle on east -->
							<rect class="rh rh-ew" x={t.x + t.width - RH/2} y={t.y + t.height/2 - RH/2} width={RH} height={RH}
								role="presentation"
								onpointerdown={(e) => startResize(e, t.id, 'radius')} />
						{/if}
					{/if}
				{/each}

				{#if tables.length === 0}
					<text x={CW / 2} y={CH / 2 - 14} text-anchor="middle"
						fill="rgba(255,255,255,0.18)" font-size="16" font-weight="700" pointer-events="none">
						Sol panelden masa ekle
					</text>
					<text x={CW / 2} y={CH / 2 + 12} text-anchor="middle"
						fill="rgba(255,255,255,0.1)" font-size="12" pointer-events="none">
						Tıkla → koltuklar · Sürükle → taşı · Tutamaçlar → boyutlandır
					</text>
				{/if}
			</svg>
			<p class="canvas-hint">
				{#if activeTool === 'wall'}Başlangıç noktasına bas, bitiş noktasında bırak
				{:else}Masa tıkla → koltuklar · Sürükle → taşı · Altın tutamaçlar → boyutlandır{/if}
			</p>
		</div>
	</div>
</section>

<style>
	.page-shell { max-width: 1600px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }
	.page-heading { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
	p { margin: 0; }
	.head-actions { display: flex; align-items: center; gap: 0.75rem; }
	.layout-name { min-height: 38px; border: 1px solid var(--line); border-radius: 7px; padding: 0.5rem 0.75rem; background: var(--surface); color: var(--text); font: inherit; font-weight: 800; }
	.save-btn { border: 0; border-radius: 8px; padding: 0.75rem 1.2rem; background: var(--accent); color: #fff; font-weight: 900; cursor: pointer; transition: background 0.2s; }
	.save-btn.saved { background: #16a34a; }
	.save-btn:disabled { opacity: 0.7; cursor: not-allowed; }
	.error-bar { padding: 0.75rem 1rem; background: color-mix(in srgb, #ef4444 12%, transparent); border: 1px solid #ef4444; border-radius: 8px; color: #ef4444; font-weight: 800; font-size: 0.85rem; }
	.layout-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }
	.layout-tab { padding: 0.45rem 0.85rem; border: 1px solid var(--line); border-radius: 7px; background: var(--surface-strong); color: var(--muted); font: inherit; font-weight: 800; font-size: 0.82rem; cursor: pointer; }
	.layout-tab.active { background: var(--accent-soft); border-color: color-mix(in srgb, var(--accent) 40%, transparent); color: var(--text); }
	.new-layout-row { display: flex; gap: 0.35rem; margin-left: auto; }
	.new-layout-row input { min-height: 34px; border: 1px solid var(--line); border-radius: 7px; padding: 0.35rem 0.65rem; background: var(--surface-strong); color: var(--text); font: inherit; font-size: 0.82rem; }
	.new-layout-row button { border: 0; border-radius: 7px; padding: 0.35rem 0.85rem; background: var(--accent); color: #fff; font-weight: 900; font-size: 0.82rem; cursor: pointer; white-space: nowrap; }
	.del-layout { border: 1px solid #ef4444; border-radius: 7px; padding: 0.35rem 0.75rem; background: transparent; color: #ef4444; font-weight: 900; font-size: 0.78rem; cursor: pointer; }

	.designer-wrap { display: grid; grid-template-columns: 220px 1fr; gap: 1rem; align-items: start; }

	.toolbar { display: flex; flex-direction: column; gap: 0.85rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 1rem; box-shadow: 0 18px 38px rgba(0,0,0,0.12); }
	.tool-section { display: flex; flex-direction: column; gap: 0.5rem; }
	.tool-label { font-size: 0.72rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin: 0; }

	.tool-btn { border: 1px solid var(--line); border-radius: 7px; padding: 0.6rem 0.75rem; background: var(--surface-strong); color: var(--muted); font: inherit; font-weight: 800; font-size: 0.85rem; cursor: pointer; text-align: left; transition: all 0.15s; }
	.tool-btn.active, .tool-btn:hover { background: var(--accent-soft, rgba(197,155,49,0.12)); border-color: color-mix(in srgb, var(--accent) 40%, transparent); color: var(--text); }

	.add-btn { display: flex; align-items: center; gap: 0.6rem; border: 1px solid var(--line); border-radius: 7px; padding: 0.6rem 0.75rem; background: var(--surface-strong); color: var(--text); font: inherit; font-weight: 800; font-size: 0.83rem; cursor: pointer; transition: all 0.15s; }
	.add-btn:hover { border-color: color-mix(in srgb, var(--accent) 40%, transparent); }

	.shape-prev { display: inline-block; background: #1e40af; }
	.shape-prev.round    { width: 18px; height: 18px; border-radius: 50%; }
	.shape-prev.rectangle { width: 26px; height: 16px; border-radius: 3px; }

	.props-panel { background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; padding: 0.75rem; }
	.props-panel label { display: flex; flex-direction: column; gap: 0.3rem; font-weight: 800; font-size: 0.82rem; }
	.props-panel label span { color: var(--muted); }
	.props-panel input { width: 100%; min-height: 34px; border: 1px solid var(--line); border-radius: 6px; padding: 0.4rem 0.55rem; background: var(--surface); color: var(--text); font: inherit; }
	.props-hint { font-size: 0.7rem; color: var(--muted); margin: 0.15rem 0; font-style: italic; }

	.remove-btn { margin-top: 0.35rem; border: 1px solid color-mix(in srgb, #ef4444 35%, transparent); border-radius: 7px; padding: 0.5rem; background: color-mix(in srgb, #ef4444 10%, transparent); color: #ef4444; font: inherit; font-weight: 900; font-size: 0.82rem; cursor: pointer; }
	.seat-btn { border: 1px solid color-mix(in srgb, #16a34a 35%, transparent); border-radius: 7px; padding: 0.5rem; background: color-mix(in srgb, #16a34a 10%, transparent); color: #16a34a; font: inherit; font-weight: 900; font-size: 0.82rem; cursor: pointer; }

	.wall-item { display: flex; align-items: center; justify-content: space-between; font-size: 0.82rem; color: var(--muted); }
	.icon-btn { border: 0; background: transparent; color: var(--muted); cursor: pointer; font-size: 0.8rem; padding: 0.15rem 0.35rem; border-radius: 4px; }
	.icon-btn:hover { color: #ef4444; }

	.legend { gap: 0.4rem; }
	.legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.78rem; color: var(--muted); }
	.dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
	.dt { background: #1e40af; }
	.ds { background: #16a34a; }
	.dstage { background: #1e3a5f; border: 1px solid #3b82f6; border-radius: 2px; }
	.lp { width: 20px; height: 4px; background: #6b7280; border-radius: 2px; flex-shrink: 0; }
	.rh-legend { background: #c59b31; width: 10px; height: 10px; border-radius: 2px; border: 1px solid #fff; }

	.canvas-wrap { display: flex; flex-direction: column; gap: 0.5rem; }
	.salon-svg { display: block; border-radius: 8px; border: 1px solid var(--line); box-shadow: 0 18px 38px rgba(0,0,0,0.22); width: 100%; max-width: 100%; height: auto; }
	.salon-svg.tool-wall { cursor: crosshair; }
	.canvas-hint { font-size: 0.78rem; color: var(--muted); text-align: center; margin: 0; }

	/* SVG resize handles */
	:global(.rh) { fill: #c59b31; stroke: #fff; stroke-width: 1.5; rx: 2; }
	:global(.rh-ew) { cursor: ew-resize; }
	:global(.rh-ns) { cursor: ns-resize; }
	:global(.rh-nwse) { cursor: nwse-resize; }

	@media (max-width: 900px) { .designer-wrap { grid-template-columns: 1fr; } }
</style>
