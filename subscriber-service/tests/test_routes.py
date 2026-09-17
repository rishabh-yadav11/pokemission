import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from tests.helpers import MockResult


class TestHealth:
    @pytest.mark.asyncio
    async def test_health(self, async_client):
        resp = await async_client.get("/api/subscriber/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "subscriber-service"


class TestSubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_new(self, async_client, mock_db, sample_subscriber):
        mock_db.execute.return_value = MockResult([])
        mock_db.get.return_value = None
        mock_db.add = MagicMock()

        async def refresh_side_effect(obj):
            obj.id = sample_subscriber.id
            obj.name = "Ash Ketchum"
            obj.email = "ash@pokemon.com"
            obj.event_types = ["generation", "rare"]

        mock_db.refresh = AsyncMock(side_effect=refresh_side_effect)

        resp = await async_client.post(
            "/api/subscriber/subscribe",
            json={"name": "Ash Ketchum", "email": "ash@pokemon.com", "event_types": ["generation", "rare"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Ash Ketchum"
        assert data["email"] == "ash@pokemon.com"
        assert data["message"] == "Subscribed successfully!"

    @pytest.mark.asyncio
    async def test_subscribe_existing(self, async_client, mock_db, sample_subscriber):
        mock_db.execute.return_value = MockResult([sample_subscriber])

        async def refresh_side_effect(obj):
            obj.id = sample_subscriber.id
            obj.name = "Ash Ketchum"
            obj.email = "ash@pokemon.com"
            obj.event_types = ["generation", "rare"]

        mock_db.refresh = AsyncMock(side_effect=refresh_side_effect)

        resp = await async_client.post(
            "/api/subscriber/subscribe",
            json={"name": "Ash Ketchum", "email": "ash@pokemon.com", "event_types": ["generation"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Subscription updated successfully"

    @pytest.mark.asyncio
    async def test_subscribe_default_event_types(self, async_client, mock_db, sample_subscriber):
        mock_db.execute.return_value = MockResult([])
        mock_db.get.return_value = None
        mock_db.add = MagicMock()

        async def refresh_side_effect(obj):
            obj.id = sample_subscriber.id
            obj.name = "Misty"
            obj.email = "misty@pokemon.com"
            obj.event_types = ["generation"]

        mock_db.refresh = AsyncMock(side_effect=refresh_side_effect)

        resp = await async_client.post(
            "/api/subscriber/subscribe",
            json={"name": "Misty", "email": "misty@pokemon.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Misty"


class TestGetAlerts:
    @pytest.mark.asyncio
    async def test_get_alerts(self, async_client, mock_db, sample_alert):
        mock_db.execute.return_value = MockResult([sample_alert])
        sid = sample_alert.subscriber_id

        resp = await async_client.get(f"/api/subscriber/{sid}/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["event_type"] == "generation"
        assert data[0]["read"] is False

    @pytest.mark.asyncio
    async def test_get_alerts_empty(self, async_client, mock_db):
        mock_db.execute.return_value = MockResult([])
        sid = uuid4()

        resp = await async_client.get(f"/api/subscriber/{sid}/alerts")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_alerts_invalid_id(self, async_client):
        resp = await async_client.get("/api/subscriber/invalid-uuid/alerts")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid subscriber ID"


class TestMarkRead:
    @pytest.mark.asyncio
    async def test_mark_read(self, async_client, mock_db, sample_alert):
        mock_db.get.return_value = sample_alert
        sid = sample_alert.subscriber_id
        aid = sample_alert.id

        resp = await async_client.put(f"/api/subscriber/{sid}/alerts/{aid}/read")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        assert sample_alert.read is True
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_mark_read_cross_tenant_403(self, async_client, mock_db, sample_alert):
        mock_db.get.return_value = sample_alert
        other_sid = uuid4()
        assert other_sid != sample_alert.subscriber_id
        resp = await async_client.put(f"/api/subscriber/{other_sid}/alerts/{sample_alert.id}/read")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Alert does not belong to subscriber"

    @pytest.mark.asyncio
    async def test_mark_read_invalid_subscriber_id_400(self, async_client):
        from uuid import uuid4 as _uuid4
        aid = _uuid4()
        resp = await async_client.put(f"/api/subscriber/not-a-uuid/alerts/{aid}/read")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid subscriber ID"

    @pytest.mark.asyncio
    async def test_mark_read_not_found(self, async_client, mock_db):
        mock_db.get.return_value = None
        sid = uuid4()
        aid = uuid4()

        resp = await async_client.put(f"/api/subscriber/{sid}/alerts/{aid}/read")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Alert not found"

    @pytest.mark.asyncio
    async def test_mark_read_invalid_id(self, async_client):
        sid = uuid4()
        resp = await async_client.put(f"/api/subscriber/{sid}/alerts/not-a-uuid/read")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid alert ID"


class TestUnsubscribe:
    @pytest.mark.asyncio
    async def test_unsubscribe(self, async_client, mock_db, sample_subscriber):
        mock_db.get.return_value = sample_subscriber
        sid = sample_subscriber.id

        resp = await async_client.delete(f"/api/subscriber/{sid}", params={"email": sample_subscriber.email})
        assert resp.status_code == 200
        assert resp.json() == {"status": "unsubscribed"}
        assert mock_db.delete.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_unsubscribe_requires_email(self, async_client, mock_db, sample_subscriber):
        mock_db.get.return_value = sample_subscriber
        resp = await async_client.delete(f"/api/subscriber/{sample_subscriber.id}")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_unsubscribe_wrong_email_403(self, async_client, mock_db, sample_subscriber):
        mock_db.get.return_value = sample_subscriber
        resp = await async_client.delete(
            f"/api/subscriber/{sample_subscriber.id}", params={"email": "attacker@evil.com"}
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_unsubscribe_not_found(self, async_client, mock_db):
        mock_db.get.return_value = None
        sid = uuid4()

        resp = await async_client.delete(f"/api/subscriber/{sid}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Subscriber not found"

    @pytest.mark.asyncio
    async def test_unsubscribe_invalid_id(self, async_client):
        resp = await async_client.delete("/api/subscriber/not-a-uuid")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid subscriber ID"
