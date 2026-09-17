import html
import uuid
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.database import get_db
from app.models import Subscriber, Alert

router = APIRouter(prefix="/api/subscriber", tags=["subscriber"])

EventType = Literal["generation", "rare", "region"]


class SubscribeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Subscriber name")
    email: EmailStr
    event_types: list[EventType] = Field(default_factory=lambda: ["generation"], max_length=3)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("event_types", mode="before")
    @classmethod
    def dedupe_event_types(cls, v: list) -> list:
        if not isinstance(v, list):
            return v
        return list(dict.fromkeys(v))

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v: list) -> list:
        if not v:
            return ["generation"]
        return v


class SubscribeResponse(BaseModel):
    message: str


@router.get("/health")
async def health():
    return {"status": "ok", "service": "subscriber-service"}


async def _rate_limit_check(request: Request) -> None:
    # Simple in-memory rate limiting (per-process). In production, use Redis/slowapi.
    # 30 req/min per IP as a basic safeguard.
    import time
    if not hasattr(_rate_limit_check, "_buckets"):
        _rate_limit_check._buckets = {}
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _rate_limit_check._buckets.get(ip, [])
    bucket = [t for t in bucket if now - t < 60]
    if len(bucket) >= 30:
        raise HTTPException(status_code=429, detail="Too many requests, please try again later")
    bucket.append(now)
    _rate_limit_check._buckets[ip] = bucket


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(req: SubscribeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    await _rate_limit_check(request)

    # Sanitize user input before storing
    safe_name = html.escape(req.name)
    safe_event_types = [html.escape(et) for et in req.event_types]

    # Single transaction with retry on unique constraint violation
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await db.execute(select(Subscriber).where(Subscriber.email == req.email))
            existing = result.scalar_one_or_none()

            if existing:
                # Uniform message to prevent email enumeration
                existing.name = safe_name
                existing.event_types = list(dict.fromkeys((existing.event_types or []) + safe_event_types))
                existing.confirmed = False  # Require confirmation flow
                await db.commit()
                return SubscribeResponse(message="If this email is new, check inbox to confirm subscription")

            sub = Subscriber(
                name=safe_name,
                email=req.email,
                event_types=safe_event_types,
                confirmed=False,  # Require confirmation token flow
            )
            db.add(sub)
            await db.flush()  # Get ID without committing

            alert = Alert(
                subscriber_id=sub.id,
                event_type="subscription",
                message=f"Welcome {safe_name}! You're subscribed to {', '.join(safe_event_types)} alerts.",
            )
            db.add(alert)

            await db.commit()
            return SubscribeResponse(message="If this email is new, check inbox to confirm subscription")

        except IntegrityError:
            await db.rollback()
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="Could not process subscription, please try again")
            continue

    raise HTTPException(status_code=500, detail="Could not process subscription")


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

    if email is None:
        raise HTTPException(status_code=422, detail="Email confirmation required")
    if email.strip().lower() != sub.email.strip().lower():
        raise HTTPException(status_code=403, detail="Email does not match subscriber")

    await db.delete(sub)
    await db.commit()
    return {"status": "unsubscribed"}