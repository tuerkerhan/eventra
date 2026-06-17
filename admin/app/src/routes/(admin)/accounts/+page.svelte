<script lang="ts">
	import { onMount } from 'svelte';

	const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

	interface Salon {
		id: string;
		name: string;
		address: string;
		currency: string;
		salon_count?: number;
		max_users: number;
		subscription_start?: string;
		subscription_end?: string;
		created_at: string;
		company_name?: string;
		city?: string;
		postal_code?: string;
		phone?: string;
		website?: string;
		contract_no?: number;
		smtp_host?: string;
		smtp_port?: number;
		smtp_username?: string;
		smtp_password?: string;
		smtp_from_email?: string;
		smtp_use_tls?: boolean;
		notification_email?: string;
		payment_iban?: string;
		payment_bank_name?: string;
		payment_account_holder?: string;
	}

	interface SalonUser {
		id: string;
		email: string;
		username: string;
		role: string;
		is_active: boolean;
		created_at: string;
	}

	let salons = $state<Salon[]>([]);
	let selectedSalon = $state<Salon | null>(null);
	let salonUsers = $state<SalonUser[]>([]);
	let loading = $state(true);
	let usersLoading = $state(false);
	let actionError = $state('');
	let deletingSalon = $state(false);
	let deletingUserId = $state('');

	// Right panel view
	let rightView = $state<'users' | 'settings'>('users');

	// Create salon
	let showCreateSalon = $state(false);
	let newSalon = $state({
		name: '', address: '', phone: '', notification_email: '',
		currency: 'TRY', vat_rate: 20, contract_prefix: 'EVT',
		reminder_days: 3, salon_count: 1, max_users: 5,
		subscription_start: '', subscription_end: '',
		owner_email: '', owner_username: '', owner_password: ''
	});
	let createError = $state('');
	let creating = $state(false);

	// Add user
	let showAddUser = $state(false);
	let newUser = $state({ email: '', username: '', password: '', role: 'staff' });
	let addUserError = $state('');
	let addingUser = $state(false);

	// Edit salon (inline)
	let editData = $state<Partial<Salon>>({});
	let editError = $state('');
	let saving = $state(false);

	const headers = () => ({
		'Content-Type': 'application/json',
		Authorization: `Bearer ${localStorage.getItem('admin_token')}`
	});

	const getError = async (r: Response, fallback: string) => {
		try {
			const body = await r.json();
			return body.detail ?? fallback;
		} catch {
			return fallback;
		}
	};

	const loadSalons = async () => {
		loading = true;
		const r = await fetch(`${API}/admin/salons`, { headers: headers() });
		if (r.ok) salons = await r.json();
		loading = false;
	};

	const loadUsers = async (salonId: string) => {
		usersLoading = true;
		const r = await fetch(`${API}/admin/salons/${salonId}/users`, { headers: headers() });
		if (r.ok) salonUsers = await r.json();
		usersLoading = false;
	};

	const selectSalon = (salon: Salon) => {
		selectedSalon = salon;
		salonUsers = [];
		actionError = '';
		rightView = 'users';
		loadUsers(salon.id);
	};

	const openSettings = () => {
		if (!selectedSalon) return;
		editData = { ...selectedSalon };
		editError = '';
		rightView = 'settings';
	};

	const saveSettings = async () => {
		if (!editData.id) return;
		saving = true;
		editError = '';
		const r = await fetch(`${API}/admin/salons/${editData.id}`, {
			method: 'PATCH',
			headers: headers(),
			body: JSON.stringify(editData)
		});
		saving = false;
		if (r.ok) {
			const updated = await r.json();
			salons = salons.map(s => s.id === updated.id ? updated : s);
			selectedSalon = updated;
			rightView = 'users';
		} else {
			editError = (await r.json()).detail ?? 'Kaydedilemedi';
		}
	};

	const createSalon = async () => {
		createError = '';
		creating = true;
		const r = await fetch(`${API}/admin/salons`, {
			method: 'POST',
			headers: headers(),
			body: JSON.stringify(newSalon)
		});
		creating = false;
		if (r.ok) {
			showCreateSalon = false;
			newSalon = {
				name: '', address: '', phone: '', notification_email: '',
				currency: 'TRY', vat_rate: 20, contract_prefix: 'EVT',
				reminder_days: 3, salon_count: 1, max_users: 5,
				subscription_start: '', subscription_end: '',
				owner_email: '', owner_username: '', owner_password: ''
			};
			await loadSalons();
		} else {
			createError = (await r.json()).detail ?? 'Salon oluşturulamadı';
		}
	};

	const addUser = async () => {
		if (!selectedSalon) return;
		addUserError = '';
		addingUser = true;
		const r = await fetch(`${API}/admin/salons/${selectedSalon.id}/users`, {
			method: 'POST',
			headers: headers(),
			body: JSON.stringify(newUser)
		});
		addingUser = false;
		if (r.ok) {
			showAddUser = false;
			newUser = { email: '', username: '', password: '', role: 'staff' };
			await loadUsers(selectedSalon.id);
		} else {
			addUserError = (await r.json()).detail ?? 'Kullanıcı eklenemedi';
		}
	};

	const removeUser = async (userId: string) => {
		if (!selectedSalon) return;
		if (!confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) return;
		actionError = '';
		deletingUserId = userId;
		const r = await fetch(`${API}/admin/salons/${selectedSalon.id}/users/${userId}`, { method: 'DELETE', headers: headers() });
		deletingUserId = '';
		if (!r.ok) {
			actionError = await getError(r, 'Kullanıcı silinemedi');
			return;
		}
		await loadUsers(selectedSalon.id);
	};

	const deleteSalon = async () => {
		if (!selectedSalon) return;
		if (!confirm(`"${selectedSalon.name}" salonunu silmek istediğinizden emin misiniz? Tüm veriler kalıcı olarak silinecektir.`)) return;
		actionError = '';
		deletingSalon = true;
		const r = await fetch(`${API}/admin/salons/${selectedSalon.id}`, { method: 'DELETE', headers: headers() });
		deletingSalon = false;
		if (!r.ok) {
			actionError = await getError(r, 'Salon silinemedi');
			return;
		}
		salons = salons.filter(s => s.id !== selectedSalon!.id);
		selectedSalon = null;
		salonUsers = [];
	};

	const formatDate = (d: string) => new Date(d).toLocaleDateString('tr-TR', { year: 'numeric', month: 'short', day: 'numeric' });

	onMount(loadSalons);
</script>

<div class="page">
	<div class="page-head">
		<div>
			<p class="eyebrow">Admin</p>
			<h1>Salonlar & Hesaplar</h1>
		</div>
		<button class="btn-primary" type="button" onclick={() => (showCreateSalon = true)}>+ Yeni Salon</button>
	</div>

	<div class="layout">
		<!-- Left: Salon list -->
		<aside class="panel salon-panel">
			<div class="panel-head">
				<h2>Salonlar</h2>
				<span class="count-badge">{salons.length}</span>
			</div>
			{#if loading}
				<p class="muted">Yükleniyor…</p>
			{:else if salons.length === 0}
				<p class="muted">Henüz salon yok.</p>
			{:else}
				<ul class="salon-list">
					{#each salons as salon}
						<li>
							<button
								type="button"
								class="salon-item"
								class:active={selectedSalon?.id === salon.id}
								onclick={() => selectSalon(salon)}
							>
								<div class="si-name">{salon.name}</div>
								<div class="si-meta">
									{#if salon.city}<span class="city-tag">{salon.city}</span>{/if}
									{#if salon.contract_no}<span class="contract-tag">#{salon.contract_no}</span>{/if}
									<span class="si-date">{formatDate(salon.created_at)}</span>
								</div>
								<div class="si-footer">
									<span class="users-badge">{salon.max_users} kullanıcı lisansı</span>
									{#if salon.smtp_host}<span class="smtp-badge">SMTP ✓</span>{/if}
								</div>
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</aside>

		<!-- Right: Detail panel -->
		<section class="panel detail-panel">
			{#if !selectedSalon}
				<div class="empty-state">
					<div class="empty-icon">🏛</div>
					<p>Sol listeden bir salon seçin.</p>
				</div>
			{:else}
				<!-- Header -->
				<div class="detail-head">
					<div class="detail-title">
						<h2>{selectedSalon.name}</h2>
						{#if selectedSalon.company_name}<p class="muted-sm">{selectedSalon.company_name}</p>{/if}
					</div>
					<div class="view-tabs">
						<button
							type="button"
							class="tab-btn"
							class:active={rightView === 'users'}
							onclick={() => (rightView = 'users')}
						>Kullanıcılar</button>
						<button
							type="button"
							class="tab-btn"
							class:active={rightView === 'settings'}
							onclick={openSettings}
						>Salon Bilgileri</button>
					</div>
				</div>
				{#if actionError}
					<div class="panel-alert alert-error">{actionError}</div>
				{/if}

				<!-- USERS TAB -->
				{#if rightView === 'users'}
					<div class="tab-body">
						<div class="capacity-row">
							<div class="capacity-bar">
								<div class="capacity-fill" style="width: {Math.min((salonUsers.length / selectedSalon.max_users) * 100, 100)}%"></div>
							</div>
							<span class="capacity-label">{salonUsers.length} / {selectedSalon.max_users} kullanıcı</span>
							{#if salonUsers.length < selectedSalon.max_users}
								<button class="btn-sm" type="button" onclick={() => (showAddUser = true)}>+ Ekle</button>
							{/if}
						</div>

						{#if usersLoading}
							<p class="muted">Yükleniyor…</p>
						{:else if salonUsers.length === 0}
							<p class="muted">Bu salonun henüz kullanıcısı yok.</p>
						{:else}
							<div class="user-list">
								{#each salonUsers as user}
									<div class="user-row">
										<div class="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
									<div class="user-info">
											<strong>{user.username}</strong>
											<span>Giriş: {user.email}</span>
										</div>
										<div class="user-right">
											<span class="role-badge" class:owner={user.role === 'owner'}>
												{user.role === 'owner' ? 'Salon Sahibi' : 'Personel'}
											</span>
											<span class="date-sm">{formatDate(user.created_at)}</span>
											<button class="btn-remove" type="button" onclick={() => removeUser(user.id)} disabled={deletingUserId === user.id}>
												{deletingUserId === user.id ? 'Siliniyor…' : 'Sil'}
											</button>
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>

				<!-- SETTINGS TAB -->
				{:else}
					<div class="tab-body settings-body">
						{#if editError}
							<div class="alert-error">{editError}</div>
						{/if}

						<div class="settings-grid">
							<!-- General -->
							<div class="settings-section">
								<p class="section-label">Genel</p>
								<label>Salon Adı<input bind:value={editData.name} /></label>
								<label>Şirket Adı<input bind:value={editData.company_name} /></label>
								<label>Şehir<input bind:value={editData.city} /></label>
								<label>Adres<textarea rows="2" bind:value={editData.address}></textarea></label>
								<label>Telefon<input bind:value={editData.phone} /></label>
								<label>Website<input bind:value={editData.website} /></label>
								<label>Sözleşme Prefix<input bind:value={editData.contract_prefix} /></label>
								<label>Salon Sayısı
									<div class="license-row">
										{#each [1,2,3,4,5] as n}
											<button
												type="button"
												class="lic-btn"
												class:active={editData.salon_count === n}
												onclick={() => (editData.salon_count = n)}
											>{n}</button>
										{/each}
									</div>
								</label>
								<label>Para Birimi
									<select bind:value={editData.currency}>
										<option>TRY</option><option>EUR</option><option>USD</option>
									</select>
								</label>
								<label>Kullanıcı Lisansı
									<div class="license-row">
										{#each [1,2,3,4,5] as n}
											<button
												type="button"
												class="lic-btn"
												class:active={editData.max_users === n}
												onclick={() => (editData.max_users = n)}
											>{n}</button>
										{/each}
									</div>
								</label>
								<label>Abonelik Başlangıç<input type="date" bind:value={editData.subscription_start} /></label>
								<label>Abonelik Bitiş<input type="date" bind:value={editData.subscription_end} /></label>
							</div>

							<!-- SMTP -->
							<div class="settings-section">
								<p class="section-label">SMTP & Mail</p>
								<label>Bildirim E-postası<input type="email" bind:value={editData.notification_email} /></label>
								<label>SMTP Host<input bind:value={editData.smtp_host} placeholder="smtp.gmail.com" /></label>
								<label>SMTP Port<input type="number" bind:value={editData.smtp_port} placeholder="587" /></label>
								<label>SMTP Kullanıcı<input bind:value={editData.smtp_username} /></label>
								<label>SMTP Şifre<input type="password" bind:value={editData.smtp_password} /></label>
								<label class="checkbox-label">
									<input type="checkbox" bind:checked={editData.smtp_use_tls} />
									<span>STARTTLS kullan</span>
								</label>
							</div>

							<!-- Payment -->
							<div class="settings-section">
								<p class="section-label">Ödeme Bilgileri (Portal)</p>
								<label>IBAN<input bind:value={editData.payment_iban} placeholder="TR00 0000 0000 0000 0000 0000 00" /></label>
								<label>Banka Adı<input bind:value={editData.payment_bank_name} /></label>
								<label>Hesap Sahibi<input bind:value={editData.payment_account_holder} /></label>
							</div>
						</div>

						<div class="settings-actions">
							<button class="btn-primary" type="button" onclick={saveSettings} disabled={saving}>
								{saving ? 'Kaydediliyor…' : 'Kaydet'}
							</button>
							<button class="btn-ghost" type="button" onclick={() => (rightView = 'users')}>İptal</button>
							<div class="danger-zone">
								<button class="btn-danger" type="button" onclick={deleteSalon} disabled={deletingSalon}>
									{deletingSalon ? 'Siliniyor…' : 'Salonu Sil'}
								</button>
							</div>
						</div>
					</div>
				{/if}
			{/if}
		</section>
	</div>
</div>

<!-- Create Salon Modal -->
{#if showCreateSalon}
	<div class="modal-bg" onclick={(e) => { if (e.target === e.currentTarget) showCreateSalon = false; }} onkeydown={(e) => { if (e.key === 'Escape') showCreateSalon = false; }} role="dialog" aria-modal="true" aria-label="Yeni salon" tabindex="-1">
		<div class="modal">
			<h2>Yeni Salon Oluştur</h2>
			{#if createError}<div class="alert-error">{createError}</div>{/if}
			<form class="modal-form" onsubmit={(e) => { e.preventDefault(); createSalon(); }}>
				<fieldset>
					<legend>Salon Bilgileri</legend>
					<label>İşletme / salon adı *<input required bind:value={newSalon.name} placeholder="İnci Davet" /></label>
					<label>Yetkili adı soyadı *<input required bind:value={newSalon.owner_username} placeholder="Ayşe Yılmaz" /></label>
					<label>Telefon<input bind:value={newSalon.phone} placeholder="05xx xxx xx xx" /></label>
					<label>E-posta *<input type="email" required bind:value={newSalon.notification_email} placeholder="info@salon.com" /></label>
					<label>Adres<textarea rows="2" bind:value={newSalon.address} placeholder="Açık adres"></textarea></label>
				</fieldset>
				<fieldset>
					<legend>Salon Hesabı</legend>
					<label>Salon sayısı ({newSalon.salon_count})
						<div class="license-row">
							{#each [1,2,3,4,5] as n}
								<button type="button" class="lic-btn" class:active={newSalon.salon_count === n} onclick={() => (newSalon.salon_count = n)}>{n}</button>
							{/each}
						</div>
					</label>
					<label>Kullanıcı sayısı ({newSalon.max_users})
						<div class="license-row">
							{#each [1,2,3,4,5] as n}
								<button type="button" class="lic-btn" class:active={newSalon.max_users === n} onclick={() => (newSalon.max_users = n)}>{n}</button>
							{/each}
						</div>
					</label>
					<div class="date-row">
						<label>Abonelik başlangıç tarihi<input type="date" bind:value={newSalon.subscription_start} /></label>
						<label>Abonelik bitiş tarihi<input type="date" bind:value={newSalon.subscription_end} /></label>
					</div>
					<label>Giriş Kullanıcı Adı *<input required bind:value={newSalon.owner_email} placeholder="inci-davet" /></label>
					<label>Şifre *<input type="password" required bind:value={newSalon.owner_password} /></label>
				</fieldset>
				<div class="modal-actions">
					<button class="btn-primary" type="submit" disabled={creating}>{creating ? 'Oluşturuluyor…' : 'Salon Oluştur'}</button>
					<button class="btn-ghost" type="button" onclick={() => (showCreateSalon = false)}>İptal</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- Add User Modal -->
{#if showAddUser && selectedSalon}
	<div class="modal-bg" onclick={(e) => { if (e.target === e.currentTarget) showAddUser = false; }} onkeydown={(e) => { if (e.key === 'Escape') showAddUser = false; }} role="dialog" aria-modal="true" aria-label="Kullanıcı ekle" tabindex="-1">
		<div class="modal">
			<h2>{selectedSalon.name} — Kullanıcı Ekle</h2>
			<p class="muted">{salonUsers.length} / {selectedSalon.max_users} kullanıcı</p>
			{#if addUserError}<div class="alert-error">{addUserError}</div>{/if}
			<form class="modal-form" onsubmit={(e) => { e.preventDefault(); addUser(); }}>
				<label>Giriş Kullanıcı Adı *<input required bind:value={newUser.email} /></label>
				<label>Görünen Ad *<input required bind:value={newUser.username} /></label>
				<label>Şifre *<input type="password" required bind:value={newUser.password} /></label>
				<label>Rol
					<select bind:value={newUser.role}>
						<option value="staff">Personel</option>
						<option value="owner">Salon Sahibi</option>
					</select>
				</label>
				<div class="modal-actions">
					<button class="btn-primary" type="submit" disabled={addingUser}>{addingUser ? 'Ekleniyor…' : 'Kullanıcı Ekle'}</button>
					<button class="btn-ghost" type="button" onclick={() => (showAddUser = false)}>İptal</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.page { display: flex; flex-direction: column; gap: 1.5rem; }
	.page-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; }
	h1, h2, p { margin: 0; }
	h1 { font-size: clamp(1.6rem, 3vw, 2.4rem); font-weight: 900; }
	h2 { font-size: 1.05rem; font-weight: 900; color: #e2e8f0; }
	.eyebrow { margin-bottom: 0.25rem; color: #c59b31; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase; }
	.muted { color: #64748b; font-size: 0.88rem; }
	.muted-sm { color: #64748b; font-size: 0.82rem; }

	/* Layout */
	.layout { display: grid; grid-template-columns: 280px 1fr; gap: 1.25rem; align-items: start; }
	.panel { background: #172033; border: 1px solid rgba(226,232,240,0.1); border-radius: 10px; overflow: hidden; }

	/* Salon panel */
	.salon-panel { }
	.panel-head { display: flex; align-items: center; gap: 0.6rem; padding: 1rem 1.1rem; border-bottom: 1px solid rgba(226,232,240,0.08); }
	.count-badge { font-size: 0.72rem; font-weight: 700; color: #64748b; background: rgba(226,232,240,0.06); border-radius: 99px; padding: 0.1rem 0.5rem; }

	.salon-list { list-style: none; margin: 0; padding: 0.4rem; display: flex; flex-direction: column; gap: 0.2rem; }

	.salon-item {
		width: 100%; text-align: left; background: transparent; border: 1px solid transparent;
		border-radius: 7px; padding: 0.7rem 0.85rem; cursor: pointer; transition: all 0.13s; color: #e2e8f0;
	}
	.salon-item:hover { background: rgba(255,255,255,0.04); border-color: rgba(226,232,240,0.08); }
	.salon-item.active { background: rgba(197,155,49,0.08); border-color: rgba(197,155,49,0.3); }

	.si-name { font-weight: 800; font-size: 0.9rem; margin-bottom: 0.25rem; }
	.si-meta { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.3rem; }
	.si-footer { display: flex; align-items: center; gap: 0.4rem; }

	.city-tag { font-size: 0.7rem; font-weight: 700; color: #94a3b8; }
	.contract-tag { font-size: 0.68rem; font-weight: 700; color: #60a5fa; background: rgba(37,99,235,0.1); border-radius: 4px; padding: 0.05rem 0.35rem; }
	.si-date { font-size: 0.7rem; color: #475569; }
	.users-badge { font-size: 0.68rem; font-weight: 700; color: #94a3b8; }
	.smtp-badge { font-size: 0.68rem; font-weight: 700; color: #16a34a; background: rgba(22,163,74,0.1); border-radius: 4px; padding: 0.05rem 0.35rem; }

	/* Detail panel */
	.detail-panel { min-height: 400px; }
	.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 0.75rem; }
	.empty-icon { font-size: 2.5rem; opacity: 0.3; }
	.empty-state p { color: #475569; font-size: 0.9rem; }

	.detail-head {
		display: flex; align-items: center; justify-content: space-between; gap: 1rem;
		padding: 1rem 1.25rem; border-bottom: 1px solid rgba(226,232,240,0.08);
	}
	.detail-title h2 { font-size: 1rem; }

	.view-tabs { display: flex; gap: 0.2rem; background: rgba(0,0,0,0.25); border-radius: 8px; padding: 0.25rem; }
	.tab-btn {
		padding: 0.4rem 0.9rem; border-radius: 6px; border: none; background: transparent;
		color: #64748b; font-weight: 800; font-size: 0.82rem; cursor: pointer; transition: all 0.13s;
	}
	.tab-btn:hover { color: #94a3b8; }
	.tab-btn.active { background: #172033; color: #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.4); }

	.tab-body { padding: 1.25rem; }

	/* Users tab */
	.capacity-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
	.capacity-bar { flex: 1; height: 5px; border-radius: 99px; background: rgba(226,232,240,0.08); overflow: hidden; }
	.capacity-fill { height: 100%; border-radius: 99px; background: #c59b31; transition: width 0.3s; }
	.capacity-label { font-size: 0.75rem; color: #64748b; white-space: nowrap; }

	.user-list { display: flex; flex-direction: column; gap: 0.5rem; }
	.user-row { display: flex; align-items: center; gap: 0.85rem; padding: 0.75rem; border-radius: 8px; background: #101827; border: 1px solid rgba(226,232,240,0.07); }
	.user-avatar { width: 36px; height: 36px; border-radius: 50%; background: #1e40af; display: grid; place-items: center; font-weight: 900; font-size: 0.95rem; flex-shrink: 0; }
	.user-info { display: flex; flex-direction: column; gap: 0.1rem; flex: 1; }
	.user-info strong { font-size: 0.88rem; color: #e2e8f0; }
	.user-info span { font-size: 0.75rem; color: #64748b; }
	.user-right { display: flex; flex-direction: column; align-items: flex-end; gap: 0.3rem; }
	.role-badge { font-size: 0.65rem; font-weight: 900; padding: 0.15rem 0.45rem; border-radius: 99px; background: rgba(226,232,240,0.08); color: #64748b; }
	.role-badge.owner { background: rgba(197,155,49,0.15); color: #c59b31; }
	.date-sm { font-size: 0.68rem; color: #475569; }

	/* Settings tab */
	.settings-body { padding: 1.25rem; }
	.settings-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; }
	.settings-section { display: flex; flex-direction: column; gap: 0.65rem; }
	.section-label { font-size: 0.68rem; font-weight: 900; color: #c59b31; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.1rem; }

	label { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.78rem; font-weight: 800; color: #64748b; }
	input, select, textarea { border: 1px solid rgba(226,232,240,0.12); border-radius: 7px; padding: 0.5rem 0.65rem; background: #101827; color: #f8fafc; font: inherit; font-size: 0.85rem; box-sizing: border-box; width: 100%; min-height: 36px; }
	input:focus, select:focus, textarea:focus { outline: none; border-color: rgba(197,155,49,0.4); }
	textarea { resize: vertical; }

	.checkbox-label { flex-direction: row !important; align-items: center; gap: 0.5rem; }
	.checkbox-label input { width: auto; min-height: auto; accent-color: #c59b31; }
	.checkbox-label span { font-size: 0.82rem; color: #94a3b8; font-weight: 700; }

	.license-row { display: flex; gap: 0.4rem; }
	.lic-btn { flex: 1; min-height: 34px; border: 1px solid rgba(226,232,240,0.1); border-radius: 6px; background: #101827; color: #64748b; font-weight: 800; font-size: 0.85rem; cursor: pointer; transition: all 0.13s; }
	.lic-btn.active { border-color: #c59b31; background: rgba(197,155,49,0.12); color: #c59b31; }
	.date-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; }

	.settings-actions { display: flex; align-items: center; gap: 0.65rem; margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid rgba(226,232,240,0.08); }
	.danger-zone { margin-left: auto; }

	/* Buttons */
	.btn-primary { border: 0; border-radius: 7px; padding: 0.65rem 1.1rem; background: #c59b31; color: #fff; font-weight: 900; font-size: 0.88rem; cursor: pointer; }
	.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
	.btn-ghost { border: 1px solid rgba(226,232,240,0.12); border-radius: 7px; padding: 0.65rem 1rem; background: transparent; color: #94a3b8; font-weight: 800; font-size: 0.88rem; cursor: pointer; }
	.btn-sm { border: 1px solid rgba(197,155,49,0.3); border-radius: 6px; padding: 0.3rem 0.7rem; background: rgba(197,155,49,0.08); color: #c59b31; font-weight: 900; font-size: 0.78rem; cursor: pointer; white-space: nowrap; }
	.btn-remove { border: 1px solid rgba(239,68,68,0.2); border-radius: 5px; padding: 0.25rem 0.55rem; background: rgba(239,68,68,0.07); color: #fca5a5; font-size: 0.72rem; font-weight: 800; cursor: pointer; }
	.btn-remove:disabled, .btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
	.btn-danger { border: 1px solid rgba(239,68,68,0.25); border-radius: 7px; padding: 0.6rem 1rem; background: rgba(239,68,68,0.07); color: #f87171; font-weight: 800; font-size: 0.85rem; cursor: pointer; }
	.btn-danger:hover { background: rgba(239,68,68,0.14); }

	/* Alerts */
	.alert-error { padding: 0.75rem 1rem; border-radius: 8px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25); color: #fca5a5; font-size: 0.85rem; font-weight: 700; margin-bottom: 0.75rem; }
	.panel-alert { margin: 1rem 1.25rem 0; }

	/* Modals */
	.modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,0.72); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 1rem; }
	.modal { background: #172033; border: 1px solid rgba(226,232,240,0.12); border-radius: 14px; padding: 1.75rem; width: 100%; max-width: 500px; max-height: 90vh; overflow-y: auto; }
	.modal-form { display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1rem; }
	fieldset { border: 1px solid rgba(226,232,240,0.1); border-radius: 8px; padding: 1rem; display: flex; flex-direction: column; gap: 0.65rem; }
	legend { font-size: 0.7rem; font-weight: 900; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; padding: 0 0.5rem; }
	.modal-actions { display: flex; gap: 0.6rem; margin-top: 0.5rem; }

	@media (max-width: 1100px) { .settings-grid { grid-template-columns: 1fr 1fr; } }
	@media (max-width: 768px) { .layout { grid-template-columns: 1fr; } .settings-grid { grid-template-columns: 1fr; } }
</style>
