<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api, type SalonApi, type VenueLayoutApi } from '$lib/api';
	import { activeSalonId, initActiveSalon } from '$lib/activeSalon';

	let { children } = $props();
	let theme = $state<'dark' | 'light'>('dark');
	let salonName = $state('');
	let salons = $state<VenueLayoutApi[]>([]);

	onMount(async () => {
		// Apply saved prefs immediately from localStorage (no flash)
		const savedTheme = localStorage.getItem('eventra-theme');
		if (savedTheme === 'light' || savedTheme === 'dark') theme = savedTheme;
		const savedName = localStorage.getItem('eventra-salon-name');
		if (savedName) salonName = savedName;
		initActiveSalon();

		try {
			const [s, layouts] = await Promise.all([
				api.get<SalonApi>('/settings/salon'),
				api.get<VenueLayoutApi[]>('/venue/layouts')
			]);
			salonName = s.name;
			localStorage.setItem('eventra-salon-name', s.name);
			salons = layouts;
			if ($activeSalonId && !layouts.some((layout) => layout.id === $activeSalonId)) {
				activeSalonId.set(layouts[0]?.id ?? '');
			}
		} catch {}
	});

	const menuItems = [
		{ name: 'Ana Sayfa', path: '/' },
		{ name: 'Takvim', path: '/calendar' },
		{ name: 'Dashboard', path: '/dashboard' },
		{ name: 'Randevular', path: '/customers' },
		{ name: 'Salon Düzeni', path: '/venue' },
		{ name: 'Sözleşmeler', path: '/contracts' },
		{ name: 'Ayarlar', path: '/settings' }
	];

	const toggleTheme = () => {
		theme = theme === 'dark' ? 'light' : 'dark';
		localStorage.setItem('eventra-theme', theme);
	};
</script>

<svelte:head>
	<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet" />
</svelte:head>

<div class="app-shell {theme}">
	<header class="topbar">
		<a class="brand" href="/" aria-label="Ana sayfa">
			<span class="brand-title">{salonName}</span>
		</a>

		<nav class="nav-gallery" aria-label="Ana menü">
			{#each menuItems as item}
				<a href={item.path} class="nav-card {$page.url.pathname === item.path ? 'active-card' : ''}">
					<span class="nav-text">{item.name}</span>
				</a>
			{/each}
		</nav>

		<div class="top-actions">
			{#if salons.length > 0}
				<select class="salon-select" bind:value={$activeSalonId}>
					<option value="">Tüm Salonlar</option>
					{#each salons as s}
						<option value={s.id}>{s.name}</option>
					{/each}
				</select>
			{/if}
			<button class="theme-toggle" type="button" onclick={toggleTheme}>
				{theme === 'dark' ? 'Açık Mod' : 'Koyu Mod'}
			</button>
			<a class="logout-link" href="/login">Çıkış</a>
		</div>
	</header>

	<main class="portal-content">
		{@render children()}
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
		color: var(--text);
		background: var(--page);
	}

	:global(*) { box-sizing: border-box; }

	/* ── Themes ── */
	.app-shell {
		--page: #0f172a;
		--surface: #172033;
		--surface-strong: #101827;
		--muted-surface: #202a3d;
		--line: rgba(226, 232, 240, 0.12);
		--text: #f8fafc;
		--muted: #a9b4c6;
		--accent: #c59b31;
		--accent-soft: rgba(197, 155, 49, 0.12);
		--danger: #ef4444;
		--good: #16a34a;
		--info: #2563eb;
		min-height: 100vh;
		background: var(--page);
		color: var(--text);
	}

	.app-shell.light {
		--page: #f5f7fb;
		--surface: #ffffff;
		--surface-strong: #eef2f7;
		--muted-surface: #e7edf5;
		--line: rgba(15, 23, 42, 0.12);
		--text: #111827;
		--muted: #56657a;
		--accent: #9a6b08;
		--accent-soft: rgba(154, 107, 8, 0.1);
		background: var(--page);
	}

	/* ── Topbar ── */
	.topbar {
		position: sticky;
		top: 0;
		z-index: 20;
		display: grid;
		grid-template-columns: minmax(180px, 220px) 1fr auto;
		align-items: center;
		gap: 1rem;
		min-height: 76px;
		padding: 0.75rem 1.5rem;
		background: color-mix(in srgb, var(--surface) 94%, transparent);
		border-bottom: 1px solid var(--line);
		box-shadow: 0 14px 36px rgba(0, 0, 0, 0.16);
	}

	/* ── Brand ── */
	.brand {
		display: inline-flex;
		align-items: center;
		color: var(--text);
		text-decoration: none;
		min-width: 0;
	}

	.brand-title {
		font-family: 'Great Vibes', cursive;
		color: var(--accent);
		font-size: clamp(1.7rem, 2.6vw, 2.3rem);
		line-height: 1;
		white-space: nowrap;
	}

	/* ── Nav ── */
	.nav-gallery {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-wrap: wrap;
		gap: 0.4rem;
		min-width: 0;
	}

	.nav-card {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0.65rem 1.1rem;
		border-radius: 8px;
		color: var(--muted);
		text-decoration: none;
		font-weight: 800;
		font-size: 1.02rem;
		border: 1px solid transparent;
		white-space: nowrap;
		transition: background 0.18s, color 0.18s, border-color 0.18s;
	}

	.nav-card:hover, .active-card {
		background: var(--accent-soft);
		border-color: color-mix(in srgb, var(--accent) 34%, transparent);
		color: var(--text);
	}

	.nav-text { line-height: 1.1; }

	/* ── Top actions ── */
	.top-actions {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 0.6rem;
	}

	.salon-select, .theme-toggle, .logout-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 40px;
		border-radius: 8px;
		padding: 0 0.9rem;
		font-weight: 800;
		font-size: 0.86rem;
		text-decoration: none;
		cursor: pointer;
		border: 1px solid var(--line);
	}

	.salon-select, .theme-toggle {
		color: var(--text);
		background: var(--surface-strong);
	}

	.salon-select {
		border-color: color-mix(in srgb, var(--accent) 40%, transparent);
		color: var(--accent);
		font-weight: 700;
	}

	.logout-link {
		color: #ffffff;
		background: #b42318;
		border-color: #b42318;
	}

	/* ── Content ── */
	.portal-content {
		min-height: calc(100vh - 76px);
		padding: 1.5rem;
		background:
			linear-gradient(180deg, color-mix(in srgb, var(--surface-strong) 40%, transparent), transparent 320px),
			var(--page);
	}

	@media (max-width: 1100px) {
		.topbar { grid-template-columns: 1fr auto; min-height: auto; }
		.nav-gallery { grid-column: 1 / -1; justify-content: flex-start; }
	}

	@media (max-width: 720px) {
		.topbar { padding: 0.85rem; }
		.top-actions { gap: 0.35rem; }
		.salon-select, .theme-toggle, .logout-link { padding: 0 0.7rem; }
		.portal-content { padding: 1rem; }
	}
</style>
