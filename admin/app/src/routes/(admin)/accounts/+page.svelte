<script lang="ts">
	import { onMount } from 'svelte';

	const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

	interface Salon {
		id: string;
		name: string;
		address: string;
		currency: string;
		max_users: number;
		created_at: string;
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

	// Create salon form
	let showCreateSalon = $state(false);
	let newSalon = $state({
		name: '', address: '', currency: 'TRY', vat_rate: 20, contract_prefix: 'EVT',
		reminder_days: 3, max_users: 1,
		owner_email: '', owner_username: '', owner_password: ''
	});
	let createError = $state('');
	let creating = $state(false);

	// Add user form
	let showAddUser = $state(false);
	let newUser = $state({ email: '', username: '', password: '', role: 'staff' });
	let addUserError = $state('');
	let addingUser = $state(false);

	const headers = () => ({
		'Content-Type': 'application/json',
		Authorization: `Bearer ${localStorage.getItem('admin_token')}`
	});

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
		loadUsers(salon.id);
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
			newSalon = { name: '', address: '', currency: 'TRY', vat_rate: 20, contract_prefix: 'EVT', reminder_days: 3, max_users: 1, owner_email: '', owner_username: '', owner_password: '' };
			await loadSalons();
		} else {
			const d = await r.json();
			createError = d.detail ?? 'Salon oluşturulamadı';
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
			const d = await r.json();
			addUserError = d.detail ?? 'Kullanıcı eklenemedi';
		}
	};

	const removeUser = async (userId: string) => {
		if (!selectedSalon) return;
		if (!confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) return;
		await fetch(`${API}/admin/salons/${selectedSalon.id}/users/${userId}`, { method: 'DELETE', headers: headers() });
		await loadUsers(selectedSalon.id);
	};

	const formatDate = (d: string) => new Date(d).toLocaleDateString('tr-TR', { year: 'numeric', month: 'short', day: 'numeric' });

	onMount(loadSalons);
</script>

<div class="accounts-shell">
	<div class="page-head">
		<div>
			<p class="eyebrow">Admin</p>
			<h1>Salonlar & Hesaplar</h1>
		</div>
		<button class="primary-btn" type="button" onclick={() => (showCreateSalon = true)}>+ Yeni Salon</button>
	</div>

	<div class="accounts-grid">
		<!-- Salon list -->
		<section class="panel">
			<h2>Salonlar <span class="count">{salons.length}</span></h2>
			{#if loading}
				<p class="muted">Yükleniyor…</p>
			{:else if salons.length === 0}
				<p class="muted">Henüz salon yok.</p>
			{:else}
				<div class="salon-list">
					{#each salons as salon}
						<button
							class="salon-item"
							class:selected={selectedSalon?.id === salon.id}
							type="button"
							onclick={() => selectSalon(salon)}
						>
							<div class="salon-name">{salon.name}</div>
							<div class="salon-meta">
								<span class="badge">{salon.max_users} kullanıcı</span>
								<span class="date">{formatDate(salon.created_at)}</span>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</section>

		<!-- Users panel -->
		<section class="panel">
			{#if !selectedSalon}
				<div class="empty-users">
					<p>Kullanıcıları görmek için sol taraftan bir salon seçin.</p>
				</div>
			{:else}
				<div class="users-head">
					<div>
						<h2>{selectedSalon.name}</h2>
						<p class="muted">{selectedSalon.address || 'Adres girilmemiş'}</p>
					</div>
					<div class="users-head-meta">
						<span class="badge">Lisans: {selectedSalon.max_users} kişi</span>
						{#if salonUsers.length < selectedSalon.max_users}
							<button class="add-user-btn" type="button" onclick={() => (showAddUser = true)}>+ Kullanıcı Ekle</button>
						{/if}
					</div>
				</div>

				<div class="capacity-bar">
					<div class="capacity-fill" style="width: {(salonUsers.length / selectedSalon.max_users) * 100}%"></div>
				</div>
				<p class="capacity-label">{salonUsers.length} / {selectedSalon.max_users} kullanıcı</p>

				{#if usersLoading}
					<p class="muted">Kullanıcılar yükleniyor…</p>
				{:else}
					<div class="user-list">
						{#each salonUsers as user}
							<div class="user-card">
								<div class="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
								<div class="user-info">
									<strong>{user.username}</strong>
									<span>{user.email}</span>
									<span class="role-badge" class:owner={user.role === 'owner'}>{user.role === 'owner' ? 'Salon Sahibi' : 'Personel'}</span>
								</div>
								<div class="user-actions">
									<span class="created-date">{formatDate(user.created_at)}</span>
									{#if user.role !== 'owner'}
										<button class="remove-btn" type="button" onclick={() => removeUser(user.id)}>Kaldır</button>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			{/if}
		</section>
	</div>
</div>

<!-- Create Salon Modal -->
{#if showCreateSalon}
	<div class="modal-backdrop" onclick={() => (showCreateSalon = false)} role="dialog" aria-modal="true" aria-label="Yeni salon oluştur">
		<div class="modal" onclick={(e) => e.stopPropagation()} role="document">
			<h2>Yeni Salon Oluştur</h2>

			{#if createError}
				<div class="error-msg">{createError}</div>
			{/if}

			<form class="modal-form" onsubmit={(e) => { e.preventDefault(); createSalon(); }}>
				<fieldset>
					<legend>Salon Bilgileri</legend>
					<label><span>Salon Adı *</span><input required bind:value={newSalon.name} placeholder="İnci Davet" /></label>
					<label><span>Adres</span><textarea rows="2" bind:value={newSalon.address} placeholder="İstanbul"></textarea></label>
					<label>
						<span>Para Birimi</span>
						<select bind:value={newSalon.currency}><option>TRY</option><option>EUR</option><option>USD</option></select>
					</label>
					<label><span>Sözleşme Prefix</span><input bind:value={newSalon.contract_prefix} placeholder="EVT" /></label>
					<label>
						<span>Kullanıcı Lisansı (maks. {newSalon.max_users} kişi)</span>
						<div class="license-select">
							{#each [1, 2, 3] as n}
								<button
									type="button"
									class="license-btn"
									class:active={newSalon.max_users === n}
									onclick={() => (newSalon.max_users = n)}
								>
									{n} kişi
								</button>
							{/each}
						</div>
					</label>
				</fieldset>

				<fieldset>
					<legend>Salon Sahibi Hesabı</legend>
					<label><span>E-posta *</span><input type="email" required bind:value={newSalon.owner_email} placeholder="sahip@salon.com" /></label>
					<label><span>Kullanıcı Adı *</span><input required bind:value={newSalon.owner_username} placeholder="salonadi" /></label>
					<label><span>Şifre *</span><input type="password" required bind:value={newSalon.owner_password} placeholder="En az 8 karakter" /></label>
				</fieldset>

				<div class="modal-actions">
					<button class="primary-btn" type="submit" disabled={creating}>{creating ? 'Oluşturuluyor…' : 'Salon Oluştur'}</button>
					<button class="cancel-btn" type="button" onclick={() => (showCreateSalon = false)}>İptal</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<!-- Add User Modal -->
{#if showAddUser && selectedSalon}
	<div class="modal-backdrop" onclick={() => (showAddUser = false)} role="dialog" aria-modal="true" aria-label="Kullanıcı ekle">
		<div class="modal" onclick={(e) => e.stopPropagation()} role="document">
			<h2>{selectedSalon.name} – Kullanıcı Ekle</h2>
			<p class="muted">Bu salona yeni bir kullanıcı ekleyin. ({salonUsers.length}/{selectedSalon.max_users} kullanıcı)</p>

			{#if addUserError}
				<div class="error-msg">{addUserError}</div>
			{/if}

			<form class="modal-form" onsubmit={(e) => { e.preventDefault(); addUser(); }}>
				<label><span>E-posta *</span><input type="email" required bind:value={newUser.email} /></label>
				<label><span>Kullanıcı Adı *</span><input required bind:value={newUser.username} /></label>
				<label><span>Şifre *</span><input type="password" required bind:value={newUser.password} /></label>
				<label>
					<span>Rol</span>
					<select bind:value={newUser.role}>
						<option value="staff">Personel</option>
						<option value="owner">Salon Sahibi</option>
					</select>
				</label>
				<div class="modal-actions">
					<button class="primary-btn" type="submit" disabled={addingUser}>{addingUser ? 'Ekleniyor…' : 'Kullanıcı Ekle'}</button>
					<button class="cancel-btn" type="button" onclick={() => (showAddUser = false)}>İptal</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.accounts-shell { display: flex; flex-direction: column; gap: 1.5rem; }

	.page-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; }
	h1, h2, p { margin: 0; }
	h1 { font-size: clamp(1.6rem, 3vw, 2.4rem); font-weight: 900; }
	h2 { font-size: 1.1rem; font-weight: 900; }

	.eyebrow { margin-bottom: 0.25rem; color: #c59b31; font-size: 0.72rem; font-weight: 900; letter-spacing: 0.1em; text-transform: uppercase; }

	.primary-btn { border: 0; border-radius: 8px; padding: 0.75rem 1.2rem; background: #c59b31; color: #fff; font-weight: 900; cursor: pointer; }

	.accounts-grid { display: grid; grid-template-columns: 300px 1fr; gap: 1.25rem; align-items: start; }

	.panel { background: #172033; border: 1px solid rgba(226,232,240,0.1); border-radius: 10px; padding: 1.25rem; }

	.count { font-size: 0.8rem; font-weight: 700; color: #64748b; margin-left: 0.4rem; }
	.muted { color: #64748b; font-size: 0.88rem; }

	.salon-list { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 1rem; }

	.salon-item {
		width: 100%; text-align: left; border: 1px solid rgba(226,232,240,0.1); border-radius: 8px;
		padding: 0.85rem 1rem; background: #101827; color: #f8fafc; cursor: pointer;
		transition: all 0.15s;
	}
	.salon-item:hover { border-color: rgba(197,155,49,0.3); }
	.salon-item.selected { border-color: #c59b31; background: rgba(197,155,49,0.08); }
	.salon-name { font-weight: 800; margin-bottom: 0.3rem; }
	.salon-meta { display: flex; align-items: center; gap: 0.65rem; }

	.badge { font-size: 0.72rem; font-weight: 900; padding: 0.2rem 0.5rem; border-radius: 99px; background: rgba(197,155,49,0.15); color: #c59b31; }
	.date { font-size: 0.75rem; color: #64748b; }

	.empty-users { display: flex; align-items: center; justify-content: center; min-height: 200px; }
	.empty-users p { color: #64748b; text-align: center; }

	.users-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
	.users-head-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem; }

	.add-user-btn { border: 1px solid rgba(197,155,49,0.35); border-radius: 7px; padding: 0.5rem 0.85rem; background: rgba(197,155,49,0.1); color: #c59b31; font-weight: 900; font-size: 0.82rem; cursor: pointer; }

	.capacity-bar { height: 6px; border-radius: 99px; background: rgba(226,232,240,0.1); margin: 0.75rem 0 0.25rem; overflow: hidden; }
	.capacity-fill { height: 100%; border-radius: 99px; background: #c59b31; transition: width 0.3s; }
	.capacity-label { font-size: 0.75rem; color: #64748b; margin-bottom: 1rem; }

	.user-list { display: flex; flex-direction: column; gap: 0.65rem; }
	.user-card { display: flex; align-items: center; gap: 0.85rem; padding: 0.85rem; border-radius: 8px; background: #101827; border: 1px solid rgba(226,232,240,0.08); }

	.user-avatar { width: 38px; height: 38px; border-radius: 50%; background: #1e40af; display: grid; place-items: center; font-weight: 900; font-size: 1rem; flex-shrink: 0; }
	.user-info { display: flex; flex-direction: column; gap: 0.15rem; flex: 1; }
	.user-info strong { font-size: 0.9rem; }
	.user-info span { font-size: 0.78rem; color: #64748b; }

	.role-badge { display: inline-block; font-size: 0.68rem; font-weight: 900; padding: 0.15rem 0.45rem; border-radius: 99px; background: rgba(226,232,240,0.08); color: #94a3b8; width: fit-content; }
	.role-badge.owner { background: rgba(197,155,49,0.15); color: #c59b31; }

	.user-actions { display: flex; flex-direction: column; align-items: flex-end; gap: 0.35rem; }
	.created-date { font-size: 0.72rem; color: #475569; }
	.remove-btn { border: 1px solid rgba(239,68,68,0.25); border-radius: 6px; padding: 0.3rem 0.65rem; background: rgba(239,68,68,0.08); color: #fca5a5; font-size: 0.75rem; font-weight: 800; cursor: pointer; }

	/* Modals */
	.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 1rem; }
	.modal { background: #172033; border: 1px solid rgba(226,232,240,0.12); border-radius: 14px; padding: 2rem; width: 100%; max-width: 520px; max-height: 90vh; overflow-y: auto; }

	.modal-form { display: flex; flex-direction: column; gap: 0.85rem; margin-top: 1.25rem; }
	fieldset { border: 1px solid rgba(226,232,240,0.1); border-radius: 8px; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
	legend { font-size: 0.75rem; font-weight: 900; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; padding: 0 0.5rem; }

	label { display: flex; flex-direction: column; gap: 0.35rem; font-weight: 800; font-size: 0.85rem; color: #94a3b8; }
	input, select, textarea { width: 100%; min-height: 40px; border: 1px solid rgba(226,232,240,0.15); border-radius: 8px; padding: 0.55rem 0.75rem; background: #101827; color: #f8fafc; font: inherit; }
	textarea { resize: vertical; }

	.license-select { display: flex; gap: 0.5rem; }
	.license-btn { flex: 1; min-height: 40px; border: 1px solid rgba(226,232,240,0.15); border-radius: 7px; background: #101827; color: #94a3b8; font-weight: 800; cursor: pointer; transition: all 0.15s; }
	.license-btn.active { border-color: #c59b31; background: rgba(197,155,49,0.12); color: #c59b31; }

	.modal-actions { display: flex; gap: 0.65rem; margin-top: 0.5rem; }
	.cancel-btn { border: 1px solid rgba(226,232,240,0.15); border-radius: 8px; padding: 0.75rem 1.2rem; background: transparent; color: #94a3b8; font-weight: 800; cursor: pointer; }

	.error-msg { padding: 0.85rem 1rem; border-radius: 8px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.25); color: #fca5a5; font-size: 0.88rem; font-weight: 700; }

	@media (max-width: 768px) { .accounts-grid { grid-template-columns: 1fr; } }
</style>
