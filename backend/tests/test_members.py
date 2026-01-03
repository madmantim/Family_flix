import pytest


def test_create_member(client):
    response = client.post("/api/members/", json={"name": "Tim"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tim"
    assert data["id"] is not None


def test_create_duplicate_member(client):
    client.post("/api/members/", json={"name": "Tim"})
    response = client.post("/api/members/", json={"name": "Tim"})
    assert response.status_code == 400


def test_get_members(client):
    client.post("/api/members/", json={"name": "Tim"})
    client.post("/api/members/", json={"name": "Sarah"})

    response = client.get("/api/members/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_member(client):
    create_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = create_resp.json()["id"]

    response = client.get(f"/api/members/{member_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Tim"


def test_get_member_not_found(client):
    response = client.get("/api/members/999")
    assert response.status_code == 404


def test_update_member(client):
    create_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = create_resp.json()["id"]

    response = client.patch(f"/api/members/{member_id}", json={"name": "Timothy"})
    assert response.status_code == 200
    assert response.json()["name"] == "Timothy"


def test_delete_member(client):
    create_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = create_resp.json()["id"]

    response = client.delete(f"/api/members/{member_id}")
    assert response.status_code == 204

    # Verify deleted
    get_resp = client.get(f"/api/members/{member_id}")
    assert get_resp.status_code == 404


def test_update_member_duplicate_name(client):
    """Test that renaming to an existing member's name fails"""
    # Create two members
    resp1 = client.post("/api/members/", json={"name": "Tim"})
    resp2 = client.post("/api/members/", json={"name": "Sarah"})
    member1_id = resp1.json()["id"]

    # Try to rename member 1 to member 2's name
    response = client.patch(
        f"/api/members/{member1_id}",
        json={"name": "Sarah"}
    )
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"].lower()
