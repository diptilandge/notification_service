def test_create_notification(client):
    payload = {
        "user_id": "user123",
        "channel": "email",
        "priority": "high",
        "payload": {"message": "Hello World"}
    }
    response = client.post("/notifications", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["user_id"] == "user123"
    assert data["status"] == "pending"
    assert "id" in data

def test_get_notification(client):
    # First create
    payload = {
        "user_id": "user456",
        "channel": "sms",
        "payload": {"code": "1234"}
    }
    create_resp = client.post("/notifications", json=payload)
    notif_id = create_resp.json()["id"]

    # Then get
    response = client.get(f"/notifications/{notif_id}")
    assert response.status_code == 200
    assert response.json()["id"] == notif_id

def test_set_and_get_preferences(client):
    payload = {
        "channel": "email",
        "opt_in": False
    }
    set_resp = client.post("/users/user789/preferences", json=payload)
    assert set_resp.status_code == 200
    assert set_resp.json()["opt_in"] is False

    get_resp = client.get("/users/user789/preferences")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert len(data) >= 1
    assert data[0]["channel"] == "email"
    assert data[0]["opt_in"] is False

def test_idempotency_key(client):
    payload = {
        "user_id": "user111",
        "channel": "push",
        "idempotency_key": "unique-key-1",
        "payload": {"msg": "Idempotent Msg"}
    }
    
    # First request
    resp1 = client.post("/notifications", json=payload)
    assert resp1.status_code == 202
    id1 = resp1.json()["id"]
    
    # Second request with same key
    resp2 = client.post("/notifications", json=payload)
    assert resp2.status_code == 202
    id2 = resp2.json()["id"]
    
    # Must return same notification record
    assert id1 == id2
