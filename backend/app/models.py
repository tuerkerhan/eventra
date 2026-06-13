import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Salon(Base):
    __tablename__ = "salons"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    address = Column(Text, default="")
    currency = Column(String, default="TRY")
    vat_rate = Column(Float, default=20.0)
    contract_prefix = Column(String, default="EVT")
    reminder_days = Column(Integer, default=3)
    max_users = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_admin = Column(String, ForeignKey("admin_users.id"), nullable=True)

    users = relationship("SalonUser", back_populates="salon", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="salon", cascade="all, delete-orphan")
    event_types = relationship("EventType", back_populates="salon", cascade="all, delete-orphan")
    venue_layouts = relationship("VenueLayout", back_populates="salon", cascade="all, delete-orphan")
    customer_field_defs = relationship("CustomerFieldDef", back_populates="salon", cascade="all, delete-orphan")
    portal_form_fields = relationship("PortalFormField", back_populates="salon", cascade="all, delete-orphan")
    org_type_fields = relationship("OrgTypeField", back_populates="salon", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="salon", cascade="all, delete-orphan")
    contract_templates = relationship("ContractTemplate", back_populates="salon", cascade="all, delete-orphan")
    event_form_field_defs = relationship("EventFormFieldDef", back_populates="salon", cascade="all, delete-orphan")


class SalonUser(Base):
    __tablename__ = "salon_users"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="staff")  # owner | staff
    is_active = Column(Boolean, default=True)
    ui_mode = Column(String, default="full")   # full | sade
    created_at = Column(DateTime, default=datetime.utcnow)

    salon = relationship("Salon", back_populates="users")


class CustomerFieldDef(Base):
    __tablename__ = "customer_field_defs"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    key = Column(String, nullable=False)
    label = Column(String, nullable=False)
    field_type = Column(String, default="text")  # text|number|date|textarea|select|checkbox|range
    options = Column(JSON, default=list)
    is_required = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    default_value = Column(String, default="")

    salon = relationship("Salon", back_populates="customer_field_defs")
    values = relationship("CustomerFieldValue", back_populates="field_def", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    name = Column(String, nullable=False, default="")
    phone = Column(String, default="")
    email = Column(String, default="")
    tc_no = Column(String, default="")
    address = Column(Text, default="")
    note = Column(Text, default="")
    portal_active = Column(Boolean, default=False)
    portal_token = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    salon = relationship("Salon", back_populates="customers")
    field_values = relationship("CustomerFieldValue", back_populates="customer", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="customer")


class CustomerFieldValue(Base):
    __tablename__ = "customer_field_values"
    id = Column(String, primary_key=True, default=_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    field_def_id = Column(String, ForeignKey("customer_field_defs.id"), nullable=False)
    value = Column(Text, default="")

    customer = relationship("Customer", back_populates="field_values")
    field_def = relationship("CustomerFieldDef", back_populates="values")


class EventType(Base):
    __tablename__ = "event_types"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String, default="#64748b")

    salon = relationship("Salon", back_populates="event_types")
    events = relationship("Event", back_populates="event_type", foreign_keys="Event.type_id")
    org_type_fields = relationship("OrgTypeField", back_populates="event_type", cascade="all, delete-orphan")


class OrgTypeField(Base):
    """Portal form fields per organization/event type. Defines what customers fill in for each event type."""
    __tablename__ = "org_type_fields"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    event_type_id = Column(String, ForeignKey("event_types.id"), nullable=False)
    key = Column(String, nullable=False)
    label = Column(String, nullable=False)
    field_type = Column(String, default="text")  # text|number|date|textarea|select|checkbox|range
    options = Column(JSON, default=list)
    is_required = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    salon = relationship("Salon", back_populates="org_type_fields")
    event_type = relationship("EventType", back_populates="org_type_fields")


class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    title = Column(String, nullable=False, default="Yeni Davet")
    event_date = Column(String, nullable=False)
    contract_date = Column(String, default="")
    start_time = Column(String, default="19:00")
    end_time = Column(String, default="23:00")
    type_id = Column(String, ForeignKey("event_types.id"), nullable=True)
    reservation_status = Column(String, default="Ön Rezervasyon")
    tc_no = Column(String, default="")
    full_name = Column(String, default="")
    mobile_phone = Column(String, default="")
    phone = Column(String, default="")
    bride_groom = Column(String, default="")
    region = Column(String, default="")
    address = Column(Text, default="")
    guest_count = Column(Integer, default=0)
    total_fee = Column(Float, default=0)
    kapora_amount = Column(Float, default=0)
    kapora_paid = Column(Boolean, default=False)
    total_paid = Column(Float, default=0)
    payment_complete = Column(Boolean, default=False)
    note = Column(Text, default="")
    reminder_enabled = Column(Boolean, default=False)
    reminder_date = Column(String, default="")
    staff = Column(String, default="")
    layout_id = Column(String, ForeignKey("venue_layouts.id"), nullable=True)
    seating_enabled = Column(Boolean, default=False)
    # Portal fields
    portal_token = Column(String, unique=True, nullable=True)
    portal_enabled = Column(Boolean, default=False)
    portal_org_type_id = Column(String, ForeignKey("event_types.id"), nullable=True)
    portal_layout_permission = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="events")
    event_type = relationship("EventType", back_populates="events", foreign_keys=[type_id])
    portal_org_type = relationship("EventType", foreign_keys=[portal_org_type_id])
    custom_fields = relationship("EventCustomField", back_populates="event", cascade="all, delete-orphan")
    guest_seatings = relationship("GuestSeating", back_populates="event", cascade="all, delete-orphan")
    layout_reservations = relationship("EventLayoutReservation", back_populates="event", cascade="all, delete-orphan")


class EventLayoutReservation(Base):
    """Which venue layouts are reserved for an event (can be multiple salons)."""
    __tablename__ = "event_layout_reservations"
    id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    layout_id = Column(String, ForeignKey("venue_layouts.id"), nullable=False)

    event = relationship("Event", back_populates="layout_reservations")
    layout = relationship("VenueLayout")


class EventCustomField(Base):
    __tablename__ = "event_custom_fields"
    id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    key = Column(String, nullable=False)
    label = Column(String, nullable=False)
    value = Column(Text, default="")
    field_type = Column(String, default="text")  # text|number|date|time|textarea|select|checkbox|range
    options = Column(JSON, default=list)
    sort_order = Column(Integer, default=0)

    event = relationship("Event", back_populates="custom_fields")


class VenueLayout(Base):
    __tablename__ = "venue_layouts"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    name = Column(String, default="Ana Salon")
    canvas_width = Column(Integer, default=900)
    canvas_height = Column(Integer, default=600)
    stage = Column(JSON, default=lambda: {"x": 300, "y": 20, "width": 300, "height": 80})
    walls = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    salon = relationship("Salon", back_populates="venue_layouts")
    tables = relationship("VenueTable", back_populates="layout", cascade="all, delete-orphan", order_by="VenueTable.table_no")


class VenueTable(Base):
    __tablename__ = "venue_tables"
    id = Column(String, primary_key=True, default=_uuid)
    layout_id = Column(String, ForeignKey("venue_layouts.id"), nullable=False)
    table_no = Column(Integer, nullable=False)
    shape = Column(String, default="square")  # square | rectangle | long
    x = Column(Float, default=0)
    y = Column(Float, default=0)
    width = Column(Float, default=80)
    height = Column(Float, default=80)
    capacity = Column(Integer, default=8)
    label = Column(String, default="")

    layout = relationship("VenueLayout", back_populates="tables")
    seatings = relationship("GuestSeating", back_populates="table", cascade="all, delete-orphan")


class GuestSeating(Base):
    __tablename__ = "guest_seatings"
    id = Column(String, primary_key=True, default=_uuid)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    table_id = Column(String, ForeignKey("venue_tables.id"), nullable=False)
    seat_no = Column(Integer, nullable=False)
    guest_name = Column(String, default="")

    event = relationship("Event", back_populates="guest_seatings")
    table = relationship("VenueTable", back_populates="seatings")


class EventFormFieldDef(Base):
    """Global event form field definitions per salon. Controls which fields appear in the event form."""
    __tablename__ = "event_form_field_defs"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    key = Column(String, nullable=False)           # matches Event column (builtins) or custom key
    label = Column(String, nullable=False)
    field_type = Column(String, default="text")    # text|number|date|time|textarea|select|checkbox
    options = Column(JSON, default=list)
    placeholder_tag = Column(String, default="")   # e.g. %gelin_damat%
    is_visible = Column(Boolean, default=True)
    is_required = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    is_builtin = Column(Boolean, default=False)    # True = standard event field, can hide but not delete

    salon = relationship("Salon", back_populates="event_form_field_defs")


class ContractTemplate(Base):
    __tablename__ = "contract_templates"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    name = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)   # docx | odt
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    salon = relationship("Salon", back_populates="contract_templates")


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False, default=0)
    amount_type = Column(String, default="fixed")       # fixed | variable
    currency = Column(String, default="TRY")            # TRY | USD | EUR
    recurrence = Column(String, default="once")         # once | weekly | monthly | yearly | custom
    custom_period_days = Column(Integer, nullable=True)
    due_date = Column(String, nullable=False)
    event_id = Column(String, ForeignKey("events.id"), nullable=True)
    is_paid = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    include_kdv = Column(Boolean, default=False)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    salon = relationship("Salon", back_populates="expenses")
    event = relationship("Event")


class PortalFormField(Base):
    """Global portal form fields for a salon (legacy, kept for backward compat)."""
    __tablename__ = "portal_form_fields"
    id = Column(String, primary_key=True, default=_uuid)
    salon_id = Column(String, ForeignKey("salons.id"), nullable=False)
    key = Column(String, nullable=False)
    label = Column(String, nullable=False)
    field_type = Column(String, default="text")
    options = Column(JSON, default=list)
    is_required = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    salon = relationship("Salon", back_populates="portal_form_fields")
