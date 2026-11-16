/**
 * ══════════════════════════════════════════════════════
 * Mervenin Mutfağı — Frontend JavaScript
 * app.js — Tüm sayfalar için paylaşılan uygulama mantığı
 * ══════════════════════════════════════════════════════
 */

// ─── YAPILANDIRMA ───────────────────────────────────────
// Dinamik API host tespiti (Yerel ağda/Wi-Fi üzerinden mobil testler için)
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  if (!hostname || hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  return `http://${hostname}:8000`;
};

const CONFIG = {
  API_BASE_URL: getApiBaseUrl(),  // Backend URL
  ENDPOINTS: {
    GENERATE_RECIPE: '/api/generate-recipe',
    FAVORITES: '/api/favorites',
    HEALTH: '/api/health',
    DIRECT_RECIPE: '/api/direct-recipe',
  },
};

// ─── UYGULAMA DURUMU ─────────────────────────────────────
const AppState = {
  ingredients: [],            // Eklenen malzemeler listesi
  selectedCuisine: null,      // Seçilen dünya mutfağı
  currentRecipe: null,        // Son oluşturulan tarif verisi (üçlü yapıyı barındırır)
  activeRecipeType: 'pratik', // Aktif tarif sekmesi (pratik, geleneksel, yaratici)
  isSavedFavorite: false,     // Favori olarak kaydedildi mi?
  isLoading: false,           // İstek devam ediyor mu?
  searchMode: 'ingredients',  // 'ingredients' (malzemeli) veya 'direct' (doğrudan yemek adı)
};

// ─── YÜKLEME ANIMASYONU MESAJLARI ────────────────────────
const LOADING_MESSAGES = [
  'Merve Şef tariflerinizi hazırlıyor... 👩‍🍳',
  'Malzemeler taze taze yıkanıyor... 🥕',
  'Gizli baharat karışımı hazırlanıyor... 🌶️',
  'Fırın en doğru dereceye ayarlanıyor... 🔥',
  'Soslar tıkır tıkır kaynıyor... 🥣',
  'Pratik, Geleneksel ve Yaratıcı seçenekler şekilleniyor... ✨',
  'Sunum tabakları hazırlanıyor... 🍽️',
  'Merve Şef son dokunuşları yapıyor... 🌿',
  'Tabaklar süsleniyor, çok az kaldı... 😍',
];

let loadingInterval = null;
let loadingMsgIndex = 0;

// ════════════════════════════════════════════════════════
// NAVIGASYON & MOBİL MENÜ
// ════════════════════════════════════════════════════════

function initNavbar() {
  const navbar = document.getElementById('navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 60) {
        navbar.style.background = 'rgba(26,26,26,0.98)';
        navbar.style.borderBottomColor = 'rgba(241,90,36,0.25)';
      } else {
        navbar.style.background = 'rgba(26,26,26,0.85)';
        navbar.style.borderBottomColor = 'rgba(241,90,36,0.15)';
      }
    }, { passive: true });
  }

  // Anasayfa mobil menü
  const mobileBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
    });
  }

  // Chef sayfası mobil menü
  const chefMobileBtn = document.getElementById('chef-mobile-menu-btn');
  const chefMobileMenu = document.getElementById('chef-mobile-menu');
  if (chefMobileBtn && chefMobileMenu) {
    chefMobileBtn.addEventListener('click', () => {
      chefMobileMenu.classList.toggle('open');
    });
  }

  // Sayfa dışına tıklamada menüleri kapat
  document.addEventListener('click', (e) => {
    if (mobileBtn && mobileMenu && !mobileBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
      mobileMenu.classList.remove('open');
    }
    if (chefMobileBtn && chefMobileMenu && !chefMobileBtn.contains(e.target) && !chefMobileMenu.contains(e.target)) {
      chefMobileMenu.classList.remove('open');
    }
  });
}
  });
}

// ════════════════════════════════════════════════════════
// MUTFAK SEÇİMİ
// ════════════════════════════════════════════════════════

/**
 * Dünya mutfağı kartına tıklandığında çağrılır.
 * @param {HTMLElement} element — Tıklanan mutfak kartı elementi
 */
function selectCuisine(element) {
  if (!element) return;

  // Önceki seçimi temizle
  document.querySelectorAll('.cuisine-card').forEach((card) => {
    card.classList.remove('selected');
    card.setAttribute('aria-pressed', 'false');
  });

  // Yeni seçimi işaretle
  element.classList.add('selected');
  element.setAttribute('aria-pressed', 'true');
  AppState.selectedCuisine = element.dataset.cuisine;

  // Hata mesajını temizle
  hideError();
}

// ════════════════════════════════════════════════════════
// MALZEME TAG SİSTEMİ
// ════════════════════════════════════════════════════════

/**
 * Malzeme tag'ı ekler.
 * @param {string} [value] — Eklenecek malzeme değeri (opsiyonel, input'tan okur)
 */
function addIngredient(value) {
  const input = document.getElementById('ingredient-input');
  const raw = value !== undefined ? value : (input ? input.value.trim() : '');

  if (!raw) return;

  // Virgülle ayrılmış birden fazla malzeme
  const parts = raw.split(',').map((s) => s.trim()).filter((s) => s.length >= 2);

  parts.forEach((part) => {
    const normalized = part.toLowerCase();
    if (!AppState.ingredients.includes(normalized) && AppState.ingredients.length < 20) {
      AppState.ingredients.push(normalized);
    }
  });

  if (input && value === undefined) {
    input.value = '';
  }

  renderTags();
  hideError();
}

/**
 * Malzeme tag'ını kaldırır.
 * @param {string} ingredient — Kaldırılacak malzeme
 */
function removeIngredient(ingredient) {
  AppState.ingredients = AppState.ingredients.filter((i) => i !== ingredient);
  renderTags();
}

/**
 * Tag listesini DOM'da render eder.
 */
function renderTags() {
  const container = document.getElementById('tags-container');
  if (!container) return;

  container.innerHTML = '';
  AppState.ingredients.forEach((ing) => {
    const chip = document.createElement('span');
    chip.className = 'tag-chip';
    chip.innerHTML = `
      ${ing}
      <span class="remove-btn" role="button" aria-label="${ing} kaldır" onclick="removeIngredient('${ing}')">×</span>
    `;
    container.appendChild(chip);
  });
}

/**
 * Input klavye olaylarını dinler.
 */
function initIngredientInput() {
  const input = document.getElementById('ingredient-input');
  if (!input) return;

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addIngredient();
