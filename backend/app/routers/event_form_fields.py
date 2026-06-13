from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..models import EventFormFieldDef, SalonUser
from ..schemas import EventFormFieldDefIn, EventFormFieldDefOut, EventFormFieldDefUpdate

router = APIRouter(prefix="/event-form-fields", tags=["event-form-fields"])

BUILTIN_FIELDS = [
    dict(key="event_date",         label="Tarih",              field_type="date",     placeholder_tag="%tarih%",              sort_order=0,  is_visible=True),
    dict(key="start_time",         label="Başlama Saati",      field_type="time",     placeholder_tag="%baslama_saati%",      sort_order=1,  is_visible=True),
    dict(key="end_time",           label="Bitiş Saati",        field_type="time",     placeholder_tag="%bitis_saati%",        sort_order=2,  is_visible=True),
    dict(key="contract_date",      label="Sözleşme Tarihi",    field_type="date",     placeholder_tag="%sozlesme_tarihi%",    sort_order=3,  is_visible=True),
    dict(key="reservation_status", label="Rezervasyon Durumu", field_type="text",     placeholder_tag="%rezervasyon_durumu%", sort_order=4,  is_visible=True),
    dict(key="tc_no",              label="T.C. Kimlik No",     field_type="text",     placeholder_tag="%tc_no%",              sort_order=5,  is_visible=True),
    dict(key="full_name",          label="Adı Soyadı",         field_type="text",     placeholder_tag="%isim%",               sort_order=6,  is_visible=True),
    dict(key="mobile_phone",       label="Mobil Telefon",      field_type="text",     placeholder_tag="%telefon%",            sort_order=7,  is_visible=True),
    dict(key="phone",              label="Sabit Telefon",      field_type="text",     placeholder_tag="",                     sort_order=8,  is_visible=True),
    dict(key="type_id",            label="Organizasyon Tipi",  field_type="select",   placeholder_tag="%tip%",                sort_order=9,  is_visible=True),
    dict(key="bride_groom",        label="Gelin ve Damat",     field_type="text",     placeholder_tag="%gelin_damat%",        sort_order=10, is_visible=True),
    dict(key="region",             label="Yöresi",             field_type="text",     placeholder_tag="%bolge%",              sort_order=11, is_visible=True),
    dict(key="guest_count",        label="Davetli Sayısı",     field_type="number",   placeholder_tag="%davetli_sayisi%",     sort_order=12, is_visible=True),
    dict(key="address",            label="Adresi",             field_type="textarea", placeholder_tag="%adres%",              sort_order=13, is_visible=True),
    dict(key="total_fee",          label="Toplam Ücret",       field_type="number",   placeholder_tag="%toplam_ucret%",       sort_order=14, is_visible=True),
    dict(key="kapora_amount",      label="Kapora Tutarı",      field_type="number",   placeholder_tag="%kapora%",             sort_order=15, is_visible=True),
    dict(key="total_paid",         label="Alınan Ücret",       field_type="number",   placeholder_tag="%odenen%",             sort_order=16, is_visible=True),
    dict(key="note",               label="Ön Açıklama",        field_type="textarea", placeholder_tag="%notlar%",             sort_order=17, is_visible=True),
    dict(key="staff",              label="Çalışanlar",         field_type="text",     placeholder_tag="%personel%",           sort_order=18, is_visible=True),
    dict(key="reminder_enabled",   label="Hatırlatma",         field_type="checkbox", placeholder_tag="",                     sort_order=19, is_visible=True),
]


def _ensure_defaults(salon_id: str, db: Session) -> None:
    existing_keys = {r.key for r in db.query(EventFormFieldDef.key).filter(
        EventFormFieldDef.salon_id == salon_id, EventFormFieldDef.is_builtin == True
    ).all()}
    for f in BUILTIN_FIELDS:
        if f["key"] not in existing_keys:
            db.add(EventFormFieldDef(salon_id=salon_id, is_builtin=True, options=[], **f))
    db.commit()


@router.get("", response_model=list[EventFormFieldDefOut])
def list_fields(db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    _ensure_defaults(user.salon_id, db)
    return (
        db.query(EventFormFieldDef)
        .filter(EventFormFieldDef.salon_id == user.salon_id)
        .order_by(EventFormFieldDef.sort_order)
        .all()
    )


@router.post("", response_model=EventFormFieldDefOut)
def add_field(body: EventFormFieldDefIn, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    existing = db.query(EventFormFieldDef).filter(
        EventFormFieldDef.salon_id == user.salon_id,
        EventFormFieldDef.key == body.key,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu anahtar zaten mevcut")
    count = db.query(EventFormFieldDef).filter(EventFormFieldDef.salon_id == user.salon_id).count()
    f = EventFormFieldDef(
        salon_id=user.salon_id,
        is_builtin=False,
        is_visible=True,
        sort_order=body.sort_order if body.sort_order else count,
        **body.model_dump(exclude={"sort_order"}),
        # override sort_order below to avoid conflict
    )
    f.sort_order = body.sort_order if body.sort_order else count
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.patch("/{field_id}", response_model=EventFormFieldDefOut)
def update_field(
    field_id: str,
    body: EventFormFieldDefUpdate,
    db: Session = Depends(get_db),
    user: SalonUser = Depends(get_current_user),
):
    f = db.query(EventFormFieldDef).filter(
        EventFormFieldDef.id == field_id,
        EventFormFieldDef.salon_id == user.salon_id,
    ).first()
    if not f:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(f, field, val)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/{field_id}", status_code=204)
def delete_field(field_id: str, db: Session = Depends(get_db), user: SalonUser = Depends(get_current_user)):
    f = db.query(EventFormFieldDef).filter(
        EventFormFieldDef.id == field_id,
        EventFormFieldDef.salon_id == user.salon_id,
    ).first()
    if not f:
        raise HTTPException(status_code=404, detail="Alan bulunamadı")
    if f.is_builtin:
        raise HTTPException(status_code=400, detail="Yerleşik alanlar silinemez, gizlenebilir")
    db.delete(f)
    db.commit()
