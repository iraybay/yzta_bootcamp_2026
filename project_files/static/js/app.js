// Global state and references
let currentSection = 'cari';
let currentTab = 'view';
let dashboardData = {};

// Chart instances tracker
let charts = {
    cari: null,
    kasa: null,
    stok: null,
    fatura: null
};

// Formatter Helpers
const formatCurrency = (val) => {
    return new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: 'TRY',
        minimumFractionDigits: 2
    }).format(val || 0);
};

// Document Ready
document.addEventListener('DOMContentLoaded', () => {
    // Initial clock run
    updateClock();
    setInterval(updateClock, 1000);

    // Initial data fetch and render
    refreshDashboard();

    // Theme toggle setup
    const themeBtn = document.getElementById('themeToggleBtn');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme !== 'light') {
        document.body.classList.remove('light-mode');
        document.body.classList.add('dark-mode');
        themeBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    } else {
        document.body.classList.add('light-mode');
        document.body.classList.remove('dark-mode');
        themeBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
    }

    themeBtn.addEventListener('click', toggleTheme);

    // Close Modal on overlay click
    const detailOverlay = document.getElementById('detailModal');
    detailOverlay.addEventListener('click', (e) => {
        if (e.target === detailOverlay) closeModal();
    });

    const globalOverlay = document.getElementById('globalActionModal');
    globalOverlay.addEventListener('click', (e) => {
        if (e.target === globalOverlay) closeGlobalActionModal();
    });

    // Search bar filter logic
    const searchInput = document.getElementById('searchInput');
    const suggestionsBox = document.getElementById('searchSuggestions');
    
    const commands = [
        { text: "Yeni Cari Kartı Oluştur (Cari Hesap Aç)", keywords: ["cari hesap aç", "yeni cari", "cari ekle", "cari aç", "cari kartı"], action: () => showSectionDetail('cari'), icon: "fa-solid fa-user-plus" },
        { text: "Cari Listesini Aç", keywords: ["cari listesi", "carileri gör", "cari listesini aç", "cari liste"], action: () => { location.href = '/cari-listesi'; }, icon: "fa-solid fa-users" },
        { text: "Kasa Listesini Aç", keywords: ["kasa listesi", "kasaları gör", "kasa listesini aç", "kasa kartları"], action: () => { location.href = '/kasa-listesi'; }, icon: "fa-solid fa-wallet" },
        { text: "Banka Listesini Aç", keywords: ["banka listesi", "bankaları gör", "banka listesini aç", "banka hesapları"], action: () => { location.href = '/banka-listesi'; }, icon: "fa-solid fa-building-columns" },
        { text: "Kasa & Banka İşlem Geçmişi", keywords: ["kasa hareketleri", "banka hareketleri", "kasa özet", "banka özet", "kasa banka"], action: () => { location.href = '/kasa-hareketler'; }, icon: "fa-solid fa-clock-rotate-left" },
        { text: "Yeni Stok Ürünü Ekle", keywords: ["stok ekle", "yeni ürün", "stok girişi", "ürün ekle"], action: () => showSectionDetail('stok'), icon: "fa-solid fa-box-open" },
        { text: "Yeni Fatura Düzenle", keywords: ["fatura kes", "fatura oluştur", "yeni fatura", "fatura ekle"], action: () => showSectionDetail('fatura'), icon: "fa-solid fa-file-invoice" },
        { text: "Mutabakat & Ödeme Raporu", keywords: ["mutabakat", "ödeme planı", "gelecek ödemeler", "rapor", "mutabakat raporu"], action: () => { location.href = '/mutabakat-raporu'; }, icon: "fa-solid fa-calendar-days" },
        { text: "Son İşlemler & Özet Ekranı", keywords: ["son işlemler", "cari hareketler", "özet", "hareketler"], action: () => { location.href = '/cari-hareketler'; }, icon: "fa-solid fa-clock-rotate-left" }
    ];

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        filterCards(query);
        
        if (query.length > 1) {
            const matches = commands.filter(cmd => 
                cmd.keywords.some(keyword => keyword.includes(query) || query.includes(keyword))
            );
            
            if (matches.length > 0) {
                suggestionsBox.innerHTML = matches.map((cmd, idx) => `
                    <div class="search-suggestion-item" data-idx="${idx}">
                        <i class="${cmd.icon}"></i>
                        <span>${cmd.text}</span>
                    </div>
                `).join('');
                suggestionsBox.style.display = 'block';
                
                // Add click listener
                suggestionsBox.querySelectorAll('.search-suggestion-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const idx = item.getAttribute('data-idx');
                        matches[idx].action();
                        suggestionsBox.style.display = 'none';
                        searchInput.value = '';
                    });
                });
            } else {
                suggestionsBox.style.display = 'none';
            }
        } else {
            suggestionsBox.style.display = 'none';
        }
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
            suggestionsBox.style.display = 'none';
        }
    });
});

// Update the real-time clock
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('tr-TR');
    
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const dateStr = now.toLocaleDateString('tr-TR', options);
    
    document.getElementById('currentTime').textContent = timeStr;
    document.getElementById('currentDate').textContent = dateStr;
}

// Toggle light/dark theme
function toggleTheme() {
    const body = document.body;
    const btn = document.getElementById('themeToggleBtn');
    
    if (body.classList.contains('light-mode')) {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
        localStorage.setItem('theme', 'dark');
    } else {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
        localStorage.setItem('theme', 'light');
    }

    // Refresh charts to update color styling
    initCharts();
}

// Fetch dashboard data from backend Flask API
async function refreshDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) throw new Error('API request failed');
        dashboardData = await response.json();
        
        renderDashboardData();
        initCharts();
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        Swal.fire({
            icon: 'error',
            title: 'Hata',
            text: 'Veriler sunucudan alınamadı. Lütfen backend sunucunuzun çalıştığından emin olun.',
            confirmButtonColor: '#0078d4'
        });
    }
}

// Render dynamic stats on main tiles
function renderDashboardData() {
    // 1. Cari Block
    document.getElementById('musteriSayisi').textContent = dashboardData.cari.musteri_sayisi;
    document.getElementById('tedarikciSayisi').textContent = dashboardData.cari.tedarikci_sayisi;
    document.getElementById('toplamAlacak').textContent = formatCurrency(dashboardData.cari.toplam_alacak);
    document.getElementById('toplamBorc').textContent = formatCurrency(dashboardData.cari.toplam_borc);

    // 2. Kasa ve Banka Block
    document.getElementById('toplamNakit').textContent = formatCurrency(dashboardData.kasa_banka.toplam_nakit);
    document.getElementById('kasaBakiye').textContent = formatCurrency(dashboardData.kasa_banka.kasa_bakiye);
    document.getElementById('bankaBakiye').textContent = formatCurrency(dashboardData.kasa_banka.banka_bakiye);

    // 3. Stok Block
    document.getElementById('toplamUrunCesidi').textContent = dashboardData.stok.toplam_urun_cesidi;
    document.getElementById('kritikStokSayisi').textContent = dashboardData.stok.kritik_stok_sayisi;
    
    const fillRate = dashboardData.stok.depo_doluluk_orani;
    document.getElementById('depoDolulukBar').style.width = `${fillRate}%`;
    document.getElementById('depoDolulukOran').textContent = `%${fillRate}`;

    // 4. Fatura ve İrsaliye Block
    document.getElementById('odenmemisFatura').textContent = dashboardData.fatura_irsaliye.odenmemis_fatura;
    document.getElementById('bekleyenIrsaliye').textContent = dashboardData.fatura_irsaliye.bekleyen_irsaliye;
    document.getElementById('aylikFaturaTutari').textContent = formatCurrency(dashboardData.fatura_irsaliye.aylik_fatura_tutari);
    document.getElementById('taslakFatura').textContent = dashboardData.fatura_irsaliye.taslak_fatura;

    // 5. BulutAI Insights
    renderAiInsights();

    // 6. Update inline Cari summary if open
    updateInlineCariSummaryIfOpen();
}

// Initialize or update dashboard mini-charts using Chart.js
function initCharts() {
    const isDark = document.body.classList.contains('dark-mode');
    const textColor = isDark ? '#cbd5e1' : '#64748b';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.05)';

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: { display: false },
            y: { display: false }
        }
    };

    // --- Chart 1: Cari (Alacak vs Borç Bar) ---
    if (charts.cari) charts.cari.destroy();
    const ctxCari = document.getElementById('chartCari').getContext('2d');
    charts.cari = new Chart(ctxCari, {
        type: 'bar',
        data: {
            labels: ['Toplam Alacak', 'Toplam Borç'],
            datasets: [{
                data: [dashboardData.cari.toplam_alacak, dashboardData.cari.toplam_borc],
                backgroundColor: ['#2a9d8f', '#ef4444'],
                borderRadius: 8,
                barThickness: 24
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: textColor, font: { size: 10 } }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, font: { size: 9 } }
                }
            }
        }
    });

    // --- Chart 2: Kasa & Banka (Line Chart) ---
    if (charts.kasa) charts.kasa.destroy();
    const ctxKasa = document.getElementById('chartKasa').getContext('2d');
    charts.kasa = new Chart(ctxKasa, {
        type: 'line',
        data: {
            labels: (dashboardData.kasa_banka && dashboardData.kasa_banka.monthly_chart) ? dashboardData.kasa_banka.monthly_chart.labels : ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz'],
            datasets: [
                {
                    label: 'Gelirler',
                    data: (dashboardData.kasa_banka && dashboardData.kasa_banka.monthly_chart) ? dashboardData.kasa_banka.monthly_chart.gelirler : [150000, 180000, 220000, 290000, 270000, 310000, dashboardData.kasa_banka.aylik_gelir],
                    borderColor: '#2a9d8f',
                    backgroundColor: 'rgba(42, 157, 143, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 0
                },
                {
                    label: 'Giderler',
                    data: (dashboardData.kasa_banka && dashboardData.kasa_banka.monthly_chart) ? dashboardData.kasa_banka.monthly_chart.giderler : [120000, 110000, 150000, 210000, 180000, 220000, dashboardData.kasa_banka.aylik_gider],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.05)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 0
                }
            ]
        },
        options: {
            ...commonOptions,
            plugins: { legend: { display: true, labels: { color: textColor, boxWidth: 10, font: { size: 9 } } } }
        }
    });

    // --- Chart 3: Stok (Doughnut Chart) ---
    if (charts.stok) charts.stok.destroy();
    const ctxStok = document.getElementById('chartStok').getContext('2d');
    const stokCategories = dashboardData.stok.kategoriler.map(c => c.ad);
    const stokRates = dashboardData.stok.kategoriler.map(c => c.adet);
    charts.stok = new Chart(ctxStok, {
        type: 'doughnut',
        data: {
            labels: stokCategories,
            datasets: [{
                data: stokRates,
                backgroundColor: ['#0077b6', '#2a9d8f', '#f59e0b', '#7209b7'],
                borderWidth: isDark ? 2 : 1,
                borderColor: isDark ? '#1e293b' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: { color: textColor, font: { size: 9 }, boxWidth: 8 }
                }
            }
        }
    });

    // --- Chart 4: Fatura ve İrsaliye (Horizontal Stacked Bar) ---
    if (charts.fatura) charts.fatura.destroy();
    const ctxFatura = document.getElementById('chartFatura').getContext('2d');
    charts.fatura = new Chart(ctxFatura, {
        type: 'bar',
        data: {
            labels: ['Fatura Durumları'],
            datasets: [
                {
                    label: 'Ödenmemiş',
                    data: [dashboardData.fatura_irsaliye.odenmemis_fatura],
                    backgroundColor: '#ef4444',
                    borderRadius: 4
                },
                {
                    label: 'Taslak',
                    data: [dashboardData.fatura_irsaliye.taslak_fatura],
                    backgroundColor: '#f59e0b',
                    borderRadius: 4
                },
                {
                    label: 'Toplam İşlem',
                    data: [dashboardData.fatura_irsaliye.kesilen_fatura_bu_ay],
                    backgroundColor: '#7209b7',
                    borderRadius: 4
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: textColor, font: { size: 9 }, boxWidth: 8 }
                }
            },
            scales: {
                x: { display: false, stacked: true },
                y: { display: false, stacked: true }
            }
        }
    });
}

// Show detailed page overlay modal
function showSectionDetail(section) {
    currentSection = section;
    
    const tabsContainer = document.querySelector('.modal-tabs');
    if (section === 'cari') {
        if (tabsContainer) tabsContainer.style.display = 'none';
        currentTab = 'add';
        switchModalTab('add');
    } else {
        if (tabsContainer) tabsContainer.style.display = 'flex';
        currentTab = 'view';
        switchModalTab('view');
    }
    
    // Switch overlays status
    document.getElementById('detailModal').classList.add('active');
    
    // Render properties depending on section
    setupModalUI();
}

// Close detailed page overlay modal
function closeModal() {
    document.getElementById('detailModal').classList.remove('active');
}

// Switch between View History and Add New Entry
function switchModalTab(tab) {
    currentTab = tab;
    
    // Manage active visual classes
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));
    
    const activeBtn = Array.from(tabBtns).find(btn => 
        tab === 'view' ? btn.textContent.includes('Özet') : btn.textContent.includes('Yeni')
    );
    if (activeBtn) activeBtn.classList.add('active');

    // Panes
    document.getElementById('tabPaneView').classList.remove('active');
    document.getElementById('tabPaneAdd').classList.remove('active');
    
    if (tab === 'view') {
        document.getElementById('tabPaneView').classList.add('active');
        renderModalData();
    } else {
        document.getElementById('tabPaneAdd').classList.add('active');
        generateFormFields();
    }
}

// Config Modal Icon and Title based on active section
function setupModalUI() {
    const titleEl = document.getElementById('modalTitle');
    const iconEl = document.getElementById('modalIcon');
    
    iconEl.className = 'fa-solid modal-title-icon ';
    
    if (currentSection === 'cari') {
        titleEl.textContent = 'Cari Hesap Yönetimi (Müşteri & Tedarikçi)';
        iconEl.classList.add('fa-users', 'icon-orange');
    } else if (currentSection === 'kasa') {
        titleEl.textContent = 'Kasa ve Banka Hesapları Yönetimi';
        iconEl.classList.add('fa-vault', 'icon-blue');
    } else if (currentSection === 'stok') {
        titleEl.textContent = 'Envanter & Stok Takibi';
        iconEl.classList.add('fa-box-open', 'icon-green');
    } else if (currentSection === 'fatura') {
        titleEl.textContent = 'Fatura ve İrsaliye İşlemleri';
        iconEl.classList.add('fa-file-invoice-dollar', 'icon-purple');
    }
    
    renderModalData();
}

// Render dynamic lists inside detail modals
function renderModalData() {
    const metricsGrid = document.getElementById('modalMetricsSummary');
    const tableBody = document.getElementById('modalTransactionsTable');
    
    metricsGrid.innerHTML = '';
    tableBody.innerHTML = '';

    if (currentSection === 'cari') {
        // Stats
        metricsGrid.innerHTML = `
            <div class="modal-metric-card">
                <span class="lbl">Müşteri Sayısı</span>
                <span class="val">${dashboardData.cari.musteri_sayisi}</span>
            </div>
            <div class="modal-metric-card">
                <span class="lbl">Tedarikçi Sayısı</span>
                <span class="val">${dashboardData.cari.tedarikci_sayisi}</span>
            </div>
            <div class="modal-metric-card">
                <span class="lbl">Net Denge</span>
                <span class="val ${dashboardData.cari.toplam_alacak - dashboardData.cari.toplam_borc >= 0 ? 'val-green' : 'val-red'}">
                    ${formatCurrency(dashboardData.cari.toplam_alacak - dashboardData.cari.toplam_borc)}
                </span>
            </div>
        `;
        
        // Table list
        dashboardData.cari.son_islemler.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.tarih}</td>
                <td>${item.tanim}</td>
                <td class="${item.tip === 'alacak' ? 'val-green' : 'val-red'}">${item.tutar > 0 ? formatCurrency(item.tutar) : '-'}</td>
                <td><span class="tile-tag ${item.tip === 'alacak' ? 'tag-green' : 'tag-orange'}">${item.tip === 'alacak' ? 'Alacak' : 'Borç'}</span></td>
            `;
            tableBody.appendChild(tr);
        });

    } else if (currentSection === 'kasa') {
        metricsGrid.innerHTML = `
            <div class="modal-metric-card">
                <span class="lbl">Kasa Bakiyesi</span>
                <span class="val">${formatCurrency(dashboardData.kasa_banka.kasa_bakiye)}</span>
            </div>
            <div class="modal-metric-card">
                <span class="lbl">Banka Bakiyesi</span>
                <span class="val">${formatCurrency(dashboardData.kasa_banka.banka_bakiye)}</span>
            </div>
            <div class="modal-metric-card">
                <span class="lbl">Toplam Nakit</span>
                <span class="val val-green">${formatCurrency(dashboardData.kasa_banka.toplam_nakit)}</span>
            </div>
        `;
        
        dashboardData.kasa_banka.son_islemler.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.tarih}</td>
                <td>
                    <strong>${item.tanim}</strong>
                    <small style="display:block; opacity:0.6; margin-top:2px;">
                        <i class="fa-solid fa-wallet" style="margin-right:4px;"></i>${item.hesap_ad || 'Kasa'}
                    </small>
                </td>
                <td class="${item.tip === 'giris' ? 'val-green' : 'val-red'}">${item.tip === 'giris' ? '+' : '-'}${formatCurrency(item.tutar)}</td>
                <td><span class="tile-tag ${item.tip === 'giris' ? 'tag-green' : 'tag-orange'}">${item.tip === 'giris' ? 'Giriş' : 'Çıkış'}</span></td>
            `;
            tableBody.appendChild(tr);
        });

    } else if (currentSection === 'stok') {
        metricsGrid.innerHTML = `
            <div class="modal-metric-card">
                <span class="lbl">Ürün Çeşidi</span>
                <span class="val">${dashboardData.stok.toplam_urun_cesidi}</span>
            </div>
            <div class="modal-metric-card">
                <span class="lbl">Kritik Stok</span>
                <span class="val val-warning">${dashboardData.stok.kritik_stok_sayisi}</span>
            </div>
            <div class="modal-metric-card">
                <span class="lbl">Depo Doluluğu</span>
                <span class="val val-green">%${dashboardData.stok.depo_doluluk_orani}</span>
            </div>
        `;
        
        dashboardData.stok.son_islemler.forEach(item => {
            const tr = document.createElement('tr');
            let tagClass = 'tag-green';
            if (item.tip === 'alarm') tagClass = 'tag-orange';
            else if (item.tip === 'cikis') tagClass = 'tag-blue';
            
            tr.innerHTML = `
                <td>${item.tarih}</td>
                <td>${item.tanim}</td>
                <td>-</td>
                <td><span class="tile-tag ${tagClass}">${item.tip.toUpperCase()}</span></td>
            `;
            tableBody.appendChild(tr);
        });

    } else if (currentSection === 'fatura') {
        metricsGrid.innerHTML = `
            <div class="modal-metric-card">
                <span class="lbl">Ödenmemiş Faturalar</span>
                <span class="val val-danger">${dashboardData.fatura_irsaliye.odenmemis_fatura}</span>
            </div>
            <div class="modal-metric-card">
                <span class="lbl">Bekleyen İrsaliyeler</span>
                <span class="val">${dashboardData.fatura_irsaliye.bekleyen_irsaliye}</span>
            </div>
            <div class="modal-metric-card">
                <span class="lbl">Bu Ay Düzenlenen</span>
                <span class="val val-purple">${formatCurrency(dashboardData.fatura_irsaliye.aylik_fatura_tutari)}</span>
            </div>
        `;
        
        dashboardData.fatura_irsaliye.son_islemler.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.tarih}</td>
                <td>${item.tanim}</td>
                <td>${item.tutar > 0 ? formatCurrency(item.tutar) : '-'}</td>
                <td><span class="tile-tag ${item.durum === 'Ödendi' ? 'tag-green' : 'tag-orange'}">${item.durum}</span></td>
            `;
            tableBody.appendChild(tr);
        });
    }
}

// Generate dynamic form elements under Add Tab based on selection
function generateFormFields() {
    const fieldsContainer = document.getElementById('dynamicFormFields');
    fieldsContainer.innerHTML = '';
    
    if (currentSection === 'cari') {
        fieldsContainer.innerHTML = `
            <div class="form-group">
                <label for="cariAd">Cari Ünvanı / Müşteri Adı <span style="color: var(--danger-color);">*</span></label>
                <input type="text" id="cariAd" class="form-control" placeholder="Örn: Akdağ İnşaat Ltd. Şti." required>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariTip">Cari Tipi</label>
                    <select id="cariTip" class="form-control">
                        <option value="musteri">Müşteri</option>
                        <option value="tedarikci">Tedarikçi</option>
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariLimit">Devir Bakiyesi / Limit (TL)</label>
                    <input type="number" id="cariLimit" class="form-control" placeholder="0.00" step="0.01">
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariVergiNo">Vergi / T.C. Kimlik No <span style="color: var(--danger-color);">*</span></label>
                    <input type="text" id="cariVergiNo" class="form-control" placeholder="10 veya 11 haneli" required>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariVergiDairesi">Vergi Dairesi</label>
                    <input type="text" id="cariVergiDairesi" class="form-control" list="vergiDairesiList" placeholder="Seçin veya Yazın">
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariYetkili">Yetkili Kişi <span style="color: var(--danger-color);">*</span></label>
                    <input type="text" id="cariYetkili" class="form-control" placeholder="Ad Soyad" required>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariGrubu">Cari Grubu / Sektör</label>
                    <input type="text" id="cariGrubu" class="form-control" list="cariGrubuList" placeholder="Seçin veya Yazın">
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariEposta">E-Posta Adresi</label>
                    <input type="email" id="cariEposta" class="form-control" placeholder="ornek@firma.com">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariTelefon">Telefon Numarası</label>
                    <input type="text" id="cariTelefon" class="form-control" placeholder="05xx xxx xx xx">
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariKredibilite">Kredibilite Notu (Ödeme Gücü)</label>
                    <select id="cariKredibilite" class="form-control">
                        <option value="A+">A+ (Mükemmel Güvenilirlik)</option>
                        <option value="A" selected>A (Yüksek Güvenilirlik)</option>
                        <option value="B">B (Orta Derece Güvenilirlik)</option>
                        <option value="C">C (Düşük Güvenilirlik / Riskli)</option>
                        <option value="D">D (Yüksek Risk)</option>
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <!-- Spacer -->
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariIl">Şehir / İl</label>
                    <select id="cariIl" class="form-control" onchange="updateCariIlceOptions()">
                        <option value="İstanbul">İstanbul</option>
                        <option value="Ankara">Ankara</option>
                        <option value="İzmir">İzmir</option>
                        <option value="Kocaeli">Kocaeli</option>
                        <option value="Karabük">Karabük</option>
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="cariIlce">İlçe</label>
                    <select id="cariIlce" class="form-control">
                        <!-- Populated dynamically -->
                    </select>
                </div>
            </div>
            
            <div class="form-group">
                <label for="cariMahalle">Mahalle</label>
                <input type="text" id="cariMahalle" class="form-control" placeholder="Örn: Caferağa Mah.">
            </div>
            <div class="form-group">
                <label for="cariAdresDetay">Açık Adres (Sokak, Apartman, Daire No)</label>
                <textarea id="cariAdresDetay" class="form-control" placeholder="Cadde, sokak, no, daire..." rows="2"></textarea>
            </div>
            
            <datalist id="vergiDairesiList">
                <option value="Kadıköy V.D.">
                <option value="Beşiktaş V.D.">
                <option value="Maslak V.D.">
                <option value="Zincirlikuyu V.D.">
                <option value="Ataşehir V.D.">
                <option value="Mecidiyeköy V.D.">
                <option value="Tuzla V.D.">
                <option value="Gebze V.D.">
                <option value="Karabük V.D.">
                <option value="Büyük Mükellefler V.D.">
            </datalist>
            <datalist id="cariGrubuList">
                <option value="İnşaat">
                <option value="Gıda Tedarik">
                <option value="Gıda Toptan">
                <option value="Teknoloji">
                <option value="Danışmanlık">
                <option value="Sanayi & Metal">
                <option value="Lojistik & Nakliye">
                <option value="Reklam & Medya">
                <option value="Mobilya Üretim">
                <option value="Kimya & Kozmetik">
                <option value="Tasarım & Mimarlık">
                <option value="Hırdavat & Yapı">
            </datalist>
        `;
        updateCariIlceOptions();

        // Suggest limit based on credibility rating
        const credSelect = document.getElementById('cariKredibilite');
        const limitInput = document.getElementById('cariLimit');
        if (credSelect && limitInput) {
            limitInput.value = 100000; // Default for 'A'
            credSelect.addEventListener('change', (e) => {
                const limits = { "A+": 150000, "A": 100000, "B": 50000, "C": 15000, "D": 5000 };
                limitInput.value = limits[e.target.value] || 0;
            });
        }
    } else if (currentSection === 'kasa') {
        fieldsContainer.innerHTML = `
            <div class="form-group">
                <label for="kasaTanim">İşlem Açıklaması</label>
                <input type="text" id="kasaTanim" class="form-control" placeholder="Örn: Yemek Bedeli Ödemesi" required>
            </div>
            <div class="form-group">
                <label for="kasaHesap">Hesap Seçimi</label>
                <select id="kasaHesap" class="form-control">
                    <option value="kasa">Merkez Kasa</option>
                    <option value="banka">Şirket Banka Hesabı</option>
                </select>
            </div>
            <div class="form-group">
                <label for="kasaTutar">Tutar (TL)</label>
                <input type="number" id="kasaTutar" class="form-control" placeholder="Negatif değerler çıkış gösterir (-500)" step="0.01" required>
            </div>
        `;
    } else if (currentSection === 'stok') {
        fieldsContainer.innerHTML = `
            <div class="form-group">
                <label for="stokAd">Ürün Adı</label>
                <input type="text" id="stokAd" class="form-control" placeholder="Örn: Logi Tech Klavye MK220" required>
            </div>
            <div class="form-group">
                <label for="stokKategori">Kategori</label>
                <select id="stokKategori" class="form-control">
                    <option value="Elektronik">Elektronik</option>
                    <option value="Ofis Malzemeleri">Ofis Malzemeleri</option>
                    <option value="Aksesuar & Sarf">Aksesuar & Sarf</option>
                </select>
            </div>
            <div class="form-group">
                <label for="stokAdet">Adet</label>
                <input type="number" id="stokAdet" class="form-control" min="1" placeholder="10" required>
            </div>
        `;
    } else if (currentSection === 'fatura') {
        fieldsContainer.innerHTML = `
            <div class="form-group">
                <label for="faturaUnvan">Cari Firma Ünvanı</label>
                <input type="text" id="faturaUnvan" class="form-control" placeholder="Örn: Yıldırım Ticaret" required>
            </div>
            <div class="form-group">
                <label for="faturaTip">Fatura Tipi</label>
                <select id="faturaTip" class="form-control">
                    <option value="satis">Satış Faturası (Gelir)</option>
                    <option value="alis">Alış Faturası (Gider)</option>
                </select>
            </div>
            <div class="form-group">
                <label for="faturaTutar">KDV Dahil Toplam Tutar (TL)</label>
                <input type="number" id="faturaTutar" class="form-control" min="0.01" step="0.01" placeholder="1250.00" required>
            </div>
        `;
    }
}

// Handle Form submits and POST to Backend APIs
async function handleFormSubmit(event) {
    event.preventDefault();
    
    let url = '';
    let payload = {};

    if (currentSection === 'cari') {
        url = '/api/cari/ekle';
        payload = {
            ad: document.getElementById('cariAd').value,
            tip: document.getElementById('cariTip').value,
            limit: document.getElementById('cariLimit').value || 0,
            vergi_no: document.getElementById('cariVergiNo').value || '',
            vergi_dairesi: document.getElementById('cariVergiDairesi').value || '',
            yetkili_kisi: document.getElementById('cariYetkili').value || '',
            eposta: document.getElementById('cariEposta').value || '',
            telefon: document.getElementById('cariTelefon').value || '',
            il: document.getElementById('cariIl').value || '',
            ilce: document.getElementById('cariIlce').value || '',
            mahalle: document.getElementById('cariMahalle').value || '',
            adres_detay: document.getElementById('cariAdresDetay').value || '',
            cari_grubu: document.getElementById('cariGrubu').value || '',
            kredibilite: document.getElementById('cariKredibilite').value || 'A'
        };
    } else if (currentSection === 'kasa') {
        url = '/api/kasa/ekle';
        payload = {
            tanim: document.getElementById('kasaTanim').value,
            hesap: document.getElementById('kasaHesap').value,
            tutar: document.getElementById('kasaTutar').value
        };
    } else if (currentSection === 'stok') {
        url = '/api/stok/ekle';
        payload = {
            ad: document.getElementById('stokAd').value,
            kategori: document.getElementById('stokKategori').value,
            adet: document.getElementById('stokAdet').value
        };
    } else if (currentSection === 'fatura') {
        url = '/api/fatura/ekle';
        payload = {
            unvan: document.getElementById('faturaUnvan').value,
            tip: document.getElementById('faturaTip').value,
            tutar: document.getElementById('faturaTutar').value
        };
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.message || 'Kayıt işlemi başarısız.');
        }

        // Successfully updated DB
        Swal.fire({
            icon: 'success',
            title: 'Başarılı!',
            text: 'Yeni kayıt başarıyla eklendi.',
            showConfirmButton: false,
            timer: 1500
        });

        closeModal();
        // Refresh local dashboard
        refreshDashboard();

    } catch (error) {
        console.error('Error submitting form:', error);
        Swal.fire({
            icon: 'error',
            title: 'Kayıt Hatası',
            text: error.message || 'Beklenmeyen bir hata oluştu.',
            confirmButtonColor: '#ef4444'
        });
    }
}

// Global quick action modal triggers
function openGlobalActionModal() {
    document.getElementById('globalActionModal').classList.add('active');
}

function closeGlobalActionModal() {
    document.getElementById('globalActionModal').classList.remove('active');
}

// Select a quick action card
function triggerQuickAction(section) {
    closeGlobalActionModal();
    // Open modal directly on dynamic form inputs
    currentSection = section;
    document.getElementById('detailModal').classList.add('active');
    setupModalUI();
    switchModalTab('add');
}

// Search queries filtering cards
function filterCards(query) {
    const cards = document.querySelectorAll('.card-tile');
    cards.forEach(card => {
        const title = card.querySelector('.tile-title').textContent.toLowerCase();
        const tag = card.querySelector('.tile-tag').textContent.toLowerCase();
        
        if (title.includes(query) || tag.includes(query)) {
            card.style.display = 'flex';
            card.style.opacity = '1';
            card.style.transform = 'scale(1)';
        } else {
            card.style.opacity = '0.3';
            card.style.transform = 'scale(0.98)';
        }
    });
}

// Quick Operations Bar Tab Toggle
let activeOpTab = null;

function toggleOperationsTab(tabName) {
    const bar = document.getElementById('operationsBar');
    const content = document.getElementById('operationsContent');
    
    // If clicking the active tab, close it
    if (activeOpTab === tabName) {
        bar.classList.remove('expanded');
        const activeBtn = document.querySelector('.op-tab-btn.active');
        if (activeBtn) activeBtn.classList.remove('active');
        activeOpTab = null;
        return;
    }
    
    // Deactivate all buttons
    const tabBtns = document.querySelectorAll('.op-tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));
    
    // Find the clicked button and activate it
    const clickedBtn = Array.from(tabBtns).find(btn => btn.outerHTML.includes(`toggleOperationsTab('${tabName}')`));
    if (clickedBtn) clickedBtn.classList.add('active');
    
    // Hide all panels
    const panels = document.querySelectorAll('.op-sub-panel');
    panels.forEach(p => p.classList.remove('active'));
    
    // Show current panel
    const currentPanel = document.getElementById(`opPanel-${tabName}`);
    if (currentPanel) currentPanel.classList.add('active');
    
    // Expand accordion content area
    bar.classList.add('expanded');
    activeOpTab = tabName;
}

// Execute Sub Action (Opens Modals)
function executeSubAction(section, tab) {
    showSectionDetail(section);
    switchModalTab(tab);
}

// Show Quick Report Helper
function triggerQuickReport(section) {
    showSectionDetail(section);
    switchModalTab('view');
    
    let msg = '';
    if (section === 'cari') msg = 'Cari Mutabakat dengesini sol alttaki grafik üzerinden analiz edebilirsiniz.';
    else if (section === 'kasa') msg = 'Nakit akış analizini "Kasa & Banka" alanındaki çizgi grafik üzerinden inceleyebilirsiniz.';
    else if (section === 'stok') msg = 'Ürün envanter dağılımını "Stok" dairesel grafiği üzerinden kontrol edebilirsiniz.';
    else if (section === 'fatura') msg = 'Fatura ödeme durumlarını "Fatura" yatay sütun grafiği üzerinden takip edebilirsiniz.';
    
    Swal.fire({
        icon: 'info',
        title: 'Grafik Raporu',
        text: msg,
        confirmButtonColor: '#0078d4',
        timer: 3500
    });
}

// Render dynamic AI insights
function renderAiInsights() {
    const listContainer = document.getElementById('aiInsightsList');
    if (!listContainer || !dashboardData) return;
    
    listContainer.innerHTML = '';
    
    // Insight 1: Cari Balance
    const cariDenge = dashboardData.cari.toplam_alacak - dashboardData.cari.toplam_borc;
    let cariText = '';
    if (cariDenge >= 0) {
        cariText = `Cari hesap dengeniz pozitif yönde. Toplam net alacağınız <strong>${formatCurrency(cariDenge)}</strong>. Alacak tahsilatlarını düzenli takip etmeniz likiditenizi koruyacaktır.`;
    } else {
        cariText = `Cari borç bakiyeniz alacaklarınızdan <strong>${formatCurrency(Math.abs(cariDenge))}</strong> daha fazla. Kasa dengesini korumak için ödeme vadelerini uzatmayı planlayın.`;
    }
    
    // Insight 2: Liquidity Summary
    const kasaText = `Kasa bakiyeniz <strong>${formatCurrency(dashboardData.kasa_banka.kasa_bakiye)}</strong>, banka bakiyeniz <strong>${formatCurrency(dashboardData.kasa_banka.banka_bakiye)}</strong> olmak üzere toplam nakit gücünüz <strong>${formatCurrency(dashboardData.kasa_banka.toplam_nakit)}</strong>.`;
    
    // Insight 3: Inventory
    const stokKritik = dashboardData.stok.kritik_stok_sayisi;
    let stokText = '';
    if (stokKritik > 0) {
        stokText = `⚠️ Envanterinizde <strong>${stokKritik} adet</strong> ürün kritik stok seviyesinin altına düştü. Mal tedarik sürecini başlatmanız tavsiye edilir.`;
    } else {
        stokText = `✓ Envanterinizdeki tüm ürün stokları ideal durumda. Kritik seviyede ürün bulunmamaktadır.`;
    }
    
    // Build list
    const items = [
        { icon: 'fa-chart-pie', text: cariText },
        { icon: 'fa-money-bill-trend-up', text: kasaText },
        { icon: 'fa-box', text: stokText }
    ];
    
    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'insight-item';
        div.innerHTML = `<i class="fa-solid ${item.icon}"></i> <span>${item.text}</span>`;
        listContainer.appendChild(div);
    });
}

// Handle AI Question Submit
async function handleAiQuestion(event) {
    event.preventDefault();
    
    const inputEl = document.getElementById('aiQuestionInput');
    const responseBox = document.getElementById('aiResponseBox');
    const responseText = document.getElementById('aiResponseText');
    const sendBtn = document.getElementById('aiSendBtn');
    
    const question = inputEl.value.trim();
    if (!question) return;
    
    // Disable inputs and show loading state
    inputEl.disabled = true;
    sendBtn.disabled = true;
    responseBox.style.display = 'flex';
    responseText.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> BulutAI verileri inceliyor ve analiz hazırlıyor...`;
    
    try {
        const response = await fetch('/api/ai/sor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ soru: question })
        });
        
        if (!response.ok) throw new Error('Yapay zeka yanıt veremedi.');
        const data = await response.json();
        
        // Add a simulated generation delay of 800ms
        setTimeout(() => {
            responseText.innerHTML = data.cevap;
            inputEl.disabled = false;
            sendBtn.disabled = false;
            inputEl.value = '';
            inputEl.focus();
        }, 800);
        
    } catch (error) {
        console.error('AI Ask Error:', error);
        responseText.innerHTML = `<span style="color: var(--danger-color);"><i class="fa-solid fa-triangle-exclamation"></i> Hata: Yanıt alınamadı. Lütfen daha sonra tekrar deneyin.</span>`;
        inputEl.disabled = false;
        sendBtn.disabled = false;
    }
}

// Collapsible inline Cari Summary toggle
function toggleCariSummaryCollapse() {
    const panel = document.getElementById('cariSummaryInlinePanel');
    const arrow = document.getElementById('cariSummaryArrow');
    if (!panel || !dashboardData) return;
    
    const isHidden = panel.style.display === 'none';
    if (isHidden) {
        // Populate
        document.getElementById('inlineAlacak').textContent = formatCurrency(dashboardData.cari.toplam_alacak);
        document.getElementById('inlineBorc').textContent = formatCurrency(dashboardData.cari.toplam_borc);
        
        const listEl = document.getElementById('inlineRecentList');
        listEl.innerHTML = '';
        
        const history = dashboardData.cari.son_islemler;
        if (!history || history.length === 0) {
            listEl.innerHTML = '<li style="color: var(--text-secondary);">Son işlem bulunmuyor.</li>';
        } else {
            history.forEach(item => {
                const li = document.createElement('li');
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.style.alignItems = 'center';
                li.style.borderBottom = '1px dashed rgba(255,255,255,0.05)';
                li.style.paddingBottom = '4px';
                
                const isAlacak = item.tip === 'alacak';
                const sign = isAlacak ? '+' : '-';
                const colorClass = isAlacak ? 'val-green' : (item.tip === 'borc' ? 'val-red' : '');
                
                li.innerHTML = `
                    <span style="color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 200px;">${item.tanim}</span>
                    <span class="${colorClass}" style="font-weight: 600;">${sign}${formatCurrency(item.tutar)}</span>
                `;
                listEl.appendChild(li);
            });
        }
        
        panel.style.display = 'block';
        arrow.style.transform = 'rotate(180deg)';
    } else {
        panel.style.display = 'none';
        arrow.style.transform = 'rotate(0deg)';
    }
}

// Update inline summary if it is open
function updateInlineCariSummaryIfOpen() {
    const panel = document.getElementById('cariSummaryInlinePanel');
    if (panel && panel.style.display !== 'none') {
        document.getElementById('inlineAlacak').textContent = formatCurrency(dashboardData.cari.toplam_alacak);
        document.getElementById('inlineBorc').textContent = formatCurrency(dashboardData.cari.toplam_borc);
        
        const listEl = document.getElementById('inlineRecentList');
        listEl.innerHTML = '';
        
        const history = dashboardData.cari.son_islemler;
        if (history) {
            history.forEach(item => {
                const li = document.createElement('li');
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.style.alignItems = 'center';
                li.style.borderBottom = '1px dashed rgba(255,255,255,0.05)';
                li.style.paddingBottom = '4px';
                
                const isAlacak = item.tip === 'alacak';
                const sign = isAlacak ? '+' : '-';
                const colorClass = isAlacak ? 'val-green' : (item.tip === 'borc' ? 'val-red' : '');
                
                li.innerHTML = `
                    <span style="color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 200px;">${item.tanim}</span>
                    <span class="${colorClass}" style="font-weight: 600;">${sign}${formatCurrency(item.tutar)}</span>
                `;
                listEl.appendChild(li);
            });
        }
    }
}

// Structured Address helpers
const ilceData = {
    "İstanbul": ["Kadıköy", "Beşiktaş", "Şişli", "Ataşehir", "Bakırköy", "Kartal", "Kağıthane", "Tuzla", "Beyoğlu", "Başakşehir", "Sarıyer", "Esenler", "Fatih", "Küçükçekmece", "Zeytinburnu", "Bağcılar", "Pendik"],
    "Ankara": ["Çankaya", "Keçiören", "Yenimahalle", "Mamak", "Etimesgut", "Sincan"],
    "İzmir": ["Konak", "Bornova", "Karşıyaka", "Buca", "Bayraklı"],
    "Kocaeli": ["Gebze", "İzmit", "Körfez", "Gölcük"],
    "Karabük": ["Merkez", "Safranbolu", "Yenice"]
};

function updateCariIlceOptions() {
    const ilSelect = document.getElementById('cariIl');
    const ilceSelect = document.getElementById('cariIlce');
    if (!ilSelect || !ilceSelect) return;
    const selectedIl = ilSelect.value;
    const ilçeler = ilceData[selectedIl] || [];
    ilceSelect.innerHTML = ilçeler.map(ilce => `<option value="${ilce}">${ilce}</option>`).join('');
}
