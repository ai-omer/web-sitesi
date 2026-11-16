"""
Mervenin Mutfagi - Backend Unit Tests
pytest + TestClient + SQLite in-memory DB (StaticPool) ile tum endpoint'leri test eder.

Calistirma:
    cd backend
    pytest test_main.py -v
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock
import unittest.mock as _um

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────
# GEMINI MOCK - import oncesi
# ─────────────────────────────────────────────

_mock_gemini = MagicMock()
_mock_gemini.api_key_configured = True
_mock_gemini.generate_recipe = AsyncMock(return_value={
    "success": True,
    "cuisine": "Turk Mutfagi",
    "pratik": {"title": "Mock Pratik", "description": "test"},
    "geleneksel": {"title": "Mock Geleneksel", "description": "test"},
    "yaratici": {"title": "Mock Yaratici", "description": "test"},
})
_mock_gemini.generate_direct_recipe = AsyncMock(return_value={
    "success": True,
    "recipe": {"title": "Kuru Fasulye", "cuisine": "Turk Mutfagi"},
})

_um.patch("gemini_service.gemini_service", _mock_gemini).start()

# ─────────────────────────────────────────────
# IN-MEMORY VERITABANI - StaticPool ile
# ─────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# StaticPool: tum session'lar ayni connection'i kullanir
# Bu in-memory SQLite testlerinde "detached connection fairy" hatasini cozumu
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

from database import Base, get_db

# Tablolari olustur - yalnizca bir kez
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ana uygulamayi import et ve override'i uygula
from main import app
app.dependency_overrides[get_db] = override_get_db

# Lifespan'daki create_tables() cagrisini override et
# (bos callable - tablolar zaten yukarida olusturuldu)
import main as _main_module
_main_module.create_tables = lambda: None

from fastapi.testclient import TestClient

# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """Tum session boyunca tek bir TestClient kullan."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ─────────────────────────────────────────────
# YARDIMCI FONKSIYONLAR
# ─────────────────────────────────────────────

_counter = [0]


def unique_user(prefix="u"):
    _counter[0] += 1
    n = _counter[0]
    return f"{prefix}{n}@test.com", f"{prefix}{n}_user"


def register(client, email, username, pwd="testpass123"):
    return client.post("/api/auth/register", json={
        "email": email, "username": username, "password": pwd
    })


def login(client, email, pwd="testpass123"):
    r = client.post("/api/auth/login", json={"email": email, "password": pwd})
    return r.json().get("access_token") if r.status_code == 200 else None


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# TESTLER
# ─────────────────────────────────────────────

class TestHealth:
    def test_health_check(self, client):
        """GET /api/health -> 200"""
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ("healthy", "degraded")
        assert "database" in data
        assert "version" in data


class TestRegister:
    def test_register_success(self, client):
        """POST /api/auth/register -> 201"""
        email, username = unique_user("reg")
        r = register(client, email, username)
        assert r.status_code == 201, f"Alinan: {r.status_code}\n{r.text}"
        d = r.json()
        assert d["success"] is True
        assert d["user"]["email"] == email
        assert "id" in d["user"]

    def test_register_duplicate_email(self, client):
        """Ayni e-posta -> 400"""
        email, u1 = unique_user("dup_e")
        _, u2 = unique_user("dup_e2")
        register(client, email, u1)
        r = register(client, email, u2)
        assert r.status_code == 400, f"Alinan: {r.status_code}"

    def test_register_duplicate_username(self, client):
        """Ayni username -> 400"""
        e1, username = unique_user("dup_u")
        e2, _ = unique_user("dup_u2")
        register(client, e1, username)
        r = register(client, e2, username)
        assert r.status_code == 400, f"Alinan: {r.status_code}"


class TestLogin:
    def test_login_success(self, client):
        """Dogru bilgiler -> 200 + token"""
        email, username = unique_user("log")
        register(client, email, username)
        r = client.post("/api/auth/login", json={"email": email, "password": "testpass123"})
        assert r.status_code == 200, f"Alinan: {r.status_code}\n{r.text}"
        d = r.json()
        assert d["success"] is True
        assert "access_token" in d

    def test_login_wrong_password(self, client):
        """Yanlis sifre -> 401"""
        email, username = unique_user("wp")
        register(client, email, username)
        r = client.post("/api/auth/login", json={"email": email, "password": "yanlis_sifre"})
        assert r.status_code == 401, f"Alinan: {r.status_code}"

    def test_login_nonexistent(self, client):
        """Olmayan kullanici -> 401"""
        r = client.post("/api/auth/login", json={"email": "yok@yok.com", "password": "abc"})
        assert r.status_code == 401


class TestMe:
    def test_me_unauthorized(self, client):
        """Token olmadan -> 401"""
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_authorized(self, client):
        """Gecerli token -> 200"""
        email, username = unique_user("me")
        register(client, email, username)
        token = login(client, email)
        assert token is not None
        r = client.get("/api/auth/me", headers=auth(token))
        assert r.status_code == 200, f"Alinan: {r.status_code}\n{r.text}"
        assert r.json()["email"] == email


class TestPosts:
    def test_get_posts_valid(self, client):
        """GET /api/posts?section=mutfak -> 200"""
        r = client.get("/api/posts?section=mutfak")
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert isinstance(r.json()["posts"], list)

    def test_get_posts_invalid_section(self, client):
        """Gecersiz section -> 422"""
        r = client.get("/api/posts?section=gecersiz")
        assert r.status_code == 422

    def test_create_post_guest(self, client):
        """Misafir post -> 201"""
        r = client.post("/api/posts", data={
            "username": "misafir_test",
            "content": "Test gonderisi - merhaba mutfak!",
            "section": "mutfak",
        })
        assert r.status_code == 201, f"Alinan: {r.status_code}\n{r.text}"
        assert r.json()["post"]["section"] == "mutfak"


class TestAdmin:
    def test_admin_summary_no_token(self, client):
        """Token yok -> 401"""
        r = client.get("/api/admin/summary")
        assert r.status_code == 401

    def test_admin_summary_normal_user_forbidden(self, client):
        """Normal user admin endpoint'e -> 403"""
        # Ilk kayit admin olur, bu yuzden once admin seed olustur
        register(client, "adm_seed1@t.com", "adm_seed1")
        email, username = unique_user("normal")
        register(client, email, username)
        token = login(client, email)
        assert token is not None
        r = client.get("/api/admin/summary", headers=auth(token))
        assert r.status_code == 403

    def test_admin_users_normal_user_forbidden(self, client):
        """Normal user /admin/users'a -> 403"""
        register(client, "adm_seed2@t.com", "adm_seed2")
        email, username = unique_user("nusr")
        register(client, email, username)
        token = login(client, email)
        r = client.get("/api/admin/users", headers=auth(token))
        assert r.status_code == 403

    def test_admin_posts_normal_user_forbidden(self, client):
        """Normal user /admin/posts'a -> 403"""
        register(client, "adm_seed3@t.com", "adm_seed3")
        email, username = unique_user("np")
        register(client, email, username)
        token = login(client, email)
        r = client.get("/api/admin/posts", headers=auth(token))
        assert r.status_code == 403


class TestFavorites:
    def test_favorites_no_token(self, client):
        """Token yok -> 401"""
        r = client.get("/api/favorites")
        assert r.status_code == 401

    def test_favorites_empty_list(self, client):
        """Yeni kullanici favorileri -> 200, bos liste"""
        email, username = unique_user("fav")
        register(client, email, username)
        token = login(client, email)
        assert token is not None
        r = client.get("/api/favorites", headers=auth(token))
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["count"] == 0
        assert d["favorites"] == []
