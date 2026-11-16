"""
Mervenin Mutfağı - Pydantic Şemaları
Request / Response veri doğrulama modelleri.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ─────────────────────────────────────────────
# REQUEST ŞEMALARI
# ─────────────────────────────────────────────

class RecipeRequest(BaseModel):
    """Tarif oluşturma isteği şeması."""
    ingredients: List[str] = Field(
        ...,
        min_length=1,
        description="Dolaptaki malzemelerin listesi",
        examples=[["domates", "yumurta", "peynir"]],
    )
    cuisine: Optional[str] = Field(
        default="Türk Mutfağı",
        description="Dünya Mutfağı: Türk Mutfağı, İtalyan Mutfağı, Meksika Mutfağı, vb.",
    )
    language: Optional[str] = Field(
        default="tr",
        description="Yanıt dili (tr/en)",
    )


class DirectRecipeRequest(BaseModel):
    """Doğrudan yemek adı ile tarif isteme şeması."""
    dish_name: str = Field(
        ...,
        min_length=2,
        description="Tarifi istenen yemeğin adı",
        examples=["Kuru Fasulye"],
    )
    language: Optional[str] = Field(
        default="tr",
        description="Yanıt dili (tr/en)",
    )


class FavoriteCreateRequest(BaseModel):
    """Favori kaydetme isteği şeması."""
    title: str = Field(..., max_length=255, description="Tarif başlığı")
    cuisine: Optional[str] = Field(default=None, max_length=100)
    ingredients: Optional[str] = Field(
        default=None,
        description="Virgülle ayrılmış malzeme listesi",
    )
    recipe_text: str = Field(..., description="Tam tarif metni")
    servings: Optional[str] = Field(default=None, max_length=50)
    prep_time: Optional[str] = Field(default=None, max_length=50)
    cook_time: Optional[str] = Field(default=None, max_length=50)
    difficulty: Optional[str] = Field(default=None, max_length=50)
    recipe_type: Optional[str] = Field(default=None, max_length=50) # pratik, geleneksel, yaratici


# ─────────────────────────────────────────────
# RESPONSE ŞEMALARI
# ─────────────────────────────────────────────

class RecipeStep(BaseModel):
    """Tek bir tarif adımı."""
    step_number: int
    description: str


class NutritionInfo(BaseModel):
    """Besin değeri bilgileri (tahmini)."""
    calories: Optional[str] = None
    protein: Optional[str] = None
    carbs: Optional[str] = None
    fat: Optional[str] = None


class SingleRecipe(BaseModel):
    """Tek bir tarif seçeneği."""
    title: Optional[str] = Field(default="Özel Tarif")
    description: Optional[str] = None
    servings: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    difficulty: Optional[str] = None
    ingredients_used: Optional[List[str]] = None
    additional_ingredients: Optional[List[str]] = None
    steps: Optional[List[Any]] = None          # str veya dict kabul eder
    tips: Optional[List[str]] = None
    nutrition: Optional[NutritionInfo] = None
    raw_text: Optional[str] = None
    malzemeler_detay: Optional[List[str]] = None
    hazirlanis_adimlari: Optional[List[str]] = None
    puf_noktalari: Optional[List[str]] = None
    sunum_onerisi: Optional[str] = None


class RecipeResponse(BaseModel):
    """
    AI tarafından üretilen üçlü tarif yanıtı.
    Tüm alanlar Optional — frontend kırılmasın diye.
    """
    success: bool = True
    cuisine: Optional[str] = None
    pratik: Optional[SingleRecipe] = None
    geleneksel: Optional[SingleRecipe] = None
    yaratici: Optional[SingleRecipe] = None
    elapsed_ms: Optional[float] = None
    error: Optional[str] = None
    message: Optional[str] = None


class DirectRecipeResponse(BaseModel):
    """Doğrudan yemek adı tarif yanıtı."""
    success: bool = True
    is_direct_recipe: bool = True
    cuisine: Optional[str] = None
    recipe: Optional[SingleRecipe] = None
    elapsed_ms: Optional[float] = None
    error: Optional[str] = None
    message: Optional[str] = None


class FavoriteResponse(BaseModel):
    """Favori tarif yanıtı."""
    id: int
    title: str
    cuisine: Optional[str] = None
    ingredients: Optional[str] = None
    recipe_text: str
    servings: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    difficulty: Optional[str] = None
    recipe_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FavoritesListResponse(BaseModel):
    """Favori listesi yanıtı."""
    success: bool = True
    count: int
    favorites: List[FavoriteResponse]


class DeleteResponse(BaseModel):
    """Silme işlemi yanıtı."""
    success: bool
    message: str


class HealthResponse(BaseModel):
    """Sağlık kontrolü yanıtı."""
    status: str
    message: str
    api_key_configured: bool
    database: str
    version: str


class ErrorResponse(BaseModel):
    """Hata yanıtı."""
    success: bool = False
    error: str
    detail: Optional[str] = None


# ─────────────────────────────────────────────
# TOPLULUK GÖNDERİ ŞEMALARI
# ─────────────────────────────────────────────

VALID_SECTIONS = {"mutfak", "vlog", "elisi"}

class CommunityPostCreate(BaseModel):
    """Topluluk gönderisi oluşturma şeması."""
    username: str = Field(..., min_length=1, max_length=100, description="Kullanıcı adı")
    content: str = Field(..., min_length=1, max_length=2000, description="Yorum/paylaşım metni")
    section: str = Field(..., description="Sekme: mutfak | vlog | elisi")

    def validate_section(self):
        if self.section not in VALID_SECTIONS:
            raise ValueError(f"Geçersiz section. İzin verilenler: {VALID_SECTIONS}")


class CommunityPostResponse(BaseModel):
    """Topluluk gönderisi yanıt şeması."""
    id: int
    username: str
    content: str
    image_url: Optional[str] = None   # Tam URL (frontend için hazır)
    section: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# KULLANICI & AUTH ŞEMALARI
# ─────────────────────────────────────────────

class UserRegister(BaseModel):
    email: str = Field(..., max_length=255, description="E-posta adresi")
    username: str = Field(..., min_length=2, max_length=100, description="Kullanıcı adı")
    password: str = Field(..., min_length=6, description="Şifre")

class UserLogin(BaseModel):
    email: str = Field(..., description="E-posta adresi")
    password: str = Field(..., description="Şifre")

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    success: bool = True
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

