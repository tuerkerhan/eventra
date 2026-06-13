<script lang="ts">
	const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	const login = async (e: Event) => {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			const r = await fetch(`${API}/auth/token`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email, password })
			});
			const data = await r.json();
			if (!r.ok) { error = data.detail ?? 'Giriş başarısız'; return; }
			if (data.role !== 'admin') { error = 'Bu hesap admin değil'; return; }
			localStorage.setItem('admin_token', data.access_token);
			window.location.href = '/accounts';
		} catch {
			error = 'Sunucuya bağlanılamadı';
		} finally {
			loading = false;
		}
	};
</script>

<div class="login-shell">
	<div class="login-card">
		<div class="login-logo">
			<span class="login-logo-text">E</span>
		</div>
		<h1>Eventra Admin</h1>
		<p class="subtitle">Yönetim Paneli</p>

		<form onsubmit={login}>
			{#if error}
				<div class="error-msg">{error}</div>
			{/if}
			<label>
				<span>E-posta</span>
				<input type="email" bind:value={email} required placeholder="admin@example.com" />
			</label>
			<label>
				<span>Şifre</span>
				<input type="password" bind:value={password} required placeholder="••••••••" />
			</label>
			<button type="submit" disabled={loading}>
				{loading ? 'Giriş yapılıyor…' : 'Giriş Yap'}
			</button>
		</form>
	</div>
</div>

<style>
	.login-shell {
		min-height: 100vh; display: flex; align-items: center; justify-content: center;
		background: linear-gradient(135deg, #0f172a 0%, #172033 100%); padding: 1rem;
	}

	.login-card {
		width: 100%; max-width: 420px; background: #172033;
		border: 1px solid rgba(226,232,240,0.1); border-radius: 16px;
		padding: 2.5rem 2rem; box-shadow: 0 30px 60px rgba(0,0,0,0.4);
		display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
	}

	.login-logo {
		width: 64px; height: 64px; border-radius: 16px; background: #c59b31;
		display: grid; place-items: center; margin-bottom: 0.5rem;
	}
	.login-logo-text { font-size: 2rem; font-weight: 900; color: #fff; }

	h1 { margin: 0; font-size: 1.6rem; font-weight: 900; }
	.subtitle { margin: 0 0 1.5rem; color: #64748b; font-size: 0.88rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }

	form { width: 100%; display: flex; flex-direction: column; gap: 1rem; }

	label { display: flex; flex-direction: column; gap: 0.4rem; font-weight: 800; font-size: 0.85rem; color: #94a3b8; }

	input {
		width: 100%; min-height: 44px; border: 1px solid rgba(226,232,240,0.15); border-radius: 8px;
		padding: 0.65rem 0.85rem; background: #101827; color: #f8fafc; font: inherit; font-size: 1rem;
	}

	button {
		width: 100%; min-height: 46px; border: 0; border-radius: 8px; margin-top: 0.5rem;
		background: #c59b31; color: #fff; font-weight: 900; font-size: 1rem; cursor: pointer;
		transition: opacity 0.2s;
	}
	button:disabled { opacity: 0.6; cursor: not-allowed; }

	.error-msg {
		padding: 0.85rem 1rem; border-radius: 8px;
		background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25);
		color: #fca5a5; font-size: 0.88rem; font-weight: 700;
	}
</style>
