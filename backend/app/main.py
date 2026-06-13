from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from .models import Base
from .routers import auth, customers, events, venue, portal, settings, admin_router, expenses, contracts, event_form_fields

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Eventra API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(events.router)
app.include_router(venue.router)
app.include_router(portal.router)
app.include_router(settings.router)
app.include_router(admin_router.router)
app.include_router(expenses.router)
app.include_router(contracts.router)
app.include_router(event_form_fields.router)


@app.get("/health")
def health():
    return {"status": "ok"}
