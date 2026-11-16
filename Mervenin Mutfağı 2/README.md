# Mervenin Mutfağı 🍳

**Production-ready, AI destekli yemek tarifi platformu.**

---

## 🚀 Hızlı Başlangıç

### 1. Backend Kurulumu

```bash
cd backend

# Sanal ortam oluştur (önerilir)
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını oluştur
copy .env.example .env
# .env dosyasını açın ve GEMINI_API_KEY'i ekleyin

# Sunucuyu başlat
python main.py
# veya
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend çalıştıktan sonra:
- API Docs: http://localhost:8000/api/docs
- Sağlık Kontrolü: http://localhost:8000/api/health

### 2. Frontend

```bash
# Doğrudan frontend/index.html dosyasını tarayıcıda açın
# veya canlı sunucu için VS Code Live Server eklentisini kullanın
```

---

## 📁 Klasör Yapısı

```
Mervenin Mutfağı 2/
├── backend/
│   ├── main.py              # FastAPI ana uygulama
│   ├── database.py          # SQLAlchemy modelleri & SQLite setup
│   ├── gemini_service.py    # Google Gemini AI entegrasyonu
│   ├── schemas.py           # Pydantic request/response şemaları
│   ├── requirements.txt     # Python bağımlılıkları
│   ├── .env.example         # Örnek ortam değişkenleri
│   └── .env                 # ⚠️ Kendi .env'inizi oluşturun (git'e eklemeyin!)
└── frontend/
    ├── index.html           # Ana sayfa
    ├── chef.html            # AI Şef Sihirbazı sayfası
    └── app.js               # Tüm JavaScript mantığı
```

---

## 🔑 API Anahtarı Alma

1. [Google AI Studio](https://aistudio.google.com/app/apikey) adresine gidin
2. Ücretsiz API anahtarı oluşturun
3. `backend/.env` dosyasına ekleyin:

```env
GEMINI_API_KEY=AIzaSy...
```

---

## 🌐 API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/api/health` | Sağlık kontrolü |
| `POST` | `/api/generate-recipe` | AI ile tarif oluştur |
| `GET` | `/api/favorites` | Favorileri listele |
| `POST` | `/api/favorites` | Favori ekle |
| `DELETE` | `/api/favorites/{id}` | Favori sil |
| `GET` | `/api/favorites/{id}` | Tek favori getir |

---

## 📢 Reklam Alanları

Frontend dosyalarında `<!-- REKLAM ALANI -->` yorumları ile işaretlenmiş alanlar:
- `index.html`: 3 adet reklam placeholder
- `chef.html`: 4 adet reklam placeholder (sol/sağ sidebar + form altı + tarif içi)

Google AdSense onaylandığında bu alanların içine AdSense kod bloklarını yapıştırabilirsiniz.

---

## ⚙️ Production Dağıtımı

- **Backend**: Heroku, Railway, Render, VPS (Nginx + Gunicorn/Uvicorn)
- **Frontend**: Netlify, Vercel, GitHub Pages veya aynı VPS
- **CORS**: `main.py`'deki `allow_origins=["*"]` değerini domain adresinizle değiştirin
- **Güvenlik**: `.env` dosyasını asla git'e commit etmeyin

---

## 🛠 Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI 0.111, Python 3.11+ |
| AI | Google Gemini 2.5 Flash |
| Veritabanı | SQLite (SQLAlchemy ORM) |
| Frontend | Vanilla HTML/CSS/JS + Tailwind CSS |
| Stil | Playfair Display + Inter fontları |

---

*© 2025 Mervenin Mutfağı. Tüm hakları saklıdır.* ❤️
