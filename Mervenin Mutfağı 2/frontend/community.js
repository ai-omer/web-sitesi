/**
 * community.js — Mervece Topluluk Paneli
 * Her sekmeye (mutfak, vlog, elisi) özgü bağımsız forum/yorum paneli.
 *
 * Kullanım: <script src="...community.js"></script>
 *           Her sayfanın HTML'indeki initCommunityPanel() çağrısı ile başlatılır.
 *
 * initCommunityPanel({
 *   section: 'mutfak',           // 'mutfak' | 'vlog' | 'elisi'
 *   containerId: 'community-panel',
 *   accentColor: '#F15A24',
 *   accentRgb: '241,90,36',
 *   bgColor: '#1A1A1A',
 *   cardBg: '#222222',
 *   borderColor: 'rgba(241,90,36,0.25)',
 *   emoji: '🍳',
 *   label: 'Mutfak',
 *   apiBase: 'http://localhost:8000',
 * })
 */

(function () {
  'use strict';

  /* ───────────────────────────────────────────
   * Yardımcı: Tarih formatlama
   * ─────────────────────────────────────────── */
  function formatDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleDateString('tr-TR', {
      day: '2-digit', month: 'long', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  /* ───────────────────────────────────────────
   * Yardımcı: Toast bildirimi
   * ─────────────────────────────────────────── */
  function showToast(msg, type, cfg) {
    const old = document.getElementById('comm-toast-' + cfg.section);
    if (old) old.remove();

    const t = document.createElement('div');
    t.id = 'comm-toast-' + cfg.section;
    const isSuccess = type === 'success';
    t.style.cssText = `
      position:fixed; bottom:28px; left:50%; transform:translateX(-50%);
      z-index:99999; padding:14px 28px; border-radius:14px; font-size:0.9rem;
      font-weight:600; font-family:'Inter',sans-serif; letter-spacing:0.01em;
      color:#fff; max-width:90vw; text-align:center; pointer-events:none;
      background:${isSuccess ? 'rgba(34,197,94,0.9)' : 'rgba(239,68,68,0.9)'};
      border:1px solid ${isSuccess ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)'};
      box-shadow:0 8px 32px rgba(0,0,0,0.4);
      animation:commFadeInUp 0.35s ease-out forwards;
    `;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => { t.style.animation = 'commFadeOut 0.4s ease forwards'; setTimeout(() => t.remove(), 400); }, 3200);
  }

  /* ───────────────────────────────────────────
   * Gönderi kartı oluştur
   * ─────────────────────────────────────────── */
  function buildPostCard(post, cfg) {
    const card = document.createElement('article');
    card.className = 'comm-post-card';
    card.style.cssText = `
      background:${cfg.cardBg}; border:1px solid ${cfg.borderColor};
      border-radius:16px; padding:20px; display:flex; flex-direction:column;
      gap:14px; animation:commFadeInUp 0.45s ease-out forwards;
      transition:border-color 0.25s, box-shadow 0.25s;
    `;
    card.onmouseenter = () => {
      card.style.borderColor = cfg.accentColor;
      card.style.boxShadow = `0 4px 24px rgba(${cfg.accentRgb},0.18)`;
    };
    card.onmouseleave = () => {
      card.style.borderColor = cfg.borderColor;
      card.style.boxShadow = 'none';
    };

    // Avatar + Kullanıcı adı + Tarih
    const header = document.createElement('div');
    header.style.cssText = 'display:flex; align-items:center; gap:12px;';

    const avatar = document.createElement('div');
    avatar.style.cssText = `
      width:40px; height:40px; border-radius:50%; flex-shrink:0;
      background:linear-gradient(135deg, ${cfg.accentColor}, ${cfg.accentColor}99);
      display:flex; align-items:center; justify-content:center;
      font-size:1.1rem; font-weight:700; color:#fff;
      box-shadow:0 2px 8px rgba(${cfg.accentRgb},0.35);
    `;
    avatar.textContent = (post.username.charAt(0) || '?').toUpperCase();

    const meta = document.createElement('div');
    meta.style.cssText = 'flex:1; min-width:0;';
    const nameEl = document.createElement('div');
    nameEl.style.cssText = `font-weight:700; font-size:0.95rem; color:#F5F5F5; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;`;
    nameEl.textContent = post.username;
    const dateEl = document.createElement('div');
    dateEl.style.cssText = 'font-size:0.75rem; color:rgba(255,255,255,0.4); margin-top:2px;';
    dateEl.textContent = formatDate(post.created_at);
    meta.appendChild(nameEl);
    meta.appendChild(dateEl);

    const sectionBadge = document.createElement('span');
    sectionBadge.style.cssText = `
      font-size:0.7rem; font-weight:600; padding:3px 10px; border-radius:99px;
      background:rgba(${cfg.accentRgb},0.15); border:1px solid rgba(${cfg.accentRgb},0.3);
      color:${cfg.accentColor}; white-space:nowrap;
    `;
    sectionBadge.textContent = cfg.emoji + ' ' + cfg.label;

    header.appendChild(avatar);
    header.appendChild(meta);
    header.appendChild(sectionBadge);

    // Yorum metni
    const text = document.createElement('p');
    text.style.cssText = 'color:rgba(245,245,245,0.85); font-size:0.9rem; line-height:1.65; margin:0; word-break:break-word;';
    text.textContent = post.content;

    card.appendChild(header);
    card.appendChild(text);

    // Görsel
    if (post.image_url) {
      const imgWrap = document.createElement('div');
      imgWrap.style.cssText = `border-radius:12px; overflow:hidden; border:1px solid ${cfg.borderColor};`;
      const img = document.createElement('img');
      img.src = post.image_url;
      img.alt = `${post.username} tarafından paylaşılan görsel`;
      img.style.cssText = 'width:100%; max-height:320px; object-fit:cover; display:block;';
      img.onerror = () => imgWrap.remove();
      imgWrap.appendChild(img);
      card.appendChild(imgWrap);
    }

    return card;
  }

  /* ───────────────────────────────────────────
   * Ana Fonksiyon
   * ─────────────────────────────────────────── */
  window.initCommunityPanel = function (cfg) {
    // Default değerler
    cfg = Object.assign({
      section: 'mutfak',
      containerId: 'community-panel',
      accentColor: '#F15A24',
      accentRgb: '241,90,36',
      bgColor: '#1A1A1A',
      cardBg: '#222222',
      borderColor: 'rgba(241,90,36,0.25)',
      emoji: '🍳',
      label: 'Mutfak',
      apiBase: (() => {
        const origin = window.location.origin;
        if (!origin || origin.startsWith('file://')) {
          return 'http://localhost:8000';
        }
        return origin;
      })(),
    }, cfg || {});

    const container = document.getElementById(cfg.containerId);
    if (!container) { console.warn('[Community] Container bulunamadı:', cfg.containerId); return; }

    /* ─── CSS (global, tek kez eklenir) ─── */
    if (!document.getElementById('comm-global-style')) {
      const style = document.createElement('style');
      style.id = 'comm-global-style';
      style.textContent = `
        @keyframes commFadeInUp {
          from { opacity:0; transform:translateY(18px); }
          to   { opacity:1; transform:translateY(0); }
        }
        @keyframes commFadeOut {
          to { opacity:0; transform:translateY(-10px); }
        }
        @keyframes commSpin {
          to { transform:rotate(360deg); }
        }
        .comm-input:focus {
          outline:none !important;
        }
        .comm-file-btn:hover { opacity:0.85; }
        .comm-submit-btn:hover { filter:brightness(1.12); transform:translateY(-1px); box-shadow:0 8px 24px rgba(0,0,0,0.3); }
        .comm-submit-btn:active { transform:translateY(0); }
        .comm-submit-btn:disabled { opacity:0.6; cursor:not-allowed; transform:none !important; }
      `;
      document.head.appendChild(style);
    }

    /* ─── Panel HTML ─── */
    container.innerHTML = '';
    container.style.cssText = `
      background:${cfg.bgColor}; font-family:'Inter',sans-serif; color:#F5F5F5;
      padding:0;
    `;

    /* Section Başlığı */
    const sectionEl = document.createElement('section');
    sectionEl.setAttribute('aria-label', `${cfg.label} Topluluk Paneli`);
    sectionEl.style.cssText = `
      max-width:800px; margin:0 auto; padding:48px 20px 60px;
    `;

    /* Başlık bloğu */
    const headerDiv = document.createElement('div');
    headerDiv.style.cssText = 'text-align:center; margin-bottom:40px;';
    headerDiv.innerHTML = `
      <div style="display:inline-flex; align-items:center; gap:8px; padding:6px 18px; border-radius:99px;
           background:rgba(${cfg.accentRgb},0.12); border:1px solid rgba(${cfg.accentRgb},0.3);
           color:${cfg.accentColor}; font-size:0.8rem; font-weight:600; margin-bottom:16px;">
        <span style="width:7px;height:7px;border-radius:50%;background:${cfg.accentColor};display:inline-block;"></span>
        Topluluk Alanı
      </div>
      <h2 style="font-family:'Playfair Display','Cormorant Garamond','Outfit','Inter',serif; font-size:clamp(1.6rem,4vw,2.2rem);
           font-weight:900; color:#F5F5F5; margin:0 0 10px;">
        ${cfg.emoji} ${cfg.label} Topluluğu
      </h2>
      <p style="color:rgba(255,255,255,0.45); font-size:0.9rem; max-width:500px; margin:0 auto; line-height:1.6;">
        ${cfg.label} dünyasından deneyimlerinizi, fotoğraflarınızı ve ipuçlarınızı paylaşın.
      </p>
    `;

    /* Form kartı */
    const formCard = document.createElement('div');
    formCard.style.cssText = `
      background:${cfg.cardBg}; border:1px solid ${cfg.borderColor};
      border-radius:20px; padding:28px; margin-bottom:36px;
      box-shadow:0 4px 32px rgba(0,0,0,0.25);
    `;

    // Kullanıcı adı input
    const usernameInput = document.createElement('input');
    usernameInput.type = 'text';
    usernameInput.id = `comm-username-${cfg.section}`;
    usernameInput.placeholder = 'Kullanıcı adınız...';
    usernameInput.maxLength = 100;
    usernameInput.className = 'comm-input';
    usernameInput.style.cssText = `
      width:100%; box-sizing:border-box; background:${cfg.bgColor};
      border:1px solid rgba(255,255,255,0.1); border-radius:12px;
      padding:12px 16px; color:#F5F5F5; font-size:0.9rem; font-family:'Inter',sans-serif;
      margin-bottom:12px; transition:border-color 0.2s;
    `;
    usernameInput.onfocus = () => usernameInput.style.borderColor = cfg.accentColor;
    usernameInput.onblur  = () => usernameInput.style.borderColor = 'rgba(255,255,255,0.1)';

    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        usernameInput.value = user.username;
        usernameInput.readOnly = true;
        usernameInput.style.opacity = '0.7';
        usernameInput.style.cursor = 'not-allowed';
        usernameInput.title = 'Giriş yaptığınız için kullanıcı adınız kilitlenmiştir.';
      } catch (e) {
        console.error(e);
      }
    }

    // Yorum textarea
    const textarea = document.createElement('textarea');
    textarea.id = `comm-content-${cfg.section}`;
    textarea.placeholder = `${cfg.label} hakkında paylaşmak istediğiniz bir şey var mı? 💬`;
    textarea.maxLength = 2000;
    textarea.rows = 4;
    textarea.className = 'comm-input';
    textarea.style.cssText = `
      width:100%; box-sizing:border-box; background:${cfg.bgColor};
      border:1px solid rgba(255,255,255,0.1); border-radius:12px;
      padding:12px 16px; color:#F5F5F5; font-size:0.9rem; font-family:'Inter',sans-serif;
      resize:vertical; margin-bottom:8px; line-height:1.6; transition:border-color 0.2s;
    `;
    textarea.onfocus = () => textarea.style.borderColor = cfg.accentColor;
    textarea.onblur  = () => textarea.style.borderColor = 'rgba(255,255,255,0.1)';

    // Karakter sayacı
    const charCount = document.createElement('div');
    charCount.style.cssText = 'text-align:right; font-size:0.72rem; color:rgba(255,255,255,0.3); margin-bottom:14px;';
    charCount.textContent = '0 / 2000';
    textarea.addEventListener('input', () => {
      charCount.textContent = `${textarea.value.length} / 2000`;
      charCount.style.color = textarea.value.length > 1800 ? '#FBBF24' : 'rgba(255,255,255,0.3)';
    });

    // Alt satır: dosya yükleme + gönder butonu
    const bottomRow = document.createElement('div');
    bottomRow.style.cssText = 'display:flex; align-items:center; gap:12px; flex-wrap:wrap;';

    // Görsel yükleme input (gizli)
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.id = `comm-image-${cfg.section}`;
    fileInput.accept = 'image/jpeg,image/png,image/gif,image/webp';
    fileInput.style.display = 'none';

    // Dosya seç butonu
    const fileBtn = document.createElement('label');
    fileBtn.htmlFor = `comm-image-${cfg.section}`;
    fileBtn.className = 'comm-file-btn';
    fileBtn.style.cssText = `
      display:inline-flex; align-items:center; gap:7px;
      padding:10px 18px; border-radius:12px; cursor:pointer;
      background:rgba(${cfg.accentRgb},0.1); border:1px solid rgba(${cfg.accentRgb},0.3);
      color:${cfg.accentColor}; font-size:0.82rem; font-weight:600;
      transition:opacity 0.2s; white-space:nowrap;
    `;
    fileBtn.innerHTML = '📷 Görsel Ekle';

    // Dosya adı göstergesi
    const fileLabel = document.createElement('span');
    fileLabel.style.cssText = 'font-size:0.78rem; color:rgba(255,255,255,0.4); flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;';
    fileLabel.textContent = 'Görsel seçilmedi';

    // Görsel önizleme
    const previewWrap = document.createElement('div');
    previewWrap.style.cssText = 'display:none; margin-top:12px; border-radius:12px; overflow:hidden; border:1px solid rgba(255,255,255,0.1); position:relative;';
    const previewImg = document.createElement('img');
    previewImg.alt = 'Görsel önizleme';
    previewImg.style.cssText = 'width:100%; max-height:240px; object-fit:cover; display:block;';
    const removeImgBtn = document.createElement('button');
    removeImgBtn.textContent = '✕ Görseli Kaldır';
    removeImgBtn.style.cssText = `
      position:absolute; top:8px; right:8px; background:rgba(0,0,0,0.65);
      border:none; color:#fff; padding:5px 12px; border-radius:8px; cursor:pointer;
      font-size:0.75rem; font-weight:600;
    `;
    removeImgBtn.onclick = () => {
      fileInput.value = '';
      previewWrap.style.display = 'none';
      fileLabel.textContent = 'Görsel seçilmedi';
      fileLabel.style.color = 'rgba(255,255,255,0.4)';
    };
    previewWrap.appendChild(previewImg);
    previewWrap.appendChild(removeImgBtn);

    fileInput.addEventListener('change', () => {
      const file = fileInput.files[0];
      if (!file) { fileLabel.textContent = 'Görsel seçilmedi'; previewWrap.style.display = 'none'; return; }
      if (file.size > 5 * 1024 * 1024) {
        showToast('⚠️ Görsel 5 MB\'dan küçük olmalıdır.', 'error', cfg);
        fileInput.value = '';
        return;
      }
      fileLabel.textContent = file.name;
      fileLabel.style.color = cfg.accentColor;
      const reader = new FileReader();
      reader.onload = (e) => { previewImg.src = e.target.result; previewWrap.style.display = 'block'; };
      reader.readAsDataURL(file);
    });

    // Gönder butonu
    const submitBtn = document.createElement('button');
    submitBtn.id = `comm-submit-${cfg.section}`;
    submitBtn.type = 'button';
    submitBtn.className = 'comm-submit-btn';
    submitBtn.style.cssText = `
      margin-left:auto; padding:10px 26px; border-radius:12px; border:none; cursor:pointer;
      background:linear-gradient(135deg, ${cfg.accentColor}, ${cfg.accentColor}CC);
      color:#fff; font-size:0.88rem; font-weight:700; font-family:'Inter',sans-serif;
      transition:all 0.2s;
    `;
    submitBtn.textContent = '🚀 Paylaş';

    bottomRow.appendChild(fileInput);
    bottomRow.appendChild(fileBtn);
    bottomRow.appendChild(fileLabel);
    bottomRow.appendChild(submitBtn);

    formCard.appendChild(usernameInput);
    formCard.appendChild(textarea);
    formCard.appendChild(charCount);
    formCard.appendChild(previewWrap);
    formCard.appendChild(bottomRow);

    /* Gönderiler listesi */
    const listHeader = document.createElement('div');
    listHeader.style.cssText = 'display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;';
    listHeader.innerHTML = `
      <h3 style="font-size:1rem; font-weight:700; color:#F5F5F5; margin:0;">
        💬 ${cfg.label} Gönderileri
      </h3>
      <span id="comm-count-${cfg.section}" style="font-size:0.78rem; color:rgba(255,255,255,0.4);"></span>
    `;

    const postsList = document.createElement('div');
    postsList.id = `comm-posts-${cfg.section}`;
    postsList.style.cssText = 'display:flex; flex-direction:column; gap:16px;';

    const emptyState = document.createElement('div');
    emptyState.id = `comm-empty-${cfg.section}`;
    emptyState.style.cssText = `
      text-align:center; padding:48px 24px;
      border:2px dashed rgba(${cfg.accentRgb},0.2); border-radius:16px;
      color:rgba(255,255,255,0.35); font-size:0.9rem; display:none;
    `;
    emptyState.innerHTML = `<div style="font-size:2.5rem; margin-bottom:12px;">${cfg.emoji}</div>
      <p style="margin:0;">Henüz gönderi yok.<br/>İlk paylaşımı sen yap!</p>`;

    const errorState = document.createElement('div');
    errorState.id = `comm-error-${cfg.section}`;
    errorState.style.cssText = `
      text-align:center; padding:32px 24px;
      background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2);
      border-radius:16px; color:rgba(255,255,255,0.5); font-size:0.85rem; display:none;
    `;
    errorState.innerHTML = '⚠️ Gönderiler yüklenemedi. Backend\'in çalıştığından emin olun.';

    /* Montaj */
    sectionEl.appendChild(headerDiv);
    sectionEl.appendChild(formCard);
    sectionEl.appendChild(listHeader);
    sectionEl.appendChild(postsList);
    sectionEl.appendChild(emptyState);
    sectionEl.appendChild(errorState);
    container.appendChild(sectionEl);

    /* ─── Gönderileri yükle ─── */
    async function loadPosts() {
      postsList.style.opacity = '0.5';
      try {
        const res = await fetch(`${cfg.apiBase}/api/posts?section=${cfg.section}`);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();

        postsList.innerHTML = '';
        postsList.style.opacity = '1';

        const countEl = document.getElementById(`comm-count-${cfg.section}`);
        if (countEl) countEl.textContent = `${data.count || 0} gönderi`;

        if (!data.posts || data.posts.length === 0) {
          emptyState.style.display = 'block';
          errorState.style.display = 'none';
        } else {
          emptyState.style.display = 'none';
          errorState.style.display = 'none';
          data.posts.forEach(post => {
            postsList.appendChild(buildPostCard(post, cfg));
          });
        }
      } catch (err) {
        postsList.style.opacity = '1';
        emptyState.style.display = 'none';
        errorState.style.display = 'block';
        console.warn('[Community] Gönderiler yüklenemedi:', err);
      }
    }

    /* ─── Gönderi paylaş ─── */
    submitBtn.addEventListener('click', async () => {
      const username = usernameInput.value.trim();
      const content = textarea.value.trim();
      const file = fileInput.files[0] || null;

      if (!username) {
        usernameInput.style.borderColor = '#EF4444';
        usernameInput.focus();
        showToast('⚠️ Kullanıcı adı boş olamaz.', 'error', cfg);
        return;
      }
      if (!content) {
        textarea.style.borderColor = '#EF4444';
        textarea.focus();
        showToast('⚠️ Yorum alanı boş olamaz.', 'error', cfg);
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = '⏳ Paylaşılıyor...';

      try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('content', content);
        formData.append('section', cfg.section);
        if (file) formData.append('image', file);

        const headers = {};
        const userToken = localStorage.getItem('token');
        if (userToken) {
          headers['Authorization'] = `Bearer ${userToken}`;
        }

        const res = await fetch(`${cfg.apiBase}/api/posts`, {
          method: 'POST',
          headers: headers,
          body: formData,
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.detail || data.message || 'Sunucu hatası');
        }

        // Formu sıfırla
        textarea.value = '';
        fileInput.value = '';
        previewWrap.style.display = 'none';
        fileLabel.textContent = 'Görsel seçilmedi';
        fileLabel.style.color = 'rgba(255,255,255,0.4)';
        charCount.textContent = '0 / 2000';
        usernameInput.style.borderColor = 'rgba(255,255,255,0.1)';
        textarea.style.borderColor = 'rgba(255,255,255,0.1)';

        showToast('🎉 Gönderiniz paylaşıldı!', 'success', cfg);

        // Yeni gönderiyi listenin başına ekle
        emptyState.style.display = 'none';
        const newCard = buildPostCard(data.post, cfg);
        newCard.style.opacity = '0';
        newCard.style.transform = 'translateY(-16px)';
        postsList.insertBefore(newCard, postsList.firstChild);
        requestAnimationFrame(() => {
          newCard.style.transition = 'opacity 0.4s, transform 0.4s';
          newCard.style.opacity = '1';
          newCard.style.transform = 'translateY(0)';
        });

        const countEl = document.getElementById(`comm-count-${cfg.section}`);
        if (countEl) {
          const cur = parseInt(countEl.textContent) || 0;
          countEl.textContent = `${cur + 1} gönderi`;
        }

      } catch (err) {
        console.error('[Community] Gönderi hatası:', err);
        showToast('❌ ' + (err.message || 'Gönderi paylaşılamadı.'), 'error', cfg);
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '🚀 Paylaş';
      }
    });

    /* İlk yükleme */
    loadPosts();
  };

})();
