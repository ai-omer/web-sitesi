/**
 * admin.js - Mervece Portal Yönetim Paneli Kontrolcüsü
 * Sadece admin rolüne sahip kullanıcıların veri yönetimi ve moderasyon işlemlerini yönetir.
 */

(function () {
  'use strict';

  // Dinamik API host tespiti (Deployment / Canlı ortam uyumluluğu ile)
  const getApiBaseUrl = () => {
    const origin = window.location.origin;
    if (!origin || origin.startsWith('file://')) {
      return 'http://localhost:8000';
    }
    // Eğer frontend ve backend aynı porttaysa veya üretim ortamındaysa
    // doğrudan window.location.origin değerini kullan.
    return origin;
  };

  const API_BASE = getApiBaseUrl();
  let currentTab = 'summary';
  let allPosts = [];
  let allUsers = [];
  let activeFilter = 'all';

  // --- Sayfa Yüklendiğinde Yetki Kontrolü ---
  window.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');

    if (!token || !userStr) {
      alert("Yetkisiz Erişim! Lütfen önce giriş yapın.");
      window.location.href = './auth.html';
      return;
    }

    try {
      const user = JSON.parse(userStr);
      if (user.role !== 'admin') {
        alert("Yetkisiz Erişim! Bu sayfaya sadece yöneticiler erişebilir.");
        window.location.href = './index.html';
        return;
      }
      
      // Kullanıcı adını başlığa yaz
      const adminNameEl = document.getElementById('admin-username');
      if (adminNameEl) adminNameEl.textContent = user.username;

    } catch (e) {
      console.error("Yetki kontrolü hatası:", e);
      window.location.href = './index.html';
      return;
    }

    // İlk yüklemede Özet Tabını başlat
    switchTab('summary');
  });

  // --- Toast Bildirim Sistemi ---
  function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.textContent = msg;
    if (type === 'success') {
      toast.style.background = 'rgba(16, 185, 129, 0.95)';
      toast.style.border = '1px solid rgba(16, 185, 129, 0.5)';
      toast.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.3)';
    } else {
      toast.style.background = 'rgba(239, 68, 68, 0.95)';
      toast.style.border = '1px solid rgba(239, 68, 68, 0.5)';
      toast.style.boxShadow = '0 0 20px rgba(239, 68, 68, 0.3)';
    }

    toast.classList.remove('opacity-0', 'translate-y-2');
    toast.classList.add('opacity-100', 'translate-y-0');

    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-2');
      toast.classList.remove('opacity-100', 'translate-y-0');
    }, 3000);
  }

  // --- Tarih Formatlama ---
  function formatDate(isoString) {
    if (!isoString) return '-';
    const d = new Date(isoString);
    return d.toLocaleDateString('tr-TR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // --- Sekme Değiştirme Mantığı ---
  window.switchTab = function (tabName) {
    currentTab = tabName;

    // Buton aktiflik sınıflarını güncelle
    const tabs = ['summary', 'users', 'posts'];
    tabs.forEach(t => {
      const btn = document.getElementById(`tab-btn-${t}`);
      const sec = document.getElementById(`section-${t}`);
      if (btn) {
        if (t === tabName) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      }
      if (sec) {
        if (t === tabName) {
          sec.classList.remove('hidden');
        } else {
          sec.classList.add('hidden');
        }
      }
    });

    // Sekmeye göre veri yükle
    if (tabName === 'summary') {
      loadSummaryData();
    } else if (tabName === 'users') {
      loadUsersData();
    } else if (tabName === 'posts') {
      loadPostsData();
    }
  };

  // --- 📊 1. Sekme: Özet Verileri ---
  async function loadSummaryData() {
    showLoader(true);
    const token = localStorage.getItem('token');

    try {
      const res = await fetch(`${API_BASE}/api/admin/summary`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Özet verileri alınamadı.");
      
      const data = await res.json();
      if (data.success && data.summary) {
        const s = data.summary;
        // Kart Değerlerini Doldur
        document.getElementById('summary-total-users').textContent = s.total_users;
        document.getElementById('summary-total-posts').textContent = s.total_posts;
        document.getElementById('summary-total-favorites').textContent = s.total_favorites;
        document.getElementById('summary-total-recipes').textContent = s.total_recipe_history;

        // Sekmelerdeki Yorum Sayıları
        document.getElementById('summary-count-mutfak').textContent = s.posts_mutfak;
        document.getElementById('summary-count-vlog').textContent = s.posts_vlog;
        document.getElementById('summary-count-elisi').textContent = s.posts_elisi;

        // İlerleme Çubukları (Yüzdesel)
        const maxPosts = Math.max(s.posts_mutfak, s.posts_vlog, s.posts_elisi, 1);
        
        const pctMutfak = (s.posts_mutfak / maxPosts) * 100;
        const pctVlog = (s.posts_vlog / maxPosts) * 100;
        const pctElisi = (s.posts_elisi / maxPosts) * 100;

        document.getElementById('bar-mutfak').style.width = `${pctMutfak}%`;
        document.getElementById('bar-vlog').style.width = `${pctVlog}%`;
        document.getElementById('bar-elisi').style.width = `${pctElisi}%`;
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      showLoader(false);
    }
  }

  // --- 👥 2. Sekme: Kullanıcı Yönetimi ---
  async function loadUsersData() {
    showLoader(true);
    const token = localStorage.getItem('token');

    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Kullanıcı listesi yüklenemedi.");

      const data = await res.json();
      allUsers = data.users || [];
      renderUsers();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      showLoader(false);
    }
  }

  function renderUsers() {
    const tbody = document.getElementById('users-tbody');
    const wrap = document.getElementById('users-table-wrap');
    const empty = document.getElementById('users-empty');
    if (!tbody) return;

    tbody.innerHTML = '';
    const loggedInUser = JSON.parse(localStorage.getItem('user') || '{}');

    if (allUsers.length === 0) {
      wrap.classList.add('hidden');
      empty.classList.remove('hidden');
      return;
    }

    wrap.classList.remove('hidden');
    empty.classList.add('hidden');

    allUsers.forEach(u => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-white/[0.02] border-b border-white/[0.04] transition-colors';

      const isSelf = u.id === loggedInUser.id;
      const roleBadge = u.role === 'admin' 
        ? `<span class="px-2.5 py-1 text-xs font-bold rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">👑 Admin</span>`
        : `<span class="px-2.5 py-1 text-xs font-medium rounded-full bg-slate-800 text-slate-300 border border-slate-700">Kullanıcı</span>`;

      tr.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap text-xs text-gray-500 font-mono">#${u.id}</td>
        <td class="px-6 py-4 whitespace-nowrap font-semibold text-white">${u.username} ${isSelf ? '<span class="text-xs text-[#E94560] font-normal">(Siz)</span>' : ''}</td>
        <td class="px-6 py-4 whitespace-nowrap text-gray-300">${u.email}</td>
        <td class="px-6 py-4 whitespace-nowrap">${roleBadge}</td>
        <td class="px-6 py-4 whitespace-nowrap text-xs text-gray-400">${formatDate(u.created_at)}</td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-xs">
          ${isSelf 
            ? `<button disabled class="px-3.5 py-1.5 rounded-lg bg-gray-800 text-gray-500 border border-gray-700 cursor-not-allowed font-semibold">Silinemez</button>`
            : `<button onclick="deleteUser(${u.id}, '${u.username}')" class="px-3.5 py-1.5 rounded-lg bg-red-950/20 text-red-400 border border-red-900/30 hover:bg-red-600 hover:text-white transition-all font-semibold">Kullanıcıyı Sil</button>`
          }
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  window.deleteUser = async function (userId, username) {
    const confirmation = confirm(`"${username}" adlı kullanıcıyı ve bu kullanıcıya ait TÜM yorum, favori ve tarif geçmişini kalıcı olarak silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!`);
    if (!confirmation) return;

    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kullanıcı silinirken hata oluştu.");

      showToast(`"${username}" başarıyla sistemden temizlendi.`, 'success');
      loadUsersData(); // Listeyi yenile
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // --- 💬 3. Sekme: İçerik & Yorum Moderasyonu ---
  async function loadPostsData() {
    showLoader(true);
    const token = localStorage.getItem('token');

    try {
      const res = await fetch(`${API_BASE}/api/admin/posts`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Gönderiler yüklenemedi.");

      const data = await res.json();
      allPosts = data.posts || [];
      renderPosts();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      showLoader(false);
    }
  }

  window.setFilter = function (filterName) {
    activeFilter = filterName;

    // Filtre buton stillerini güncelle
    const filters = ['all', 'mutfak', 'vlog', 'elisi'];
    filters.forEach(f => {
      const btn = document.getElementById(`filter-btn-${f}`);
      if (btn) {
        if (f === filterName) {
          btn.classList.add('bg-white/10', 'text-white', 'border-white/20');
          btn.classList.remove('text-gray-400', 'border-transparent');
        } else {
          btn.classList.remove('bg-white/10', 'text-white', 'border-white/20');
          btn.classList.add('text-gray-400', 'border-transparent');
        }
      }
    });

    renderPosts();
  };

  function renderPosts() {
    const feed = document.getElementById('posts-feed');
    const empty = document.getElementById('posts-empty');
    if (!feed) return;

    feed.innerHTML = '';

    const filtered = activeFilter === 'all' 
      ? allPosts 
      : allPosts.filter(p => p.section === activeFilter);

    if (filtered.length === 0) {
      feed.classList.add('hidden');
      empty.classList.remove('hidden');
      return;
    }

    feed.classList.remove('hidden');
    empty.classList.add('hidden');

    filtered.forEach(post => {
      const card = document.createElement('div');
      card.className = 'glass p-6 rounded-2xl relative flex flex-col gap-4 group hover:border-[#E94560]/30 transition-all duration-300';

      // Bölüm badge renkleri
      let badgeStyle = '';
      let sectionName = '';
      if (post.section === 'mutfak') {
        badgeStyle = 'bg-orange-950/40 text-[#F15A24] border-[#F15A24]/30';
        sectionName = '🍳 Mutfak';
      } else if (post.section === 'vlog') {
        badgeStyle = 'bg-purple-950/40 text-[#A855F7] border-[#A855F7]/30';
        sectionName = '🎥 Vlog';
      } else {
        badgeStyle = 'bg-emerald-950/40 text-[#10B981] border-[#10B981]/30';
        sectionName = '🧶 Elişi';
      }

      card.innerHTML = `
        <!-- Üst Bilgi Satırı -->
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-base shadow bg-gradient-to-tr from-[#E94560]/80 to-purple-600/80">
            ${(post.username.charAt(0) || '?').toUpperCase()}
          </div>
          <div>
            <h4 class="font-bold text-white text-sm leading-tight">${post.username}</h4>
            <span class="text-xs text-gray-500">${formatDate(post.created_at)}</span>
          </div>
          <span class="ml-auto text-[10px] uppercase font-bold px-2 py-0.5 rounded-md border ${badgeStyle}">
            ${sectionName}
          </span>
        </div>

        <!-- Gönderi İçeriği -->
        <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">${post.content}</p>

        <!-- Yüklenen Fotoğraf (varsa) -->
        ${post.image_url ? `
          <div class="rounded-xl overflow-hidden border border-white/5 bg-black/20">
            <a href="${post.image_url}" target="_blank" title="Büyük boyutta gör">
              <img src="${post.image_url}" alt="Yorum görseli" class="w-full max-h-64 object-cover hover:scale-[1.02] transition-transform duration-300 cursor-zoom-in" onerror="this.parentElement.parentElement.remove()">
            </a>
          </div>
        ` : ''}

        <!-- Silme Aksiyon Butonu (Kırmızı, Sağ Üst) -->
        <button onclick="deletePost(${post.id})" class="absolute top-4 right-4 md:opacity-0 group-hover:opacity-100 transition-opacity duration-200 px-3 py-1.5 rounded-lg bg-red-950/50 hover:bg-red-600 text-red-400 hover:text-white border border-red-900/30 hover:border-red-500/30 text-xs font-bold shadow-lg" title="Yorumu sistemden kaldır">
          Yorumu Kaldır
        </button>
      `;
      feed.appendChild(card);
    });
  }

  window.deletePost = async function (postId) {
    const confirmation = confirm("Bu yorumu/gönderiyi kalıcı olarak silmek istediğinizden emin misiniz?");
    if (!confirmation) return;

    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE}/api/admin/posts/${postId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Yorum silinirken hata oluştu.");

      showToast("Yorum başarıyla kaldırıldı.", 'success');
      loadPostsData(); // Listeyi yenile
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // --- Genel Yükleniyor Spinner Kontrolü ---
  function showLoader(visible) {
    const loader = document.getElementById('loading');
    if (loader) {
      if (visible) {
        loader.classList.remove('hidden');
      } else {
        loader.classList.add('hidden');
      }
    }
  }

  // --- Çıkış Yapma İşlemi ---
  window.handleLogout = function () {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = './index.html';
  };

})();
