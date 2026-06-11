<script lang="ts">
	import { page } from '$app/stores';

	const menuItems = [
		{ name: 'Özet Paneli', path: '/', icon: '/dashboard-icon.png' },
		{ name: 'Takvim & Ajanda', path: '/calendar', icon: '/takvim-icon.png' },
		{ name: 'Müşteri Portalı', path: '/customers', icon: '/musteriler-icon.png' },
		{ name: 'Sözleşmeler', path: '/contracts', icon: '/contract-icon.png' },
		{ name: 'Portal Ayarları', path: '/settings', icon: '/ayarlar-icon.png' }
	];
</script>

<svelte:head>
	<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap" rel="stylesheet">
</svelte:head>

<div class="top-navbar-layout">
	<header class="lux-navbar">
		
		<div class="brand-zone">
			<div class="logo-spotlight"></div>
			<img src="/logo-yatay.png" alt="Eventra Logo" class="brand-logo" />
		</div>
		
		<nav class="nav-gallery">
			{#each menuItems as item}
				<a 
					href={item.path} 
					class="nav-card {$page.url.pathname === item.path ? 'active-card' : ''}"
				>
					<div class="icon-container">
						<img 
							src="/crown-icon.png" 
							alt="Crown" 
							class="crown-icon {$page.url.pathname === item.path ? 'is-active' : ''}"
						/>

						<img src={item.icon} alt={item.name} class="massive-icon" />
					</div>

					<span class="nav-text">{item.name}</span>

					{#if $page.url.pathname === item.path}
						<div class="active-indicator"></div>
					{/if}
				</a>
			{/each}
		</nav>

		<div class="profile-zone">
			<div class="user-details">
				<div class="inci-brand-wrapper">
					<img src="/crown-icon.png" alt="İnci Crown" class="inci-text-crown" />
					<h1 class="inci-text">İnci Davet</h1>
				</div>
				<span class="user-role">Demo Hesabı - Tam Erişim</span>
			</div>
			
			<div class="profile-frame">
				<img src="/ikon.png" alt="Profile" class="client-avatar" />
			</div>
		</div>
	</header>

	<main class="portal-content">
		<slot />
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: 'Inter', system-ui, -apple-system, sans-serif;
		background-color: #0B132B;
	}

	.top-navbar-layout {
		display: flex;
		flex-direction: column;
		height: 100vh;
		width: 100vw;
		overflow: hidden;
		background-color: #0B132B;
	}

	.lux-navbar {
		height: 160px;
		background: #0B132B;
		border-bottom: 2px solid rgba(212, 175, 55, 0.2);
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0 2rem;
		z-index: 20;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
	}

	.brand-zone {
		position: relative;
		display: flex;
		align-items: center;
		height: 100%;
		padding-right: 2rem;
	}

	.logo-spotlight {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 300px;
		height: 300px;
		background: radial-gradient(circle, rgba(246, 238, 220, 0.15) 0%, transparent 60%);
		z-index: 0;
		pointer-events: none;
	}

	.brand-logo {
		width: 240px;
		position: relative;
		z-index: 1;
		filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.2));
	}

	.nav-gallery {
		display: flex;
		gap: 1.5rem;
		height: 100%;
		align-items: center;
	}

	.nav-card {
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: center;
		align-items: center;
		background: transparent;
		border-radius: 16px;
		padding: 1rem 1.5rem;
		text-decoration: none;
		transition: all 0.3s ease;
		height: 120px;
		min-width: 140px;
	}

	.nav-card:hover {
		background: rgba(28, 36, 56, 0.8);
		transform: translateY(-2px);
	}

	.active-card {
		background: linear-gradient(180deg, #1C2438 0%, rgba(11, 19, 43, 0) 100%);
		border-bottom: 3px solid #D4AF37;
		border-radius: 16px 16px 0 0;
	}

	.icon-container {
		position: relative;
		width: 75px;
		height: 75px;
		display: flex;
		justify-content: center;
		align-items: center;
		margin-bottom: 0.5rem;
		z-index: 2;
	}

	.massive-icon {
		width: 100%;
		height: 100%;
		object-fit: contain;
		filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.6));
		transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
	}

	.nav-card:hover .massive-icon, .active-card .massive-icon {
		transform: scale(1.15);
		filter: drop-shadow(0 0 15px rgba(212, 175, 55, 0.5));
	}

	/* YENİ PURE CSS KRAL TACI ANİMASYONU */
	.crown-icon {
		position: absolute;
		top: -22px;
		width: 36px;
		height: 36px;
		object-fit: contain;
		z-index: 3;
		filter: drop-shadow(0 0 12px rgba(212, 175, 55, 0.9));
		
		/* Başlangıçta görünmez ve küçültülmüş */
		opacity: 0;
		transform: scale(0.3);
		/* Svelte elasticOut hissiyatını veren CSS transition */
		transition: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
	}

	/* Nav-card hover olduğunda veya sayfa aktifse taç büyüyerek belirir */
	.nav-card:hover .crown-icon,
	.crown-icon.is-active {
		opacity: 1;
		transform: scale(1);
	}

	.nav-text {
		color: #F6EEDC;
		font-size: 0.95rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		z-index: 2;
		transition: color 0.3s;
	}

	.active-card .nav-text {
		color: #D4AF37;
		font-weight: 700;
	}

	.active-indicator {
		position: absolute;
		bottom: 0;
		width: 100%;
		height: 3px;
		background: #D4AF37;
		box-shadow: 0 -2px 10px rgba(212, 175, 55, 0.5);
	}

	/* SAĞ PROFİL VE İNCİ DAVET */
	.profile-zone {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.user-details {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.2rem;
	}

	.inci-brand-wrapper {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
		margin-top: 15px;
	}

	.inci-text-crown {
		position: absolute;
		top: -22px;
		left: 50%;
		transform: translateX(-50%);
		width: 28px;
		height: 28px;
		object-fit: contain;
		z-index: 3;
		filter: drop-shadow(0 0 8px rgba(212, 175, 55, 0.8));
	}

	.inci-text {
		font-family: 'Great Vibes', cursive;
		color: #D4AF37;
		font-size: 2.2rem;
		margin: 0;
		font-weight: normal;
		text-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
		line-height: 1;
	}

	.user-role {
		color: #F6EEDC;
		font-size: 0.85rem;
		letter-spacing: 1px;
		opacity: 0.8;
	}

	.profile-frame {
		width: 80px;
		height: 80px;
		background: #0B132B;
		border: 2px solid #D4AF37;
		border-radius: 16px;
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 6px;
		box-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
		position: relative;
		z-index: 2;
	}

	.client-avatar {
		width: 100%;
		height: 100%;
		object-fit: contain;
		filter: drop-shadow(0 2px 5px rgba(0,0,0,0.5));
	}

	.portal-content {
		flex-grow: 1;
		padding: 2.5rem;
		overflow-y: auto;
		background: radial-gradient(circle at top right, rgba(28, 36, 56, 0.6) 0%, #0B132B 100%);
	}
</style>