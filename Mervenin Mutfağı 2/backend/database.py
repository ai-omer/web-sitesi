"""
Mervenin Mutfağı - Database Models & Setup
SQLAlchemy ile SQLite veritabanı tanımları.
Uygulama ilk çalıştığında tablolar otomatik oluşturulur.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, create_engine, text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os
import logging

logger = logging.getLogger("mervenin_mutfagi.database")

# Görsel yükleme dizini
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- Veritabanı Bağlantısı ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'mervenin_mutfagi.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite için gerekli
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Modeller ---

class User(Base):
    """Kullanıcı tablosu (Auth için)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)  # 'user' | 'admin'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class SavedRecipe(Base):
    """Kullanıcıların beğendiği ve saklanan tarif içerikleri."""
    __tablename__ = "saved_recipes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    cuisine = Column(String(100), nullable=True)
    ingredients = Column(Text, nullable=True)          # Virgülle ayrılmış malzeme listesi
    recipe_text = Column(Text, nullable=False)         # Tarif metni
    servings = Column(String(50), nullable=True)
    prep_time = Column(String(50), nullable=True)
    cook_time = Column(String(50), nullable=True)
    difficulty = Column(String(50), nullable=True)
    recipe_type = Column(String(50), nullable=True)     # pratik, geleneksel, yaratici
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<SavedRecipe(id={self.id}, title='{self.title}')>"


class Favorite(Base):
    """Kullanıcı ve içerik (Tarif vb.) eşleşme tablosu."""
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    item_type = Column(String(50), nullable=False, index=True)  # 'recipe' | 'vlog' | 'elisi'
    item_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, type='{self.item_type}')>"


class RecipeHistory(Base):
    """Oluşturulan tüm tariflerin geçmişi (analitik ve öneri için)."""
    __tablename__ = "recipe_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cuisine = Column(String(100), nullable=True)
    ingredients = Column(Text, nullable=True)
    recipe_title = Column(String(255), nullable=True)
    generation_time_ms = Column(Float, nullable=True)  # Yanıt süresi (milisaniye)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<RecipeHistory(id={self.id}, title='{self.recipe_title}')>"


class CommunityPost(Base):
    """Topluluk gönderileri — her sekmeye (mutfak/vlog/elisi) ayrı."""
    __tablename__ = "community_posts"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id    = Column(Integer, nullable=True, index=True)       # Oturum açmışsa kullanıcı ID
    username   = Column(String(100), nullable=False)
    content    = Column(Text, nullable=False)
    image_path = Column(String(500), nullable=True)   # Opsiyonel görsel yolu
    section    = Column(String(20), nullable=False, index=True)  # 'mutfak' | 'vlog' | 'elisi'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<CommunityPost(id={self.id}, section='{self.section}', user='{self.username}')>"


# --- Veritabanı Dependency ---

def get_db():
    """FastAPI endpoint'lerinde kullanılacak DB session dependency'si."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Tüm tabloları oluşturur. İlk çalışmada şema migration kontrolü yapar."""
    # Eski favorites tablosunu kontrol et ve gerekiyorsa sil
    with engine.begin() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(favorites);")).fetchall()
            columns = [r[1] for r in res]
            if len(columns) > 0 and "user_id" not in columns:
                logger.warning("Uyumsuz favorites tablosu tespit edildi, siliniyor...")
                conn.execute(text("DROP TABLE favorites;"))

            # Eski community_posts tablosunu kontrol et ve gerekiyorsa sil
            res_cp = conn.execute(text("PRAGMA table_info(community_posts);")).fetchall()
            columns_cp = [r[1] for r in res_cp]
            if len(columns_cp) > 0 and "user_id" not in columns_cp:
                logger.warning("Uyumsuz community_posts tablosu tespit edildi, siliniyor...")
                conn.execute(text("DROP TABLE community_posts;"))
        except Exception as e:
            logger.warning("Tablo kontrolu sirasinda hata olustu: %s", e)

    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)
    logger.info("Veritabani tablolari basariyla olusturuldu/dogrulandi.")

