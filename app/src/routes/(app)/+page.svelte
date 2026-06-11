<script lang="ts">
	interface Event {
		id: string;
		couple: string;
		date: string;
		startTime: string;
		endTime: string;
		type: string;
		totalPrice: number;
		paidAmount: number;
		paymentStatus: 'KAPORA_ALINDI' | 'KISMI_ODEME' | 'TAMAMLANDI';
		contractSigned: boolean;
		orgDetailsReceived: boolean;
	}

	const today = new Date('2026-06-11');
	
	const getDaysLeft = (eventDateStr: string) => {
		const parts = eventDateStr.split('.');
		const targetDate = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
		const diffTime = targetDate.getTime() - today.getTime();
		return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
	};

	const upcomingEvents: Event[] = [
		{
			id: '2962',
			couple: 'Ayşe & Ahmet',
			date: '18.06.2026',
			startTime: '19:00',
			endTime: '23:30',
			type: 'DÜĞÜN',
			totalPrice: 150000,
			paidAmount: 25000,
			paymentStatus: 'KAPORA_ALINDI',
			contractSigned: true,
			orgDetailsReceived: false
		},
		{
			id: '2963',
			couple: 'Burcu & Cem',
			date: '25.06.2026',
			startTime: '20:00',
			endTime: '24:00',
			type: 'NİŞAN',
			totalPrice: 85000,
			paidAmount: 50000,
			paymentStatus: 'KISMI_ODEME',
			contractSigned: true,
			orgDetailsReceived: true
		},
		{
			id: '2964',
			couple: 'Derya & Emre',
			date: '02.07.2026',
			startTime: '14:00',
			endTime: '18:00',
			type: 'KINA',
			totalPrice: 60000,
			paidAmount: 60000,
			paymentStatus: 'TAMAMLANDI',
			contractSigned: true,
			orgDetailsReceived: true
		}
	];

	const getStatusColor = (status: string) => {
		if (status === 'KAPORA_ALINDI') return '#ef4444'; 
		if (status === 'KISMI_ODEME') return '#3b82f6';   
		if (status === 'TAMAMLANDI') return '#10b981';    
		return '#94a3b8';
	};
</script>

<div class="dashboard-wrapper">
	<div class="page-header">
		<h1 class="section-title">Yaklaşan Etkinlikler & Rezervasyonlar</h1>
		<p class="section-subtitle">Tüm operasyonel süreçlerinizi buradan takip edebilirsiniz.</p>
	</div>

	<div class="events-grid">
		{#each upcomingEvents as event}
			<div class="event-card" style="border-top: 4px solid {getStatusColor(event.paymentStatus)}">
				
				<div class="event-header">
					<div class="date-badge">
						<span class="day">{event.date.split('.')[0]}</span>
						<span class="month">{event.date.split('.')[1]}/{event.date.split('.')[2]}</span>
					</div>
					<div class="event-main-info">
						<h3 class="couple-name">{event.couple} <span class="event-type">({event.type})</span></h3>
						<div class="time-info">⏰ {event.startTime} - {event.endTime} | Sözleşme No: #{event.id}</div>
					</div>
					<div class="countdown">
						<div class="days-left">{getDaysLeft(event.date)}</div>
						<div class="days-label">GÜN KALDI</div>
					</div>
				</div>

				<hr class="card-divider" />

				<div class="event-details">
					<div class="finance-block">
						<div class="finance-status" style="color: {getStatusColor(event.paymentStatus)}">
							{event.paymentStatus.replace('_', ' ')}
						</div>
						<div class="finance-numbers">
							<div class="amount-row">
								<span>Toplam:</span>
								<strong>₺{event.totalPrice.toLocaleString('tr-TR')}</strong>
							</div>
							<div class="amount-row">
								<span>Alınan:</span>
								<strong style="color: #D4AF37">₺{event.paidAmount.toLocaleString('tr-TR')}</strong>
							</div>
							<div class="amount-row remaining">
								<span>Kalan:</span>
								<strong>₺{(event.totalPrice - event.paidAmount).toLocaleString('tr-TR')}</strong>
							</div>
						</div>
					</div>

					<div class="checklist-block">
						<h4 class="checklist-title">Operasyon Durumu</h4>
						<label class="check-item">
							<input type="checkbox" checked={event.contractSigned} disabled />
							<span class="check-text">Sözleşme İmzalandı</span>
						</label>
						<label class="check-item">
							<input type="checkbox" checked={event.orgDetailsReceived} disabled />
							<span class="check-text">Organizasyon Bilgileri Alındı</span>
						</label>
					</div>
				</div>
				
				<div class="action-block">
					<button class="detail-btn">Sözleşme Detaylarına Git</button>
				</div>
			</div>
		{/each}
	</div>
</div>

<style>
	.dashboard-wrapper {
		display: flex;
		flex-direction: column;
		gap: 2rem;
		max-width: 1600px;
		margin: 0 auto; /* Ekranı ortalar */
	}

	.page-header {
		margin-bottom: 1rem;
	}

	.section-title {
		color: #D4AF37;
		margin: 0 0 0.5rem 0;
		font-size: 2rem;
		font-weight: 800;
	}

	.section-subtitle {
		color: #94a3b8;
		margin: 0;
		font-size: 1rem;
	}

	/* YATAY DÜZEN: Kartlar ekran genişliğine göre yan yana dizilir */
	.events-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(600px, 1fr));
		gap: 2rem;
	}

	.event-card {
		background: #1C2438;
		border-radius: 12px;
		padding: 1.5rem;
		box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
		display: flex;
		flex-direction: column;
		gap: 1rem;
		transition: transform 0.2s, box-shadow 0.2s;
	}

	.event-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
	}

	.event-header {
		display: flex;
		align-items: center;
		gap: 1.5rem;
	}

	.date-badge {
		background: #0B132B;
		border: 1px solid #D4AF37;
		border-radius: 8px;
		padding: 1rem;
		text-align: center;
		min-width: 80px;
	}

	.day { display: block; font-size: 2rem; font-weight: 800; color: #F6EEDC; line-height: 1; }
	.month { display: block; font-size: 0.9rem; color: #D4AF37; margin-top: 5px; }

	.event-main-info { flex-grow: 1; }
	.couple-name { color: #F6EEDC; font-size: 1.6rem; margin: 0 0 0.5rem 0; }
	.event-type { color: #D4AF37; font-weight: normal; font-size: 1.1rem; }
	.time-info { color: #94a3b8; font-size: 0.95rem; }

	.countdown {
		background: rgba(212, 175, 55, 0.05);
		padding: 1rem 1.5rem;
		border-radius: 8px;
		text-align: center;
		border: 1px dashed rgba(212, 175, 55, 0.3);
	}

	.days-left { font-size: 2.2rem; font-weight: 800; color: #D4AF37; line-height: 1; }
	.days-label { font-size: 0.8rem; color: #F6EEDC; margin-top: 4px; letter-spacing: 1px; }

	.card-divider { border: none; height: 1px; background: rgba(212, 175, 55, 0.1); margin: 0.5rem 0; }

	.event-details {
		display: flex;
		gap: 1.5rem;
	}

	.finance-block {
		flex: 1;
		background: #0B132B;
		padding: 1.2rem;
		border-radius: 8px;
	}

	.finance-status { font-weight: 800; font-size: 1rem; margin-bottom: 1rem; letter-spacing: 0.5px; }
	.finance-numbers { display: flex; flex-direction: column; gap: 0.5rem; color: #F6EEDC; font-size: 0.95rem; }
	.amount-row { display: flex; justify-content: space-between; align-items: center; }
	.amount-row.remaining { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed rgba(212, 175, 55, 0.2); font-size: 1.1rem; }

	.checklist-block {
		flex: 1;
		background: rgba(11, 19, 43, 0.5);
		padding: 1.2rem;
		border-radius: 8px;
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.checklist-title { color: #94a3b8; margin: 0; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }
	.check-item { display: flex; align-items: center; gap: 0.8rem; color: #F6EEDC; font-size: 0.95rem; }
	.check-item input[type="checkbox"] { width: 18px; height: 18px; accent-color: #D4AF37; }

	.action-block { margin-top: 0.5rem; }
	
	.detail-btn {
		width: 100%;
		background: #1C2438;
		color: #D4AF37;
		border: 1px solid #D4AF37;
		padding: 1rem;
		border-radius: 8px;
		font-weight: 700;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.detail-btn:hover { background: #D4AF37; color: #0B132B; }
</style>