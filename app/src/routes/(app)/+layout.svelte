<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api, type SalonApi } from '$lib/api';

	let { children } = $props();
	let theme = $state<'dark' | 'light'>('dark');
	let uiMode = $state<'full' | 'sade'>('full');
	let salonName = $state('İnci Davet');

	onMount(async () => {
		// Apply saved prefs immediately from localStorage (no flash)
		const savedTheme = localStorage.getItem('eventra-theme');
		if (savedTheme === 'light' || savedTheme === 'dark') theme = savedTheme;
		const savedMode = localStorage.getItem('eventra-uimode');
		if (savedMode === 'sade' || savedMode === 'full') uiMode = savedMode as 'full' | 'sade';

		try {
			const [s, prefs] = await Promise.all([
				api.get<SalonApi>('/settings/salon'),
				api.get<{ ui_mode: string }>('/settings/me')
			]);
			salonName = s.name;
			if (prefs.ui_mode === 'sade' || prefs.ui_mode === 'full') {
				uiMode = prefs.ui_mode;
				localStorage.setItem('eventra-uimode', prefs.ui_mode);
			}
		} catch {}
	});

	const menuItems = [
		{ name: 'Ana Sayfa', path: '/', icon: '/anasayfa.png' },
		{ name: 'Dashboard', path: '/dashboard', icon: '/dashboard-icon.png' },
		{ name: 'Takvim', path: '/calendar', icon: '/takvim-icon.png' },
		{ name: 'Randevular', path: '/customers', icon: '/musteriler-icon.png' },
		{ name: 'Salon Düzeni', path: '/venue', icon: '/salon-duzeni.png' },
		{ name: 'Sözleşmeler', path: '/contracts', icon: '/contract-icon.png' },
		{ name: 'Ayarlar', path: '/settings', icon: '/ayarlar-icon.png' }
	];

	const toggleTheme = () => {
		theme = theme === 'dark' ? 'light' : 'dark';
		localStorage.setItem('eventra-theme', theme);
	};

	const toggleMode = async () => {
		uiMode = uiMode === 'full' ? 'sade' : 'full';
		localStorage.setItem('eventra-uimode', uiMode);
		try { await api.patch('/settings/me', { ui_mode: uiMode }); } catch {}
	};
</script>

<svelte:head>
	<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet" />
</svelte:head>

<div class="app-shell {theme} {uiMode}">
	<header class="topbar">
		<a class="brand" href="/" aria-label="Ana sayfa">
			<span class="brand-logo-wrap">
				<img src="/ikon.png" alt="" class="brand-logo" />
			</span>
			<span class="brand-title-wrap">
				{#if uiMode === 'full'}
					<img src="/crown-icon.png" alt="" class="brand-crown" />
				{/if}
				<span class="brand-title">{salonName}</span>
			</span>
		</a>

		<nav class="nav-gallery" aria-label="Ana menü">
			{#each menuItems as item}
				<a href={item.path} class="nav-card {$page.url.pathname === item.path ? 'active-card' : ''}">
					{#if uiMode === 'full'}
						<div class="icon-container">
							<img
								src="/crown-icon.png"
								alt=""
								class="crown-icon {$page.url.pathname === item.path ? 'is-active' : ''}"
							/>
							<img src={item.icon} alt="" class="nav-icon" />
						</div>
					{/if}
					<span class="nav-text">{item.name}</span>
				</a>
			{/each}
		</nav>

		<div class="top-actions">
			<button class="mode-toggle" type="button" onclick={toggleMode}>
				{uiMode === 'full' ? 'Sade' : 'Renkli'}
			</button>
			<button class="theme-toggle" type="button" onclick={toggleTheme}>
				{theme === 'dark' ? 'Light' : 'Dark'}
			</button>
			<a class="logout-link" href="/login">Logout</a>
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
		grid-template-columns: minmax(210px, 260px) 1fr auto;
		align-items: center;
		gap: 1rem;
		min-height: 142px;
		padding: 1rem 1.5rem;
		background: color-mix(in srgb, var(--surface) 94%, transparent);
		border-bottom: 1px solid var(--line);
		box-shadow: 0 14px 36px rgba(0, 0, 0, 0.16);
		transition: min-height 0.25s ease;
	}

	/* Sade mod — topbar daha küçük */
	.sade .topbar {
		min-height: 64px;
	}

	/* ── Brand ── */
	.brand {
		display: inline-flex;
		align-items: center;
		gap: 0.75rem;
		color: var(--text);
		text-decoration: none;
		min-width: 0;
	}

	.brand-logo-wrap {
		position: relative;
		display: grid;
		place-items: center;
		width: 64px;
		height: 64px;
		border: 1px solid var(--line);
		border-radius: 8px;
		background: var(--accent-soft);
		box-shadow: 0 0 26px color-mix(in srgb, var(--accent) 20%, transparent);
		transition: all 0.25s ease;
	}

	.sade .brand-logo-wrap {
		width: 38px;
		height: 38px;
	}

	.brand-logo {
		width: 50px;
		height: 50px;
		object-fit: contain;
		filter: drop-shadow(0 8px 14px rgba(0, 0, 0, 0.24));
		transition: all 0.25s ease;
	}

	.sade .brand-logo { width: 28px; height: 28px; }

	.brand-title-wrap {
		position: relative;
		display: inline-flex;
		align-items: center;
		padding-top: 0.8rem;
	}

	.sade .brand-title-wrap { padding-top: 0; }

	.brand-crown {
		position: absolute;
		top: -18px;
		left: 50%;
		transform: translateX(-50%);
		width: 30px;
		height: 30px;
		object-fit: contain;
		filter: drop-shadow(0 0 10px rgba(197, 155, 49, 0.8));
		animation: crown-pop 2.8s ease-in-out infinite;
	}

	.brand-title {
		font-family: 'Great Vibes', cursive;
		color: var(--accent);
		font-size: clamp(2.05rem, 3vw, 2.7rem);
		line-height: 1;
		white-space: nowrap;
		transition: font-size 0.25s ease;
	}

	.sade .brand-title { font-size: 1.15rem; font-family: inherit; font-weight: 900; }

	/* ── Nav — full mode ── */
	.nav-gallery {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.9rem;
		min-width: 0;
		overflow-x: auto;
		padding: 1rem 0.35rem 0.35rem;
	}

	.sade .nav-gallery {
		padding: 0;
		gap: 0.25rem;
	}

	.nav-card {
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		gap: 0.4rem;
		min-width: 112px;
		min-height: 108px;
		padding: 0.7rem 0.85rem;
		border-radius: 8px;
		color: var(--muted);
		text-decoration: none;
		font-weight: 700;
		font-size: 0.88rem;
		border: 1px solid transparent;
		white-space: nowrap;
		transition: background 0.18s, color 0.18s, border-color 0.18s, transform 0.18s, min-height 0.25s, min-width 0.25s, padding 0.25s;
	}

	.nav-card:hover { transform: translateY(-2px); }

	.nav-card:hover, .active-card {
		background: var(--accent-soft);
		border-color: color-mix(in srgb, var(--accent) 34%, transparent);
		color: var(--text);
	}

	/* Sade nav — sadece metin, compact */
	.sade .nav-card {
		min-width: auto;
		min-height: auto;
		padding: 0.5rem 0.85rem;
		font-size: 0.86rem;
		border-radius: 7px;
		flex-direction: row;
	}

	.sade .nav-card:hover { transform: none; }

	/* ── Nav icons (full only) ── */
	.icon-container {
		position: relative;
		display: grid;
		place-items: center;
		width: 62px;
		height: 62px;
	}

	.nav-icon {
		width: 60px;
		height: 60px;
		object-fit: contain;
		filter: drop-shadow(0 8px 14px rgba(0, 0, 0, 0.34));
		transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), filter 0.2s ease;
	}

	.nav-card:hover .nav-icon, .active-card .nav-icon {
		transform: scale(1.12);
		filter: drop-shadow(0 0 15px color-mix(in srgb, var(--accent) 56%, transparent));
	}

	.crown-icon {
		position: absolute;
		top: -20px;
		width: 34px;
		height: 34px;
		object-fit: contain;
		z-index: 2;
		opacity: 0;
		transform: scale(0.3) translateY(8px);
		filter: drop-shadow(0 0 12px rgba(197, 155, 49, 0.85));
		transition: all 0.48s cubic-bezier(0.68, -0.55, 0.265, 1.55);
	}

	.nav-card:hover .crown-icon, .crown-icon.is-active {
		opacity: 1;
		transform: scale(1) translateY(0);
	}

	.nav-text { text-align: center; line-height: 1.1; }

	/* ── Top actions ── */
	.top-actions {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 0.6rem;
	}

	.theme-toggle, .mode-toggle, .logout-link {
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

	.theme-toggle, .mode-toggle {
		color: var(--text);
		background: var(--surface-strong);
	}

	.mode-toggle {
		border-color: color-mix(in srgb, var(--accent) 40%, transparent);
		color: var(--accent);
	}

	.logout-link {
		color: #ffffff;
		background: #b42318;
		border-color: #b42318;
	}

	/* ── Content ── */
	.portal-content {
		min-height: calc(100vh - 142px);
		padding: 1.5rem;
		background:
			linear-gradient(180deg, color-mix(in srgb, var(--surface-strong) 40%, transparent), transparent 320px),
			var(--page);
		transition: min-height 0.25s ease;
	}

	.sade .portal-content { min-height: calc(100vh - 64px); }

	@keyframes crown-pop {
		0%, 100% { transform: translateX(-50%) translateY(0) scale(1); }
		50%       { transform: translateX(-50%) translateY(-3px) scale(1.06); }
	}

	@media (max-width: 1100px) {
		.topbar { grid-template-columns: 1fr auto; min-height: auto; }
		.nav-gallery { grid-column: 1 / -1; justify-content: flex-start; }
	}

	@media (max-width: 720px) {
		.topbar { padding: 0.85rem; }
		.top-actions { gap: 0.35rem; }
		.brand-logo-wrap { width: 52px; height: 52px; }
		.brand-logo { width: 40px; height: 40px; }
		.nav-card { min-width: 92px; min-height: 94px; }
		.icon-container, .nav-icon { width: 48px; height: 48px; }
		.theme-toggle, .mode-toggle, .logout-link { padding: 0 0.7rem; }
		.portal-content { padding: 1rem; }
	}
</style>
