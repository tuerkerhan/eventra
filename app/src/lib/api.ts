const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || 'http://localhost:5174';

export function getToken(): string {
	if (typeof document === 'undefined') return '';
	const match = document.cookie.match(/(?:^|;\s*)token=([^;]*)/);
	return match ? decodeURIComponent(match[1]) : '';
}

export function setToken(token: string) {
	const secure = location.protocol === 'https:' ? '; Secure' : '';
	document.cookie = `token=${encodeURIComponent(token)}; path=/; max-age=${7 * 24 * 3600}; SameSite=Lax${secure}`;
}

export function clearToken() {
	const secure = location.protocol === 'https:' ? '; Secure' : '';
	document.cookie = `token=; path=/; max-age=0; SameSite=Lax${secure}`;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
	const headers: Record<string, string> = {};
	if (body !== undefined) headers['Content-Type'] = 'application/json';
	const token = getToken();
	if (token) headers['Authorization'] = `Bearer ${token}`;

	const res = await fetch(`${API}${path}`, {
		method,
		headers,
		body: body !== undefined ? JSON.stringify(body) : undefined
	});

	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`);
	}
	if (res.status === 204) return undefined as T;
	return res.json() as Promise<T>;
}

async function requestForm<T>(method: string, path: string, body: FormData): Promise<T> {
	const headers: Record<string, string> = {};
	const token = getToken();
	if (token) headers['Authorization'] = `Bearer ${token}`;
	const res = await fetch(`${API}${path}`, { method, headers, body });
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`);
	}
	if (res.status === 204) return undefined as T;
	return res.json() as Promise<T>;
}

export const api = {
	get: <T>(path: string) => request<T>('GET', path),
	post: <T>(path: string, body: unknown) => request<T>('POST', path, body),
	postForm: <T>(path: string, body: FormData) => requestForm<T>('POST', path, body),
	patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
	put: <T>(path: string, body: unknown) => request<T>('PUT', path, body),
	del: (path: string) => request<void>('DELETE', path)
};

// ─── Types ────────────────────────────────────────────────────────────────────

export interface EventTypeApi {
	id: string;
	name: string;
	color: string;
}

export interface EventCustomFieldApi {
	id?: string;
	key: string;
	label: string;
	value: string;
	field_type: string;
	options: string[];
	sort_order: number;
}

export interface EventApi {
	id: string;
	appointment_no: number | null;
	title: string;
	event_date: string;
	contract_date: string;
	start_time: string;
	end_time: string;
	type_id: string | null;
	event_type: EventTypeApi | null;
	reservation_status: string;
	tc_no: string;
	full_name: string;
	mobile_phone: string;
	phone: string;
	bride_groom: string;
	region: string;
	address: string;
	guest_count: number;
	total_fee: number;
	kapora_amount: number;
	kapora_paid: boolean;
	total_paid: number;
	payment_complete: boolean;
	payment_enabled: boolean;
	customer_payment_claimed: boolean;
	email: string;
	note: string;
	reminder_enabled: boolean;
	reminder_date: string;
	notifications_enabled: boolean;
	staff: string;
	customer_id: string | null;
	layout_id: string | null;
	seating_enabled: boolean;
	portal_token: string | null;
	portal_enabled: boolean;
	portal_title: string;
	portal_message: string;
	portal_org_type_id: string | null;
	portal_form_type_id: string | null;
	portal_layout_permission: boolean;
	portal_photos: { name: string; url: string }[];
	reserved_layout_ids: string[];
	custom_fields: EventCustomFieldApi[];
	created_at: string;
}

export interface EventTypeFieldDefApi {
	id: string;
	event_type_id: string;
	key: string;
	label: string;
	field_type: string;
	options: string[];
	is_required: boolean;
	sort_order: number;
}

export interface PaymentInstallmentApi {
	id: string;
	event_id: string;
	amount: number;
	added_by_name: string;
	created_at: string;
}

export interface VenueTableApi {
	id: string;
	table_no: number;
	shape: string;
	x: number;
	y: number;
	width: number;
	height: number;
	capacity: number;
	label: string;
}

export interface VenueLayoutApi {
	id: string;
	name: string;
	canvas_width: number;
	canvas_height: number;
	stage: Record<string, number>;
	walls: Record<string, unknown>[];
	tables: VenueTableApi[];
	created_at: string;
}

export interface CustomerApi {
	id: string;
	name: string;
	phone: string;
	email: string;
	tc_no: string;
	address: string;
	note: string;
	portal_active: boolean;
	portal_token: string | null;
	created_at: string;
	updated_at: string;
}

export interface SalonApi {
	id: string;
	name: string;
	address: string;
	currency: string;
	vat_rate: number;
	contract_prefix: string;
	reminder_days: number;
	max_users: number;
	payment_bank_name: string;
	payment_iban: string;
	payment_account_holder: string;
	payment_description: string;
	smtp_host: string;
	smtp_port: number;
	smtp_username: string;
	smtp_password: string;
	smtp_from_email: string;
	smtp_use_tls: boolean;
	notification_email: string;
	company_name: string;
	city: string;
	postal_code: string;
	phone: string;
	website: string;
	contract_no: string;
}

export interface SalonUserApi {
	id: string;
	email: string;
	username: string;
	role: string;
	is_active: boolean;
	created_at: string;
}

export interface SupportTicketApi {
	id: string;
	title: string;
	urgency: string;
	description: string;
	status: string;
	created_at: string;
	salon_name?: string;
}

export interface NotificationApi {
	id: string;
	event_id: string | null;
	type: string;
	title: string;
	message: string;
	is_read: boolean;
	created_at: string;
}

export interface ExpenseApi {
	id: string;
	title: string;
	amount: number;
	amount_type: 'fixed' | 'variable';
	currency: 'TRY' | 'USD' | 'EUR';
	recurrence: 'once' | 'weekly' | 'monthly' | 'yearly' | 'custom';
	custom_period_days: number | null;
	due_date: string;
	event_id: string | null;
	event_title: string | null;
	is_paid: boolean;
	is_approved: boolean;
	include_kdv: boolean;
	note: string;
	created_at: string;
}

export interface EventFormFieldDefApi {
	id: string;
	key: string;
	label: string;
	field_type: string;
	options: string[];
	placeholder_tag: string;
	is_visible: boolean;
	is_required: boolean;
	sort_order: number;
	is_builtin: boolean;
}

export interface OrgTypeFieldApi {
	id: string;
	event_type_id: string;
	key: string;
	label: string;
	field_type: string;
	options: string[];
	is_required: boolean;
	sort_order: number;
}

export interface CustomerFormTypeApi {
	id: string;
	name: string;
}

export interface CustomerFormTypeFieldApi {
	id: string;
	customer_form_type_id: string;
	key: string;
	label: string;
	field_type: string;
	options: string[];
	is_required: boolean;
	sort_order: number;
}

export interface PortalFormSubmissionApi {
	id: string;
	event_id: string;
	submitted_at: string;
	data: Record<string, unknown>;
}

export interface NotificationTemplateApi {
	id: string;
	event_type_id: string;
	days_before: number;
	message_template: string;
	is_active: boolean;
	created_at: string;
}

export interface EventNotificationScheduleApi {
	id: string;
	days_before: number;
	message: string;
	send_date: string;
	is_sent: boolean;
	sent_at: string | null;
}
