import { writable } from 'svelte/store';

export type FieldType = 'text' | 'number' | 'date' | 'time' | 'textarea' | 'select' | 'checkbox' | 'range';

export interface ContractField {
	key: string;
	label: string;
	value: string;
	type: FieldType;
	options?: string[];
}

export interface CalendarEvent {
	id: string;
	title: string;
	date: string;
	contractDate: string;
	start: string;
	end: string;
	type: string;
	reservationStatus: 'Kesin Rezervasyon' | 'Ön Rezervasyon';
	tcNo: string;
	fullName: string;
	mobilePhone: string;
	phone: string;
	brideGroom: string;
	region: string;
	address: string;
	guestCount: number;
	total: number;
	kapora: number;
	kaporaPaid: boolean;
	paid: number;
	paymentComplete: boolean;
	note: string;
	reminderEnabled: boolean;
	reminderDate: string;
	staff: string;
	contractFields: ContractField[];
}

const INITIAL_EVENTS: CalendarEvent[] = [
	{
		id: '2962', title: 'Ayşe & Ahmet', date: '2026-06-18', contractDate: '2026-06-08',
		start: '19:00', end: '23:30', type: 'Düğün', reservationStatus: 'Kesin Rezervasyon',
		tcNo: '12345678910', fullName: 'Ayşe Yılmaz', mobilePhone: '0532 000 00 00', phone: '',
		brideGroom: 'Ayşe Yılmaz & Ahmet Demir', region: 'Üsküdar', address: 'İnci Davet Salonu, İstanbul',
		guestCount: 420, total: 150000, kapora: 25000, kaporaPaid: true, paid: 25000, paymentComplete: false,
		note: 'Menü B, ekstra fotoğrafçı ve sahne ışığı istendi.', reminderEnabled: true,
		reminderDate: '2026-06-15', staff: 'Elif, Mert, Can',
		contractFields: [
			{ key: 'menu_package', label: 'Menü Paketi', value: 'Menü B', type: 'select', options: ['Menü A', 'Menü B', 'Menü C'] },
			{ key: 'music_start', label: 'Müzik Başlangıç', value: '20:00', type: 'time' },
			{ key: 'special_clause', label: 'Özel Madde', value: 'Salon süslemesi altın-beyaz tema olacaktır.', type: 'textarea' }
		]
	},
	{
		id: '2963', title: 'Burcu & Cem', date: '2026-06-25', contractDate: '2026-06-10',
		start: '20:00', end: '00:00', type: 'Nişan', reservationStatus: 'Kesin Rezervasyon',
		tcNo: '', fullName: 'Burcu Kaya', mobilePhone: '0544 111 22 33', phone: '',
		brideGroom: 'Burcu Kaya & Cem Arslan', region: 'Kadıköy', address: 'İnci Davet Teras Salonu',
		guestCount: 180, total: 85000, kapora: 15000, kaporaPaid: true, paid: 50000, paymentComplete: false,
		note: 'Pasta dışarıdan gelecek.', reminderEnabled: true, reminderDate: '2026-06-22', staff: 'Mert, Seda',
		contractFields: [
			{ key: 'menu_package', label: 'Menü Paketi', value: 'Menü A', type: 'select', options: ['Menü A', 'Menü B', 'Menü C'] },
			{ key: 'stage_request', label: 'Sahne Talebi', value: 'Küçük sahne', type: 'text' }
		]
	},
	{
		id: '2964', title: 'Derya & Emre', date: '2026-07-02', contractDate: '2026-06-12',
		start: '14:00', end: '18:00', type: 'Kına', reservationStatus: 'Kesin Rezervasyon',
		tcNo: '', fullName: 'Derya Aksoy', mobilePhone: '0555 222 33 44', phone: '',
		brideGroom: 'Derya Aksoy & Emre Çelik', region: 'Ataşehir', address: 'İnci Davet Salon 2',
		guestCount: 140, total: 60000, kapora: 10000, kaporaPaid: true, paid: 60000, paymentComplete: true,
		note: 'Kına tahtı ve giriş müziği hazır.', reminderEnabled: false, reminderDate: '', staff: 'Seda, Can',
		contractFields: [{ key: 'henna_set', label: 'Kına Seti', value: 'Premium', type: 'text' }]
	}
];

export const INITIAL_EVENT_TYPES = [
	{ name: 'Düğün', color: '#b45309' },
	{ name: 'Nişan', color: '#7c3aed' },
	{ name: 'Kına', color: '#be123c' },
	{ name: 'Kurumsal', color: '#0f766e' },
	{ name: 'Mezuniyet', color: '#2563eb' }
];

export const eventsStore = writable<CalendarEvent[]>(INITIAL_EVENTS);
export const eventTypesStore = writable<{ name: string; color: string }[]>(INITIAL_EVENT_TYPES);
