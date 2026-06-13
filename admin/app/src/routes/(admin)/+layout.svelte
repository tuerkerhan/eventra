<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	let { children } = $props();
	let token = $state('');

	onMount(() => {
		const t = localStorage.getItem('admin_token');
		if (!t) goto('/login');
		else token = t;
	});

	const logout = () => {
		localStorage.removeItem('admin_token');
		goto('/login');
	};

	const navItems = [
		{ name: 'Salonlar & Hesaplar', path: '/accounts' }
	];
</script>

<div class="admin-shell">
	<aside class="sidebar">
		<div class="sidebar-brand">
			<span class="brand-e">E</span>
			<span class="brand-name">Admin</span>
		</div>
		<nav class="sidebar-nav">
			{#each navItems as item}
				<a href={item.path} class="nav-link" class:active={$page.url.pathname === item.path}>{item.name}</a>
			{/each}
		</nav>
		<button class="logout-btn" type="button" onclick={logout}>Çıkış Yap</button>
	</aside>

	<main class="admin-main">
		{@render children()}
	</main>
</div>

<style>
	.admin-shell { display: grid; grid-template-columns: 220px 1fr; min-height: 100vh; }

	.sidebar {
		display: flex; flex-direction: column; gap: 0;
		background: #172033; border-right: 1px solid rgba(226,232,240,0.1);
		padding: 1.5rem 1rem;
	}

	.sidebar-brand { display: flex; align-items: center; gap: 0.65rem; margin-bottom: 2rem; }
	.brand-e { width: 36px; height: 36px; border-radius: 8px; background: #c59b31; display: grid; place-items: center; font-size: 1.1rem; font-weight: 900; color: #fff; }
	.brand-name { font-size: 1rem; font-weight: 900; color: #f8fafc; }

	.sidebar-nav { display: flex; flex-direction: column; gap: 0.35rem; flex: 1; }

	.nav-link {
		padding: 0.65rem 0.85rem; border-radius: 8px; color: #64748b;
		text-decoration: none; font-weight: 800; font-size: 0.88rem; transition: all 0.15s;
	}
	.nav-link:hover, .nav-link.active { background: rgba(197,155,49,0.12); color: #f8fafc; }
	.nav-link.active { color: #c59b31; }

	.logout-btn {
		margin-top: auto; border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; padding: 0.65rem;
		background: rgba(239,68,68,0.08); color: #fca5a5; font-weight: 800; font-size: 0.85rem; cursor: pointer;
	}

	.admin-main { padding: 2rem 2.5rem; }

	@media (max-width: 768px) {
		.admin-shell { grid-template-columns: 1fr; }
		.sidebar { flex-direction: row; align-items: center; flex-wrap: wrap; padding: 0.75rem 1rem; }
		.sidebar-brand { margin-bottom: 0; }
		.admin-main { padding: 1rem; }
	}
</style>
