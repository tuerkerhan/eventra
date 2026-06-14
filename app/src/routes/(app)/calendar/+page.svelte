<script lang="ts">
	import { onMount } from 'svelte';
	import { fly, fade } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import { api, PORTAL_URL, type EventApi, type EventTypeApi, type VenueLayoutApi, type EventFormFieldDefApi, type CustomerFormTypeApi } from '$lib/api';

	type CalendarView = 'Günlük' | 'Haftalık' | 'Aylık' | 'Yıllık';

	const HOUR_H = 64;
	const TSTART = 8;
	const TEND = 25;
	const TIMELINE_H = (TEND - TSTART) * HOUR_H;
	const HOURS_ARR = Array.from({ length: TEND - TSTART + 1 }, (_, i) => TSTART + i);
	const HALF_H = Array.from({ length: (TEND - TSTART) * 2 }, (_, i) => TSTART * 60 + (i + 1) * 30).filter((m) => m % 60 !== 0);

	const pad = (v: number) => v.toString().padStart(2, '0');
	const dateKey = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
	const timeToMins = (t: string): number => {
		if (!t) return TSTART * 60;
		const [h, m] = t.split(':').map(Number);
		let total = h * 60 + (m || 0);
		if (total < TSTART * 60) total += 24 * 60;
		return total;
	};
	const minsToY = (mins: number) => ((mins - TSTART * 60) / 60) * HOUR_H;
	const minsToTime = (m: number) => `${pad(Math.floor(m / 60) % 24)}:${pad(m % 60)}`;
	const getWeekStart = (d: Date): Date => {
		const offset = (d.getDay() + 6) % 7;
		const s = new Date(d);
		s.setDate(d.getDate() - offset);
		s.setHours(0, 0, 0, 0);
		return s;
	};

	// ── State ────────────────────────────────────────────────────────────────────
	let activeView = $state<CalendarView>('Aylık');
	let currentDate = $state(new Date());
	let weekStart = $state(getWeekStart(new Date()));
	let selectedEventId = $state<string | null>(null);
	let clickedDate = $state(dateKey(new Date()));
	let newTypeName = $state('');
	let newTypeColor = $state('#64748b');
	let activeTab = $state<'genel' | 'portal'>('genel');
	let savingEvent = $state(false);
	let portalCopied = $state(false);

	// API data
	let events = $state<EventApi[]>([]);
	let eventTypes = $state<EventTypeApi[]>([]);
	let layouts = $state<VenueLayoutApi[]>([]);
	let formFieldDefs = $state<EventFormFieldDefApi[]>([]);
	let customerFormTypes = $state<CustomerFormTypeApi[]>([]);
	let loadError = $state('');

	let timelineRef: HTMLDivElement;
	let weekScrollRef: HTMLDivElement;
	let titleInputRef: HTMLInputElement | undefined = $state();

	// ── Day-view: create drag ────────────────────────────────────────────────────
	let tlDragging = false;
	let tlDragStartMins: number | null = null;
	let dragSelStart = $state<number | null>(null);
	let dragSelEnd = $state<number | null>(null);

	// ── Day-view: event move drag ────────────────────────────────────────────────
	let evMoving = false;
	let evMoveId: string | null = null;
	let evMoveDur = 0;
	let evMoveOffset = 0;
	let evMoveMoved = false;
	let evMovePreview = $state<number | null>(null);

	// ── Weekly-view: create drag (per column) ───────────────────────────────────
	let wkCreating = false;
	let wkCreateStartMins: number | null = null;
	let wkDragSelStart = $state<number | null>(null);
	let wkDragSelEnd = $state<number | null>(null);
	let wkDragDayKey = $state<string | null>(null);

	// ── Weekly-view: event move drag ─────────────────────────────────────────────
	let wkEvMoving = false;
	let wkEvMoveId: string | null = null;
	let wkEvMoveDur = 0;
	let wkEvMoveOffset = 0;
	let wkEvMoveMoved = false;
	let wkEvMovePreview = $state<number | null>(null);

	// ── Holidays ─────────────────────────────────────────────────────────────────
	const officialHolidays = [
		{ date: '2026-01-01', label: 'Yılbaşı' }, { date: '2026-04-23', label: '23 Nisan' },
		{ date: '2026-05-01', label: 'Emek ve Dayanışma' }, { date: '2026-05-19', label: '19 Mayıs' },
		{ date: '2026-07-15', label: '15 Temmuz' }, { date: '2026-08-30', label: 'Zafer Bayramı' },
		{ date: '2026-10-29', label: 'Cumhuriyet Bayramı' }
	];

	// ── Helpers ──────────────────────────────────────────────────────────────────
	const typeColor = (typeId: string | null) => eventTypes.find(t => t.id === typeId)?.color ?? '#64748b';
	const typeName = (typeId: string | null) => eventTypes.find(t => t.id === typeId)?.name ?? '';
	const formatMoney = (v: number) => `₺${Math.round(v).toLocaleString('tr-TR')}`;
	const holidayForDay = (d: Date) => officialHolidays.find((h) => h.date === dateKey(d));
	const eventsForDay = (d: Date) => events.filter((e) => e.event_date === dateKey(d));

	// ── Derived ──────────────────────────────────────────────────────────────────
	const selectedEvent = $derived(events.find((e) => e.id === selectedEventId) ?? null);
	const hiddenBuiltins = $derived(new Set(
		formFieldDefs.filter(f => f.is_builtin && !f.is_visible).map(f => f.key)
	));
	const visibleCustomDefs = $derived(formFieldDefs.filter(f => !f.is_builtin && f.is_visible));
	const mergedCustomFields = $derived.by(() => {
		if (!selectedEvent) return [];
		return visibleCustomDefs.map(def => {
			const existing = selectedEvent.custom_fields.find(f => f.key === def.key);
			return existing ?? { key: def.key, label: def.label, value: def.field_type === 'checkbox' ? 'false' : '', field_type: def.field_type, options: def.options, sort_order: def.sort_order };
		});
	});
	const dayViewEvents = $derived(eventsForDay(new Date(clickedDate)));
	const dayViewLayout = $derived(computeOverlapLayout(dayViewEvents));
	const monthEvents = (mi: number) => events.filter((e) => Number(e.event_date.slice(5, 7)) === mi + 1);
	const isToday = (dateStr: string) => dateStr === dateKey(new Date());
	const monthLabel = () => currentDate.toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' });
	const portalLink = (ev: EventApi) => ev.portal_token ? `${PORTAL_URL}/${ev.portal_token}` : '';

	const paymentColor = (ev: EventApi) => {
		if (ev.payment_complete) return '#16a34a';
		if (ev.total_paid > 0 && ev.total_paid < ev.total_fee) return '#2563eb';
		if (ev.total_paid === 0) return '#f59e0b';
		return '#dc2626';
	};
	const paymentLabel = (ev: EventApi) => {
		if (ev.payment_complete) return 'Tamamlandı';
		if (ev.total_paid > 0 && ev.total_paid < ev.total_fee) return 'Kısmi';
		if (ev.total_paid === 0) return 'Bekliyor';
		return 'Kapora';
	};

	const weekLabel = () => {
		const days = weekDays7();
		const f = days[0]; const l = days[6];
		if (f.getMonth() === l.getMonth())
			return `${f.getDate()}–${l.getDate()} ${f.toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' })}`;
		return `${f.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })} – ${l.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}`;
	};
	const calendarDays = () => {
		const first = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
		const offset = (first.getDay() + 6) % 7;
		const start = new Date(first);
		start.setDate(first.getDate() - offset);
		return Array.from({ length: 42 }, (_, i) => {
			const d = new Date(start); d.setDate(start.getDate() + i); return d;
		});
	};
	const weekDays7 = () => Array.from({ length: 7 }, (_, i) => {
		const d = new Date(weekStart); d.setDate(weekStart.getDate() + i); return d;
	});
	const yearMonths = () => Array.from({ length: 12 }, (_, i) => new Date(currentDate.getFullYear(), i, 1));
	const weekDayNames = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];

	const getNowY = () => {
		const now = new Date();
		let mins = now.getHours() * 60 + now.getMinutes();
		if (mins < TSTART * 60) mins += 24 * 60;
		return minsToY(mins);
	};

	// ── Overlap layout ───────────────────────────────────────────────────────────
	function computeOverlapLayout(evList: EventApi[]): Map<string, { col: number; total: number }> {
		if (evList.length === 0) return new Map();
		const sorted = [...evList].sort((a, b) => timeToMins(a.start_time) - timeToMins(b.start_time));
		const colEnds: number[] = [];
		const assigned: number[] = [];
		for (const ev of sorted) {
			const s = timeToMins(ev.start_time);
			const e = timeToMins(ev.end_time);
			let c = colEnds.findIndex(ce => ce <= s);
			if (c === -1) c = colEnds.length;
			colEnds[c] = e;
			assigned.push(c);
		}
		const result = new Map<string, { col: number; total: number }>();
		for (let i = 0; i < sorted.length; i++) {
			const s = timeToMins(sorted[i].start_time);
			const e = timeToMins(sorted[i].end_time);
			let maxC = assigned[i];
			for (let j = 0; j < sorted.length; j++) {
				if (i === j) continue;
				const os = timeToMins(sorted[j].start_time);
				const oe = timeToMins(sorted[j].end_time);
				if (s < oe && e > os) maxC = Math.max(maxC, assigned[j]);
			}
			result.set(sorted[i].id, { col: assigned[i], total: maxC + 1 });
		}
		return result;
	}

	// ── Coordinate helper ────────────────────────────────────────────────────────
	const refToMins = (ref: HTMLDivElement, clientY: number): number => {
		const rect = ref.getBoundingClientRect();
		const y = clientY - rect.top + ref.scrollTop;
		const raw = TSTART * 60 + (y / HOUR_H) * 60;
		return Math.max(TSTART * 60, Math.min(TEND * 60, Math.round(raw / 15) * 15));
	};

	// ── PATCH payload builder ────────────────────────────────────────────────────
	function buildPayload(ev: EventApi) {
		return {
			title: ev.title, event_date: ev.event_date, contract_date: ev.contract_date,
			start_time: ev.start_time, end_time: ev.end_time, type_id: ev.type_id,
			reservation_status: ev.reservation_status, tc_no: ev.tc_no,
			full_name: ev.full_name, mobile_phone: ev.mobile_phone, phone: ev.phone,
			bride_groom: ev.bride_groom, region: ev.region, address: ev.address,
			guest_count: ev.guest_count, total_fee: ev.total_fee,
			kapora_amount: ev.kapora_amount, kapora_paid: ev.kapora_paid,
			total_paid: ev.total_paid, payment_complete: ev.payment_complete,
			note: ev.note, reminder_enabled: ev.reminder_enabled,
			reminder_date: ev.reminder_date, staff: ev.staff, customer_id: ev.customer_id,
			layout_id: ev.layout_id, seating_enabled: ev.seating_enabled,
			portal_enabled: ev.portal_enabled, portal_org_type_id: ev.portal_org_type_id,
			portal_form_type_id: ev.portal_form_type_id,
			portal_layout_permission: ev.portal_layout_permission,
			reserved_layout_ids: ev.reserved_layout_ids, custom_fields: ev.custom_fields
		};
	}

	function focusTitleInput() {
		setTimeout(() => titleInputRef?.focus(), 50);
	}

	// ── Mount ────────────────────────────────────────────────────────────────────
	onMount(async () => {
		try {
			const [evs, types, lyts, ffdefs, cfTypes] = await Promise.all([
				api.get<EventApi[]>('/events'),
				api.get<EventTypeApi[]>('/events/types'),
				api.get<VenueLayoutApi[]>('/venue/layouts'),
				api.get<EventFormFieldDefApi[]>('/event-form-fields'),
				api.get<CustomerFormTypeApi[]>('/customer-forms/types')
			]);
			events = evs;
			eventTypes = types;
			layouts = lyts;
			formFieldDefs = ffdefs;
			customerFormTypes = cfTypes;
		} catch (e) {
			loadError = e instanceof Error ? e.message : 'Veri yükleme hatası';
		}
	});

	// ── Navigation ───────────────────────────────────────────────────────────────
	const moveMonth = (step: number) => { currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + step, 1); };
	const moveYear = (step: number) => { currentDate = new Date(currentDate.getFullYear() + step, currentDate.getMonth(), 1); };
	const moveWeek = (step: number) => { const d = new Date(weekStart); d.setDate(d.getDate() + step * 7); weekStart = d; };
	const moveDay = (step: number) => { const d = new Date(clickedDate + 'T12:00:00'); d.setDate(d.getDate() + step); clickedDate = dateKey(d); };
	const navigate = (step: number) => {
		if (activeView === 'Yıllık') moveYear(step);
		else if (activeView === 'Haftalık') moveWeek(step);
		else if (activeView === 'Günlük') moveDay(step);
		else moveMonth(step);
	};
	const goToday = () => { const t = new Date(); currentDate = new Date(t.getFullYear(), t.getMonth(), 1); clickedDate = dateKey(t); weekStart = getWeekStart(t); };
	const selectEvent = (id: string) => { selectedEventId = id; };

	// ── Event CRUD ───────────────────────────────────────────────────────────────
	async function addReservation() {
		try {
			const ev = await api.post<EventApi>('/events', {
				title: '', event_date: clickedDate,
				start_time: '19:00', end_time: '23:00',
				type_id: eventTypes[0]?.id ?? null,
				reservation_status: 'Ön Rezervasyon'
			});
			events = [...events, ev];
			selectedEventId = ev.id;
			focusTitleInput();
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Hata');
		}
	}

	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	function scheduleAutoSave() {
		if (saveTimeout) clearTimeout(saveTimeout);
		saveTimeout = setTimeout(doSave, 800);
	}

	async function doSave() {
		if (!selectedEvent) return;
		savingEvent = true;
		try {
			const updated = await api.patch<EventApi>(`/events/${selectedEvent.id}`, buildPayload(selectedEvent));
			events = events.map(e => e.id === updated.id ? updated : e);
		} catch {
			// silent fail on auto-save
		} finally {
			savingEvent = false;
		}
	}

	function updateSelected<K extends keyof EventApi>(key: K, value: EventApi[K]) {
		if (!selectedEventId) return;
		events = events.map(e => {
			if (e.id !== selectedEventId) return e;
			const updated = { ...e, [key]: value };
			if (key === 'event_date') currentDate = new Date(`${value as string}T12:00:00`);
			if ((key === 'total_paid' || key === 'total_fee') && Number(updated.total_fee) > 0 && Number(updated.total_paid) >= Number(updated.total_fee)) {
				updated.payment_complete = true;
			}
			return updated;
		});
		scheduleAutoSave();
	}

	function updateCustomField(fieldKey: string, value: string) {
		if (!selectedEventId) return;
		events = events.map(e => {
			if (e.id !== selectedEventId) return e;
			const existing = e.custom_fields.find(f => f.key === fieldKey);
			if (existing) {
				return { ...e, custom_fields: e.custom_fields.map(f => f.key === fieldKey ? { ...f, value } : f) };
			}
			const def = formFieldDefs.find(d => d.key === fieldKey);
			return { ...e, custom_fields: [...e.custom_fields, {
				key: fieldKey, label: def?.label ?? fieldKey, value,
				field_type: def?.field_type ?? 'text', options: def?.options ?? [], sort_order: def?.sort_order ?? 0
			}]};
		});
		scheduleAutoSave();
	}

	function closePanel() {
		selectedEventId = null;
	}

	async function deleteEvent() {
		if (!selectedEventId || !confirm('Bu daveti sil?')) return;
		await api.del(`/events/${selectedEventId}`);
		events = events.filter(e => e.id !== selectedEventId);
		selectedEventId = null;
	}

	async function addEventType() {
		const name = newTypeName.trim();
		if (!name || eventTypes.some(t => t.name === name)) return;
		const t = await api.post<EventTypeApi>('/events/types', { name, color: newTypeColor });
		eventTypes = [...eventTypes, t];
		newTypeName = ''; newTypeColor = '#64748b';
	}

	function copyPortalLink() {
		const link = selectedEvent ? portalLink(selectedEvent) : '';
		if (!link) return;
		navigator.clipboard.writeText(link).then(() => {
			portalCopied = true;
			setTimeout(() => (portalCopied = false), 2000);
		});
	}

	// ── Day-view: create drag handlers ───────────────────────────────────────────
	const onTimelineDown = (e: PointerEvent) => {
		const target = e.target as HTMLElement;
		if (target.closest('.day-ev')) return;
		tlDragging = true;
		tlDragStartMins = refToMins(timelineRef, e.clientY);
		dragSelStart = tlDragStartMins;
		dragSelEnd = tlDragStartMins + 60;
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
	};
	const onTimelineMove = (e: PointerEvent) => {
		if (!tlDragging || tlDragStartMins === null) return;
		const m = refToMins(timelineRef, e.clientY);
		if (m > tlDragStartMins) { dragSelEnd = m; dragSelStart = tlDragStartMins; }
		else { dragSelStart = m; dragSelEnd = tlDragStartMins; }
	};
	const onTimelineUp = async () => {
		if (tlDragging && dragSelStart !== null && dragSelEnd !== null && dragSelEnd - dragSelStart >= 15) {
			try {
				const ev = await api.post<EventApi>('/events', {
					title: '', event_date: clickedDate,
					start_time: minsToTime(dragSelStart), end_time: minsToTime(dragSelEnd),
					type_id: eventTypes[0]?.id ?? null,
					reservation_status: 'Ön Rezervasyon'
				});
				events = [...events, ev];
				selectedEventId = ev.id;
				focusTitleInput();
			} catch {}
		}
		tlDragging = false; tlDragStartMins = null; dragSelStart = null; dragSelEnd = null;
	};

	// ── Day-view: event move drag handlers ───────────────────────────────────────
	const onEvDayDown = (e: PointerEvent, ev: EventApi) => {
		e.stopPropagation();
		evMoving = true;
		evMoveId = ev.id;
		evMoveDur = timeToMins(ev.end_time) - timeToMins(ev.start_time);
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		evMoveOffset = ((e.clientY - rect.top) / HOUR_H) * 60;
		evMovePreview = timeToMins(ev.start_time);
		evMoveMoved = false;
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
	};
	const onEvDayMove = (e: PointerEvent) => {
		if (!evMoving) return;
		evMoveMoved = true;
		const m = refToMins(timelineRef, e.clientY);
		evMovePreview = Math.max(TSTART * 60, Math.min((TEND - 1) * 60, Math.round((m - evMoveOffset) / 15) * 15));
	};
	const onEvDayUp = async (ev: EventApi) => {
		if (evMoving) {
			if (evMoveMoved && evMovePreview !== null) {
				const cur = events.find(e => e.id === ev.id);
				if (cur) {
					const ns = minsToTime(evMovePreview);
					const ne = minsToTime(evMovePreview + evMoveDur);
					events = events.map(e => e.id === ev.id ? { ...e, start_time: ns, end_time: ne } : e);
					try {
						const upd = await api.patch<EventApi>(`/events/${ev.id}`, { ...buildPayload(cur), start_time: ns, end_time: ne });
						events = events.map(e => e.id === upd.id ? upd : e);
					} catch {}
				}
			} else if (!evMoveMoved) {
				selectedEventId = ev.id;
			}
		}
		evMoving = false; evMoveId = null; evMovePreview = null; evMoveMoved = false;
	};

	// ── Weekly-view: create drag handlers (per column) ───────────────────────────
	const onWcolDown = (e: PointerEvent, day: Date) => {
		if ((e.target as HTMLElement).closest('.wk-ev')) return;
		wkCreating = true;
		wkDragDayKey = dateKey(day);
		wkCreateStartMins = refToMins(weekScrollRef, e.clientY);
		wkDragSelStart = wkCreateStartMins;
		wkDragSelEnd = wkCreateStartMins + 60;
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
	};
	const onWcolMove = (e: PointerEvent) => {
		if (!wkCreating || wkCreateStartMins === null) return;
		const m = refToMins(weekScrollRef, e.clientY);
		if (m > wkCreateStartMins) { wkDragSelEnd = m; wkDragSelStart = wkCreateStartMins; }
		else { wkDragSelStart = m; wkDragSelEnd = wkCreateStartMins; }
	};
	const onWcolUp = async (day: Date) => {
		if (wkCreating && wkDragSelStart !== null && wkDragSelEnd !== null && wkDragSelEnd - wkDragSelStart >= 15) {
			const dk = dateKey(day);
			clickedDate = dk;
			try {
				const ev = await api.post<EventApi>('/events', {
					title: '', event_date: dk,
					start_time: minsToTime(wkDragSelStart), end_time: minsToTime(wkDragSelEnd),
					type_id: eventTypes[0]?.id ?? null,
					reservation_status: 'Ön Rezervasyon'
				});
				events = [...events, ev];
				selectedEventId = ev.id;
				focusTitleInput();
			} catch {}
		}
		wkCreating = false; wkCreateStartMins = null;
		wkDragSelStart = null; wkDragSelEnd = null; wkDragDayKey = null;
	};

	// ── Weekly-view: event move drag handlers ────────────────────────────────────
	const onWkEvDown = (e: PointerEvent, ev: EventApi) => {
		e.stopPropagation();
		wkEvMoving = true;
		wkEvMoveId = ev.id;
		wkEvMoveDur = timeToMins(ev.end_time) - timeToMins(ev.start_time);
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		wkEvMoveOffset = ((e.clientY - rect.top) / HOUR_H) * 60;
		wkEvMovePreview = timeToMins(ev.start_time);
		wkEvMoveMoved = false;
		(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
	};
	const onWkEvMove = (e: PointerEvent) => {
		if (!wkEvMoving) return;
		wkEvMoveMoved = true;
		const m = refToMins(weekScrollRef, e.clientY);
		wkEvMovePreview = Math.max(TSTART * 60, Math.min((TEND - 1) * 60, Math.round((m - wkEvMoveOffset) / 15) * 15));
	};
	const onWkEvUp = async (ev: EventApi) => {
		if (wkEvMoving) {
			if (wkEvMoveMoved && wkEvMovePreview !== null) {
				const cur = events.find(e => e.id === ev.id);
				if (cur) {
					const ns = minsToTime(wkEvMovePreview);
					const ne = minsToTime(wkEvMovePreview + wkEvMoveDur);
					events = events.map(e => e.id === ev.id ? { ...e, start_time: ns, end_time: ne } : e);
					try {
						const upd = await api.patch<EventApi>(`/events/${ev.id}`, { ...buildPayload(cur), start_time: ns, end_time: ne });
						events = events.map(e => e.id === upd.id ? upd : e);
					} catch {}
				}
			} else if (!wkEvMoveMoved) {
				selectedEventId = ev.id;
			}
		}
		wkEvMoving = false; wkEvMoveId = null; wkEvMovePreview = null; wkEvMoveMoved = false;
	};
</script>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape' && selectedEvent) closePanel(); }} />

<section class="calendar-shell">
	{#if loadError}
		<div class="error-bar">{loadError}</div>
	{/if}

	<div class="page-heading">
		<div>
			<p class="eyebrow">Takvim</p>
			<h1>{monthLabel()}</h1>
		</div>
		<div class="view-switch">
			{#each ['Günlük', 'Haftalık', 'Aylık', 'Yıllık'] as view}
				<button class:active={activeView === view} type="button"
					onclick={() => (activeView = view as CalendarView)}>{view}</button>
			{/each}
		</div>
	</div>

	<div class="calendar-toolbar">
		<button type="button" onclick={() => navigate(-1)}>‹</button>
		<strong class="tbl-label">
			{#if activeView === 'Yıllık'}{currentDate.getFullYear()}
			{:else if activeView === 'Haftalık'}{weekLabel()}
			{:else if activeView === 'Günlük'}{new Date(clickedDate + 'T12:00:00').toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' })}
			{:else}{monthLabel()}{/if}
		</strong>
		<button type="button" onclick={() => navigate(1)}>›</button>
		<button type="button" onclick={goToday}>Bugün</button>
		<span class="selected-date-label">{new Date(clickedDate + 'T12:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' })}</span>
		{#if savingEvent}<span class="saving-indicator">Kaydediliyor…</span>{/if}
		<button class="primary" type="button" onclick={addReservation}>+ Yeni Davet</button>
	</div>

	<div class="type-legend-bar">
		{#each eventTypes as t}
			<span class="legend-chip" style="--c:{t.color}">{t.name}</span>
		{/each}
		<label class="legend-add">
			<input class="legend-type-input" placeholder="+ Tip ekle…" bind:value={newTypeName} onkeydown={(e) => e.key === 'Enter' && addEventType()} />
			<input class="color-input" type="color" bind:value={newTypeColor} title="Renk" />
			{#if newTypeName.trim()}<button type="button" class="legend-add-btn" onclick={addEventType}>Ekle</button>{/if}
		</label>
	</div>

	<section class="calendar-panel">
			{#if activeView === 'Aylık'}
				<div class="weekday-row">{#each weekDayNames as d}<span>{d}</span>{/each}</div>
				<div class="month-grid">
					{#each calendarDays() as day}
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div class="day-cell"
							class:muted-day={day.getMonth() !== currentDate.getMonth()}
							class:selected-day={dateKey(day) === clickedDate}
							class:today-day={isToday(dateKey(day))}
							onclick={() => (clickedDate = dateKey(day))}
							onkeydown={(e) => e.key === 'Enter' && (clickedDate = dateKey(day))}
							role="button" tabindex="0">
							<div class="day-top">
								<strong>{day.getDate()}</strong>
								{#if holidayForDay(day)}<small class="holiday">{holidayForDay(day)?.label}</small>{/if}
							</div>
							{#each eventsForDay(day) as item}
								<button class="event-chip" style="--pay:{paymentColor(item)};--type:{typeColor(item.type_id)}"
									type="button" onclick={(e) => { e.stopPropagation(); selectEvent(item.id); }}>
									<span class="chip-time">{item.start_time}</span>
									{item.title}
									<span class="chip-ticks">
										{#if item.kapora_paid}<span class="tick tick-k">K✓</span>{/if}
										{#if item.payment_complete}<span class="tick tick-p">₺✓</span>{/if}
										{#if item.portal_enabled}<span class="tick tick-portal">P</span>{/if}
									</span>
								</button>
							{/each}
						</div>
					{/each}
				</div>

			{:else if activeView === 'Haftalık'}
				<div class="week-view">
					<div class="wk-header-row">
						<div class="tgutter"></div>
						{#each weekDays7() as day}
							<button class="wcol-head" class:today={isToday(dateKey(day))} class:wk-selected={dateKey(day) === clickedDate}
								type="button" onclick={() => { clickedDate = dateKey(day); }}>
								<span class="wday-name">{day.toLocaleDateString('tr-TR', { weekday: 'short' })}</span>
								<strong class="wday-num">{day.getDate()}</strong>
								{#if eventsForDay(day).length > 0}
									<span class="wday-badge">{eventsForDay(day).length}</span>
								{/if}
							</button>
						{/each}
					</div>
					<div class="wk-scroll" bind:this={weekScrollRef}>
						<div class="wk-body" style="height:{TIMELINE_H}px">
							{#each HOURS_ARR as hour}
								<div class="tl-label" style="top:{minsToY(hour * 60) - 9}px">{pad(hour % 24)}:00</div>
								<div class="tl-line" style="top:{minsToY(hour * 60)}px; left:56px; right:0"></div>
							{/each}
							{#each HALF_H as m}
								<div class="tl-half" style="top:{minsToY(m)}px; left:56px; right:0"></div>
							{/each}
							<div class="wcols" style="left:56px; right:0; top:0; height:{TIMELINE_H}px">
								{#each weekDays7() as day}
									{@const dayEvs = eventsForDay(day)}
									{@const colLayout = computeOverlapLayout(dayEvs)}
									<!-- svelte-ignore a11y_no_static_element_interactions -->
									<div class="wcol"
										class:today={isToday(dateKey(day))}
										class:wk-selected={dateKey(day) === clickedDate}
										onclick={() => (clickedDate = dateKey(day))}
										onpointerdown={(e) => onWcolDown(e, day)}
										onpointermove={(e) => onWcolMove(e)}
										onpointerup={() => onWcolUp(day)}
										role="button" tabindex="0"
										style="touch-action:none">
										{#if wkDragDayKey === dateKey(day) && wkDragSelStart !== null && wkDragSelEnd !== null}
											<div class="drag-sel" style="top:{minsToY(wkDragSelStart)}px; height:{Math.max(16, minsToY(wkDragSelEnd) - minsToY(wkDragSelStart))}px; left:0; right:0">
												<span>{minsToTime(wkDragSelStart)} – {minsToTime(wkDragSelEnd)}</span>
											</div>
										{/if}
										{#each dayEvs as ev}
											{@const isMoving = wkEvMoveId === ev.id}
											{@const startM = isMoving && wkEvMovePreview !== null ? wkEvMovePreview : timeToMins(ev.start_time)}
											{@const dur = isMoving ? wkEvMoveDur : timeToMins(ev.end_time) - timeToMins(ev.start_time)}
											{@const evTop = minsToY(startM)}
											{@const evH = Math.max(30, minsToY(startM + dur) - minsToY(startM))}
											{@const lo = isMoving ? { col: 0, total: 1 } : (colLayout.get(ev.id) ?? { col: 0, total: 1 })}
											<button class="wk-ev" class:ev-moving={isMoving}
												type="button"
												style="top:{evTop}px; height:{evH}px; left:calc({(lo.col / lo.total) * 100}% + 2px); right:calc({((lo.total - lo.col - 1) / lo.total) * 100}% + 2px); --type:{typeColor(ev.type_id)}; --pay:{paymentColor(ev)}"
												onpointerdown={(e) => onWkEvDown(e, ev)}
												onpointermove={(e) => onWkEvMove(e)}
												onpointerup={() => onWkEvUp(ev)}>
												<b>{ev.title}</b>
												<span>{minsToTime(startM)}</span>
											</button>
										{/each}
									</div>
								{/each}
							</div>
						</div>
					</div>
				</div>

			{:else if activeView === 'Günlük'}
				<div class="day-view">
					<div class="day-view-header">
						<strong>{new Date(clickedDate + 'T12:00:00').toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</strong>
						<span>{dayViewEvents.length} randevu</span>
					</div>
					<div class="day-scroll" bind:this={timelineRef}>
						<div class="day-body" style="height:{TIMELINE_H}px">
							{#each HOURS_ARR as hour}
								<div class="tl-label" style="top:{minsToY(hour * 60) - 9}px">{pad(hour % 24)}:00</div>
								<div class="tl-line" style="top:{minsToY(hour * 60)}px; left:56px; right:0"></div>
							{/each}
							{#each HALF_H as m}
								<div class="tl-half" style="top:{minsToY(m)}px; left:56px; right:0"></div>
							{/each}
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<div class="events-lane"
								onpointerdown={onTimelineDown} onpointermove={onTimelineMove} onpointerup={onTimelineUp}
								style="touch-action:none; left:56px; right:0; top:0; height:{TIMELINE_H}px">
								{#if dragSelStart !== null && dragSelEnd !== null}
									<div class="drag-sel" style="top:{minsToY(dragSelStart)}px; height:{Math.max(16, minsToY(dragSelEnd) - minsToY(dragSelStart))}px">
										<span>{minsToTime(dragSelStart)} – {minsToTime(dragSelEnd)}</span>
									</div>
								{/if}
								{#each dayViewEvents as ev}
									{@const isMoving = evMoveId === ev.id}
									{@const startM = isMoving && evMovePreview !== null ? evMovePreview : timeToMins(ev.start_time)}
									{@const dur = isMoving ? evMoveDur : timeToMins(ev.end_time) - timeToMins(ev.start_time)}
									{@const evTop = minsToY(startM)}
									{@const evH = Math.max(32, minsToY(startM + dur) - minsToY(startM))}
									{@const lo = isMoving ? { col: 0, total: 1 } : (dayViewLayout.get(ev.id) ?? { col: 0, total: 1 })}
									<button class="day-ev" class:ev-moving={isMoving}
										type="button"
										style="top:{evTop}px; height:{evH}px; left:calc({(lo.col / lo.total) * 100}% + 2px); right:calc({((lo.total - lo.col - 1) / lo.total) * 100}% + 2px); --type:{typeColor(ev.type_id)}; --pay:{paymentColor(ev)}"
										onpointerdown={(e) => onEvDayDown(e, ev)}
										onpointermove={(e) => onEvDayMove(e)}
										onpointerup={() => onEvDayUp(ev)}>
										<b>{ev.title}</b>
										<span>{minsToTime(startM)}–{minsToTime(startM + dur)} · {typeName(ev.type_id)}</span>
									</button>
								{/each}
							</div>
							{#if isToday(clickedDate)}
								{@const ny = getNowY()}
								<div class="now-dot" style="top:{ny - 5}px; left:51px"></div>
								<div class="now-line" style="top:{ny}px; left:56px; right:0"></div>
							{/if}
						</div>
					</div>
				</div>

			{:else}
				<div class="year-grid">
					{#each yearMonths() as month}
						<button class="year-month" type="button" onclick={() => { currentDate = month; activeView = 'Aylık'; }}>
							<strong>{month.toLocaleDateString('tr-TR', { month: 'long' })}</strong>
							<span>{monthEvents(month.getMonth()).length} davet</span>
							<small>{officialHolidays.filter(h => Number(h.date.slice(5,7)) === month.getMonth() + 1).length} resmi gün</small>
						</button>
					{/each}
				</div>
			{/if}
		</section>

	{#if selectedEvent}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="drawer-backdrop" onclick={closePanel} transition:fade={{ duration: 200 }}></div>
		<aside class="drawer" transition:fly={{ x: 580, duration: 320, easing: cubicOut }}>
			<div class="drawer-header">
				<button class="drawer-back" type="button" onclick={closePanel}>← Geri</button>
				<div class="drawer-title-group">
					<strong class="drawer-ev-name">{selectedEvent.full_name || selectedEvent.title || '—'}</strong>
					<span class="drawer-ev-date">{new Date(selectedEvent.event_date + 'T12:00:00').toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
				</div>
				<span class="drawer-status" style="--pay:{paymentColor(selectedEvent)}">{paymentLabel(selectedEvent)}</span>
			</div>

			<div class="drawer-body">
				<div class="detail-card">
					<div class="payment-ticks">
						<label class="tick-label" class:ticked={selectedEvent.kapora_paid}>
							<input type="checkbox" checked={selectedEvent.kapora_paid} onchange={(e) => updateSelected('kapora_paid', e.currentTarget.checked)} />
							Kapora Ödendi
						</label>
						<label class="tick-label" class:ticked={selectedEvent.payment_complete}>
							<input type="checkbox" checked={selectedEvent.payment_complete} onchange={(e) => updateSelected('payment_complete', e.currentTarget.checked)} />
							Ödeme Tamamlandı
						</label>
					</div>
					<input class="title-input" bind:this={titleInputRef}
						placeholder="İsim giriniz…"
						value={selectedEvent.title}
						oninput={(e) => updateSelected('title', e.currentTarget.value)} />
					<div class="detail-money">
						<div><span>Toplam</span><strong>{formatMoney(selectedEvent.total_fee)}</strong></div>
						<div><span>Kapora</span><strong>{formatMoney(selectedEvent.kapora_amount)}</strong><small class:paid-ok={selectedEvent.kapora_paid}>{selectedEvent.kapora_paid ? '✓' : '…'}</small></div>
						<div><span>Alınan</span><strong>{formatMoney(selectedEvent.total_paid)}</strong></div>
						<div><span>Kalan</span><strong>{formatMoney(selectedEvent.total_fee - selectedEvent.total_paid)}</strong></div>
					</div>
				</div>

				<div class="form-panel">
					<div class="tabs">
						<button class:active={activeTab === 'genel'} type="button" onclick={() => (activeTab = 'genel')}>Genel</button>
						<button class:active={activeTab === 'portal'} type="button" onclick={() => (activeTab = 'portal')}>
							Portal {#if selectedEvent.portal_enabled}<span class="portal-dot"></span>{/if}
						</button>
					</div>

					{#if activeTab === 'genel'}
						<div class="form-grid compact">
							<label><span>Tarihi</span><input type="date" value={selectedEvent.event_date} oninput={(e) => updateSelected('event_date', e.currentTarget.value)} /></label>
							{#if !hiddenBuiltins.has('start_time')}<label><span>Başlama</span><input type="time" value={selectedEvent.start_time} oninput={(e) => updateSelected('start_time', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('end_time')}<label><span>Bitiş</span><input type="time" value={selectedEvent.end_time} oninput={(e) => updateSelected('end_time', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('contract_date')}<label><span>Sözleşme Tarihi</span><input type="date" value={selectedEvent.contract_date} oninput={(e) => updateSelected('contract_date', e.currentTarget.value)} /></label>{/if}
							<label><span>Sözleşme No</span><input value={selectedEvent.id} readonly /></label>
							{#if !hiddenBuiltins.has('reservation_status')}
							<div class="radio-group">
								<label><input type="radio" checked={selectedEvent.reservation_status === 'Kesin Rezervasyon'} onchange={() => updateSelected('reservation_status', 'Kesin Rezervasyon')} /> Kesin</label>
								<label><input type="radio" checked={selectedEvent.reservation_status === 'Ön Rezervasyon'} onchange={() => updateSelected('reservation_status', 'Ön Rezervasyon')} /> Ön</label>
							</div>
							{/if}
						</div>
						<div class="form-grid">
							{#if !hiddenBuiltins.has('tc_no')}<label><span>T.C. Kimlik No</span><input value={selectedEvent.tc_no} oninput={(e) => updateSelected('tc_no', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('full_name')}<label><span>Adı Soyadı</span><input value={selectedEvent.full_name} oninput={(e) => updateSelected('full_name', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('mobile_phone')}<label><span>Mobil Telefon</span><input value={selectedEvent.mobile_phone} oninput={(e) => updateSelected('mobile_phone', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('phone')}<label><span>Telefon</span><input value={selectedEvent.phone} oninput={(e) => updateSelected('phone', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('type_id')}
							<label><span>Organizasyon Tipi</span>
								<select value={selectedEvent.type_id ?? ''} onchange={(e) => updateSelected('type_id', e.currentTarget.value || null)}>
									<option value="">— Seçin —</option>
									{#each eventTypes as t}<option value={t.id}>{t.name}</option>{/each}
								</select>
							</label>
							{/if}
							{#if !hiddenBuiltins.has('bride_groom')}<label><span>Gelin ve Damat</span><input value={selectedEvent.bride_groom} oninput={(e) => updateSelected('bride_groom', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('region')}<label><span>Yöresi</span><input value={selectedEvent.region} oninput={(e) => updateSelected('region', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('guest_count')}<label><span>Davetli Sayısı</span><input type="number" value={selectedEvent.guest_count} oninput={(e) => updateSelected('guest_count', Number(e.currentTarget.value))} /></label>{/if}
							{#if !hiddenBuiltins.has('address')}<label class="full"><span>Adresi</span><textarea rows="2" value={selectedEvent.address} oninput={(e) => updateSelected('address', e.currentTarget.value)}></textarea></label>{/if}
							{#if !hiddenBuiltins.has('total_fee')}<label><span>Toplam Ücret</span><input type="number" value={selectedEvent.total_fee} oninput={(e) => updateSelected('total_fee', Number(e.currentTarget.value))} /></label>{/if}
							{#if !hiddenBuiltins.has('kapora_amount')}
							<label><span>Kapora Tutarı</span>
								<div class="kapora-row">
									<input type="number" value={selectedEvent.kapora_amount} oninput={(e) => updateSelected('kapora_amount', Number(e.currentTarget.value))} />
									<label class="tick-inline" class:ticked={selectedEvent.kapora_paid}>
										<input type="checkbox" checked={selectedEvent.kapora_paid} onchange={(e) => updateSelected('kapora_paid', e.currentTarget.checked)} />Ödendi
									</label>
								</div>
							</label>
							{/if}
							{#if !hiddenBuiltins.has('total_paid')}<label><span>Alınan Ücret</span><input type="number" value={selectedEvent.total_paid} oninput={(e) => updateSelected('total_paid', Number(e.currentTarget.value))} /></label>{/if}
							<label><span>Kalan</span><input value={formatMoney(selectedEvent.total_fee - selectedEvent.total_paid)} readonly /></label>
							{#if !hiddenBuiltins.has('note')}<label class="full"><span>Ön Açıklama</span><textarea rows="3" value={selectedEvent.note} oninput={(e) => updateSelected('note', e.currentTarget.value)}></textarea></label>{/if}
							{#if !hiddenBuiltins.has('staff')}<label class="full"><span>Çalışanlar</span><input value={selectedEvent.staff} oninput={(e) => updateSelected('staff', e.currentTarget.value)} /></label>{/if}
							{#if !hiddenBuiltins.has('reminder_enabled')}
							<div class="reminder-row full">
								<label><input type="checkbox" checked={selectedEvent.reminder_enabled} onchange={(e) => updateSelected('reminder_enabled', e.currentTarget.checked)} /> Yaklaşınca Hatırlat</label>
								<label><span>Tarih</span><input type="date" value={selectedEvent.reminder_date} oninput={(e) => updateSelected('reminder_date', e.currentTarget.value)} /></label>
							</div>
							{/if}
						</div>

						{#if mergedCustomFields.length > 0}
						<div class="custom-fields-section">
							<h4>Ek Alanlar</h4>
							<div class="attribute-list">
								{#each mergedCustomFields as field}
									<label class="attribute-row">
										<span>{field.label}</span>
										{#if field.field_type === 'textarea'}
											<textarea rows="2" value={field.value} oninput={(e) => updateCustomField(field.key, e.currentTarget.value)}></textarea>
										{:else if field.field_type === 'select'}
											<select value={field.value} onchange={(e) => updateCustomField(field.key, e.currentTarget.value)}>
												<option value="">— Seçin —</option>
												{#each field.options ?? [] as opt}<option value={opt}>{opt}</option>{/each}
											</select>
										{:else if field.field_type === 'checkbox'}
											<label class="checkbox-inline"><input type="checkbox" checked={field.value === 'true'} onchange={(e) => updateCustomField(field.key, String(e.currentTarget.checked))} />{field.label}</label>
										{:else}
											<input type={field.field_type} value={field.value} oninput={(e) => updateCustomField(field.key, e.currentTarget.value)} />
										{/if}
									</label>
								{/each}
							</div>
						</div>
						{/if}

						<div class="layouts-section">
							<h4>Rezerve Edilen Salonlar</h4>
							{#if layouts.length === 0}
								<p class="empty-hint">Henüz salon düzeni oluşturulmamış.</p>
							{:else}
								<div class="layout-checks">
									{#each layouts as layout}
										<label class="layout-check">
											<input type="checkbox"
												checked={selectedEvent.reserved_layout_ids.includes(layout.id)}
												onchange={(e) => {
													const current = selectedEvent!.reserved_layout_ids;
													const next = e.currentTarget.checked
														? [...current, layout.id]
														: current.filter(id => id !== layout.id);
													updateSelected('reserved_layout_ids', next);
												}}
											/>
											{layout.name}
										</label>
									{/each}
								</div>
							{/if}
						</div>

						<button class="danger-btn" onclick={deleteEvent}>Daveti Sil</button>

					{:else if activeTab === 'portal'}
						<div class="portal-section">
							<label class="toggle-row">
								<input type="checkbox" checked={selectedEvent.portal_enabled}
									onchange={(e) => updateSelected('portal_enabled', e.currentTarget.checked)} />
								<span>Müşteri portali aktif</span>
							</label>

							{#if selectedEvent.portal_enabled}
								<label><span>Müşteri Formu Tipi</span>
									<select value={selectedEvent.portal_form_type_id ?? ''}
										onchange={(e) => updateSelected('portal_form_type_id', e.currentTarget.value || null)}>
										<option value="">— Seçin —</option>
										{#each customerFormTypes as t}<option value={t.id}>{t.name}</option>{/each}
									</select>
								</label>

								<label class="toggle-row">
									<input type="checkbox" checked={selectedEvent.portal_layout_permission}
										onchange={(e) => updateSelected('portal_layout_permission', e.currentTarget.checked)} />
									<span>Salon düzeni izni (müşteri misafir listesi yapabilir)</span>
								</label>

								{#if selectedEvent.portal_layout_permission && layouts.length > 0}
									<div class="layout-perm-hint">
										<small>Hangi salonların düzenini müşteri görebilir? (Yukarıda rezerve edilenleri seç)</small>
										<div class="layout-checks">
											{#each layouts.filter(l => selectedEvent!.reserved_layout_ids.includes(l.id)) as layout}
												<span class="layout-badge">{layout.name}</span>
											{/each}
											{#if selectedEvent.reserved_layout_ids.length === 0}
												<span class="empty-hint">Önce Genel sekmesinden salon rezerve et.</span>
											{/if}
										</div>
									</div>
								{/if}

								{#if selectedEvent.portal_token}
									<div class="portal-link-block">
										<span class="portal-link-label">Portal Linki</span>
										<div class="portal-link-row">
											<input readonly value={portalLink(selectedEvent)} />
											<button onclick={copyPortalLink}>{portalCopied ? '✓ Kopyalandı' : 'Kopyala'}</button>
										</div>
										<a href={portalLink(selectedEvent)} target="_blank" class="open-link">Portali Aç ↗</a>
									</div>
								{/if}
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</aside>
	{/if}
</section>

<style>
	.calendar-shell { max-width: 1720px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }
	.page-heading { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
	h1, h4, p { margin: 0; }
	h1 { font-size: clamp(1.9rem, 3vw, 3rem); }
	h4 { font-size: 0.82rem; color: var(--muted); font-weight: 900; margin-bottom: 0.35rem; text-transform: uppercase; letter-spacing: 0.06em; }
	.eyebrow { margin-bottom: 0.25rem; color: var(--accent); font-size: 0.78rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; }
	.error-bar { padding: 0.75rem 1rem; background: color-mix(in srgb, var(--danger) 12%, transparent); border: 1px solid var(--danger); border-radius: 8px; color: var(--danger); font-weight: 800; font-size: 0.85rem; }
	.saving-indicator { font-size: 0.78rem; color: var(--muted); font-weight: 800; }
	.view-switch { display: inline-flex; gap: 0.35rem; padding: 0.35rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }
	button, input, select, textarea { font: inherit; }
	.view-switch button { border: 0; border-radius: 7px; padding: 0.65rem 0.85rem; color: var(--muted); background: transparent; font-weight: 900; cursor: pointer; }
	.view-switch .active { color: #fff; background: var(--accent); }
	.calendar-toolbar { display: flex; align-items: center; gap: 0.5rem; padding: 0.65rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; flex-wrap: wrap; }
	.calendar-toolbar button { border: 0; border-radius: 7px; padding: 0.65rem 0.85rem; color: var(--muted); background: transparent; font-weight: 900; cursor: pointer; }
	.calendar-toolbar .primary { color: #fff; background: var(--accent); margin-left: auto; }
	.tbl-label { min-width: 200px; text-align: center; font-size: 1rem; }
	.selected-date-label { font-size: 0.82rem; font-weight: 800; color: var(--accent); padding: 0.35rem 0.65rem; border-radius: 6px; background: var(--accent-soft); white-space: nowrap; }
	.calendar-panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 1rem; overflow: hidden; }
	/* ── Type legend bar ── */
	.type-legend-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; padding: 0.5rem 0.75rem; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; margin-bottom: 0.5rem; }
	.legend-chip { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.65rem; border-radius: 99px; font-size: 0.78rem; font-weight: 900; border: 1px solid color-mix(in srgb, var(--c) 40%, transparent); background: color-mix(in srgb, var(--c) 14%, var(--surface)); color: var(--text); }
	.legend-chip::before { content: ''; display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--c); flex-shrink: 0; }
	.legend-add { flex-direction: row !important; align-items: center; gap: 0.4rem; margin-left: auto; flex-shrink: 0; }
	.legend-type-input { min-height: 32px; height: 32px; width: 140px; font-size: 0.78rem; }
	.legend-add .color-input { width: 32px; height: 32px; min-height: 32px; border: 0; padding: 0; background: transparent; cursor: pointer; }
	.legend-add-btn { border: 0; border-radius: 6px; padding: 0.35rem 0.65rem; background: var(--accent); color: #fff; font-weight: 900; cursor: pointer; font-size: 0.78rem; white-space: nowrap; }
	/* ── Drawer ── */
	.drawer-backdrop { position: fixed; inset: 0; z-index: 24; background: rgba(0,0,0,0.38); cursor: pointer; }
	.drawer { position: fixed; top: 0; right: 0; bottom: 0; width: min(560px, 98vw); z-index: 25; background: var(--surface); border-left: 1px solid var(--line); box-shadow: -12px 0 48px rgba(0,0,0,0.28); display: flex; flex-direction: column; overflow: hidden; }
	.drawer-header { display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; border-bottom: 1px solid var(--line); background: var(--surface); flex-shrink: 0; position: sticky; top: 0; z-index: 2; }
	.drawer-back { border: 1px solid var(--line); border-radius: 7px; padding: 0.4rem 0.8rem; background: var(--surface-strong); color: var(--text); font-weight: 900; font-size: 0.82rem; cursor: pointer; white-space: nowrap; flex-shrink: 0; }
	.drawer-back:hover { background: var(--accent-soft); border-color: var(--accent); }
	.drawer-title-group { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; flex: 1; }
	.drawer-ev-name { font-size: 1rem; font-weight: 900; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.drawer-ev-date { font-size: 0.75rem; color: var(--muted); }
	.drawer-status { display: inline-flex; padding: 0.3rem 0.6rem; border-radius: 999px; color: var(--pay); background: color-mix(in srgb, var(--pay) 14%, transparent); font-weight: 900; font-size: 0.78rem; flex-shrink: 0; }
	.drawer-body { flex: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 1rem; }
	.weekday-row, .month-grid { display: grid; grid-template-columns: repeat(7, minmax(0,1fr)); gap: 0.4rem; }
	.weekday-row { margin-bottom: 0.5rem; color: var(--muted); font-weight: 900; text-align: center; }
	.day-cell { min-height: 120px; padding: 0.6rem; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-strong); cursor: pointer; }
	.day-cell:hover { border-color: color-mix(in srgb, var(--accent) 45%, transparent); }
	.selected-day { border-color: var(--accent) !important; background: color-mix(in srgb, var(--accent) 8%, var(--surface-strong)) !important; }
	.today-day .day-top strong { background: var(--accent); color: #fff; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; }
	.muted-day { opacity: 0.4; }
	.day-top { display: flex; align-items: center; justify-content: space-between; gap: 0.35rem; margin-bottom: 0.4rem; }
	.holiday { color: var(--accent); font-size: 0.68rem; font-weight: 900; }
	.event-chip { width: 100%; display: flex; align-items: center; gap: 0.3rem; margin-top: 0.3rem; padding: 0.38rem 0.45rem; font-weight: 900; font-size: 0.76rem; text-align: left; cursor: pointer; border: 1px solid color-mix(in srgb, var(--type) 32%, transparent); border-left: 5px solid var(--pay); border-radius: 7px; background: color-mix(in srgb, var(--type) 20%, var(--surface)); color: var(--text); }
	.chip-time { color: var(--muted); font-size: 0.7rem; }
	.chip-ticks { margin-left: auto; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 0.15rem; }
	.tick { font-size: 0.58rem; font-weight: 900; padding: 0.12rem 0.32rem; border-radius: 4px; line-height: 1.2; white-space: nowrap; }
	.tick-k { background: #f59e0b; color: #fff; }
	.tick-p { background: #16a34a; color: #fff; }
	.tick-portal { background: #2563eb; color: #fff; }
	/* ── Week view ── */
	.week-view { display: flex; flex-direction: column; }
	.wk-header-row { display: grid; grid-template-columns: 56px repeat(7, 1fr); border-bottom: 2px solid var(--line); }
	.wcol-head { display: flex; flex-direction: column; align-items: center; gap: 0.2rem; padding: 0.65rem 0.35rem; border: 0; background: transparent; color: var(--muted); cursor: pointer; font: inherit; border-bottom: 2px solid transparent; transition: all 0.15s; position: relative; }
	.wcol-head.today .wday-num { background: var(--accent); color: #fff; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; }
	.wcol-head.wk-selected { border-bottom-color: var(--accent); color: var(--text); }
	.wday-name { font-size: 0.72rem; font-weight: 900; text-transform: uppercase; letter-spacing: 0.05em; }
	.wday-num { font-size: 1.15rem; font-weight: 900; }
	.wday-badge { position: absolute; top: 6px; right: 6px; background: var(--accent); color: #fff; font-size: 0.6rem; font-weight: 900; border-radius: 99px; padding: 0.05rem 0.35rem; }
	.wk-scroll { overflow-y: auto; max-height: 560px; }
	.wk-body { position: relative; overflow: hidden; }
	.wcols { position: absolute; display: grid; grid-template-columns: repeat(7, 1fr); }
	.wcol { position: relative; border-left: 1px solid var(--line); min-height: 100%; cursor: crosshair; }
	.wcol.wk-selected { background: color-mix(in srgb, var(--accent) 4%, transparent); }
	.wk-ev { position: absolute; border: 0; border-left: 4px solid var(--pay); border-radius: 6px; background: color-mix(in srgb, var(--type) 28%, var(--surface)); color: var(--text); font: inherit; font-size: 0.73rem; font-weight: 900; cursor: grab; text-align: left; overflow: hidden; padding: 0.3rem 0.4rem; }
	.wk-ev:active, .wk-ev.ev-moving { cursor: grabbing; opacity: 0.8; z-index: 10; box-shadow: 0 4px 20px rgba(0,0,0,0.18); }
	/* ── Day view ── */
	.day-view { display: flex; flex-direction: column; }
	.day-view-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 0.75rem 0 0.65rem; border-bottom: 1px solid var(--line); }
	.day-view-header strong { font-size: 1rem; }
	.day-view-header span { font-size: 0.78rem; color: var(--muted); }
	.day-scroll { overflow-y: auto; max-height: 560px; }
	.day-body { position: relative; }
	.events-lane { position: absolute; cursor: crosshair; }
	.day-ev { position: absolute; border: 0; border-left: 5px solid var(--pay); border-radius: 7px; background: color-mix(in srgb, var(--type) 28%, var(--surface)); color: var(--text); font: inherit; font-size: 0.8rem; font-weight: 900; cursor: grab; text-align: left; overflow: hidden; padding: 0.35rem 0.55rem; display: flex; flex-direction: column; gap: 0.2rem; }
	.day-ev:active, .day-ev.ev-moving { cursor: grabbing; opacity: 0.8; z-index: 10; box-shadow: 0 8px 28px rgba(0,0,0,0.2); }
	.drag-sel { position: absolute; background: color-mix(in srgb, var(--accent) 20%, transparent); border: 2px solid var(--accent); border-radius: 7px; display: flex; align-items: flex-start; padding: 0.3rem 0.5rem; pointer-events: none; }
	.drag-sel span { font-size: 0.78rem; font-weight: 900; color: var(--accent); }
	.now-dot { position: absolute; width: 10px; height: 10px; border-radius: 50%; background: #ef4444; z-index: 3; }
	.now-line { position: absolute; height: 2px; background: #ef4444; z-index: 2; opacity: 0.8; }
	.tl-label { position: absolute; left: 4px; font-size: 0.68rem; font-weight: 900; color: var(--muted); white-space: nowrap; user-select: none; }
	.tl-line { position: absolute; height: 1px; background: color-mix(in srgb, var(--line) 180%, transparent); }
	.tl-half { position: absolute; height: 1px; background: color-mix(in srgb, var(--line) 70%, transparent); }
	/* ── Year view ── */
	.year-grid { display: grid; grid-template-columns: repeat(4, minmax(130px,1fr)); gap: 0.65rem; }
	.year-month { display: flex; flex-direction: column; gap: 0.35rem; padding: 0.85rem; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-strong); color: var(--text); text-align: left; cursor: pointer; }
	.year-month span, .year-month small { color: var(--muted); font-size: 0.8rem; }
	/* ── Drawer inner cards ── */
	.detail-card, .form-panel { background: var(--surface-strong); border: 1px solid var(--line); border-radius: 8px; padding: 1rem; }
	.payment-ticks { display: flex; flex-direction: column; gap: 0.4rem; }
	.tick-label { display: flex; align-items: center; gap: 0.4rem; font-size: 0.82rem; font-weight: 800; color: var(--muted); cursor: pointer; }
	.tick-label.ticked { color: var(--text); }
	.tick-label input { accent-color: var(--accent); }
	.detail-money { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-top: 1rem; }
	.detail-money div { display: flex; flex-direction: column; gap: 0.2rem; padding: 0.65rem; border-radius: 8px; background: var(--surface-strong); border: 1px solid var(--line); }
	.detail-money span { color: var(--muted); font-size: 0.75rem; }
	.detail-money small { font-size: 0.75rem; }
	.title-input { width: 100%; border: 0; border-bottom: 2px solid var(--line); border-radius: 0; padding: 0.2rem 0; background: transparent; color: var(--text); font-size: 1.25rem; font-weight: 900; min-height: unset; margin-bottom: 0.75rem; }
	.title-input:focus { outline: none; border-bottom-color: var(--accent); }
	.title-input::placeholder { color: var(--muted); font-weight: 600; }
	.paid-ok { color: #16a34a; font-weight: 900; }
	.kapora-row { display: flex; align-items: center; gap: 0.5rem; }
	.kapora-row input:first-child { flex: 1; }
	.tick-inline { display: flex; align-items: center; gap: 0.3rem; font-size: 0.78rem; font-weight: 800; color: var(--muted); white-space: nowrap; cursor: pointer; }
	.tick-inline.ticked { color: #16a34a; }
	.tick-inline input { width: auto; min-height: auto; accent-color: var(--accent); }
	.tabs { display: flex; gap: 0.25rem; margin: -1rem -1rem 1rem; padding: 0.65rem 0.85rem 0; border-bottom: 1px solid var(--line); }
	.tabs button { border: 1px solid var(--line); border-bottom: 0; border-radius: 8px 8px 0 0; padding: 0.65rem 1rem; color: var(--muted); background: var(--surface-strong); font-weight: 900; cursor: pointer; display: flex; align-items: center; gap: 0.35rem; }
	.tabs .active { color: var(--text); background: var(--surface); }
	.portal-dot { width: 8px; height: 8px; border-radius: 50%; background: #2563eb; }
	.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 0.75rem; }
	.form-grid.compact { grid-template-columns: repeat(3, minmax(0,1fr)); margin-bottom: 0.85rem; padding-bottom: 0.85rem; border-bottom: 1px solid var(--line); }
	label, .attribute-row { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; }
	label span, .attribute-row span { color: var(--muted); font-size: 0.78rem; }
	input, select, textarea { width: 100%; min-height: 38px; border: 1px solid var(--line); border-radius: 7px; padding: 0.55rem 0.65rem; background: var(--surface-strong); color: var(--text); }
	textarea { resize: vertical; }
	input[readonly] { opacity: 0.72; }
	.full { grid-column: 1 / -1; }
	.radio-group, .reminder-row { display: flex; flex-direction: column; justify-content: center; gap: 0.5rem; padding: 0.65rem; border-radius: 8px; background: var(--surface-strong); border: 1px solid var(--line); }
	.radio-group label, .reminder-row label:first-child { flex-direction: row; align-items: center; }
	.radio-group input, .reminder-row input[type='checkbox'] { width: auto; min-height: auto; accent-color: var(--accent); }
	.layouts-section { padding-top: 0.85rem; margin-top: 0.5rem; border-top: 1px solid var(--line); }
	.layout-checks { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
	.layout-check { display: flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.65rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 7px; font-size: 0.82rem; font-weight: 800; cursor: pointer; }
	.layout-check input { width: auto; min-height: auto; accent-color: var(--accent); }
	.empty-hint { color: var(--muted); font-size: 0.78rem; }
	.danger-btn { margin-top: 0.5rem; padding: 0.65rem; width: 100%; background: transparent; border: 1px solid var(--danger); border-radius: 7px; color: var(--danger); font-weight: 900; cursor: pointer; }
	.attribute-list { display: flex; flex-direction: column; gap: 0.7rem; }
	.attribute-row { padding: 0.65rem; border-radius: 8px; background: var(--surface-strong); border: 1px solid var(--line); }
	.checkbox-inline { flex-direction: row; align-items: center; gap: 0.5rem; }
	.checkbox-inline input { width: auto; min-height: auto; }
	/* ── Portal ── */
	.portal-section { display: flex; flex-direction: column; gap: 0.85rem; }
	.toggle-row { flex-direction: row !important; align-items: center; gap: 0.5rem; }
	.toggle-row input { width: auto; min-height: auto; accent-color: var(--accent); }
	.portal-link-block { display: flex; flex-direction: column; gap: 0.5rem; padding: 0.85rem; background: color-mix(in srgb, #2563eb 8%, var(--surface-strong)); border: 1px solid color-mix(in srgb, #2563eb 30%, var(--line)); border-radius: 8px; }
	.portal-link-label { font-size: 0.78rem; font-weight: 900; color: #2563eb; }
	.portal-link-row { display: flex; gap: 0.5rem; }
	.portal-link-row input { flex: 1; font-size: 0.8rem; }
	.portal-link-row button { border: 0; border-radius: 7px; padding: 0.55rem 0.85rem; background: #2563eb; color: #fff; font-weight: 900; cursor: pointer; white-space: nowrap; }
	.open-link { font-size: 0.78rem; color: #2563eb; text-decoration: none; font-weight: 800; }
	.layout-perm-hint { display: flex; flex-direction: column; gap: 0.35rem; }
	.layout-perm-hint small { color: var(--muted); font-size: 0.78rem; }
	.layout-badge { display: inline-flex; padding: 0.35rem 0.65rem; background: var(--surface-strong); border: 1px solid var(--line); border-radius: 6px; font-size: 0.78rem; font-weight: 800; }
	@media (max-width: 760px) {
		.month-grid, .weekday-row, .form-grid, .form-grid.compact { grid-template-columns: 1fr; }
		.year-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
		.drawer { width: 100vw; }
		.legend-type-input { width: 100px; }
	}
</style>
