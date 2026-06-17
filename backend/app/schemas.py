from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr


# ─── Auth ────────────────────────────────────────────────────────────────────

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    salon_id: str | None = None
    username: str | None = None


class LoginIn(BaseModel):
    email: str
    password: str


# ─── Admin ───────────────────────────────────────────────────────────────────

class AdminCreateIn(BaseModel):
    email: str
    password: str
    admin_secret: str


class SalonCreateIn(BaseModel):
    name: str
    company_name: str = ""
    address: str = ""
    city: str = ""
    postal_code: str = ""
    phone: str = ""
    website: str = ""
    currency: str = "TRY"
    vat_rate: float = 20.0
    contract_prefix: str = "EVT"
    reminder_days: int = 3
    salon_count: int = 1
    max_users: int = 5
    subscription_start: str = ""
    subscription_end: str = ""
    notification_email: str = ""
    owner_email: str
    owner_username: str
    owner_password: str


class SalonOut(BaseModel):
    id: str
    name: str
    company_name: str = ""
    address: str
    city: str = ""
    postal_code: str = ""
    phone: str = ""
    website: str = ""
    currency: str
    vat_rate: float
    contract_prefix: str
    contract_no: int = 0
    reminder_days: int
    salon_count: int = 1
    max_users: int
    subscription_start: str = ""
    subscription_end: str = ""
    created_at: datetime
    payment_bank_name: str = ""
    payment_iban: str = ""
    payment_account_holder: str = ""
    payment_description: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    notification_email: str = ""

    model_config = {"from_attributes": True}


class SalonUserOut(BaseModel):
    id: str
    salon_id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SalonUserCreateIn(BaseModel):
    email: str
    username: str
    password: str
    role: str = "staff"


# ─── Settings ────────────────────────────────────────────────────────────────

class UserPrefsOut(BaseModel):
    id: str
    email: str
    username: str
    role: str
    ui_mode: str

    model_config = {"from_attributes": True}


class UserPrefsUpdate(BaseModel):
    ui_mode: str | None = None


class SalonUpdateIn(BaseModel):
    name: str | None = None
    company_name: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    website: str | None = None
    currency: str | None = None
    vat_rate: float | None = None
    contract_prefix: str | None = None
    reminder_days: int | None = None
    salon_count: int | None = None
    max_users: int | None = None
    subscription_start: str | None = None
    subscription_end: str | None = None
    payment_bank_name: str | None = None
    payment_iban: str | None = None
    payment_account_holder: str | None = None
    payment_description: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool | None = None
    notification_email: str | None = None


# ─── Admin Settings ───────────────────────────────────────────────────────────

class AdminSettingsIn(BaseModel):
    support_phone: str = ""
    booking_link: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    shared_support_email: str = ""


class AdminSettingsOut(BaseModel):
    id: str
    support_phone: str
    booking_link: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_use_tls: bool
    shared_support_email: str

    model_config = {"from_attributes": True}


# ─── Support Tickets ──────────────────────────────────────────────────────────

class SupportTicketIn(BaseModel):
    title: str
    urgency: str = "normal"
    description: str = ""


class SupportTicketOut(BaseModel):
    id: str
    salon_id: str
    salon_name: str = ""
    user_id: str | None
    title: str
    urgency: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SupportTicketUpdateIn(BaseModel):
    status: str | None = None


# ─── Admin Notifications ──────────────────────────────────────────────────────

class AdminNotificationOut(BaseModel):
    id: str
    type: str
    title: str
    message: str
    salon_id: str | None
    ref_id: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Admin Broadcast ──────────────────────────────────────────────────────────

class AdminBroadcastIn(BaseModel):
    subject: str
    body: str
    salon_ids: list[str] | None = None  # None = all
    send_email: bool = True
    send_notification: bool = True


class AdminTestMailIn(BaseModel):
    to_email: str


class CustomerFieldDefIn(BaseModel):
    key: str
    label: str
    field_type: str = "text"
    options: list[str] = []
    is_required: bool = False
    sort_order: int = 0
    default_value: str = ""


class CustomerFieldDefOut(BaseModel):
    id: str
    key: str
    label: str
    field_type: str
    options: list[str]
    is_required: bool
    sort_order: int
    default_value: str

    model_config = {"from_attributes": True}


# ─── Org Type Fields ─────────────────────────────────────────────────────────

class OrgTypeFieldIn(BaseModel):
    event_type_id: str
    key: str
    label: str
    field_type: str = "text"
    options: list[str] = []
    is_required: bool = False
    sort_order: int = 0


class OrgTypeFieldOut(BaseModel):
    id: str
    event_type_id: str
    key: str
    label: str
    field_type: str
    options: list[str]
    is_required: bool
    sort_order: int

    model_config = {"from_attributes": True}


# ─── Customers ───────────────────────────────────────────────────────────────

class CustomerFieldValueIn(BaseModel):
    field_def_id: str
    value: str


class CustomerIn(BaseModel):
    name: str
    phone: str = ""
    email: str = ""
    tc_no: str = ""
    address: str = ""
    note: str = ""
    portal_active: bool = False
    custom_values: list[CustomerFieldValueIn] = []


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    tc_no: str | None = None
    address: str | None = None
    note: str | None = None
    portal_active: bool | None = None
    custom_values: list[CustomerFieldValueIn] | None = None


class CustomerFieldValueOut(BaseModel):
    field_def_id: str
    key: str
    label: str
    field_type: str
    options: list[str]
    value: str

    model_config = {"from_attributes": True}


class CustomerOut(BaseModel):
    id: str
    name: str
    phone: str
    email: str
    tc_no: str
    address: str
    note: str
    portal_active: bool
    portal_token: str | None
    created_at: datetime
    updated_at: datetime
    custom_values: list[CustomerFieldValueOut] = []

    model_config = {"from_attributes": True}


# ─── Events ──────────────────────────────────────────────────────────────────

class EventCustomFieldIn(BaseModel):
    key: str
    label: str
    value: str = ""
    field_type: str = "text"
    options: list[str] = []
    sort_order: int = 0


class EventLayoutReservationOut(BaseModel):
    id: str
    layout_id: str
    layout_name: str = ""

    model_config = {"from_attributes": True}


class EventIn(BaseModel):
    title: str
    event_date: str
    contract_date: str = ""
    start_time: str = "19:00"
    end_time: str = "23:00"
    type_id: str | None = None
    reservation_status: str = "Ön Rezervasyon"
    tc_no: str = ""
    full_name: str = ""
    mobile_phone: str = ""
    phone: str = ""
    bride_groom: str = ""
    region: str = ""
    address: str = ""
    guest_count: int = 0
    total_fee: float = 0
    kapora_amount: float = 0
    kapora_paid: bool = False
    total_paid: float = 0
    payment_complete: bool = False
    payment_enabled: bool = False
    email: str = ""
    note: str = ""
    reminder_enabled: bool = False
    reminder_date: str = ""
    notifications_enabled: bool = True
    staff: str = ""
    customer_id: str | None = None
    layout_id: str | None = None
    seating_enabled: bool = False
    # Portal
    portal_enabled: bool = False
    portal_title: str = "Davetiniz"
    portal_message: str = ""
    portal_org_type_id: str | None = None
    portal_form_type_id: str | None = None
    portal_layout_permission: bool = False
    reserved_layout_ids: list[str] = []
    custom_fields: list[EventCustomFieldIn] = []


class EventUpdate(EventIn):
    title: str | None = None
    event_date: str | None = None


class EventCustomFieldOut(BaseModel):
    id: str
    key: str
    label: str
    value: str
    field_type: str
    options: list[str]
    sort_order: int

    model_config = {"from_attributes": True}


class EventTypeIn(BaseModel):
    name: str
    color: str = "#64748b"


class EventTypeOut(BaseModel):
    id: str
    name: str
    color: str

    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: str
    appointment_no: int | None = None
    title: str
    event_date: str
    contract_date: str
    start_time: str
    end_time: str
    type_id: str | None
    event_type: EventTypeOut | None = None
    reservation_status: str
    tc_no: str
    full_name: str
    mobile_phone: str
    phone: str
    bride_groom: str
    region: str
    address: str
    guest_count: int
    total_fee: float
    kapora_amount: float
    kapora_paid: bool
    total_paid: float
    payment_complete: bool
    payment_enabled: bool = False
    customer_payment_claimed: bool = False
    email: str = ""
    note: str
    reminder_enabled: bool
    reminder_date: str
    notifications_enabled: bool = True
    staff: str
    customer_id: str | None
    layout_id: str | None
    seating_enabled: bool
    portal_token: str | None
    portal_enabled: bool
    portal_title: str = "Davetiniz"
    portal_message: str = ""
    portal_org_type_id: str | None
    portal_form_type_id: str | None
    portal_layout_permission: bool
    portal_photos: list[dict] = []
    reserved_layout_ids: list[str] = []
    custom_fields: list[EventCustomFieldOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Venue Layout ─────────────────────────────────────────────────────────────

class VenueTableIn(BaseModel):
    table_no: int
    shape: str = "square"
    x: float = 0
    y: float = 0
    width: float = 80
    height: float = 80
    capacity: int = 8
    label: str = ""


class VenueTableOut(BaseModel):
    id: str
    table_no: int
    shape: str
    x: float
    y: float
    width: float
    height: float
    capacity: int
    label: str

    model_config = {"from_attributes": True}


class VenueLayoutIn(BaseModel):
    name: str = "Ana Salon"
    canvas_width: int = 900
    canvas_height: int = 600
    stage: dict[str, Any] = {"x": 300, "y": 20, "width": 300, "height": 80}
    walls: list[dict[str, Any]] = []
    tables: list[VenueTableIn] = []


class VenueLayoutOut(BaseModel):
    id: str
    name: str
    canvas_width: int
    canvas_height: int
    stage: dict[str, Any]
    walls: list[dict[str, Any]]
    tables: list[VenueTableOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Guest Seating ───────────────────────────────────────────────────────────

class GuestSeatIn(BaseModel):
    table_id: str
    seat_no: int
    guest_name: str


class GuestSeatOut(BaseModel):
    id: str
    table_id: str
    seat_no: int
    guest_name: str

    model_config = {"from_attributes": True}


# ─── Portal ──────────────────────────────────────────────────────────────────

class PortalFormFieldIn(BaseModel):
    key: str
    label: str
    field_type: str = "text"
    options: list[str] = []
    is_required: bool = False
    sort_order: int = 0


class PortalFormFieldOut(BaseModel):
    id: str
    key: str
    label: str
    field_type: str
    options: list[str]
    is_required: bool
    sort_order: int

    model_config = {"from_attributes": True}


class PortalLayoutInfo(BaseModel):
    id: str
    name: str


class PortalEventInfo(BaseModel):
    salon_name: str
    event_date: str
    start_time: str
    end_time: str
    bride_groom: str
    guest_count: int
    event_type_name: str
    portal_title: str = "Davetiniz"
    seating_enabled: bool
    portal_layout_permission: bool
    reserved_layouts: list[PortalLayoutInfo]
    form_fields: list[PortalFormFieldOut]
    # Payment
    appointment_no: int | None = None
    payment_enabled: bool = False
    payment_bank_name: str = ""
    payment_iban: str = ""
    payment_account_holder: str = ""
    payment_description: str = ""
    payment_complete: bool = False
    customer_payment_claimed: bool = False
    portal_message: str = ""
    portal_photos: list[dict] = []


class PortalSeatSubmit(BaseModel):
    seatings: list[GuestSeatIn]


class PortalFormSubmit(BaseModel):
    data: dict[str, Any]


# ─── Event Form Field Defs ────────────────────────────────────────────────────

class EventFormFieldDefIn(BaseModel):
    key: str
    label: str
    field_type: str = "text"
    options: list[str] = []
    placeholder_tag: str = ""
    is_required: bool = False
    sort_order: int = 0


class EventFormFieldDefUpdate(BaseModel):
    label: str | None = None
    is_visible: bool | None = None
    is_required: bool | None = None
    sort_order: int | None = None


class EventFormFieldDefOut(BaseModel):
    id: str
    key: str
    label: str
    field_type: str
    options: list[str]
    placeholder_tag: str
    is_visible: bool
    is_required: bool
    sort_order: int
    is_builtin: bool

    model_config = {"from_attributes": True}


# ─── Event-type-specific form fields (internal "Etkinlik Form Alanı") ───────

class EventTypeFieldDefIn(BaseModel):
    event_type_id: str
    key: str
    label: str
    field_type: str = "text"
    options: list[str] = []
    is_required: bool = False
    sort_order: int = 0


class EventTypeFieldDefOut(BaseModel):
    id: str
    event_type_id: str
    key: str
    label: str
    field_type: str
    options: list[str]
    is_required: bool
    sort_order: int

    model_config = {"from_attributes": True}


# ─── Payment installments (ara ödeme) ────────────────────────────────────────

class PaymentInstallmentIn(BaseModel):
    amount: float


class PaymentInstallmentOut(BaseModel):
    id: str
    event_id: str
    amount: float
    added_by_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Contract Templates ──────────────────────────────────────────────────────

class ContractTemplateOut(BaseModel):
    id: str
    name: str
    original_filename: str
    file_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Expenses ────────────────────────────────────────────────────────────────

class ExpenseIn(BaseModel):
    title: str
    amount: float
    amount_type: str = "fixed"
    currency: str = "TRY"
    recurrence: str = "once"
    custom_period_days: int | None = None
    due_date: str
    event_id: str | None = None
    is_paid: bool = False
    include_kdv: bool = False
    note: str = ""


class ExpenseUpdate(BaseModel):
    title: str | None = None
    amount: float | None = None
    amount_type: str | None = None
    currency: str | None = None
    recurrence: str | None = None
    custom_period_days: int | None = None
    due_date: str | None = None
    event_id: str | None = None
    is_paid: bool | None = None
    is_approved: bool | None = None
    include_kdv: bool | None = None
    note: str | None = None


class ExpenseOut(BaseModel):
    id: str
    title: str
    amount: float
    amount_type: str
    currency: str
    recurrence: str
    custom_period_days: int | None
    due_date: str
    event_id: str | None
    event_title: str | None = None
    is_paid: bool
    is_approved: bool
    include_kdv: bool
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Customer Form Types ──────────────────────────────────────────────────────

class CustomerFormTypeIn(BaseModel):
    name: str


class CustomerFormTypeOut(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class CustomerFormTypeFieldIn(BaseModel):
    customer_form_type_id: str
    key: str
    label: str
    field_type: str = "text"
    options: list[str] = []
    is_required: bool = False
    sort_order: int = 0


class CustomerFormTypeFieldOut(BaseModel):
    id: str
    customer_form_type_id: str
    key: str
    label: str
    field_type: str
    options: list[str]
    is_required: bool
    sort_order: int

    model_config = {"from_attributes": True}


class PortalFormSubmissionOut(BaseModel):
    id: str
    event_id: str
    submitted_at: datetime
    data: dict

    model_config = {"from_attributes": True}


# ─── Notifications ────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: str
    event_id: str | None
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Notification Templates ────────────────────────────────────────────────────

class NotificationTemplateIn(BaseModel):
    event_type_id: str
    days_before: int
    message_template: str = ""
    is_active: bool = True


class NotificationTemplateOut(BaseModel):
    id: str
    event_type_id: str | None
    days_before: int
    message_template: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EventNotificationScheduleOut(BaseModel):
    id: str
    days_before: int
    message: str
    send_date: str
    is_sent: bool
    sent_at: datetime | None

    model_config = {"from_attributes": True}


# ─── Mail ──────────────────────────────────────────────────────────────────────

class SmtpTestIn(BaseModel):
    to_email: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool | None = None


class SendCustomerMailIn(BaseModel):
    appointment_no: int
    subject: str
    body: str
