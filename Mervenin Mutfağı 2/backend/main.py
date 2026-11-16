"""
Mervenin Mutfağı - FastAPI Ana Uygulama
Production-ready, CORS yapılandırılmış, hata yönetimli backend.
"""

import os
import time
import logging
import uuid
import hashlib
import secrets
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, Query, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Ortam değişkenlerini .env dosyasından yükle
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from database import create_tables, get_db, User, SavedRecipe, Favorite, RecipeHistory, CommunityPost, UPLOADS_DIR
from schemas import (
    RecipeRequest,
    RecipeResponse,
    DirectRecipeRequest,
    DirectRecipeResponse,
    FavoriteCreateRequest,
    FavoriteResponse,
    FavoritesListResponse,
    DeleteResponse,
    HealthResponse,
    ErrorResponse,
    CommunityPostCreate,
    CommunityPostResponse,
    VALID_SECTIONS,
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from gemini_service import gemini_service

# ─────────────────────────────────────────────
# LOGGING YAPILANDIRMASI
# ─────────────────────────────────────────────
import logging.handlers as _log_handlers

_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log")
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_LOG_DATE = "%Y-%m-%d %H:%M:%S"

# Kök logger'ı yapılandır
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)

# 1) Konsol (StreamHandler) — mevcut gibi
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE))
_root_logger.addHandler(_console_handler)

# 2) Dosya (RotatingFileHandler) — 5 MB × 3 yedek kopya
_file_handler = _log_handlers.RotatingFileHandler(
    _LOG_FILE,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8",
)
_file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE))
_root_logger.addHandler(_file_handler)

logger = logging.getLogger("mervenin_mutfagi")
logger.info("Loglama sistemi hazir — dosya: %s", _LOG_FILE)

# ─────────────────────────────────────────────
# LIFESPAN (Startup / Shutdown)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama başlangıcında ve kapanışında çalışacak işlemler."""
    logger.info("Mervenin Mutfagi backend baslatiliyor...")
    create_tables()
    logger.info("Gemini AI hazir: %s", gemini_service.api_key_configured)
    logger.info("Backend tamamen hazir!")
    yield
    logger.info("Mervenin Mutfagi backend kapatiliyor...")


# ─────────────────────────────────────────────
# FASTAPI UYGULAMASI
# ─────────────────────────────────────────────
app = FastAPI(
    title="Mervenin Mutfağı API",
    description=(
        "Mervenin Mutfağı platformunun resmi backend API'si. "
        "Yapay zeka destekli tarif üretimi ve kullanıcı yönetimi."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
    max_age=600,
)


@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Process-Time"] = f"{process_time}ms"
    return response


# ─────────────────────────────────────────────
# GLOBAL HATA YÖNETİMİ
# ─────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Beklenmeyen hata [{request.url}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "internal_server_error",
            "message": "Sunucuda beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.",
        },
    )


# ─────────────────────────────────────────────
# AUTH / JWT UTILS & SECURITY HELPERS
# ─────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "merve_secret_key_9876543210")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 Gün

def hash_password(password: str) -> str:
    """PBKDF2_HMAC-SHA256 ile güvenli ve ek derleyici gerektirmeyen şifreleme."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{key.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verilen şifre ile hash eşleşmesini kontrol eder."""
    try:
        salt, key_hex = hashed_password.split(':')
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return key.hex() == key_hex
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    """JWT Access Token üretir."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """JWT Token'ı çözer. Süresi dolmuş ve geçersiz token'ları ayrı loglar."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token suresi dolmus (ExpiredSignatureError).")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("Gecersiz JWT token: %s", exc)
        return None
    except Exception as exc:
        logger.error("JWT decode beklenmeyen hata: %s", exc, exc_info=True)
        return None

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Aktif oturum açmış kullanıcıyı getiren FastAPI Dependency'si."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum açmanız gerekiyor.",
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş oturum.",
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı.",
        )
    return user

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """İsteğe bağlı aktif kullanıcıyı getiren Dependency (Giriş yapılmamışsa None döner)."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = payload.get("sub")
    return db.query(User).filter(User.id == user_id).first()


# ─────────────────────────────────────────────
# AUTHENTICATION ENDPOINTS
# ─────────────────────────────────────────────

@app.post(
    "/api/auth/register",
    tags=["Auth"],
    summary="Yeni kullanıcı kaydı",
    response_class=JSONResponse,
)
async def register(request: UserRegister, db: Session = Depends(get_db)):
    """Sistemde yeni bir kullanıcı oluşturur."""
    # E-posta çakışma kontrolü
    existing_email = db.query(User).filter(User.email == request.email.strip().lower()).first()
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Bu e-posta adresi zaten kullanımda.",
        )

    # Kullanıcı adı çakışma kontrolü
    existing_username = db.query(User).filter(User.username == request.username.strip()).first()
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Bu kullanıcı adı zaten kullanımda.",
        )

    # Şifre hashleme ve kaydetme
    hashed = hash_password(request.password)
    
    # İlk kayıt olan kullanıcıyı admin yap (kolay yönetim için), diğerlerini user yap
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else "user"

    new_user = User(
        email=request.email.strip().lower(),
        username=request.username.strip(),
        password_hash=hashed,
        role=role,
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Kayıt başarıyla tamamlandı! 🎉",
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "username": new_user.username,
                    "role": new_user.role,
                }
            }
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"Kayıt hatası: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Kayıt oluşturulurken hata oluştu.")


@app.post(
    "/api/auth/login",
    tags=["Auth"],
    summary="Kullanıcı girişi",
    response_model=TokenResponse,
)
async def login(request: UserLogin, db: Session = Depends(get_db)):
    """Kullanıcı adı/şifre doğrular ve JWT token döner."""
    user = db.query(User).filter(User.email == request.email.strip().lower()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="E-posta adresi veya şifre hatalı.",
        )

    # Token üret
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
    
    return TokenResponse(
        success=True,
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            created_at=user.created_at,
        )
    )


@app.get(
    "/api/auth/me",
    tags=["Auth"],
    summary="Aktif profil detayları",
    response_model=UserResponse,
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Aktif oturum sahibinin profil detaylarını döner."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        created_at=current_user.created_at,
    )


# ─────────────────────────────────────────────
# SAĞLIK KONTROLÜ
# ─────────────────────────────────────────────
@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Sağlık kontrolü",
)
async def health_check(db: Session = Depends(get_db)):
    """API ve veritabanı durumunu test eder."""
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.error(f"DB sağlık kontrolü hatası: {exc}")
        db_status = "error"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        message="Mervenin Mutfağı API çalışıyor 🍳",
        api_key_configured=gemini_service.api_key_configured,
        database=db_status,
        version="1.0.0",
    )


# ─────────────────────────────────────────────
# TARİF OLUŞTURMA
# ─────────────────────────────────────────────
@app.post(
    "/api/generate-recipe",
    tags=["Recipe"],
    summary="Merve Şef ile tarif oluştur",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_recipe(
    request: RecipeRequest,
    db: Session = Depends(get_db),
):
    """Kullanıcının malzemelerine göre 3 gurme tarif seçeneği üretir."""
    start_time = time.time()

    if not request.ingredients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="En az bir malzeme girmelisiniz.",
        )

    clean_ingredients = [
        ing.strip()
        for ing in request.ingredients
        if ing.strip() and len(ing.strip()) >= 2
    ]

    if not clean_ingredients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Geçerli malzeme bulunamadı. Lütfen en az 2 karakterli malzeme girin.",
        )

    cuisine = request.cuisine or "Türk Mutfağı"

    try:
        result = await gemini_service.generate_recipe(
            ingredients=clean_ingredients,
            cuisine=cuisine,
        )
    except Exception as exc:
        logger.error(f"generate_recipe beklenmeyen hata: {exc}", exc_info=True)
        result = {
            "success": False,
            "error": "unexpected_error",
            "message": "Tarif oluşturulurken beklenmeyen bir hata oluştu.",
        }

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    try:
        recipe_title = "Üçlü Tarif"
        if result.get("success") and "pratik" in result:
            recipe_title = result["pratik"].get("title", recipe_title)

        history_entry = RecipeHistory(
            cuisine=cuisine,
            ingredients=", ".join(clean_ingredients),
            recipe_title=recipe_title,
            generation_time_ms=elapsed_ms,
            success=result.get("success", False),
            error_message=result.get("message") if not result.get("success") else None,
        )
        db.add(history_entry)
        db.commit()
    except Exception as db_exc:
        logger.warning(f"Geçmiş kaydedilemedi: {db_exc}")
        db.rollback()

    if result.get("error") == "api_key_missing":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": "api_key_missing",
                "message": result.get("message", "API anahtarı yapılandırılmamış."),
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": result.get("success", False),
            "cuisine": result.get("cuisine", cuisine),
            "pratik": result.get("pratik"),
            "geleneksel": result.get("geleneksel"),
            "yaratici": result.get("yaratici"),
            "elapsed_ms": elapsed_ms,
            "error": result.get("error"),
            "message": result.get("message"),
        },
    )


@app.post(
    "/api/direct-recipe",
    tags=["Recipe"],
    summary="Doğrudan yemek adı ile tarif al",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_direct_recipe(
    request: DirectRecipeRequest,
    db: Session = Depends(get_db),
):
    """Kullanıcının yazdığı yemek adına göre detaylı bir tarif üretir."""
    start_time = time.time()

    if not request.dish_name or not request.dish_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Yemek adı boş olamaz.",
        )

    dish_name = request.dish_name.strip()

    try:
        result = await gemini_service.generate_direct_recipe(
            dish_name=dish_name,
            language=request.language or "tr",
        )
    except Exception as exc:
        logger.error(f"direct_recipe beklenmeyen hata: {exc}", exc_info=True)
        result = {
            "success": False,
            "error": "unexpected_error",
            "message": "Tarif oluşturulurken beklenmeyen bir hata oluştu.",
        }

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    try:
        recipe_title = dish_name
        cuisine = "Türk Mutfağı"
        if result.get("success") and "recipe" in result and result["recipe"]:
            recipe_title = result["recipe"].get("title", recipe_title)
            cuisine = result["recipe"].get("cuisine", cuisine)

        history_entry = RecipeHistory(
            cuisine=cuisine,
            ingredients=dish_name,
            recipe_title=recipe_title,
            generation_time_ms=elapsed_ms,
            success=result.get("success", False),
            error_message=result.get("message") if not result.get("success") else None,
        )
        db.add(history_entry)
        db.commit()
    except Exception as db_exc:
        logger.warning(f"Geçmiş kaydedilemedi: {db_exc}")
        db.rollback()

    if result.get("error") == "api_key_missing":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "error": "api_key_missing",
                "message": result.get("message", "API anahtarı yapılandırılmamış."),
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": result.get("success", False),
            "is_direct_recipe": True,
            "cuisine": result.get("recipe", {}).get("cuisine", "Türk Mutfağı") if (result.get("success") and result.get("recipe")) else None,
            "recipe": result.get("recipe"),
            "elapsed_ms": elapsed_ms,
            "error": result.get("error"),
            "message": result.get("message"),
        },
    )


# ─────────────────────────────────────────────
# FAVORİ YÖNETİMİ (KULLANICIYA ÖZEL)
# ─────────────────────────────────────────────

@app.get(
    "/api/favorites",
    tags=["Favorites"],
    summary="Kullanıcının kendi favorilerini listele",
    response_class=JSONResponse,
)
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aktif kullanıcının beğendiği favori tarifleri döner."""
    try:
        # Favori tablosundan eşleşen SavedRecipe kayıtlarını getir
        favorites_mapping = db.query(Favorite).filter(
            Favorite.user_id == current_user.id,
            Favorite.item_type == "recipe"
        ).all()

        recipe_ids = [f.item_id for f in favorites_mapping]
        saved_recipes = db.query(SavedRecipe).filter(SavedRecipe.id.in_(recipe_ids)).all() if recipe_ids else []

        # JSONResponse dönerken id olarak eşleme tablosunun id'sini kullanırsak, delete ederken sorun yaşamayız
        fav_map = {f.item_id: f.id for f in favorites_mapping}

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(saved_recipes),
                "favorites": [
                    {
                        "id": fav_map.get(r.id), # Favorite mapping ID
                        "title": r.title,
                        "cuisine": r.cuisine,
                        "ingredients": r.ingredients,
                        "recipe_text": r.recipe_text,
                        "servings": r.servings,
                        "prep_time": r.prep_time,
                        "cook_time": r.cook_time,
                        "difficulty": r.difficulty,
                        "recipe_type": r.recipe_type,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in saved_recipes
                ],
            },
        )
    except Exception as exc:
        logger.error(f"Favoriler listelenirken hata: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Favoriler yüklenirken hata oluştu.",
        )


@app.post(
    "/api/favorites",
    tags=["Favorites"],
    summary="Kullanıcı favorilerine tarif ekle",
    status_code=status.HTTP_201_CREATED,
    response_class=JSONResponse,
)
async def create_favorite(
    request: FavoriteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aktif kullanıcı için tarif kaydeder."""
    try:
        # Aynı başlıkta ve türde bu kullanıcı için kayıtlı favori var mı?
        existing = (
            db.query(Favorite)
            .join(SavedRecipe, SavedRecipe.id == Favorite.item_id)
            .filter(Favorite.user_id == current_user.id)
            .filter(Favorite.item_type == "recipe")
            .filter(SavedRecipe.title == request.title)
            .filter(SavedRecipe.recipe_type == request.recipe_type)
            .first()
        )
        if existing:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Bu tarif zaten favorilerinizde!",
                    "id": existing.id,
                    "already_exists": True,
                },
            )

        # SavedRecipe oluştur — flush() ile ID al, henüz commit etme
        saved_recipe = SavedRecipe(
            title=request.title,
            cuisine=request.cuisine,
            ingredients=request.ingredients,
            recipe_text=request.recipe_text,
            servings=request.servings,
            prep_time=request.prep_time,
            cook_time=request.cook_time,
            difficulty=request.difficulty,
            recipe_type=request.recipe_type,
        )
        db.add(saved_recipe)
        db.flush()  # ID üretildi ama transaction açık — atomik işlem için commit YOK

        # Eşleme ekle — SavedRecipe ile birlikte tek atomik commit
        favorite = Favorite(
            user_id=current_user.id,
            item_type="recipe",
            item_id=saved_recipe.id
        )
        db.add(favorite)
        db.commit()  # SavedRecipe + Favorite birlikte commit edildi (atomik)
        db.refresh(saved_recipe)
        db.refresh(favorite)

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Tarif favorilere eklendi! ❤️",
                "id": favorite.id,
                "already_exists": False,
            },
        )
    except Exception as exc:
        logger.error(f"Favori eklenirken hata: {exc}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Favori kaydedilirken hata oluştu.",
        )


@app.delete(
    "/api/favorites/{favorite_id}",
    tags=["Favorites"],
    summary="Favori kaldır",
    response_class=JSONResponse,
)
async def delete_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcının kendi favori eşleşmesini kaldırır."""
    try:
        favorite = db.query(Favorite).filter(
            Favorite.id == favorite_id,
            Favorite.user_id == current_user.id
        ).first()

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beğenilen içerik bulunamadı.",
            )

        # İlişkili SavedRecipe kaydını temizle (sadece bu favori kullanıyordu)
        if favorite.item_type == "recipe":
            saved_recipe = db.query(SavedRecipe).filter(SavedRecipe.id == favorite.item_id).first()
            if saved_recipe:
                db.delete(saved_recipe)

        db.delete(favorite)
        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Tarif favorilerden kaldırıldı.",
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Favori silinirken hata: {exc}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Favori silinirken hata oluştu.",
        )


# ─────────────────────────────────────────────
# KULLANICI PROFİL PANELİ ENPOINTLERİ
# ─────────────────────────────────────────────

@app.get(
    "/api/profile/favorites",
    tags=["Profile"],
    summary="Kullanıcının profil favorileri",
    response_class=JSONResponse,
)
async def get_profile_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Profil sayfası için favorileri döner (get_favorites ile aynı işlev)."""
    return await get_favorites(current_user, db)


@app.get(
    "/api/profile/posts",
    tags=["Profile"],
    summary="Kullanıcının kendi yorum/gönderileri",
    response_class=JSONResponse,
)
async def get_profile_posts(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Oturum açmış kullanıcının paylaştığı tüm topluluk gönderilerini döner."""
    try:
        base_url = str(request.base_url).rstrip('/')
        posts = (
            db.query(CommunityPost)
            .filter(CommunityPost.user_id == current_user.id)
            .order_by(CommunityPost.created_at.desc())
            .all()
        )
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(posts),
                "posts": [
                    {
                        "id": p.id,
                        "username": p.username,
                        "content": p.content,
                        "image_url": f"{base_url}/uploads/{os.path.basename(p.image_path)}" if p.image_path else None,
                        "section": p.section,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                    }
                    for p in posts
                ]
            }
        )
    except Exception as exc:
        logger.error(f"Profil gönderileri listelenirken hata: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Profil gönderileri yüklenirken hata oluştu.")


@app.delete(
    "/api/profile/posts/{post_id}",
    tags=["Profile"],
    summary="Kullanıcının kendi yorumunu silmesi",
    response_class=JSONResponse,
)
async def delete_my_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcının sadece kendi paylaştığı yorumu silmesini sağlar."""
    try:
        post = db.query(CommunityPost).filter(
            CommunityPost.id == post_id,
            CommunityPost.user_id == current_user.id
        ).first()

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Gönderi bulunamadı veya silme yetkiniz yok.",
            )

        # Görseli diskten sil
        if post.image_path and os.path.exists(post.image_path):
            try:
                os.remove(post.image_path)
            except Exception as e:
                logger.warning(f"Görsel silinemedi: {e}")

        db.delete(post)
        db.commit()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Gönderiniz başarıyla silindi.",
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Kendi gönderisini silerken hata: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gönderi silinirken hata oluştu.")


# ─────────────────────────────────────────────
# ADMİN PANELİ ENDPOINTLERİ
# ─────────────────────────────────────────────

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Admin rolü doğrulaması yapan yardımcı dependency."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yönetici yetkisi gerekiyor.",
        )
    return current_user


@app.get(
    "/api/admin/posts",
    tags=["Admin"],
    summary="Tüm yorumları listele (Yönetici)",
    response_class=JSONResponse,
)
async def get_admin_posts(
    request: Request,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Moderatör için sistemdeki tüm sekmelere ait tüm yorumları listeler."""
    try:
        base_url = str(request.base_url).rstrip('/')
        posts = (
            db.query(CommunityPost)
            .order_by(CommunityPost.created_at.desc())
            .all()
        )
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(posts),
                "posts": [
                    {
                        "id": p.id,
                        "username": p.username,
                        "content": p.content,
                        "image_url": f"{base_url}/uploads/{os.path.basename(p.image_path)}" if p.image_path else None,
                        "section": p.section,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                    }
                    for p in posts
                ]
            }
        )
    except Exception as exc:
        logger.error(f"Admin gönderileri yüklenirken hata: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gönderiler yüklenirken hata oluştu.")


@app.delete(
    "/api/admin/posts/{post_id}",
    tags=["Admin"],
    summary="Yorumu sistemden sil (Yönetici)",
    response_class=JSONResponse,
)
async def delete_admin_post(
    post_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Yöneticinin herhangi bir yorumu sistemden kalıcı olarak silmesini sağlar."""
    try:
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Yorum bulunamadı.")

        if post.image_path and os.path.exists(post.image_path):
            try:
                os.remove(post.image_path)
            except Exception as e:
                logger.warning(f"Görsel silinemedi: {e}")

        db.delete(post)
        db.commit()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Gönderi yönetici tarafından silindi.",
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Admin yorum silerken hata: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Yorum silinirken hata oluştu.")


@app.get(
    "/api/admin/summary",
    tags=["Admin"],
    summary="Sistem özet verilerini getir (Yönetici)",
    response_class=JSONResponse,
)
async def get_admin_summary(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Sistemdeki toplam kullanıcı, gönderi, favori ve tarif geçmişi sayılarını döner."""
    try:
        total_users = db.query(User).count()
        total_posts = db.query(CommunityPost).count()
        posts_mutfak = db.query(CommunityPost).filter(CommunityPost.section == "mutfak").count()
        posts_vlog = db.query(CommunityPost).filter(CommunityPost.section == "vlog").count()
        posts_elisi = db.query(CommunityPost).filter(CommunityPost.section == "elisi").count()
        total_favorites = db.query(Favorite).count()
        total_recipe_history = db.query(RecipeHistory).count()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "summary": {
                    "total_users": total_users,
                    "total_posts": total_posts,
                    "posts_mutfak": posts_mutfak,
                    "posts_vlog": posts_vlog,
                    "posts_elisi": posts_elisi,
                    "total_favorites": total_favorites,
                    "total_recipe_history": total_recipe_history,
                }
            }
        )
    except Exception as exc:
        logger.error(f"Admin özet bilgileri yüklenirken hata: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Özet veriler yüklenirken hata oluştu.")


@app.get(
    "/api/admin/users",
    tags=["Admin"],
    summary="Tüm kayıtlı kullanıcıları listele (Yönetici)",
    response_class=JSONResponse,
)
async def get_admin_users(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Tüm kayıtlı kullanıcıların bilgilerini listeler."""
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(users),
                "users": [
                    {
                        "id": u.id,
                        "email": u.email,
                        "username": u.username,
                        "role": u.role,
                        "created_at": u.created_at.isoformat() if u.created_at else None,
                    }
                    for u in users
                ]
            }
        )
    except Exception as exc:
        logger.error(f"Admin kullanıcıları listelerken hata: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Kullanıcılar yüklenirken hata oluştu.")


@app.delete(
    "/api/admin/users/{user_id}",
    tags=["Admin"],
    summary="Kullanıcıyı ve tüm verilerini sistemden sil (Yönetici)",
    response_class=JSONResponse,
)
async def delete_admin_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Bir kullanıcıyı siler. Bağlı favorilerini, SavedRecipe'lerini ve gönderilerini de temizler."""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi hesabınızı silemezsiniz.",
        )
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

        # 1. Kullanıcının favorilerini ve SavedRecipe'lerini sil
        user_favorites = db.query(Favorite).filter(Favorite.user_id == user_id).all()
        for fav in user_favorites:
            if fav.item_type == "recipe":
                saved_recipe = db.query(SavedRecipe).filter(SavedRecipe.id == fav.item_id).first()
                if saved_recipe:
                    db.delete(saved_recipe)
            db.delete(fav)

        # 2. Kullanıcının community gönderilerini sil (görsel dahil)
        user_posts = db.query(CommunityPost).filter(CommunityPost.user_id == user_id).all()
        for post in user_posts:
            if post.image_path and os.path.exists(post.image_path):
                try:
                    os.remove(post.image_path)
                except Exception as e:
                    logger.warning(f"Kullanıcının gönderi görseli silinemedi: {e}")
            db.delete(post)

        # 3. Kullanıcıyı sil
        db.delete(user)
        db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"'{user.username}' adlı kullanıcı ve tüm verileri silindi."
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Admin kullanıcı silerken hata: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Kullanıcı silinirken hata oluştu.")


# ─────────────────────────────────────────────
# KÖKÜ YÖNLENDIRME
# ─────────────────────────────────────────────
@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return JSONResponse(
        content={
            "message": "Mervenin Mutfagi API'ye hos geldiniz!",
            "docs": "/api/docs",
            "health": "/api/health",
            "version": "1.0.0",
        }
    )


# ─────────────────────────────────────────────
# TOPLULUK GÖNDERİLERİ (GUEST & LOGGED IN)
# ─────────────────────────────────────────────

@app.get(
    "/api/posts",
    tags=["Community"],
    summary="Sekmeye göre topluluk gönderilerini listele",
    response_class=JSONResponse,
)
async def get_posts(
    request: Request,
    section: str = Query(..., description="Sekme adı: mutfak | vlog | elisi"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Verilen sekmeye ait topluluk gönderilerini tarihe göre azalan sırada döner."""
    if section not in VALID_SECTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Geçersiz section. Kabul edilenler: {sorted(VALID_SECTIONS)}",
        )
    try:
        base_url = str(request.base_url).rstrip('/')
        posts = (
            db.query(CommunityPost)
            .filter(CommunityPost.section == section)
            .order_by(CommunityPost.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        total = db.query(CommunityPost).filter(CommunityPost.section == section).count()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "section": section,
                "count": total,
                "posts": [
                    {
                        "id": p.id,
                        "username": p.username,
                        "content": p.content,
                        "image_url": f"{base_url}/uploads/{os.path.basename(p.image_path)}" if p.image_path else None,
                        "section": p.section,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                    }
                    for p in posts
                ],
            },
        )
    except Exception as exc:
        logger.error(f"Topluluk gönderileri listelenirken hata: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gönderiler yüklenirken hata oluştu.")


@app.post(
    "/api/posts",
    tags=["Community"],
    summary="Yeni topluluk gönderisi ekle",
    status_code=status.HTTP_201_CREATED,
    response_class=JSONResponse,
)
async def create_post(
    request: Request,
    username: str = Form(...),
    content: str = Form(...),
    section: str = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Yeni bir topluluk gönderisi oluşturur. Oturum varsa kullanıcı ile eşler."""
    username = username.strip()
    content = content.strip()
    section = section.strip().lower()

    # Oturum açmışsa kimlik bilgilerini sabitle
    user_id = None
    if current_user:
        username = current_user.username
        user_id = current_user.id

    if not username or len(username) > 100:
        raise HTTPException(status_code=422, detail="Geçerli bir kullanıcı adı girin (maks 100 karakter).")
    if not content or len(content) > 2000:
        raise HTTPException(status_code=422, detail="Geçerli bir yorum girin (maks 2000 karakter).")
    if section not in VALID_SECTIONS:
        raise HTTPException(status_code=422, detail=f"Geçersiz section. Kabul edilenler: {sorted(VALID_SECTIONS)}")

    # Görsel yükleme
    image_path = None
    if image and image.filename:
        allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        if image.content_type not in allowed_types:
            raise HTTPException(status_code=422, detail="Yalnızca JPEG, PNG, GIF veya WebP görsel yükleyebilirsiniz.")

        ext = os.path.splitext(image.filename)[-1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            ext = ".jpg"

        contents = await image.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="Görsel boyutu 5 MB'ı geçemez.")

        filename = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(UPLOADS_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(contents)
        image_path = save_path
        logger.info(f"Görsel kaydedildi: {filename}")

    try:
        post = CommunityPost(
            user_id=user_id,
            username=username,
            content=content,
            section=section,
            image_path=image_path,
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        base_url = str(request.base_url).rstrip('/')
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Gönderiniz paylaşıldı! 🎉",
                "post": {
                    "id": post.id,
                    "username": post.username,
                    "content": post.content,
                    "image_url": f"{base_url}/uploads/{os.path.basename(post.image_path)}" if post.image_path else None,
                    "section": post.section,
                    "created_at": post.created_at.isoformat() if post.created_at else None,
                },
            },
        )
    except Exception as exc:
        logger.error(f"Topluluk gönderisi eklenirken hata: {exc}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Gönderi kaydedilirken hata oluştu.")


# Statik görsellere erişim — /uploads/{filename}
@app.get("/uploads/{filename}", tags=["Community"], include_in_schema=False)
async def serve_upload(filename: str):
    """Yüklenen görsellere statik erişim sağlar."""
    from fastapi.responses import FileResponse
    file_path = os.path.join(UPLOADS_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Görsel bulunamadı.")
    real = os.path.realpath(file_path)
    if not real.startswith(os.path.realpath(UPLOADS_DIR)):
        raise HTTPException(status_code=403, detail="Erişim reddedildi.")
    return FileResponse(file_path)


# Frontend statik dosyalarını servis et (Eğer dizin mevcutsa)
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Frontend statik dosyaları '{frontend_dir}' konumundan servis ediliyor.")


# ─────────────────────────────────────────────
# UYGULAMA GİRİŞ NOKTASI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
