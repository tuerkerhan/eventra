<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type EventApi, type SalonApi, type ExpenseApi } from '$lib/api';

	// ─── State ────────────────────────────────────────────────────────────────
	let events = $state<EventApi[]>([]);
	let expenses = $state<ExpenseApi[]>([]);
	let salon = $state<SalonApi | null>(null);
	let displayCurrency = $state<'TRY' | 'USD' | 'EUR'>('TRY');
	let tryPerUSD_raw = $state(0); // 1 USD = X TRY
	let tryPerEUR_raw = $state(0); // 1 EUR = X TRY
	let rateDate = $state('');
	let rateLoading = $state(true);

	// Expense modal
	let showExpenseForm = $state(false);
	let savingExpense = $state(false);
	let expenseForm = $state({
		title: '', amount: 0, amount_type: 'fixed' as 'fixed' | 'variable',
		currency: 'TRY' as 'TRY' | 'USD' | 'EUR',
		recurrence: 'once' as 'once' | 'weekly' | 'monthly' | 'yearly' | 'custom',
		custom_period_days: 30, due_date: '', event_id: '', include_kdv: false, note: ''
	});

	// KDV calculator
	let kdvMode = $state<'net-to-gross' | 'gross-to-net'>('gross-to-net');
	let kdvInput = $state(0);
	let kdvRate = $state(20);

	// Currency converter
	let convAmount = $state(0);
	let convFrom = $state<'TRY' | 'USD' | 'EUR'>('USD');
	let convTo = $state<'TRY' | 'USD' | 'EUR'>('TRY');

	const today = new Date();
	today.setHours(0, 0, 0, 0);

	// ─── Exchange rates ────────────────────────────────────────────────────────
	onMount(async () => {
		try {
			// base=USD is always supported; TRY and EUR come in rates
			const r = await fetch('https://api.frankfurter.dev/v1/latest?base=USD&symbols=TRY,EUR');
			if (r.ok) {
				const d = await r.json();
				tryPerUSD_raw = d.rates?.TRY ?? 0;
				// EUR/TRY: 1 EUR = (TRY/USD) / (EUR/USD)
				const eurUsd = d.rates?.EUR ?? 0;
				tryPerEUR_raw = eurUsd > 0 ? (d.rates?.TRY ?? 0) / eurUsd : 0;
				rateDate = d.date ?? '';
			}
		} catch {}
		rateLoading = false;

		try {
			const [evs, exps, s] = await Promise.all([
				api.get<EventApi[]>('/events'),
				api.get<ExpenseApi[]>('/expenses'),
				api.get<SalonApi>('/settings/salon')
			]);
			events = evs;
			expenses = exps;
			salon = s;
			if (salon) kdvRate = salon.vat_rate;
		} catch {}
	});

	// ─── Currency helpers ─────────────────────────────────────────────────────
	const tryPerUSD = $derived(tryPerUSD_raw);
	const tryPerEUR = $derived(tryPerEUR_raw);
	const usdPerTRY = $derived(tryPerUSD_raw > 0 ? 1 / tryPerUSD_raw : 0);
	const eurPerTRY = $derived(tryPerEUR_raw > 0 ? 1 / tryPerEUR_raw : 0);

	function toTRY(amount: number, currency: 'TRY' | 'USD' | 'EUR'): number {
		if (currency === 'TRY') return amount;
		if (currency === 'USD') return amount * tryPerUSD;
		return amount * tryPerEUR;
	}

	function fromTRY(amount: number): number {
		if (displayCurrency === 'TRY') return amount;
		if (displayCurrency === 'USD') return amount * usdPerTRY;
		return amount * eurPerTRY;
	}

	function toDisplay(amount: number, fromCurrency: 'TRY' | 'USD' | 'EUR' = 'TRY'): number {
		return fromTRY(toTRY(amount, fromCurrency));
	}

	const currSymbol = $derived(displayCurrency === 'TRY' ? '₺' : displayCurrency === 'USD' ? '$' : '€');

	function fmt(v: number, decimals = 0): string {
		return `${currSymbol}${v.toLocaleString('tr-TR', { maximumFractionDigits: decimals, minimumFractionDigits: decimals })}`;
	}

	function fmtTL(v: number): string {
		return `₺${Math.round(v).toLocaleString('tr-TR')}`;
	}

	function fmtShort(v: number): string {
		const a = Math.abs(v);
		if (a >= 1_000_000) return `${(v / 1_000_000).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}M`;
		if (a >= 1_000) return `${(v / 1_000).toLocaleString('tr-TR', { maximumFractionDigits: 0 })}B`;
		return v.toLocaleString('tr-TR', { maximumFractionDigits: 0 });
	}

	function fmtRate(v: number): string {
		return v.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	}

	// ─── Date helpers ─────────────────────────────────────────────────────────
	function monthKey(offset = 0): string {
		const d = new Date(today.getFullYear(), today.getMonth() + offset, 1);
		return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
	}

	function daysLeft(dateStr: string): number {
		const d = new Date(dateStr + 'T00:00:00');
		return Math.ceil((d.getTime() - today.getTime()) / 86400000);
	}

	function fmtDate(s: string): string {
		return new Date(s + 'T00:00:00').toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' });
	}

	// ─── Derived metrics ──────────────────────────────────────────────────────
	const thisKey = $derived(monthKey(0));
	const prevKey = $derived(monthKey(-1));

	const thisEvents = $derived(events.filter(e => e.event_date.startsWith(thisKey)));
	const prevEvents = $derived(events.filter(e => e.event_date.startsWith(prevKey)));

	const grossIncome = $derived(thisEvents.reduce((s, e) => s + e.total_fee, 0));
	const collected = $derived(thisEvents.reduce((s, e) => s + e.total_paid, 0));
	const prevGross = $derived(prevEvents.reduce((s, e) => s + e.total_fee, 0));
	const netIncome = $derived(salon ? grossIncome / (1 + salon.vat_rate / 100) : grossIncome);
	const kdvAmount = $derived(grossIncome - netIncome);
	const incomeChange = $derived(prevGross > 0 ? ((grossIncome - prevGross) / prevGross) * 100 : null);

	const thisExpensesTRY = $derived(
		expenses.filter(e => e.due_date.startsWith(thisKey)).reduce((s, e) => s + toTRY(e.amount, e.currency), 0)
	);
	const prevExpensesTRY = $derived(
		expenses.filter(e => e.due_date.startsWith(prevKey)).reduce((s, e) => s + toTRY(e.amount, e.currency), 0)
	);
	const expenseChange = $derived(prevExpensesTRY > 0 ? ((thisExpensesTRY - prevExpensesTRY) / prevExpensesTRY) * 100 : null);

	const netProfit = $derived(grossIncome - thisExpensesTRY);
	const profitMargin = $derived(grossIncome > 0 ? (netProfit / grossIncome) * 100 : 0);

	const unpaidExpenses = $derived(
		expenses.filter(e => !e.is_paid).sort((a, b) => a.due_date.localeCompare(b.due_date))
	);
	const pendingApproval = $derived(expenses.filter(e => !e.is_approved && !e.is_paid));
	const overdue = $derived(unpaidExpenses.filter(e => daysLeft(e.due_date) < 0));
	const dueSoon = $derived(unpaidExpenses.filter(e => { const d = daysLeft(e.due_date); return d >= 0 && d <= 7; }));
	const unpaidTotal = $derived(unpaidExpenses.reduce((s, e) => s + toTRY(e.amount, e.currency), 0));

	// ─── Chart data (last 6 months) ───────────────────────────────────────────
	const chartMonths = $derived.by(() => {
		return Array.from({ length: 6 }, (_, i) => {
			const d = new Date(today.getFullYear(), today.getMonth() - (5 - i), 1);
			const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
			const label = d.toLocaleDateString('tr-TR', { month: 'short' });
			const inc = events.filter(e => e.event_date.startsWith(key)).reduce((s, e) => s + e.total_fee, 0);
			const exp = expenses.filter(e => e.due_date.startsWith(key)).reduce((s, e) => s + toTRY(e.amount, e.currency), 0);
			return { key, label, income: fromTRY(inc), expense: fromTRY(exp) };
		});
	});

	const chartMax = $derived.by(() => {
		const all = chartMonths.flatMap(m => [m.income, m.expense]);
		const raw = Math.max(...all, 1);
		const mag = Math.pow(10, Math.floor(Math.log10(raw)));
		return Math.ceil(raw / mag) * mag;
	});

	// SVG bar chart constants
	const CX0 = 58, CX1 = 580, CY0 = 12, CY1 = 188;
	const PW = CX1 - CX0;
	const PH = CY1 - CY0;
	const GW = PW / 6;
	const BW = GW * 0.32;

	function bx(mi: number, bi: number) { return CX0 + mi * GW + GW * 0.09 + bi * (BW + GW * 0.07); }
	function by(v: number) { return CY0 + (1 - v / chartMax) * PH; }
	function bh(v: number) { return (v / Math.max(chartMax, 1)) * PH; }
	function lx(mi: number) { return CX0 + mi * GW + GW / 2; }

	const yTicks = $derived.by(() =>
		Array.from({ length: 5 }, (_, i) => ({
			y: CY1 - (i / 4) * PH,
			label: fmtShort(chartMax * i / 4)
		}))
	);

	// Donut chart
	const R = 68, SW = 30;
	const CIRC = 2 * Math.PI * R;

	const paidAmt = $derived(thisEvents.reduce((s, e) => s + (e.payment_complete ? e.total_fee : 0), 0));
	const partialAmt = $derived(thisEvents.reduce((s, e) => s + (!e.payment_complete && e.total_paid > 0 ? e.total_paid : 0), 0));
	const unpaidAmt = $derived(grossIncome - paidAmt - partialAmt);

	const donutTotal = $derived(Math.max(grossIncome, 1));
	const paidLen = $derived((paidAmt / donutTotal) * CIRC);
	const partialLen = $derived((partialAmt / donutTotal) * CIRC);
	const unpaidLen = $derived((Math.max(unpaidAmt, 0) / donutTotal) * CIRC);

	// ─── Expense status helpers ───────────────────────────────────────────────
	function expStatus(e: ExpenseApi): { color: string; label: string; dot: string } {
		if (e.is_paid) return { color: '#16a34a', label: 'Ödendi', dot: 'green' };
		if (!e.is_approved) return { color: '#8b5cf6', label: 'Onay Bekliyor', dot: 'purple' };
		const d = daysLeft(e.due_date);
		if (d < 0) return { color: '#dc2626', label: 'Vadesi Geçti', dot: 'red' };
		if (d <= 3) return { color: '#f59e0b', label: `${d}g kaldı`, dot: 'orange' };
		if (d <= 7) return { color: '#f97316', label: `${d}g kaldı`, dot: 'amber' };
		return { color: '#64748b', label: `${d}g kaldı`, dot: 'gray' };
	}

	const recurrenceLabel: Record<string, string> = {
		once: 'Tek seferlik', weekly: 'Haftalık', monthly: 'Aylık', yearly: 'Yıllık', custom: 'Özel'
	};

	// ─── KDV calculator ───────────────────────────────────────────────────────
	const kdvCalcResult = $derived.by(() => {
		const rate = kdvRate / 100;
		if (kdvMode === 'gross-to-net') {
			const net = kdvInput / (1 + rate);
			return { net, gross: kdvInput, kdv: kdvInput - net };
		} else {
			const gross = kdvInput * (1 + rate);
			return { net: kdvInput, gross, kdv: gross - kdvInput };
		}
	});

	// ─── Currency converter ───────────────────────────────────────────────────
	const convResult = $derived.by(() => {
		const tryAmt = toTRY(convAmount, convFrom);
		if (convTo === 'TRY') return tryAmt;
		if (convTo === 'USD') return tryAmt * usdPerTRY;
		return tryAmt * eurPerTRY;
	});

	const convSymbol = (c: string) => c === 'TRY' ? '₺' : c === 'USD' ? '$' : '€';

	// ─── Expense actions ──────────────────────────────────────────────────────
	async function markPaid(e: ExpenseApi) {
		await api.patch(`/expenses/${e.id}`, { is_paid: true });
		expenses = await api.get<ExpenseApi[]>('/expenses');
	}

	async function approveExpense(e: ExpenseApi) {
		await api.patch(`/expenses/${e.id}`, { is_approved: true });
		expenses = await api.get<ExpenseApi[]>('/expenses');
	}

	async function deleteExpense(e: ExpenseApi) {
		if (!confirm(`"${e.title}" silinsin mi?`)) return;
		await api.del(`/expenses/${e.id}`);
		expenses = await api.get<ExpenseApi[]>('/expenses');
	}

	async function saveExpense(ev: Event) {
		ev.preventDefault();
		savingExpense = true;
		try {
			await api.post('/expenses', {
				title: expenseForm.title,
				amount: expenseForm.amount,
				amount_type: expenseForm.amount_type,
				currency: expenseForm.currency,
				recurrence: expenseForm.recurrence,
				custom_period_days: expenseForm.recurrence === 'custom' ? expenseForm.custom_period_days : null,
				due_date: expenseForm.due_date,
				event_id: expenseForm.event_id || null,
				include_kdv: expenseForm.include_kdv,
				note: expenseForm.note
			});
			expenses = await api.get<ExpenseApi[]>('/expenses');
			showExpenseForm = false;
			expenseForm = { title: '', amount: 0, amount_type: 'fixed', currency: 'TRY', recurrence: 'once', custom_period_days: 30, due_date: '', event_id: '', include_kdv: false, note: '' };
		} finally {
			savingExpense = false;
		}
	}

	function changeSign(v: number | null): string {
		if (v === null) return '';
		return v >= 0 ? `+%${Math.abs(v).toFixed(1)}` : `-%${Math.abs(v).toFixed(1)}`;
	}
	function changeColor(v: number | null, inverted = false): string {
		if (v === null) return 'var(--muted)';
		const pos = inverted ? v < 0 : v >= 0;
		return pos ? '#16a34a' : '#dc2626';
	}
</script>

<section class="db-shell">

	<!-- ─── HEADER ─────────────────────────────────────────────────────── -->
	<div class="db-header">
		<div>
			<p class="eyebrow">Dashboard</p>
			<h1>Finansal Özet</h1>
			<p class="subtitle">Gerçek zamanlı gelir, gider ve nakit akışı takibi.</p>
		</div>
		<div class="header-right">
			<div class="rate-box">
				{#if rateLoading}
					<span class="muted">Kur yükleniyor…</span>
				{:else if tryPerUSD_raw > 0}
					<span class="rate-item"><span class="rate-flag">$</span> 1 USD = <strong>₺{fmtRate(tryPerUSD_raw)}</strong></span>
					<span class="rate-sep">·</span>
					<span class="rate-item"><span class="rate-flag">€</span> 1 EUR = <strong>₺{fmtRate(tryPerEUR_raw)}</strong></span>
					{#if rateDate}<span class="rate-date">({rateDate})</span>{/if}
				{:else}
					<span class="muted">Kur alınamadı · TL gösteriliyor</span>
				{/if}
			</div>
			<div class="currency-toggle">
				{#each (['TRY', 'USD', 'EUR'] as const) as c}
					<button class:active={displayCurrency === c} onclick={() => (displayCurrency = c)} type="button">{c}</button>
				{/each}
			</div>
		</div>
	</div>

	<!-- ─── KPI CARDS ──────────────────────────────────────────────────── -->
	<div class="kpi-grid">
		<div class="kpi-card accent">
			<span>Bu Ay Brüt Gelir</span>
			<strong>{fmt(toDisplay(grossIncome))}</strong>
			{#if incomeChange !== null}
				<small style="color:{changeColor(incomeChange)}">{changeSign(incomeChange)} geçen ay</small>
			{:else}
				<small class="muted">{thisEvents.length} etkinlik</small>
			{/if}
		</div>
		<div class="kpi-card">
			<span>Net Gelir (KDV hariç)</span>
			<strong>{fmt(toDisplay(netIncome))}</strong>
			<small class="muted">KDV: {fmtTL(kdvAmount)}</small>
		</div>
		<div class="kpi-card">
			<span>Bu Ay Tahsilat</span>
			<strong>{fmt(toDisplay(collected))}</strong>
			<small class="muted">{grossIncome > 0 ? Math.round(collected / grossIncome * 100) : 0}% tahsil edildi</small>
		</div>
		<div class="kpi-card {netProfit >= 0 ? 'good' : 'bad'}">
			<span>Net Kâr</span>
			<strong>{fmt(toDisplay(netProfit))}</strong>
			<small style="color:{netProfit >= 0 ? '#16a34a' : '#dc2626'}">Marj %{profitMargin.toFixed(1)}</small>
		</div>
		<div class="kpi-card">
			<span>Bu Ay Gider</span>
			<strong>{fmt(toDisplay(thisExpensesTRY))}</strong>
			{#if expenseChange !== null}
				<small style="color:{changeColor(expenseChange, true)}">{changeSign(expenseChange)} geçen ay</small>
			{:else}
				<small class="muted">Geçen ay: {fmt(toDisplay(prevExpensesTRY))}</small>
			{/if}
		</div>
		<div class="kpi-card {overdue.length > 0 ? 'bad' : ''}">
			<span>Vadesi Geçen Gider</span>
			<strong>{overdue.length}</strong>
			<small style="color:#dc2626">{overdue.length > 0 ? fmtTL(overdue.reduce((s,e)=>s+toTRY(e.amount,e.currency),0)) : 'Yok'}</small>
		</div>
		<div class="kpi-card {pendingApproval.length > 0 ? 'warn' : ''}">
			<span>Onay Bekleyen</span>
			<strong>{pendingApproval.length}</strong>
			<small class="muted">{pendingApproval.length > 0 ? 'Değişken gider' : 'Temiz'}</small>
		</div>
		<div class="kpi-card">
			<span>Ödenmemiş Gider</span>
			<strong>{fmt(toDisplay(unpaidTotal))}</strong>
			<small class="muted">{unpaidExpenses.length} kalem · {dueSoon.length} bu hafta</small>
		</div>
	</div>

	<!-- ─── CHARTS ─────────────────────────────────────────────────────── -->
	<div class="charts-row">
		<!-- Bar chart -->
		<div class="panel chart-panel">
			<div class="panel-head">
				<div><h2>Son 6 Ay — Gelir & Gider</h2><p>{displayCurrency} cinsinden</p></div>
				<div class="legend">
					<span><i class="dot green"></i>Gelir</span>
					<span><i class="dot red"></i>Gider</span>
				</div>
			</div>
			<svg viewBox="0 0 600 220" class="bar-svg" aria-label="Aylık gelir gider grafiği">
				<!-- gridlines -->
				{#each yTicks as tick}
					<line x1={CX0} y1={tick.y} x2={CX1} y2={tick.y} stroke="var(--line)" stroke-width="1" />
					<text x={CX0 - 6} y={tick.y + 4} text-anchor="end" class="axis-label">{tick.label}</text>
				{/each}
				<!-- bars -->
				{#each chartMonths as m, i}
					{#if bh(m.income) > 0}
						<rect x={bx(i, 0)} y={by(m.income)} width={BW} height={bh(m.income)} rx="3" fill="#16a34a" opacity="0.85" />
					{/if}
					{#if bh(m.expense) > 0}
						<rect x={bx(i, 1)} y={by(m.expense)} width={BW} height={bh(m.expense)} rx="3" fill="#dc2626" opacity="0.75" />
					{/if}
					<text x={lx(i)} y={CY1 + 14} text-anchor="middle" class="axis-label">{m.label}</text>
				{/each}
				<!-- x axis line -->
				<line x1={CX0} y1={CY1} x2={CX1} y2={CY1} stroke="var(--line)" stroke-width="1.5" />
				<!-- y axis line -->
				<line x1={CX0} y1={CY0} x2={CX0} y2={CY1} stroke="var(--line)" stroke-width="1.5" />
			</svg>
		</div>

		<!-- Donut chart -->
		<div class="panel donut-panel">
			<div class="panel-head">
				<div><h2>Bu Ay Tahsilat</h2><p>Gelir dağılımı</p></div>
			</div>
			<div class="donut-wrap">
				<svg viewBox="0 0 200 200" class="donut-svg" aria-label="Tahsilat dağılım grafiği">
					<circle cx="100" cy="100" r={R} fill="none" stroke="var(--muted-surface)" stroke-width={SW} />
					{#if donutTotal > 0}
						{#if paidLen > 0}
							<circle cx="100" cy="100" r={R} fill="none" stroke="#16a34a" stroke-width={SW}
								stroke-dasharray="{paidLen} {CIRC}" transform="rotate(-90 100 100)" />
						{/if}
						{#if partialLen > 0}
							<circle cx="100" cy="100" r={R} fill="none" stroke="#2563eb" stroke-width={SW}
								stroke-dasharray="{partialLen} {CIRC}"
								stroke-dashoffset={-paidLen}
								transform="rotate(-90 100 100)" />
						{/if}
						{#if unpaidLen > 0}
							<circle cx="100" cy="100" r={R} fill="none" stroke="#dc2626" stroke-width={SW}
								stroke-dasharray="{unpaidLen} {CIRC}"
								stroke-dashoffset={-(paidLen + partialLen)}
								transform="rotate(-90 100 100)" />
						{/if}
					{/if}
					<text x="100" y="96" text-anchor="middle" class="donut-center-big">{grossIncome > 0 ? Math.round(collected / grossIncome * 100) : 0}%</text>
					<text x="100" y="113" text-anchor="middle" class="donut-center-small">tahsil edildi</text>
				</svg>
				<div class="donut-legend">
					<div><i class="dot green"></i><span>Tamamlandı</span><strong>{fmtTL(paidAmt)}</strong></div>
					<div><i class="dot blue"></i><span>Kısmi</span><strong>{fmtTL(partialAmt)}</strong></div>
					<div><i class="dot red"></i><span>Bekliyor</span><strong>{fmtTL(Math.max(unpaidAmt, 0))}</strong></div>
				</div>
			</div>
		</div>
	</div>

	<!-- ─── EXPENSE SECTION ────────────────────────────────────────────── -->
	<div class="section-head">
		<div>
			<h2>Giderler</h2>
			<p>{expenses.length} kayıt · {unpaidExpenses.length} ödenmemiş</p>
		</div>
		<button class="primary-btn" type="button" onclick={() => (showExpenseForm = true)}>+ Gider Ekle</button>
	</div>

	<!-- Unpaid list -->
	{#if unpaidExpenses.length > 0}
		<div class="panel">
			<p class="panel-subtitle">Ödenmemiş Giderler</p>
			<div class="expense-list">
				{#each unpaidExpenses as e}
					{@const st = expStatus(e)}
					<div class="expense-row" style="--status:{st.color}">
						<div class="exp-dot {st.dot}"></div>
						<div class="exp-main">
							<strong>{e.title}</strong>
							<div class="exp-tags">
								<span class="badge">{recurrenceLabel[e.recurrence]}</span>
								{#if e.event_title}<span class="badge blue">{e.event_title}</span>{/if}
								{#if !e.is_approved}<span class="badge purple">Onay bekliyor</span>{/if}
								{#if e.include_kdv}<span class="badge gray">KDV dahil</span>{/if}
							</div>
						</div>
						<div class="exp-amount">
							<strong>{fmt(toDisplay(e.amount, e.currency))}</strong>
							{#if e.currency !== 'TRY' && displayCurrency === 'TRY'}
								<small>{e.amount.toLocaleString('tr-TR')} {e.currency}</small>
							{/if}
						</div>
						<div class="exp-due">
							<span>{fmtDate(e.due_date)}</span>
							<span class="due-badge" style="color:{st.color}">{st.label}</span>
						</div>
						<div class="exp-actions">
							{#if !e.is_approved}
								<button class="act-btn green" onclick={() => approveExpense(e)} title="Onayla">✓ Onayla</button>
							{:else}
								<button class="act-btn green" onclick={() => markPaid(e)} title="Ödendi olarak işaretle">✓ Ödendi</button>
							{/if}
							<button class="act-btn red" onclick={() => deleteExpense(e)} title="Sil">✕</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- All expenses -->
	{#if expenses.filter(e => e.is_paid).length > 0}
		<div class="panel">
			<p class="panel-subtitle">Ödenmiş Giderler</p>
			<div class="expense-list">
				{#each expenses.filter(e => e.is_paid) as e}
					{@const st = expStatus(e)}
					<div class="expense-row paid">
						<div class="exp-dot green"></div>
						<div class="exp-main">
							<strong>{e.title}</strong>
							<div class="exp-tags">
								<span class="badge">{recurrenceLabel[e.recurrence]}</span>
								{#if e.event_title}<span class="badge blue">{e.event_title}</span>{/if}
							</div>
						</div>
						<div class="exp-amount">
							<strong>{fmt(toDisplay(e.amount, e.currency))}</strong>
						</div>
						<div class="exp-due">
							<span>{fmtDate(e.due_date)}</span>
							<span class="due-badge" style="color:#16a34a">Ödendi</span>
						</div>
						<div class="exp-actions">
							<button class="act-btn red" onclick={() => deleteExpense(e)} title="Sil">✕</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	{#if expenses.length === 0}
		<div class="panel empty-state">
			<p>Henüz gider kaydı yok.</p>
			<button class="primary-btn" type="button" onclick={() => (showExpenseForm = true)}>İlk gideri ekle</button>
		</div>
	{/if}

	<!-- ─── TOOLS ROW ───────────────────────────────────────────────────── -->
	<div class="tools-row">
		<!-- KDV Calculator -->
		<div class="panel tool-panel">
			<h2>KDV Hesaplayıcı</h2>
			<p class="muted">Oran: %{kdvRate}</p>
			<div class="kdv-mode">
				<button class:active={kdvMode === 'gross-to-net'} onclick={() => (kdvMode = 'gross-to-net')} type="button">KDV'li → KDV'siz</button>
				<button class:active={kdvMode === 'net-to-gross'} onclick={() => (kdvMode = 'net-to-gross')} type="button">KDV'siz → KDV'li</button>
			</div>
			<div class="tool-input-row">
				<input type="number" bind:value={kdvInput} min="0" placeholder="0" />
				<input type="number" bind:value={kdvRate} min="0" max="100" style="max-width:72px" />
				<span class="muted">%</span>
			</div>
			<div class="kdv-result">
				<div><span>Brüt (KDV dahil)</span><strong>₺{kdvCalcResult.gross.toLocaleString('tr-TR', {maximumFractionDigits: 2})}</strong></div>
				<div><span>Net (KDV hariç)</span><strong>₺{kdvCalcResult.net.toLocaleString('tr-TR', {maximumFractionDigits: 2})}</strong></div>
				<div class="kdv-line"><span>KDV Tutarı</span><strong style="color:#f59e0b">₺{kdvCalcResult.kdv.toLocaleString('tr-TR', {maximumFractionDigits: 2})}</strong></div>
			</div>
		</div>

		<!-- Currency Converter -->
		<div class="panel tool-panel">
			<h2>Döviz Çevirici</h2>
			{#if tryPerUSD_raw > 0}
				<p class="muted">$ {fmtRate(tryPerUSD_raw)} · € {fmtRate(tryPerEUR_raw)}</p>
			{:else}
				<p class="muted">Kur verisi yok</p>
			{/if}
			<div class="conv-row">
				<input type="number" bind:value={convAmount} min="0" placeholder="0" />
				<select bind:value={convFrom}>
					<option value="TRY">TRY ₺</option>
					<option value="USD">USD $</option>
					<option value="EUR">EUR €</option>
				</select>
				<span class="conv-arrow">→</span>
				<select bind:value={convTo}>
					<option value="TRY">TRY ₺</option>
					<option value="USD">USD $</option>
					<option value="EUR">EUR €</option>
				</select>
			</div>
			<div class="conv-result">
				<span>{convAmount.toLocaleString('tr-TR')} {convFrom}</span>
				<span class="conv-eq">=</span>
				<strong>{convResult.toLocaleString('tr-TR', {maximumFractionDigits: 2})} {convTo}</strong>
			</div>
			<div class="conv-rates">
				<span>1 $ = ₺{fmtRate(tryPerUSD)}</span>
				<span>·</span>
				<span>1 € = ₺{fmtRate(tryPerEUR)}</span>
				<span>·</span>
				<span>1 € = ${usdPerTRY > 0 ? fmtRate(eurPerTRY / usdPerTRY) : '—'}</span>
			</div>
		</div>
	</div>
</section>

<!-- ─── EXPENSE FORM MODAL ──────────────────────────────────────────────── -->
{#if showExpenseForm}
	<div class="modal-back" onclick={() => (showExpenseForm = false)} role="dialog" aria-modal="true" aria-label="Gider ekle">
		<div class="modal" onclick={(ev) => ev.stopPropagation()} role="document">
			<div class="modal-head">
				<h2>Yeni Gider</h2>
				<button class="close-btn" type="button" onclick={() => (showExpenseForm = false)}>✕</button>
			</div>

			<form onsubmit={saveExpense} class="expense-form">
				<label><span>Başlık *</span><input required bind:value={expenseForm.title} placeholder="Elektrik faturası" /></label>

				<div class="form-row">
					<label style="flex:1"><span>Tutar *</span><input type="number" required min="0" step="0.01" bind:value={expenseForm.amount} placeholder="0" /></label>
					<label style="width:110px"><span>Para Birimi</span>
						<select bind:value={expenseForm.currency}>
							<option value="TRY">₺ TRY</option>
							<option value="USD">$ USD</option>
							<option value="EUR">€ EUR</option>
						</select>
					</label>
				</div>

				<div class="form-group">
					<span>Tutar Tipi</span>
					<div class="btn-group">
						<button type="button" class:active={expenseForm.amount_type === 'fixed'} onclick={() => (expenseForm.amount_type = 'fixed')}>Sabit</button>
						<button type="button" class:active={expenseForm.amount_type === 'variable'} onclick={() => (expenseForm.amount_type = 'variable')}>Değişken</button>
					</div>
					{#if expenseForm.amount_type === 'variable'}
						<p class="warn-note">Değişken giderler onaylandıktan sonra işleme alınır.</p>
					{/if}
				</div>

				<div class="form-group">
					<span>Tekrarlama</span>
					<div class="btn-group wrap">
						{#each [['once','Tek seferlik'],['weekly','Haftalık'],['monthly','Aylık'],['yearly','Yıllık'],['custom','Özel']] as [val, lbl]}
							<button type="button" class:active={expenseForm.recurrence === val} onclick={() => (expenseForm.recurrence = val as typeof expenseForm.recurrence)}>{lbl}</button>
						{/each}
					</div>
					{#if expenseForm.recurrence === 'custom'}
						<label><span>Periyot (gün)</span><input type="number" min="1" bind:value={expenseForm.custom_period_days} /></label>
					{/if}
				</div>

				<label><span>Vade Tarihi *</span><input type="date" required bind:value={expenseForm.due_date} /></label>

				<label>
					<span>Bağlı Davet (opsiyonel)</span>
					<select bind:value={expenseForm.event_id}>
						<option value="">— Seçin —</option>
						{#each events as ev}
							<option value={ev.id}>{ev.title} · {ev.event_date}</option>
						{/each}
					</select>
				</label>

				<label class="checkbox-label">
					<input type="checkbox" bind:checked={expenseForm.include_kdv} />
					<span>Tutar KDV dahil</span>
				</label>

				<label><span>Not (opsiyonel)</span><textarea rows="2" bind:value={expenseForm.note} placeholder="Açıklama…"></textarea></label>

				<div class="modal-actions">
					<button class="primary-btn" type="submit" disabled={savingExpense}>{savingExpense ? 'Kaydediliyor…' : 'Kaydet'}</button>
					<button class="cancel-btn" type="button" onclick={() => (showExpenseForm = false)}>İptal</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.db-shell { max-width: 1560px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.25rem; }

	/* Header */
	.db-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
	.eyebrow { margin: 0 0 0.2rem; color: var(--accent); font-size: 0.78rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; }
	h1 { margin: 0; font-size: clamp(1.8rem, 3vw, 2.8rem); }
	h2 { margin: 0; font-size: 1.1rem; }
	p, h1, h2 { margin: 0; }
	.subtitle { color: var(--muted); margin-top: 0.2rem; }
	.header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 0.6rem; }
	.rate-box { display: flex; align-items: center; gap: 0.65rem; font-size: 0.84rem; }
	.rate-item { display: flex; align-items: center; gap: 0.3rem; }
	.rate-flag { font-size: 1rem; }
	.rate-sep { color: var(--line); }
	.rate-date { color: var(--muted); font-size: 0.75rem; }
	.currency-toggle { display: flex; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
	.currency-toggle button { padding: 0.45rem 0.85rem; font-weight: 800; font-size: 0.82rem; background: var(--surface-strong); color: var(--muted); border: none; cursor: pointer; transition: all 0.15s; }
	.currency-toggle button.active { background: var(--accent); color: #fff; }

	/* KPIs */
	.kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.85rem; }
	.kpi-card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 1.1rem; display: flex; flex-direction: column; gap: 0.4rem; box-shadow: 0 10px 24px rgba(0,0,0,0.1); }
	.kpi-card span { color: var(--muted); font-size: 0.82rem; font-weight: 800; }
	.kpi-card strong { font-size: clamp(1.4rem, 2.2vw, 2rem); line-height: 1.1; }
	.kpi-card small { font-size: 0.78rem; font-weight: 700; }
	.kpi-card.accent { background: linear-gradient(135deg, var(--accent-soft), var(--surface)); }
	.kpi-card.good { border-color: rgba(22,163,74,0.3); }
	.kpi-card.bad { border-color: rgba(220,38,38,0.3); background: rgba(220,38,38,0.04); }
	.kpi-card.warn { border-color: rgba(139,92,246,0.3); background: rgba(139,92,246,0.04); }
	.muted { color: var(--muted); }

	/* Charts */
	.charts-row { display: grid; grid-template-columns: 1fr 340px; gap: 1rem; }
	.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 1.1rem; box-shadow: 0 10px 24px rgba(0,0,0,0.1); }
	.chart-panel { min-width: 0; }
	.panel-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 0.85rem; gap: 1rem; }
	.panel-head p { color: var(--muted); font-size: 0.82rem; margin-top: 0.2rem; }
	.panel-subtitle { color: var(--muted); font-size: 0.75rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.75rem; }
	.legend { display: flex; gap: 0.85rem; align-items: center; flex-wrap: wrap; }
	.legend span { display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.82rem; font-weight: 800; color: var(--muted); }
	.dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
	.dot.green { background: #16a34a; }
	.dot.red { background: #dc2626; }
	.dot.blue { background: #2563eb; }
	.dot.orange { background: #f97316; }
	.dot.amber { background: #f59e0b; }
	.dot.purple { background: #8b5cf6; }
	.dot.gray { background: #64748b; }

	/* Bar chart */
	.bar-svg { width: 100%; height: auto; display: block; overflow: visible; }
	:global(.axis-label) { font-size: 10px; fill: var(--muted); font-family: Inter, sans-serif; }
	:global(.donut-center-big) { font-size: 22px; font-weight: 900; fill: var(--text); font-family: Inter, sans-serif; }
	:global(.donut-center-small) { font-size: 10px; fill: var(--muted); font-family: Inter, sans-serif; }

	/* Donut */
	.donut-panel { display: flex; flex-direction: column; }
	.donut-wrap { display: flex; flex-direction: column; align-items: center; gap: 1rem; }
	.donut-svg { width: 160px; height: 160px; }
	.donut-legend { width: 100%; display: flex; flex-direction: column; gap: 0.5rem; }
	.donut-legend div { display: flex; align-items: center; gap: 0.5rem; font-size: 0.82rem; }
	.donut-legend span { color: var(--muted); flex: 1; }
	.donut-legend strong { font-size: 0.88rem; }

	/* Section head */
	.section-head { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
	.section-head h2 { font-size: 1.25rem; }
	.section-head p { color: var(--muted); font-size: 0.82rem; margin-top: 0.15rem; }
	.primary-btn { background: var(--accent); color: #fff; border: none; border-radius: 8px; padding: 0.7rem 1.1rem; font-weight: 900; font-size: 0.88rem; cursor: pointer; white-space: nowrap; }
	.primary-btn:disabled { opacity: 0.6; cursor: not-allowed; }

	/* Expense list */
	.expense-list { display: flex; flex-direction: column; gap: 0.55rem; }
	.expense-row { display: grid; grid-template-columns: 14px 1fr auto auto auto; align-items: center; gap: 0.85rem; padding: 0.85rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; transition: border-color 0.15s; }
	.expense-row:hover { border-color: color-mix(in srgb, var(--accent) 30%, transparent); }
	.expense-row.paid { opacity: 0.6; }
	.exp-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--status); flex-shrink: 0; }
	.exp-dot.green { background: #16a34a; }
	.exp-dot.red { background: #dc2626; }
	.exp-dot.orange { background: #f97316; }
	.exp-dot.amber { background: #f59e0b; }
	.exp-dot.purple { background: #8b5cf6; }
	.exp-dot.gray { background: #64748b; }
	.exp-main { min-width: 0; display: flex; flex-direction: column; gap: 0.3rem; }
	.exp-main strong { font-size: 0.92rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.exp-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; }
	.badge { font-size: 0.7rem; font-weight: 800; padding: 0.15rem 0.45rem; border-radius: 99px; background: var(--muted-surface); color: var(--muted); }
	.badge.blue { background: rgba(37,99,235,0.12); color: #2563eb; }
	.badge.purple { background: rgba(139,92,246,0.12); color: #8b5cf6; }
	.badge.gray { background: var(--muted-surface); color: var(--muted); }
	.exp-amount { text-align: right; min-width: 90px; }
	.exp-amount strong { font-size: 0.96rem; }
	.exp-amount small { display: block; color: var(--muted); font-size: 0.72rem; }
	.exp-due { text-align: right; min-width: 100px; font-size: 0.78rem; display: flex; flex-direction: column; gap: 0.15rem; }
	.exp-due span { color: var(--muted); }
	.due-badge { font-weight: 900; }
	.exp-actions { display: flex; gap: 0.4rem; }
	.act-btn { border: none; border-radius: 7px; padding: 0.35rem 0.65rem; font-weight: 800; font-size: 0.76rem; cursor: pointer; transition: opacity 0.15s; }
	.act-btn:hover { opacity: 0.8; }
	.act-btn.green { background: rgba(22,163,74,0.12); color: #16a34a; }
	.act-btn.red { background: rgba(220,38,38,0.1); color: #dc2626; }

	/* Empty */
	.empty-state { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 2.5rem; text-align: center; color: var(--muted); }

	/* Tools */
	.tools-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
	.tool-panel { display: flex; flex-direction: column; gap: 0.85rem; }
	.tool-panel h2 { font-size: 1.05rem; }
	.kdv-mode { display: flex; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; width: fit-content; }
	.kdv-mode button { padding: 0.4rem 0.85rem; font-weight: 800; font-size: 0.8rem; background: var(--surface-strong); color: var(--muted); border: none; cursor: pointer; transition: all 0.15s; }
	.kdv-mode button.active { background: var(--accent); color: #fff; }
	.tool-input-row { display: flex; align-items: center; gap: 0.5rem; }
	.kdv-result { display: flex; flex-direction: column; gap: 0.55rem; }
	.kdv-result div { display: flex; justify-content: space-between; align-items: center; padding: 0.65rem 0.85rem; background: var(--surface-strong); border-radius: 7px; font-size: 0.88rem; }
	.kdv-result span { color: var(--muted); }
	.kdv-line { border-top: 1px solid var(--line); }
	.conv-row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
	.conv-arrow { color: var(--muted); font-size: 1.1rem; }
	.conv-result { display: flex; align-items: center; gap: 0.75rem; background: var(--surface-strong); border-radius: 8px; padding: 0.85rem 1rem; }
	.conv-eq { color: var(--muted); font-size: 1.1rem; }
	.conv-result strong { font-size: 1.3rem; color: var(--accent); }
	.conv-result span:first-child { color: var(--muted); }
	.conv-rates { display: flex; gap: 0.5rem; font-size: 0.76rem; color: var(--muted); flex-wrap: wrap; }

	/* Shared inputs */
	input[type="number"], input[type="text"], input[type="date"], select, textarea {
		width: 100%; min-height: 38px; border: 1px solid var(--line); border-radius: 7px;
		padding: 0.45rem 0.7rem; background: var(--surface-strong); color: var(--text); font: inherit; font-size: 0.9rem;
	}
	select { cursor: pointer; }

	/* Modal */
	.modal-back { position: fixed; inset: 0; background: rgba(0,0,0,0.65); display: flex; align-items: center; justify-content: center; z-index: 50; padding: 1rem; backdrop-filter: blur(4px); }
	.modal { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; width: 100%; max-width: 520px; max-height: 92vh; overflow-y: auto; padding: 1.5rem; box-shadow: 0 40px 80px rgba(0,0,0,0.4); }
	.modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; }
	.close-btn { background: var(--surface-strong); border: 1px solid var(--line); border-radius: 7px; width: 32px; height: 32px; cursor: pointer; font-size: 0.9rem; color: var(--muted); }
	.expense-form { display: flex; flex-direction: column; gap: 0.85rem; }
	.expense-form label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; font-size: 0.84rem; color: var(--muted); }
	.form-row { display: flex; gap: 0.65rem; }
	.form-group { display: flex; flex-direction: column; gap: 0.45rem; }
	.form-group > span { font-size: 0.84rem; font-weight: 800; color: var(--muted); }
	.btn-group { display: flex; flex-wrap: wrap; gap: 0.4rem; }
	.btn-group button { padding: 0.4rem 0.85rem; border: 1px solid var(--line); border-radius: 7px; background: var(--surface-strong); color: var(--muted); font-weight: 800; font-size: 0.82rem; cursor: pointer; transition: all 0.15s; }
	.btn-group button.active { border-color: var(--accent); background: var(--accent-soft); color: var(--text); }
	.btn-group.wrap { flex-wrap: wrap; }
	.warn-note { font-size: 0.78rem; color: #8b5cf6; font-weight: 700; margin: 0; }
	.checkbox-label { flex-direction: row !important; align-items: center; gap: 0.5rem !important; }
	.checkbox-label input { width: auto; min-height: auto; }
	.modal-actions { display: flex; gap: 0.65rem; padding-top: 0.5rem; }
	.cancel-btn { background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; padding: 0.7rem 1.1rem; font-weight: 800; font-size: 0.88rem; cursor: pointer; color: var(--muted); }

	/* Responsive */
	@media (max-width: 1200px) {
		.kpi-grid { grid-template-columns: repeat(4, 1fr); }
		.charts-row { grid-template-columns: 1fr; }
		.donut-wrap { flex-direction: row; justify-content: center; }
	}
	@media (max-width: 900px) {
		.kpi-grid { grid-template-columns: repeat(2, 1fr); }
		.tools-row { grid-template-columns: 1fr; }
	}
	@media (max-width: 640px) {
		.kpi-grid { grid-template-columns: 1fr 1fr; }
		.expense-row { grid-template-columns: 14px 1fr auto; }
		.exp-due, .exp-actions { grid-column: 3; }
		.expense-row { grid-template-columns: 14px 1fr; }
		.exp-amount, .exp-due, .exp-actions { grid-column: 2; }
	}
</style>
