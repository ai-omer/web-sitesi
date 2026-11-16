/**
 * ══════════════════════════════════════════════════════
 * Mervenin Mutfağı — Frontend JavaScript
 * app.js — Mutfak sayfası uygulama mantığı
 * ══════════════════════════════════════════════════════
 */

// ─── YAPILANDIRMA ───────────────────────────────────────
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  if (!hostname || hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  return `http://${hostname}:8000`;
};

const CONFIG = {
  API_BASE_URL: getApiBaseUrl(),
  ENDPOINTS: {
    GENERATE_RECIPE: '/api/generate-recipe',
    FAVORITES: '/api/favorites',
    HEALTH: '/api/health',
    DIRECT_RECIPE: '/api/direct-recipe',
  },
};

// ─── UYGULAMA DURUMU ─────────────────────────────────────
const AppState = {
  ingredients: [],
  selectedCuisine: null,
  currentRecipe: null,
  activeRecipeType: 'pratik',
  isSavedFavorite: false,
  isLoading: false,
  searchMode: 'ingredients',
  baseServings: 4,
  currentServings: 4,
};

// ─── YÜKLEME MESAJLARI ────────────────────────────────────
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

  const mobileBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
    });
  }

  const chefMobileBtn = document.getElementById('chef-mobile-menu-btn');
  const chefMobileMenu = document.getElementById('chef-mobile-menu');
  if (chefMobileBtn && chefMobileMenu) {
    chefMobileBtn.addEventListener('click', () => {
      chefMobileMenu.classList.toggle('open');
    });
  }

  document.addEventListener('click', (e) => {
    if (mobileBtn && mobileMenu && !mobileBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
      mobileMenu.classList.remove('open');
    }
    if (chefMobileBtn && chefMobileMenu && !chefMobileBtn.contains(e.target) && !chefMobileMenu.contains(e.target)) {
      chefMobileMenu.classList.remove('open');
    }
  });
}

// ════════════════════════════════════════════════════════
// MUTFAK SEÇİMİ
// ════════════════════════════════════════════════════════

function selectCuisine(element) {
  if (!element) return;

  document.querySelectorAll('.cuisine-card').forEach((card) => {
    card.classList.remove('selected');
    card.setAttribute('aria-pressed', 'false');
  });

  element.classList.add('selected');
  element.setAttribute('aria-pressed', 'true');
  AppState.selectedCuisine = element.dataset.cuisine;

  hideError();
}

// ════════════════════════════════════════════════════════
// MALZEME TAG SİSTEMİ
// ════════════════════════════════════════════════════════

function addIngredient(value) {
  const input = document.getElementById('ingredient-input');
  const raw = value !== undefined ? value : (input ? input.value.trim() : '');

  if (!raw) return;

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

function removeIngredient(ingredient) {
  AppState.ingredients = AppState.ingredients.filter((i) => i !== ingredient);
  renderTags();
}

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

function initIngredientInput() {
  const input = document.getElementById('ingredient-input');
  if (!input) return;

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addIngredient();
    } else if (e.key === ',' || e.key === ';') {
      e.preventDefault();
      addIngredient();
    }
  });
}

// ════════════════════════════════════════════════════════
// DOĞRUDAN TARİF MODU
// ════════════════════════════════════════════════════════

function initDirectInput() {
  const input = document.getElementById('direct-recipe-input');
  if (!input) return;

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleGenerateSubmit();
    }
  });
}

function setDirectRecipeQuery(value) {
  const input = document.getElementById('direct-recipe-input');
  if (input) {
    input.value = value;
    input.focus();
  }
}

// ════════════════════════════════════════════════════════
// FORM MOD GEÇİŞİ
// ════════════════════════════════════════════════════════

function switchFormMode(mode) {
  AppState.searchMode = mode;

  const ingredientsFields = document.getElementById('ingredients-mode-fields');
  const directFields = document.getElementById('direct-mode-fields');
  const btnIngredients = document.getElementById('form-mode-ingredients');
  const btnDirect = document.getElementById('form-mode-direct');

  if (mode === 'ingredients') {
    if (ingredientsFields) ingredientsFields.classList.remove('hidden');
    if (directFields) directFields.classList.add('hidden');
    if (btnIngredients) {
      btnIngredients.classList.add('border-brand-orange', 'text-brand-orange');
      btnIngredients.classList.remove('border-transparent', 'text-gray-400');
    }
    if (btnDirect) {
      btnDirect.classList.remove('border-brand-orange', 'text-brand-orange');
      btnDirect.classList.add('border-transparent', 'text-gray-400');
    }
  } else {
    if (directFields) directFields.classList.remove('hidden');
    if (ingredientsFields) ingredientsFields.classList.add('hidden');
    if (btnDirect) {
      btnDirect.classList.add('border-brand-orange', 'text-brand-orange');
      btnDirect.classList.remove('border-transparent', 'text-gray-400');
    }
    if (btnIngredients) {
      btnIngredients.classList.remove('border-brand-orange', 'text-brand-orange');
      btnIngredients.classList.add('border-transparent', 'text-gray-400');
    }
  }

  hideError();
}

// ════════════════════════════════════════════════════════
// HATA GÖSTER / GİZLE
// ════════════════════════════════════════════════════════

function showError(message) {
  const el = document.getElementById('form-error');
  if (el) {
    el.textContent = message;
    el.classList.remove('hidden');
  }
}

function hideError() {
  const el = document.getElementById('form-error');
  if (el) el.classList.add('hidden');
}

// ════════════════════════════════════════════════════════
// YÜKLEME ANİMASYONU
// ════════════════════════════════════════════════════════

function showLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.remove('hidden');

  loadingMsgIndex = 0;
  const textEl = document.getElementById('loading-text');
  if (textEl) textEl.textContent = LOADING_MESSAGES[0];

  loadingInterval = setInterval(() => {
    loadingMsgIndex = (loadingMsgIndex + 1) % LOADING_MESSAGES.length;
    if (textEl) textEl.textContent = LOADING_MESSAGES[loadingMsgIndex];
  }, 2500);
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.add('hidden');
  if (loadingInterval) {
    clearInterval(loadingInterval);
    loadingInterval = null;
  }
}

// ════════════════════════════════════════════════════════
// TARİF OLUŞTURMA (ANA FORM GÖNDERİMİ)
// ════════════════════════════════════════════════════════

async function handleGenerateSubmit() {
  if (AppState.isLoading) return;

  hideError();

  if (AppState.searchMode === 'direct') {
    await generateDirectRecipe();
  } else {
    await generateRecipe();
  }
}

async function generateRecipe() {
  if (AppState.ingredients.length === 0) {
    showError('Lütfen en az bir malzeme ekleyin.');
    return;
  }

  AppState.isLoading = true;
  AppState.isSavedFavorite = false;
  showLoading();

  try {
    const body = {
      ingredients: AppState.ingredients,
      cuisine: AppState.selectedCuisine || null,
    };

    const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.GENERATE_RECIPE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 503 || (data && data.detail && data.detail.includes('API'))) {
        hideLoading();
        AppState.isLoading = false;
        showApiKeyWarning();
        return;
      }
      throw new Error(data.detail || 'Tarif oluşturulamadı.');
    }

    AppState.currentRecipe = data;
    AppState.activeRecipeType = 'pratik';

    hideLoading();
    AppState.isLoading = false;

    // Sekme sürelerini güncelle
    updateTabTimes(data);

    // Doğrudan tarif sekmelerini gizle, üçlü sekmeleri göster
    const tabsContainer = document.getElementById('recipe-tabs-container');
    if (tabsContainer) tabsContainer.classList.remove('hidden');

    // Pratik sekmeyi aktif yap
    switchRecipeTab('pratik');

  } catch (err) {
    hideLoading();
    AppState.isLoading = false;
    console.error('Tarif hatası:', err);
    showRecipeError(err.message || 'Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.');
  }
}

async function generateDirectRecipe() {
  const input = document.getElementById('direct-recipe-input');
  const query = input ? input.value.trim() : '';

  if (!query) {
    showError('Lütfen bir yemek adı yazın.');
    return;
  }

  AppState.isLoading = true;
  AppState.isSavedFavorite = false;
  showLoading();

  try {
    const body = { dish_name: query };

    const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.DIRECT_RECIPE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 503 || (data && data.detail && data.detail.includes('API'))) {
        hideLoading();
        AppState.isLoading = false;
        showApiKeyWarning();
        return;
      }
      throw new Error(data.detail || 'Tarif oluşturulamadı.');
    }

    AppState.currentRecipe = data;
    AppState.activeRecipeType = 'direkt';

    hideLoading();
    AppState.isLoading = false;

    // Doğrudan tarif modunda sekmeleri gizle
    const tabsContainer = document.getElementById('recipe-tabs-container');
    if (tabsContainer) tabsContainer.classList.add('hidden');

    // Tarifi render et
    renderActiveRecipe(data.recipe, 'direkt');

  } catch (err) {
    hideLoading();
    AppState.isLoading = false;
    console.error('Direkt tarif hatası:', err);
    showRecipeError(err.message || 'Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.');
  }
}

// ════════════════════════════════════════════════════════
// SEKME GEÇİŞİ (pratik / geleneksel / yaratici)
// ════════════════════════════════════════════════════════

function switchRecipeTab(type) {
  if (!AppState.currentRecipe) return;

  AppState.activeRecipeType = type;

  // Tab buton stillerini güncelle
  ['pratik', 'geleneksel', 'yaratici'].forEach((t) => {
    const btn = document.getElementById(`tab-${t}`);
    if (!btn) return;
    if (t === type) {
      btn.classList.add('border-brand-orange', 'text-brand-orange');
      btn.classList.remove('border-transparent', 'text-gray-400');
    } else {
      btn.classList.remove('border-brand-orange', 'text-brand-orange');
      btn.classList.add('border-transparent', 'text-gray-400');
    }
  });

  const recipe = AppState.currentRecipe[type];
  if (recipe) {
    renderActiveRecipe(recipe, type);
  }
}

function updateTabTimes(data) {
  ['pratik', 'geleneksel', 'yaratici'].forEach((t) => {
    const timeEl = document.getElementById(`tab-${t}-time`);
    if (timeEl && data[t]) {
      timeEl.textContent = data[t].total_time || data[t].cook_time || '-';
    }
  });
}

// ════════════════════════════════════════════════════════
// MALZEME PORSİYON HESAPLAMA YARDIMCILARI
// ════════════════════════════════════════════════════════

function formatScaledNumber(val) {
  if (Math.abs(val - Math.round(val)) < 0.01) {
    return Math.round(val).toString();
  }

  const integerPart = Math.floor(val);
  const fractionalPart = val - integerPart;

  let fracStr = "";
  if (Math.abs(fractionalPart - 0.25) < 0.05) {
    fracStr = "1/4";
  } else if (Math.abs(fractionalPart - 0.5) < 0.05) {
    fracStr = "1/2";
  } else if (Math.abs(fractionalPart - 0.75) < 0.05) {
    fracStr = "3/4";
  }

  if (fracStr) {
    return integerPart > 0 ? `${integerPart} ${fracStr}` : fracStr;
  }

  return val.toFixed(1).replace('.', ',').replace(',0', '');
}

function scaleIngredient(str, ratio) {
  if (ratio === 1) return str;

  // regex to match fractions (e.g. 1/2), decimals (e.g. 1.5 or 1,5), and integers (e.g. 2) at the start of string
  const fractionRegex = /^(\d+)\/(\d+)/;
  const decimalRegex = /^(\d+[\.,]\d+)/;
  const integerRegex = /^(\d+)/;

  let match;

  if ((match = str.match(fractionRegex))) {
    const num = parseInt(match[1]);
    const den = parseInt(match[2]);
    const val = (num / den) * ratio;
    const formatted = formatScaledNumber(val);
    return str.replace(fractionRegex, formatted);
  }

  if ((match = str.match(decimalRegex))) {
    const val = parseFloat(match[1].replace(',', '.')) * ratio;
    const formatted = formatScaledNumber(val);
    return str.replace(decimalRegex, formatted);
  }

  if ((match = str.match(integerRegex))) {
    const val = parseInt(match[1]) * ratio;
    const formatted = formatScaledNumber(val);
    return str.replace(integerRegex, formatted);
  }

  return str;
}

function updateIngredientsList(recipe) {
  const ratio = AppState.currentServings / AppState.baseServings;

  const detailedIngredients = recipe.malzemeler_detay || [];
  const basicIngredients = recipe.ingredients_used || AppState.ingredients || [];
  const basicSection = document.getElementById('basic-ingredients-section');

  if (detailedIngredients.length > 0) {
    const scaledDetailed = detailedIngredients.map(ing => scaleIngredient(ing, ratio));
    renderList('result-malzemeler-detay', scaledDetailed, (ing) =>
      `<li class="flex items-start gap-2"><span class="text-brand-orange mt-0.5 text-xs">◆</span><span>${escapeHtml(ing)}</span></li>`
    );
    if (basicSection) basicSection.classList.add('hidden');
  } else {
    setTextById('result-malzemeler-detay', '');
    if (basicSection) {
      basicSection.classList.remove('hidden');
      const scaledBasic = basicIngredients.map(ing => scaleIngredient(ing, ratio));
      renderList('result-ingredients-used', scaledBasic, (ing) =>
        `<li class="flex items-start gap-2"><span class="text-brand-orange mt-0.5 text-xs">◆</span><span>${escapeHtml(ing)}</span></li>`
      );
    }
  }

  const additionalSection = document.getElementById('additional-ingredients-section');
  const additionalList = recipe.additional_ingredients || [];
  if (additionalList.length > 0 && additionalSection) {
    const scaledAdditional = additionalList.map(ing => scaleIngredient(ing, ratio));
    additionalSection.classList.remove('hidden');
    renderList('result-additional-ingredients', scaledAdditional, (ing) =>
      `<li class="flex items-start gap-2"><span class="text-gray-500 mt-0.5 text-xs">◇</span><span>${escapeHtml(ing)}</span></li>`
    );
  } else if (additionalSection) {
    additionalSection.classList.add('hidden');
  }
}

// ════════════════════════════════════════════════════════
// TARİF RENDER (AKTİF SEKME)
// ════════════════════════════════════════════════════════

function renderActiveRecipe(recipe, type) {
  const resultSection = document.getElementById('recipe-result');
  const successCard = document.getElementById('recipe-success-card');
  const errorCard = document.getElementById('recipe-error-card');
  const apiKeyWarning = document.getElementById('api-key-warning');

  if (!resultSection || !recipe) return;

  if (errorCard) errorCard.classList.add('hidden');
  if (apiKeyWarning) apiKeyWarning.classList.add('hidden');
  if (successCard) successCard.classList.remove('hidden');

  // Favori buton durumu
  const favBtn = document.getElementById('favorite-btn');
  if (favBtn) {
    if (AppState.isSavedFavorite) {
      favBtn.style.color = '#ef4444';
      favBtn.title = 'Favorilere Eklendi ✓';
    } else {
      favBtn.style.color = '';
      favBtn.title = 'Favorilere Ekle';
    }
  }

  // Başlık ve açıklama
  setTextById('result-title', recipe.title || 'Merve Şef Önerisi');
  setTextById('result-description', recipe.description || '');

  // Badgeler
  const displayCuisine = (AppState.currentRecipe && AppState.currentRecipe.cuisine) || AppState.selectedCuisine || 'Dünya Mutfağı';
  setTextById('result-cuisine-badge', `🍳 ${displayCuisine}`);

  const typeLabels = {
    pratik: '⚡ Pratik Seçenek',
    geleneksel: '🏛️ Geleneksel Seçenek',
    yaratici: '💡 Yaratıcı Seçenek',
    direkt: '🔍 Doğrudan Tarif',
  };
  setTextById('result-type-badge', typeLabels[type] || 'Özel Tarif');
  setTextById('result-difficulty-badge', recipe.difficulty || 'Kolay');

  // Süre ve porsiyon
  let parsedServings = parseInt(recipe.servings);
  if (isNaN(parsedServings) || parsedServings <= 0) {
    parsedServings = 4;
  }
  AppState.baseServings = parsedServings;

  if (!AppState.currentServings || AppState.currentServings <= 0) {
    AppState.currentServings = parsedServings;
  }

  setTextById('result-servings', AppState.currentServings);
  setTextById('result-prep-time', recipe.prep_time || '—');
  setTextById('result-cook-time', recipe.cook_time || '—');
  setTextById('result-total-time', recipe.total_time || '—');

  // Malzemeleri ölçekleyerek listele
  updateIngredientsList(recipe);

  // Hazırlanış Adımları
  const newStepsEl = document.getElementById('result-hazirlanis-adimlari');
  const oldStepsEl = document.getElementById('result-steps');
  const detailedSteps = recipe.hazirlanis_adimlari || [];
  const oldSteps = recipe.steps || [];

  if (newStepsEl) newStepsEl.innerHTML = '';
  if (oldStepsEl) oldStepsEl.innerHTML = '';

  if (detailedSteps.length > 0 && newStepsEl) {
    if (oldStepsEl) oldStepsEl.classList.add('hidden');
    newStepsEl.classList.remove('hidden');

    detailedSteps.forEach((step, idx) => {
      const li = document.createElement('li');
      li.className = 'flex gap-4 items-start fade-in';
      li.style.animationDelay = `${idx * 0.05}s`;
      li.innerHTML = `
        <div class="step-number flex-shrink-0 mt-0.5">${idx + 1}</div>
        <div class="rounded-2xl p-4 flex-1 text-sm text-gray-300 leading-relaxed" style="background: #1A1A1A; border: 1px solid #333;">${escapeHtml(step)}</div>
      `;
      newStepsEl.appendChild(li);
    });
  } else if (oldSteps.length > 0 && oldStepsEl) {
    if (newStepsEl) newStepsEl.classList.add('hidden');
    oldStepsEl.classList.remove('hidden');

    if (oldSteps.length === 1 && recipe.raw_text) {
      const li = document.createElement('li');
      li.className = 'rounded-2xl p-5 text-sm text-gray-300 leading-relaxed whitespace-pre-line';
      li.style.background = '#1A1A1A';
      li.style.border = '1px solid #333';
      li.textContent = recipe.raw_text;
      oldStepsEl.appendChild(li);
    } else {
      oldSteps.forEach((step, idx) => {
        const li = document.createElement('li');
        li.className = 'flex gap-4 items-start fade-in';
        li.style.animationDelay = `${idx * 0.05}s`;

        const stepNum = typeof step === 'object' ? step.step_number : idx + 1;
        const stepDesc = typeof step === 'object' ? step.description : step;

        li.innerHTML = `
          <div class="step-number flex-shrink-0 mt-0.5">${stepNum}</div>
          <div class="rounded-2xl p-4 flex-1 text-sm text-gray-300 leading-relaxed" style="background: #1A1A1A; border: 1px solid #333;">${escapeHtml(stepDesc)}</div>
        `;
        oldStepsEl.appendChild(li);
      });
    }
  }

  // Püf Noktaları
  const pufNoktalariSection = document.getElementById('puf-noktalari-section');
  const pufNoktalari = recipe.puf_noktalari || [];
  if (pufNoktalariSection) {
    pufNoktalariSection.classList.toggle('hidden', pufNoktalari.length === 0);
    renderList('result-puf-noktalari', pufNoktalari, (tip) =>
      `<li class="flex items-start gap-2.5 text-sm text-gray-300"><span class="text-brand-orange mt-1">💡</span><span class="flex-1">${escapeHtml(tip)}</span></li>`
    );
  }

  // Eski İpuçları
  const tipsSection = document.getElementById('tips-section');
  const tips = recipe.tips || [];
  if (tipsSection) {
    tipsSection.classList.toggle('hidden', pufNoktalari.length > 0 || tips.length === 0);
    renderList('result-tips', tips, (tip) =>
      `<li class="flex items-start gap-2 text-sm text-gray-300"><span class="text-brand-orange mt-0.5">•</span><span>${escapeHtml(tip)}</span></li>`
    );
  }

  // Sunum Önerisi
  const sunumSection = document.getElementById('sunum-section');
  const sunumOnerisi = recipe.sunum_onerisi || '';
  if (sunumSection) {
    if (sunumOnerisi) {
      sunumSection.classList.remove('hidden');
      const sunumTextEl = document.getElementById('result-sunum-onerisi');
      if (sunumTextEl) sunumTextEl.textContent = sunumOnerisi;
    } else {
      sunumSection.classList.add('hidden');
    }
  }

  // Besin Değerleri
  const nutritionCard = document.getElementById('nutrition-card');
  const nutritionGrid = document.getElementById('nutrition-grid');
  const nutrition = recipe.nutrition;
  if (nutritionCard && nutritionGrid && nutrition) {
    const hasData = nutrition.calories || nutrition.protein || nutrition.carbs || nutrition.fat;
    nutritionCard.classList.toggle('hidden', !hasData);
    if (hasData) {
      nutritionGrid.innerHTML = [
        { label: '🔥 Kalori', value: nutrition.calories },
        { label: '💪 Protein', value: nutrition.protein },
        { label: '🌾 Karbonhidrat', value: nutrition.carbs },
        { label: '🫒 Yağ', value: nutrition.fat },
      ]
        .filter((n) => n.value)
        .map(
          (n) => `
          <div class="flex justify-between items-center text-xs py-1.5 border-b border-gray-800">
            <span class="text-gray-400">${n.label}</span>
            <span class="text-white font-medium">${n.value}</span>
          </div>`
        )
        .join('');
    }
  }

  // Favori mesajını gizle
  const favMsg = document.getElementById('favorite-success-msg');
  if (favMsg) favMsg.classList.add('hidden');

  // Formu gizle, tarifi göster
  const formModeTabs = document.getElementById('form-mode-tabs');
  const ingredientsFields = document.getElementById('ingredients-mode-fields');
  const directFields = document.getElementById('direct-mode-fields');
  const generateBtn = document.getElementById('generate-btn');
  const formErrorEl = document.getElementById('form-error');
  if (formModeTabs) formModeTabs.classList.add('hidden');
  if (ingredientsFields) ingredientsFields.classList.add('hidden');
  if (directFields) directFields.classList.add('hidden');
  if (generateBtn) generateBtn.classList.add('hidden');
  if (formErrorEl) formErrorEl.classList.add('hidden');

  resultSection.classList.remove('hidden');
  setTimeout(() => {
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

// ════════════════════════════════════════════════════════
// HATA GÖSTERİMİ
// ════════════════════════════════════════════════════════

function showApiKeyWarning() {
  const resultSection = document.getElementById('recipe-result');
  const apiKeyWarning = document.getElementById('api-key-warning');
  const successCard = document.getElementById('recipe-success-card');
  const errorCard = document.getElementById('recipe-error-card');

  if (successCard) successCard.classList.add('hidden');
  if (errorCard) errorCard.classList.add('hidden');
  if (apiKeyWarning) apiKeyWarning.classList.remove('hidden');
  if (resultSection) resultSection.classList.remove('hidden');

  const formModeTabs = document.getElementById('form-mode-tabs');
  const ingredientsFields = document.getElementById('ingredients-mode-fields');
  const directFields = document.getElementById('direct-mode-fields');
  const generateBtnEl = document.getElementById('generate-btn');
  if (formModeTabs) formModeTabs.classList.add('hidden');
  if (ingredientsFields) ingredientsFields.classList.add('hidden');
  if (directFields) directFields.classList.add('hidden');
  if (generateBtnEl) generateBtnEl.classList.add('hidden');

  setTimeout(() => resultSection?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

function showRecipeError(message) {
  const resultSection = document.getElementById('recipe-result');
  const apiKeyWarning = document.getElementById('api-key-warning');
  const successCard = document.getElementById('recipe-success-card');
  const errorCard = document.getElementById('recipe-error-card');
  const errorMsg = document.getElementById('recipe-error-message');

  if (successCard) successCard.classList.add('hidden');
  if (apiKeyWarning) apiKeyWarning.classList.add('hidden');
  if (errorCard) errorCard.classList.remove('hidden');
  if (resultSection) resultSection.classList.remove('hidden');
  if (errorMsg) errorMsg.textContent = message;

  const formModeTabs = document.getElementById('form-mode-tabs');
  const ingredientsFields = document.getElementById('ingredients-mode-fields');
  const directFields = document.getElementById('direct-mode-fields');
  const generateBtnEl = document.getElementById('generate-btn');
  if (formModeTabs) formModeTabs.classList.add('hidden');
  if (ingredientsFields) ingredientsFields.classList.add('hidden');
  if (directFields) directFields.classList.add('hidden');
  if (generateBtnEl) generateBtnEl.classList.add('hidden');

  setTimeout(() => resultSection?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// ════════════════════════════════════════════════════════
// FAVORİLERİ KAYDETME
// ════════════════════════════════════════════════════════

async function saveFavorite() {
  if (!AppState.currentRecipe || AppState.isSavedFavorite) return;

  const token = localStorage.getItem('token');
  if (!token) {
    alert('Tariflerinizi favorilere eklemek için lütfen giriş yapın veya kayıt olun.');
    const isSubDir = window.location.pathname.includes('/mutfak/');
    window.location.href = isSubDir ? '../auth.html' : './auth.html';
    return;
  }

  let recipe;
  let recipeType = AppState.activeRecipeType;

  if (AppState.currentRecipe.is_direct_recipe) {
    recipe = AppState.currentRecipe.recipe;
    recipeType = 'direkt';
  } else {
    recipe = AppState.currentRecipe[recipeType];
  }

  if (!recipe) return;

  try {
    const body = {
      title: recipe.title || 'Merve Şef Tarif Önerisi',
      cuisine: (AppState.currentRecipe && AppState.currentRecipe.cuisine) || AppState.selectedCuisine || 'Dünya Mutfağı',
      ingredients: recipe.ingredients_used
        ? recipe.ingredients_used.join(', ')
        : (recipe.malzemeler_detay ? recipe.malzemeler_detay.join(', ') : ''),
      recipe_text: formatRecipeAsText(recipe),
      servings: recipe.servings,
      prep_time: recipe.prep_time,
      cook_time: recipe.cook_time,
      difficulty: recipe.difficulty,
      recipe_type: recipeType,
    };

    const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.FAVORITES}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (response.ok && data.success) {
      AppState.isSavedFavorite = true;

      const favBtn = document.getElementById('favorite-btn');
      if (favBtn) {
        favBtn.style.color = '#ef4444';
        favBtn.title = 'Favorilere Eklendi ✓';
        const span = favBtn.querySelector('span');
        if (span) span.textContent = 'Defterimde ✓';
      }

      const favMsg = document.getElementById('favorite-success-msg');
      if (favMsg) {
        favMsg.textContent = data.already_exists
          ? '✅ Bu tarif zaten favorilerinizde!'
          : '❤️ Tarif favorilerinize eklendi!';
        favMsg.classList.remove('hidden');
        setTimeout(() => favMsg.classList.add('hidden'), 3000);
      }
    }
  } catch (err) {
    console.error('Favori kaydedilemedi:', err);
  }
}

function formatRecipeAsText(recipe) {
  const lines = [];
  if (recipe.title) lines.push(`# ${recipe.title}`);
  if (recipe.description) lines.push(`\n${recipe.description}`);

  const malzemeler = recipe.malzemeler_detay || recipe.ingredients_used || [];
  if (malzemeler.length > 0) {
    lines.push('\n## Malzemeler');
    malzemeler.forEach((ing) => lines.push(`• ${ing}`));
  }

  const adimlar = recipe.hazirlanis_adimlari || recipe.steps || [];
  if (adimlar.length > 0) {
    lines.push('\n## Hazırlanış Adımları');
    adimlar.forEach((step, i) => {
      const desc = typeof step === 'object' ? step.description : step;
      lines.push(`${i + 1}. ${desc}`);
    });
  }

  const pufNoktalari = recipe.puf_noktalari || recipe.tips || [];
  if (pufNoktalari.length > 0) {
    lines.push('\n## Merve Şef\'ten Püf Noktaları');
    pufNoktalari.forEach((tip) => lines.push(`💡 ${tip}`));
  }

  const sunum = recipe.sunum_onerisi || '';
  if (sunum) {
    lines.push(`\n## Sunum Önerisi\n🍽️ ${sunum}`);
  }

  return lines.join('\n');
}

// ════════════════════════════════════════════════════════
// PANO KOPYALAMA
// ════════════════════════════════════════════════════════

function copyRecipeToClipboard() {
  if (!AppState.currentRecipe) return;

  let recipe;
  if (AppState.currentRecipe.is_direct_recipe) {
    recipe = AppState.currentRecipe.recipe;
  } else {
    recipe = AppState.currentRecipe[AppState.activeRecipeType];
  }

  if (!recipe) return;

  const text = formatRecipeAsText(recipe);
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.querySelector('button[onclick="copyRecipeToClipboard()"]');
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '✅';
      setTimeout(() => { btn.innerHTML = orig; }, 2000);
    }
  }).catch(() => {
    console.warn('Panoya kopyalanamadı.');
  });
}

// ════════════════════════════════════════════════════════
// PORSİYON AYARLAMA
// ════════════════════════════════════════════════════════

function adjustServings(delta) {
  if (!AppState.currentRecipe) return;

  let recipe;
  if (AppState.currentRecipe.is_direct_recipe) {
    recipe = AppState.currentRecipe.recipe;
  } else {
    recipe = AppState.currentRecipe[AppState.activeRecipeType];
  }
  if (!recipe) return;

  const next = Math.max(1, AppState.currentServings + delta);
  if (next === AppState.currentServings) return;

  AppState.currentServings = next;
  setTextById('result-servings', next);

  updateIngredientsList(recipe);
}

// ════════════════════════════════════════════════════════
// FORM SIFIRLAMA
// ════════════════════════════════════════════════════════

function resetForm() {
  AppState.ingredients = [];
  AppState.selectedCuisine = null;
  AppState.currentRecipe = null;
  AppState.isSavedFavorite = false;
  AppState.activeRecipeType = 'pratik';
  AppState.baseServings = 4;
  AppState.currentServings = 4;

  renderTags();

  document.querySelectorAll('.cuisine-card').forEach((card) => {
    card.classList.remove('selected');
    card.setAttribute('aria-pressed', 'false');
  });

  const ingredientInput = document.getElementById('ingredient-input');
  if (ingredientInput) ingredientInput.value = '';

  const directInput = document.getElementById('direct-recipe-input');
  if (directInput) directInput.value = '';

  // Formu yeniden göster
  const formModeTabs = document.getElementById('form-mode-tabs');
  const generateBtnEl = document.getElementById('generate-btn');
  if (formModeTabs) formModeTabs.classList.remove('hidden');
  if (generateBtnEl) generateBtnEl.classList.remove('hidden');

  switchFormMode('ingredients');

  const resultSection = document.getElementById('recipe-result');
  if (resultSection) resultSection.classList.add('hidden');

  // Sonuç sekmelerini sıfırla
  const tabsContainer = document.getElementById('recipe-tabs-container');
  if (tabsContainer) tabsContainer.classList.remove('hidden');

  hideError();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ════════════════════════════════════════════════════════
// YAZDIR
// ════════════════════════════════════════════════════════

function printRecipe() {
  window.print();
}

// ════════════════════════════════════════════════════════
// İLETİŞİM FORMU
// ════════════════════════════════════════════════════════

function handleContactSubmit(event) {
  event.preventDefault();

  const submitBtn = document.getElementById('contact-submit-btn');
  const successMsg = document.getElementById('contact-success');

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = '⏳ Gönderiliyor...';
  }

  setTimeout(() => {
    if (submitBtn) {
      submitBtn.textContent = '✅ Gönderildi!';
      submitBtn.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
    }
    if (successMsg) successMsg.classList.remove('hidden');

    setTimeout(() => {
      const form = document.getElementById('contact-form');
      if (form) form.reset();
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = '✉️ Mesajı Gönder';
        submitBtn.style.background = '';
      }
      if (successMsg) successMsg.classList.add('hidden');
    }, 5000);
  }, 1500);
}

// ════════════════════════════════════════════════════════
// YARDIMCI FONKSİYONLAR
// ════════════════════════════════════════════════════════

function setTextById(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text || '';
}

function renderList(containerId, items, template) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = (items || []).map(template).join('');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const href = anchor.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

function initScrollAnimations() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px',
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.card-hover, section > div > *').forEach((el) => {
    if (el.style.opacity === '') {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
      observer.observe(el);
    }
  });
}

async function checkBackendHealth() {
  try {
    const resp = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.HEALTH}`, {
      signal: AbortSignal.timeout(3000),
    });
    if (resp.ok) {
      const data = await resp.json();
      if (!data.api_key_configured) {
        console.warn('⚠️ GEMINI_API_KEY yapilandirilmamis.');
      }
    }
  } catch {
    console.warn('⚠️ Backend\'e baglanilamiyor.');
  }
}

// ════════════════════════════════════════════════════════
// UYGULAMA BAŞLATICI
// ════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initIngredientInput();
  initDirectInput();
  initSmoothScroll();

  AppState.searchMode = 'ingredients';

  checkBackendHealth();

  setTimeout(initScrollAnimations, 100);
});
