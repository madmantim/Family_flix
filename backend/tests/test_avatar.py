import pytest
from io import BytesIO
from PIL import Image


def create_test_image(width=400, height=300, format="PNG"):
    """Create a test image in memory"""
    img = Image.new("RGB", (width, height), color="red")
    buffer = BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def test_upload_avatar_success(client):
    # Create member first
    member_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = member_resp.json()["id"]

    # Upload avatar
    image = create_test_image(400, 300)
    response = client.post(
        f"/api/members/{member_id}/avatar",
        files={"file": ("test.png", image, "image/png")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] is not None
    assert f"/static/avatars/{member_id}.jpg" in data["avatar_url"]


def test_upload_avatar_member_not_found(client):
    image = create_test_image()
    response = client.post(
        "/api/members/999/avatar",
        files={"file": ("test.png", image, "image/png")}
    )
    assert response.status_code == 404


def test_upload_avatar_invalid_file_type(client):
    # Create member first
    member_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = member_resp.json()["id"]

    # Try uploading a text file
    response = client.post(
        f"/api/members/{member_id}/avatar",
        files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
    )

    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


def test_upload_avatar_overwrites_existing(client):
    # Create member
    member_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = member_resp.json()["id"]

    # Upload first avatar
    image1 = create_test_image(400, 300)
    client.post(
        f"/api/members/{member_id}/avatar",
        files={"file": ("test1.png", image1, "image/png")}
    )

    # Upload second avatar (should overwrite)
    image2 = create_test_image(500, 500)
    response = client.post(
        f"/api/members/{member_id}/avatar",
        files={"file": ("test2.png", image2, "image/png")}
    )

    assert response.status_code == 200
    # URL should be the same (overwritten file)
    assert f"/static/avatars/{member_id}.jpg" in response.json()["avatar_url"]
