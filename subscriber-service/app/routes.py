import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import Subscriber, Alert

router = APIRouter(prefix="/api/subscriber", tags=["subscriber"])


class SubscribeRequest(BaseModel):
    name: str
    email: str
    event_types: list[str] = ["generation"]


class SubscribeResponse(BaseModel):
    id: str
    name: str
    email: str
    event_types: list[str]
    message: str


@router.get("/health")
async def health():
    return {"status": "ok", "service": "subscriber-service"}


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(req: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscriber).where(Subscriber.email == req.email))
    existing = result.scalar_one_or_none()
    if existing:
        existing.name = req.name
        existing.event_types = list(set(existing.event_types + req.event_types))
        existing.confirmed = True
        await db.commit()
        await db.refresh(existing)
        return SubscribeResponse(
            id=str(existing.id),
            name=existing.name,
            email=existing.email,
            event_types=existing.event_types,
            message="Subscription updated successfully",
        )

    sub = Subscriber(
        name=req.name,
        email=req.email,
        event_types=req.event_types,
        confirmed=True,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)

    alert = Alert(
        subscriber_id=sub.id,
        event_type="subscription",
        message=f"Welcome {sub.name}! You're subscribed to {', '.join(sub.event_types)} alerts.",
    )
    db.add(alert)
    await db.commit()

    return SubscribeResponse(
        id=str(sub.id),
        name=sub.name,
        email=sub.email,
        event_types=sub.event_types,
        message="Subscribed successfully!",
    )


@router.get("/{subscriber_id}/alerts")
async def get_alerts(subscriber_id: str, db: AsyncSession = Depends(get_db)):
    try:
        sid = uuid.UUID(subscriber_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscriber ID")

    result = await db.execute(
        select(Alert)
        .where(Alert.subscriber_id == sid)
        .order_by(desc(Alert.created_at))
        .limit(50)
    )
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "event_type": a.event_type,
            "message": a.message,
            "link": a.link,
            "read": a.read,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]


@router.put("/{subscriber_id}/alerts/{alert_id}/read")
async def mark_read(subscriber_id: str, alert_id: str, db: AsyncSession = Depends(get_db)):
    try:
        sid = uuid.UUID(subscriber_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscriber ID")
    try:
        aid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    alert = await db.get(Alert, aid)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.subscriber_id != sid:
        raise HTTPException(status_code=403, detail="Alert does not belong to subscriber")
    alert.read = True
    await db.commit()
    return {"status": "ok"}


@router.delete("/{subscriber_id}")
async def unsubscribe(
    subscriber_id: str,
    email: str | None = Query(default=None, description="Account email for ownership confirmation"),
    db: AsyncSession = Depends(get_db),
):
    try:
        sid = uuid.UUID(subscriber_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscriber ID")

    sub = await db.get(Subscriber, sid)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    # Minimal ownership check until real auth (JWT/session) lands.
    # TODO(auth): replace email check with authenticated principal (JWT)
    # and enforce sub.owner_id == current_user.id -> 403 otherwise.
    # TODO(rate-limit): add per-IP/per-ID limiter (e.g. slowapi) on this route.
    # TODO(soft-delete): prefer deleted_at flag over hard delete.
    if email is None:
        raise HTTPException(status_code=422, detail="Email confirmation required")
    if email.strip().lower() != sub.email.strip().lower():
        raise HTTPException(status_code=403, detail="Email does not match subscriber")

    await db.delete(sub)
    await db.commit()
    return {"status": "unsubscribed"}
