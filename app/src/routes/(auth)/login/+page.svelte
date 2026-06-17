<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, setToken } from '$lib/api';

	let email = $state('');
	let password = $state('');
	let rememberMe = $state(false);
	let isLoading = $state(false);
	let errorMessage = $state('');

	const handleSubmit = async () => {
		isLoading = true;
		errorMessage = '';
		try {
			const data = await api.post<{ access_token: string; role: string; salon_id: string; username: string }>(
				'/auth/token',
				{ email, password }
			);
			setToken(data.access_token);
			if (data.username) localStorage.setItem('eventra-username', data.username);
			if (data.salon_id) localStorage.setItem('eventra-salon-id', data.salon_id);
			goto('/');
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Giriş başarısız';
			isLoading = false;
		}
	};
</script>

<div class="login-container">
	<div class="login-card">
		<div class="brand">
			<div class="logo-spotlight"></div>
			<img src="/logo-yatay.png" alt="Eventra Logo" class="logo-image" />
		</div>

		<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
			<div class="input-group">
				<label for="email">Kullanıcı adı</label>
				<input 
					type="text" 
					id="email" 
					bind:value={email} 
					placeholder="Kullanıcı adınız..." 
					required 
				/>
			</div>

			<div class="input-group">
				<label for="password">Şifre</label>
				<input 
					type="password" 
					id="password" 
					bind:value={password} 
					placeholder="••••••••" 
					required 
				/>
			</div>

			<div class="form-options">
				<label class="checkbox-container">
					<input type="checkbox" bind:checked={rememberMe} />
					<span class="checkmark"></span>
					Beni Hatırla
				</label>
				<a href="/forgot-password" class="forgot-link">Şifremi unuttum</a>
			</div>

			{#if errorMessage}
				<div class="error-message">
					{errorMessage}
				</div>
			{/if}

			<button type="submit" disabled={isLoading} class="gold-button">
				<span class="btn-content">
					{#if isLoading}
						Giriş Yapılıyor...
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
							<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
							<path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
						</svg>
						SİSTEME GİRİŞ YAP
					{/if}
				</span>
			</button>
		</form>
	</div>

	<div class="login-footer">
		&copy; 2026 Eventra CRM System. All rights reserved.
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: 'Inter', system-ui, -apple-system, sans-serif;
		background-color: #0B132B;
	}

	.login-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100vh;
		
		/* Radial Gradient + Zarif bir CSS Grid Texture */
		background: 
			radial-gradient(circle at center, rgba(28, 36, 56, 0.9) 0%, rgba(11, 19, 43, 1) 100%),
			linear-gradient(rgba(212, 175, 55, 0.03) 1px, transparent 1px),
			linear-gradient(90deg, rgba(212, 175, 55, 0.03) 1px, transparent 1px);
		background-size: 100% 100%, 40px 40px, 40px 40px;
		
		padding: 2rem;
		box-sizing: border-box;
	}

	.login-card {
		background: #0B132B;
		padding: 3.5rem 3rem;
		border-radius: 12px;
		width: 100%;
		max-width: 440px;
		display: flex;
		flex-direction: column;
		gap: 2rem;
		box-sizing: border-box;
		border: 3px solid #D4AF37; 
		
		/* Orijinal Pavyon Neon box-shadow */
		box-shadow: 
			0 0 15px rgba(212, 175, 55, 0.7),
			0 0 30px rgba(212, 175, 55, 0.5),
			0 0 60px rgba(212, 175, 55, 0.3),
			0 15px 35px rgba(0, 0, 0, 0.8);
			
		animation: golden-neon-pulse 3s infinite ease-in-out;
		position: relative;
		z-index: 10;
	}

	.brand {
		text-align: center;
		display: flex;
		justify-content: center;
		align-items: center;
		margin-bottom: 1rem;
		position: relative;
	}

	.logo-spotlight {
		content: '';
		position: absolute;
		width: 140%;
		height: 140%;
		background: radial-gradient(circle, rgba(246, 238, 220, 0.2) 0%, transparent 65%);
		z-index: 0;
		pointer-events: none;
	}

	.logo-image {
		width: 100%;
		max-width: 320px;
		height: auto;
		display: block;
		position: relative;
		z-index: 1;
		filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.5)); 
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 1.75rem;
	}

	.input-group {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	label {
		color: #F6EEDC;
		font-size: 0.9rem;
		font-weight: 500;
		letter-spacing: 0.5px;
	}

	input[type="text"],
	input[type="password"] {
		background: #1C2438;
		border: 1px solid rgba(212, 175, 55, 0.3);
		color: #F6EEDC;
		padding: 1rem 1.25rem;
		border-radius: 8px;
		font-size: 1rem;
		transition: all 0.2s;
		box-sizing: border-box;
	}

	input:focus {
		outline: none;
		border-color: #D4AF37;
		box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.3);
	}

	/* FORM OPTIONS (Beni Hatırla & Şifremi Unuttum) */
	.form-options {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.85rem;
	}

	.checkbox-container {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		color: #94a3b8;
		user-select: none;
		transition: color 0.2s;
	}

	.checkbox-container:hover {
		color: #F6EEDC;
	}

	.checkbox-container input {
		accent-color: #D4AF37;
		width: 16px;
		height: 16px;
		cursor: pointer;
	}

	.forgot-link {
		color: #D4AF37;
		text-decoration: none;
		transition: text-shadow 0.2s, color 0.2s;
	}

	.forgot-link:hover {
		color: #F6EEDC;
		text-shadow: 0 0 8px rgba(246, 238, 220, 0.6);
	}

	.error-message {
		color: #ef4444;
		font-size: 0.875rem;
		background: rgba(239, 68, 68, 0.1);
		padding: 0.75rem;
		border-radius: 8px;
		border: 1px solid rgba(239, 68, 68, 0.2);
		text-align: center;
	}

	/* SÜSLENMİŞ BUTTON & SHINE EFEKTİ */
	.gold-button {
		position: relative;
		background: linear-gradient(135deg, #D4AF37 0%, #b5952f 100%);
		color: #0B132B;
		border: none;
		padding: 1rem;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 800;
		cursor: pointer;
		transition: all 0.3s ease-in-out;
		margin-top: 0.5rem;
		text-transform: uppercase;
		letter-spacing: 1.5px;
		overflow: hidden; /* İçeriden taşan parlama efekti için kritik */
	}

	.btn-content {
		position: relative;
		z-index: 2;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.6rem;
	}

	/* Butonun üzerinden geçen beyaz ışık parlaması (Shine Animation) */
	.gold-button::before {
		content: '';
		position: absolute;
		top: 0;
		left: -100%;
		width: 50%;
		height: 100%;
		background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.5), transparent);
		transform: skewX(-25deg);
		animation: btn-shine 4s infinite;
		z-index: 1;
	}

	.gold-button:hover:not(:disabled) {
		background: #F6EEDC;
		color: #D4AF37;
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(212, 175, 55, 0.5);
	}

	.gold-button:disabled {
		background: #1C2438;
		color: rgba(246, 238, 220, 0.5);
		cursor: not-allowed;
		opacity: 0.7;
	}

	/* SAYFA ALTI FOOTER TEXT */
	.login-footer {
		margin-top: 2.5rem;
		color: rgba(246, 238, 220, 0.4);
		font-size: 0.8rem;
		letter-spacing: 1px;
	}

	/* KEYFRAMES */
	@keyframes golden-neon-pulse {
		0%, 100% {
			box-shadow: 
				0 0 15px rgba(212, 175, 55, 0.7),
				0 0 30px rgba(212, 175, 55, 0.5),
				0 0 60px rgba(212, 175, 55, 0.3),
				0 15px 35px rgba(0, 0, 0, 0.8);
		}
		50% {
			box-shadow: 
				0 0 20px rgba(212, 175, 55, 0.9),
				0 0 40px rgba(212, 175, 55, 0.7),
				0 0 80px rgba(212, 175, 55, 0.5),
				0 15px 35px rgba(0, 0, 0, 0.8);
		}
	}

	@keyframes btn-shine {
		0% { left: -100%; }
		20% { left: 200%; }
		100% { left: 200%; }
	}
</style>
