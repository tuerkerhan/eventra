<script lang="ts">
	interface MonthMetric {
		month: string;
		revenue: number;
		expense: number;
		events: number;
		lastYearRevenue: number;
	}

	interface StaffMetric {
		name: string;
		role: string;
		events: number;
		hours: number;
		cost: number;
		rating: number;
	}

	interface EventCost {
		id: string;
		title: string;
		date: string;
		revenue: number;
		expense: number;
		staff: string;
	}

	let months = $state<MonthMetric[]>([
		{ month: 'Oca', revenue: 420000, expense: 238000, events: 6, lastYearRevenue: 360000 },
		{ month: 'Şub', revenue: 390000, expense: 225000, events: 5, lastYearRevenue: 310000 },
		{ month: 'Mar', revenue: 510000, expense: 288000, events: 7, lastYearRevenue: 445000 },
		{ month: 'Nis', revenue: 680000, expense: 392000, events: 9, lastYearRevenue: 520000 },
		{ month: 'May', revenue: 760000, expense: 438000, events: 11, lastYearRevenue: 615000 },
		{ month: 'Haz', revenue: 905000, expense: 504000, events: 13, lastYearRevenue: 710000 }
	]);

	let staff = $state<StaffMetric[]>([
		{ name: 'Elif', role: 'Operasyon', events: 8, hours: 54, cost: 48600, rating: 4.8 },
		{ name: 'Mert', role: 'Salon Şefi', events: 7, hours: 49, cost: 44100, rating: 4.6 },
		{ name: 'Seda', role: 'Müşteri İlişkileri', events: 6, hours: 38, cost: 34200, rating: 4.9 },
		{ name: 'Can', role: 'Teknik', events: 5, hours: 32, cost: 28800, rating: 4.5 }
	]);

	let eventCosts = $state<EventCost[]>([
		{ id: '2962', title: 'Ayşe & Ahmet Düğün', date: '2026-06-18', revenue: 150000, expense: 78000, staff: 'Elif, Mert, Can' },
		{ id: '2963', title: 'Burcu & Cem Nişan', date: '2026-06-25', revenue: 85000, expense: 41000, staff: 'Mert, Seda' },
		{ id: '2964', title: 'Derya & Emre Kına', date: '2026-07-02', revenue: 60000, expense: 26500, staff: 'Seda, Can' },
		{ id: '2965', title: 'Kurumsal Gala', date: '2026-07-09', revenue: 210000, expense: 126000, staff: 'Elif, Mert, Seda, Can' }
	]);

	const sum = (items: number[]) => items.reduce((total, value) => total + value, 0);
	const totalRevenue = () => sum(months.map((item) => item.revenue));
	const totalExpense = () => sum(months.map((item) => item.expense));
	const totalEvents = () => sum(months.map((item) => item.events));
	const totalLastYear = () => sum(months.map((item) => item.lastYearRevenue));
	const maxRevenue = () => Math.max(...months.map((item) => item.revenue), 1);
	const currentMonth = () => months[months.length - 1];
	const yoy = () => ((currentMonth().revenue - currentMonth().lastYearRevenue) / Math.max(currentMonth().lastYearRevenue, 1)) * 100;
	const margin = () => ((totalRevenue() - totalExpense()) / Math.max(totalRevenue(), 1)) * 100;
	const staffHourCost = () => sum(staff.map((person) => person.cost)) / Math.max(sum(staff.map((person) => person.hours)), 1);
	const averageRating = () => sum(staff.map((person) => person.rating)) / Math.max(staff.length, 1);
	const formatMoney = (value: number) => `₺${Math.round(value).toLocaleString('tr-TR')}`;
	const formatPercent = (value: number) => `%${value.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`;
</script>

<section class="dashboard-shell">
	<div class="page-heading">
		<div>
			<p class="eyebrow">Dashboard</p>
			<h1>İşletme performansı</h1>
			<p>Ciro, gider, personel ve etkinlik maliyetleri buradaki girişlerden hesaplanır.</p>
		</div>
		<div class="period-chip">2026 · Ocak-Haziran</div>
	</div>

	<div class="metric-grid">
		<div class="metric-card"><span>Toplam ciro</span><strong>{formatMoney(totalRevenue())}</strong><small>Geçen yıl aynı döneme göre {formatPercent(((totalRevenue() - totalLastYear()) / Math.max(totalLastYear(), 1)) * 100)}</small></div>
		<div class="metric-card"><span>Toplam gider</span><strong>{formatMoney(totalExpense())}</strong><small>Etkinlik başı gider {formatMoney(totalExpense() / Math.max(totalEvents(), 1))}</small></div>
		<div class="metric-card"><span>Net marj</span><strong>{formatPercent(margin())}</strong><small>{currentMonth().month} geçen yıl aynı aya göre {formatPercent(yoy())}</small></div>
		<div class="metric-card"><span>Etkinlik adedi</span><strong>{totalEvents()}</strong><small>Aylık ortalama {(totalEvents() / months.length).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}</small></div>
	</div>

	<div class="dashboard-grid">
		<section class="panel wide">
			<div class="panel-head">
				<div>
					<h2>Aylık performans</h2>
					<p>Aşağıdaki girişler grafiği ve üst göstergeleri besler.</p>
				</div>
			</div>
			<div class="chart">
				{#each months as item}
					<div class="chart-month">
						<div class="bars">
							<span class="bar revenue" style="height: {(item.revenue / maxRevenue()) * 100}%"></span>
							<span class="bar expense" style="height: {(item.expense / maxRevenue()) * 100}%"></span>
							<span class="bar last-year" style="height: {(item.lastYearRevenue / maxRevenue()) * 100}%"></span>
						</div>
						<strong>{item.month}</strong>
					</div>
				{/each}
			</div>
			<div class="legend">
				<span><i class="revenue"></i>Ciro</span>
				<span><i class="expense"></i>Gider</span>
				<span><i class="last-year"></i>Geçen yıl</span>
			</div>
			<div class="editable-table">
				<div class="table-head month-head">
					<span>Ay</span><span>Ciro</span><span>Gider</span><span>Etkinlik</span><span>Geçen yıl ciro</span>
				</div>
				{#each months as item}
					<div class="table-row month-row">
						<input bind:value={item.month} aria-label="Ay" />
						<input type="number" bind:value={item.revenue} aria-label="{item.month} ciro" />
						<input type="number" bind:value={item.expense} aria-label="{item.month} gider" />
						<input type="number" bind:value={item.events} aria-label="{item.month} etkinlik adedi" />
						<input type="number" bind:value={item.lastYearRevenue} aria-label="{item.month} geçen yıl ciro" />
					</div>
				{/each}
			</div>
		</section>

		<section class="panel">
			<div class="panel-head">
				<div>
					<h2>Ortalama göstergeler</h2>
					<p>Personel ve ay girişlerinden anlık hesaplanır.</p>
				</div>
			</div>
			<div class="stat-list">
				<div><span>Davet başı ciro</span><strong>{formatMoney(totalRevenue() / Math.max(totalEvents(), 1))}</strong></div>
				<div><span>Davet başı gider</span><strong>{formatMoney(totalExpense() / Math.max(totalEvents(), 1))}</strong></div>
				<div><span>Personel saat maliyeti</span><strong>{formatMoney(staffHourCost())}</strong></div>
				<div><span>Ortalama memnuniyet</span><strong>{averageRating().toLocaleString('tr-TR', { maximumFractionDigits: 1 })}/5</strong></div>
			</div>
		</section>

		<section class="panel">
			<div class="panel-head">
				<div>
					<h2>Çalışan girişleri</h2>
					<p>Çalışanın görev, saat, maliyet ve puanı burada girilir.</p>
				</div>
			</div>
			<div class="staff-editor">
				{#each staff as person}
					<div class="staff-card">
						<input bind:value={person.name} aria-label="Çalışan adı" />
						<input bind:value={person.role} aria-label="{person.name} görev" />
						<div class="mini-grid">
							<label><span>Etkinlik</span><input type="number" bind:value={person.events} /></label>
							<label><span>Saat</span><input type="number" bind:value={person.hours} /></label>
							<label><span>Maliyet</span><input type="number" bind:value={person.cost} /></label>
							<label><span>Puan</span><input type="number" step="0.1" min="0" max="5" bind:value={person.rating} /></label>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<section class="panel wide">
			<div class="panel-head">
				<div>
					<h2>Etkinlik gider kayıtları</h2>
					<p>Her davetin ciro, gider ve çalışan bilgisi burada düzenlenir.</p>
				</div>
			</div>
			<div class="editable-table">
				<div class="table-head cost-head">
					<span>Davet</span><span>Tarih</span><span>Ciro</span><span>Gider</span><span>Net</span><span>Ekip</span>
				</div>
				{#each eventCosts as event}
					<div class="table-row cost-row">
						<input bind:value={event.title} aria-label="Davet adı" />
						<input type="date" bind:value={event.date} aria-label="{event.title} tarih" />
						<input type="number" bind:value={event.revenue} aria-label="{event.title} ciro" />
						<input type="number" bind:value={event.expense} aria-label="{event.title} gider" />
						<strong>{formatMoney(event.revenue - event.expense)}</strong>
						<input bind:value={event.staff} aria-label="{event.title} ekip" />
					</div>
				{/each}
			</div>
		</section>
	</div>
</section>

<style>
	.dashboard-shell {
		max-width: 1560px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.page-heading {
		display: flex;
		justify-content: space-between;
		align-items: end;
		gap: 1rem;
	}

	h1,
	h2,
	p {
		margin: 0;
	}

	h1 {
		font-size: clamp(1.9rem, 3vw, 3rem);
	}

	.eyebrow {
		margin-bottom: 0.25rem;
		color: var(--accent);
		font-size: 0.78rem;
		font-weight: 900;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.page-heading p,
	.panel-head p,
	.metric-card span,
	.metric-card small,
	.stat-list span,
	label span,
	.table-head {
		color: var(--muted);
	}

	.period-chip,
	.metric-card,
	.panel {
		background: var(--surface);
		border: 1px solid var(--line);
		border-radius: 8px;
		box-shadow: 0 18px 38px rgba(0, 0, 0, 0.12);
	}

	.period-chip {
		padding: 0.75rem 0.9rem;
		font-weight: 900;
	}

	.metric-grid,
	.dashboard-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 1rem;
	}

	.metric-card,
	.panel {
		padding: 1rem;
		min-width: 0;
	}

	.metric-card {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	.metric-card strong {
		font-size: clamp(1.45rem, 2.5vw, 2.1rem);
	}

	.panel.wide {
		grid-column: span 3;
	}

	.panel-head {
		margin-bottom: 1rem;
	}

	.panel h2 {
		font-size: 1.15rem;
		margin-bottom: 0.2rem;
	}

	.chart {
		display: grid;
		grid-template-columns: repeat(6, minmax(64px, 1fr));
		gap: 0.8rem;
		height: 250px;
	}

	.chart-month {
		display: grid;
		grid-template-rows: 1fr auto;
		gap: 0.5rem;
		text-align: center;
	}

	.bars {
		display: flex;
		align-items: end;
		justify-content: center;
		gap: 0.35rem;
		padding: 0.75rem 0.4rem;
		background: var(--surface-strong);
		border: 1px solid var(--line);
		border-radius: 8px;
	}

	.bar {
		width: 22%;
		min-height: 12px;
		border-radius: 6px 6px 0 0;
	}

	.revenue {
		background: #16a34a;
	}

	.expense {
		background: #dc2626;
	}

	.last-year {
		background: #2563eb;
	}

	.legend {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
		margin: 0.75rem 0;
		color: var(--muted);
		font-weight: 800;
		font-size: 0.85rem;
	}

	.legend span {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
	}

	.legend i {
		width: 11px;
		height: 11px;
		border-radius: 3px;
	}

	.stat-list,
	.staff-editor,
	.editable-table {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}

	.stat-list div,
	.staff-card,
	.table-row {
		background: var(--surface-strong);
		border: 1px solid var(--line);
		border-radius: 8px;
	}

	.stat-list div {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		padding: 0.85rem;
	}

	.staff-card {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.65rem;
		padding: 0.75rem;
	}

	.mini-grid {
		grid-column: 1 / -1;
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.5rem;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-weight: 800;
	}

	input {
		width: 100%;
		min-height: 38px;
		border: 1px solid var(--line);
		border-radius: 7px;
		padding: 0.5rem 0.6rem;
		background: var(--surface);
		color: var(--text);
		font: inherit;
	}

	.table-head,
	.table-row {
		display: grid;
		gap: 0.55rem;
		align-items: center;
		min-width: 850px;
	}

	.table-head {
		color: var(--muted);
		font-size: 0.76rem;
		font-weight: 900;
		text-transform: uppercase;
		padding: 0 0.65rem;
	}

	.table-row {
		padding: 0.65rem;
	}

	.month-head,
	.month-row {
		grid-template-columns: 0.6fr 1fr 1fr 0.8fr 1fr;
	}

	.cost-head,
	.cost-row {
		grid-template-columns: 1.35fr 0.9fr 0.9fr 0.9fr 0.8fr 1.2fr;
	}

	@media (max-width: 1150px) {
		.metric-grid,
		.dashboard-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.panel.wide {
			grid-column: span 2;
		}
	}

	@media (max-width: 720px) {
		.page-heading {
			flex-direction: column;
			align-items: stretch;
		}

		.metric-grid,
		.dashboard-grid,
		.mini-grid,
		.staff-card {
			grid-template-columns: 1fr;
		}

		.panel.wide {
			grid-column: auto;
		}

		.chart {
			overflow-x: auto;
		}
	}
</style>
