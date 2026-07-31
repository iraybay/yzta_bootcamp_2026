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
        { text: "Fatura & İrsaliye Ekranını Aç", keywords: ["fatura listesi", "irsaliye takibi", "fatura ve irsaliye", "irsaliye ekle", "fatura gör", "fatura takibi"], action: () => { location.href = '/fatura-irsaliye'; }, icon: "fa-solid fa-file-invoice-dollar" },
        { text: "Mutabakat & Ödeme Raporu", keywords: ["mutabakat", "ödeme planı", "gelecek ödemeler", "rapor", "mutabakat raporu"], action: () => { location.href = '/mutabakat-raporu'; }, icon: "fa-solid fa-calendar-days" },
        { text: "Son İşlemler & Özet Ekranı", keywords: ["son işlemler", "cari hareketler", "özet", "hareketler"], action: () => { location.href = '/cari-hareketler'; }, icon: "fa-solid fa-clock-rotate-left" }
    ];

    searchInput.addEventListener('input', async (e) => {
        const query = e.target.value.toLowerCase().trim();
        filterCards(query);
        
        if (query.length > 1) {
            const staticMatches = commands.filter(cmd => 
                cmd.keywords.some(keyword => keyword.includes(query) || query.includes(keyword))
            ).map(cmd => ({
                text: cmd.text,
                icon: cmd.icon,
                action: cmd.action
            }));
            
            try {
                const response = await fetch(`/api/global-search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (data.success) {
                    const dbMatches = data.results.map(item => ({
                        text: item.text,
                        icon: item.icon,
                        action: () => { location.href = item.target; }
                    }));
                    
                    const allMatches = [...staticMatches, ...dbMatches];
                    
                    if (allMatches.length > 0) {
                        suggestionsBox.innerHTML = allMatches.map((cmd, idx) => `
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
                                allMatches[idx].action();
                                suggestionsBox.style.display = 'none';
                                searchInput.value = '';
                            });
                        });
                    } else {
                        suggestionsBox.style.display = 'none';
                    }
                }
            } catch (err) {
                console.error("Global search error:", err);
            }
        } else {
            suggestionsBox.style.display = 'none';
        }
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const firstSuggestion = suggestionsBox.querySelector('.search-suggestion-item');
            if (firstSuggestion) {
                firstSuggestion.click();
            }
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
            text: 'Veriler sunucudan alınamadı. Hata Detayı: ' + error.message,
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
            labels: (dashboardData.kasa_banka && dashboardData.kasa_banka.monthly_chart) ? dashboardData.kasa_banka.monthly_chart.labels : [],
            datasets: [
                {
                    label: 'Gelirler',
                    data: (dashboardData.kasa_banka && dashboardData.kasa_banka.monthly_chart) ? dashboardData.kasa_banka.monthly_chart.gelirler : [],
                    borderColor: '#2a9d8f',
                    backgroundColor: 'rgba(42, 157, 143, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 0
                },
                {
                    label: 'Giderler',
                    data: (dashboardData.kasa_banka && dashboardData.kasa_banka.monthly_chart) ? dashboardData.kasa_banka.monthly_chart.giderler : [],
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
    if (section === 'fatura') {
        location.href = '/fatura-irsaliye?action=new';
        return;
    }
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
    }
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
            let typeText = '';
            let tagClass = '';
            
            if (item.tip === 'giris') {
                typeText = 'Giriş';
                tagClass = 'tag-green';
            } else if (item.tip === 'cikis') {
                typeText = 'Çıkış';
                tagClass = 'tag-orange';
            } else if (item.tip === 'sayim_fazlasi') {
                typeText = 'Sayım fazlası';
                tagClass = 'tag-purple';
            } else if (item.tip === 'fire') {
                typeText = 'Fire';
                tagClass = 'tag-blue';
            } else {
                typeText = item.tip;
                tagClass = 'tag-gray';
            }
            
            // Format date as DD.MM.YYYY
            let formattedDate = item.tarih;
            if (item.tarih) {
                const parts = item.tarih.split('-');
                if (parts.length === 3) {
                    formattedDate = `${parts[2]}.${parts[1]}.${parts[0]}`;
                }
            }
            
            tr.innerHTML = `
                <td>${formattedDate}</td>
                <td>${item.tanim}</td>
                <td>-</td>
                <td><span class="tile-tag ${tagClass}" style="text-transform: none;">${typeText}</span></td>
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
                <label for="stokId">Ürün Seçin *</label>
                <select id="stokId" class="form-control" required>
                    <option value="">Yükleniyor...</option>
                </select>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="stokTip">İşlem Tipi *</label>
                    <select id="stokTip" class="form-control">
                        <option value="giris">Stok girişi</option>
                        <option value="cikis">Stok çıkışı</option>
                        <option value="sayim_fazlasi">Sayım fazlası</option>
                        <option value="fire">Fire / zayiat</option>
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="stokMiktar">Miktar *</label>
                    <input type="number" id="stokMiktar" class="form-control" min="1" value="1" required>
                </div>
            </div>
            <div class="form-group">
                <label for="stokAciklama">Açıklama</label>
                <input type="text" id="stokAciklama" class="form-control" placeholder="Örn: Malzeme alımı, Satış çıkışı, Hasar fire vb.">
            </div>
        `;
        fetch('/api/stok/liste')
            .then(res => res.json())
            .then(json => {
                const list = json.data || [];
                const selectEl = document.getElementById('stokId');
                if (selectEl) {
                    selectEl.innerHTML = list.map(s => `<option value="${s.id}">${s.ad} (Mevcut: ${s.adet})</option>`).join('');
                }
            })
            .catch(err => console.error("Stok listesi yuklenemedi", err));
    } else if (currentSection === 'fatura') {
        let cariOptionsHtml = (dashboardData.cari && dashboardData.cari.tum_liste ? dashboardData.cari.tum_liste : []).map(c => `<option value="${c.ad}">${c.ad}</option>`).join('');

        fieldsContainer.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaBelgeNo">Fatura / İrsaliye Seri & No</label>
                    <input type="text" id="faturaBelgeNo" class="form-control" placeholder="Örn: FT-2026-000101">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaTip">Belge İşlem Tipi *</label>
                    <select id="faturaTip" class="form-control">
                        <option value="satis">Satış Faturası (Gelir)</option>
                        <option value="alis">Alış Faturası (Gider)</option>
                        <option value="irsaliye">Sevk İrsaliyesi</option>
                        <option value="irsaliyeli_fatura">İrsaliyeli Fatura</option>
                    </select>
                </div>
            </div>

            <div class="form-group">
                <label for="faturaUnvan">Cari Firma / Müşteri Ünvanı *</label>
                <input type="text" id="faturaUnvan" class="form-control" list="cariFirmaList" placeholder="Firma veya müşteri adı girin veya seçin..." required>
                <datalist id="cariFirmaList">
                    ${cariOptionsHtml}
                </datalist>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaVergiDairesi">Vergi Dairesi</label>
                    <input type="text" id="faturaVergiDairesi" class="form-control" placeholder="Örn: Büyük Mükellefler V.D.">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaVergiNo">Vergi No / TCKN</label>
                    <input type="text" id="faturaVergiNo" class="form-control" placeholder="Örn: 9876543210" maxlength="11">
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaEposta">E-posta Adresi</label>
                    <input type="email" id="faturaEposta" class="form-control" placeholder="fatura@firma.com">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaTelefon">Telefon</label>
                    <input type="tel" id="faturaTelefon" class="form-control" placeholder="0532 000 00 00">
                </div>
            </div>

            <div class="form-group">
                <label for="faturaAdres">Teslimat / Fatura Adresi</label>
                <input type="text" id="faturaAdres" class="form-control" placeholder="Örn: Maslak Mah. Dereboyu Cad. No:42 Sarıyer / İstanbul">
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaTarih">Fatura Tarihi</label>
                    <input type="date" id="faturaTarih" class="form-control" value="2026-07-24">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaVade">Vade / Sevk Tarihi</label>
                    <input type="date" id="faturaVade" class="form-control" value="2026-08-15">
                </div>
            </div>

            <div class="form-group">
                <label for="faturaKalemAciklama">Mal / Hizmet Kalem Açıklaması</label>
                <input type="text" id="faturaKalemAciklama" class="form-control" placeholder="Örn: Yazılım Danışmanlık ve Donanım Kurulum Hizmet Bedeli">
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaMatrah">Matrah Tutar (TL) *</label>
                    <input type="number" step="0.01" id="faturaMatrah" class="form-control" placeholder="1000.00" oninput="calcFaturaToplam()" required>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaKdv">KDV Oranı (%)</label>
                    <select id="faturaKdv" class="form-control" onchange="calcFaturaToplam()">
                        <option value="20" selected>%20 KDV</option>
                        <option value="10">%10 KDV</option>
                        <option value="1">%1 KDV</option>
                        <option value="0">%0 (Muaf)</option>
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaToplam">Genel Toplam (TL)</label>
                    <input type="number" step="0.01" id="faturaToplam" class="form-control" placeholder="1200.00" style="font-weight: 700; color: var(--primary-color);" readonly>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaDurum">İşlem / Ödeme Durumu</label>
                    <select id="faturaDurum" class="form-control">
                        <option value="Ödenmedi" selected>Ödenmedi</option>
                        <option value="Ödendi">Ödendi</option>
                        <option value="Bekliyor">Bekliyor (Yolda)</option>
                        <option value="Teslim Edildi">Teslim Edildi</option>
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label for="faturaNot">Not / Şartlar</label>
                    <input type="text" id="faturaNot" class="form-control" placeholder="Örn: 30 Gün Vadeli Ödeme Şartı">
                </div>
            </div>
        `;
    }
}

function calcFaturaToplam() {
    const matrah = parseFloat(document.getElementById('faturaMatrah')?.value || 0);
    const kdv = parseFloat(document.getElementById('faturaKdv')?.value || 20);
    const toplam = matrah + (matrah * kdv / 100);
    const toplamInput = document.getElementById('faturaToplam');
    if (toplamInput) toplamInput.value = toplam.toFixed(2);
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
        url = '/api/stok/hareket-ekle';
        payload = {
            stok_id: document.getElementById('stokId').value,
            tip: document.getElementById('stokTip').value,
            miktar: document.getElementById('stokMiktar').value,
            aciklama: document.getElementById('stokAciklama').value || ''
        };
    } else if (currentSection === 'fatura') {
        url = '/api/fatura/ekle';
        const matrah = parseFloat(document.getElementById('faturaMatrah')?.value || 0);
        const kdv = parseFloat(document.getElementById('faturaKdv')?.value || 20);
        const tutar = matrah + (matrah * kdv / 100);

        payload = {
            unvan: document.getElementById('faturaUnvan').value,
            tip: document.getElementById('faturaTip').value,
            tutar: tutar > 0 ? tutar : parseFloat(document.getElementById('faturaToplam')?.value || 0),
            durum: document.getElementById('faturaDurum')?.value || 'Ödenmedi',
            tarih: document.getElementById('faturaTarih')?.value || '2026-07-24',
            aciklama: document.getElementById('faturaKalemAciklama')?.value || document.getElementById('faturaNot')?.value || ''
        };
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const resData = await response.json();
        if (!response.ok || (resData && resData.success === false)) {
            throw new Error(resData.message || 'Kayıt işlemi başarısız.');
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

let globalChatHistory = [];

// Handle AI Question Submit
async function handleAiQuestion(event) {
    event.preventDefault();
    
    const inputEl = document.getElementById('aiQuestionInput');
    const chatHistory = document.getElementById('aiChatHistory');
    const sendBtn = document.getElementById('aiSendBtn');
    
    const question = inputEl.value.trim();
    if (!question) return;
    
    // Clear input field immediately
    inputEl.value = '';
    
    // Add user message to history
    globalChatHistory.push({ role: 'user', content: question });
    
    // Display Chat History container
    chatHistory.style.display = 'flex';
    
    // Append User message bubble
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.textContent = question;
    chatHistory.appendChild(userBubble);
    
    // Append AI loading bubble
    const aiBubble = document.createElement('div');
    aiBubble.className = 'chat-bubble ai';
    aiBubble.innerHTML = `<span class="ai-text"><i class="fa-solid fa-circle-notch fa-spin"></i> BulutAI verileri inceliyor...</span>`;
    chatHistory.appendChild(aiBubble);
    
    // Auto-scroll
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    // Disable inputs
    inputEl.disabled = true;
    sendBtn.disabled = true;
    
    try {
        const response = await fetch('/api/ai/sor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ soru: question, history: globalChatHistory })
        });
        
        let textResult = '';
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            textResult = errData.message || 'Yapay zeka yanıt veremedi.';
        } else {
            const data = await response.json();
            textResult = data.cevap;
        }
        
        // Add assistant response to history
        globalChatHistory.push({ role: 'assistant', content: textResult });
        
        // Add a simulated generation delay of 400ms for smoothness
        setTimeout(() => {
            aiBubble.innerHTML = `<span class="ai-text">${textResult}</span>`;
            inputEl.disabled = false;
            sendBtn.disabled = false;
            inputEl.focus();
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }, 400);
        
    } catch (error) {
        console.error('AI Ask Error:', error);
        aiBubble.innerHTML = `<span class="ai-text" style="color: #ef4444;"><i class="fa-solid fa-triangle-exclamation"></i> Bağlantı hatası: Sorunuza yanıt alınamadı.</span>`;
        inputEl.disabled = false;
        sendBtn.disabled = false;
        chatHistory.scrollTop = chatHistory.scrollHeight;
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

// Reusable SweetAlert2 modal for invoice payments/collections
async function showInvoicePaymentPopup(faturaId, cariId, belgeNo, tutar, tip, onComplete) {
    try {
        const res = await fetch('/api/kasa-banka/hesaplar');
        const json = await res.json();
        if (!json.success) throw new Error("Hesaplar yüklenemedi.");
        const accounts = json.data || [];
        
        if (accounts.length === 0) {
            Swal.fire('Hata', 'Ödeme alabilmek için öncelikle tanımlı bir kasa veya banka hesabı olmalıdır.', 'error');
            return;
        }
        
        let optionsHtml = '';
        accounts.forEach(acc => {
            const displayBal = new Intl.NumberFormat('tr-TR', { style: 'currency', currency: acc.doviz_turu }).format(acc.bakiye || 0);
            optionsHtml += `<option value="${acc.id}">${acc.ad} (${acc.doviz_turu}) - Bakiye: ${displayBal}</option>`;
        });
        
        const html = `
            <div style="text-align: left; font-family: 'Inter', sans-serif;">
                <div style="margin-bottom: 14px;">
                    <label style="font-weight: 600; font-size: 13px; color: var(--text-secondary); display: block; margin-bottom: 6px;">Tahsilat / Ödeme Yapılacak Hesap</label>
                    <select id="payHesapId" class="swal2-input" style="width: 100%; margin: 0; padding: 0 10px; height: 40px; font-size: 13px; border-radius: 6px;">
                        ${optionsHtml}
                    </select>
                </div>
                <div style="margin-bottom: 14px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div>
                        <label style="font-weight: 600; font-size: 13px; color: var(--text-secondary); display: block; margin-bottom: 6px;">Tutar (TRY)</label>
                        <input type="number" id="payTutar" class="swal2-input" style="width: 100%; margin: 0; height: 40px; font-size: 13px; border-radius: 6px;" value="${tutar}" step="0.01" min="0.01">
                    </div>
                    <div>
                        <label style="font-weight: 600; font-size: 13px; color: var(--text-secondary); display: block; margin-bottom: 6px;">Ödeme Tarihi</label>
                        <input type="date" id="payTarih" class="swal2-input" style="width: 100%; margin: 0; height: 40px; font-size: 13px; border-radius: 6px;" value="${new Date().toISOString().split('T')[0]}">
                    </div>
                </div>
                <div>
                    <label style="font-weight: 600; font-size: 13px; color: var(--text-secondary); display: block; margin-bottom: 6px;">İşlem Açıklaması</label>
                    <input type="text" id="payTanim" class="swal2-input" style="width: 100%; margin: 0; height: 40px; font-size: 13px; border-radius: 6px;" value="${belgeNo} Nolu Fatura Tahsilatı/Ödemesi">
                </div>
            </div>
        `;
        
        Swal.fire({
            title: 'Fatura Ödemesini İşle',
            html: html,
            icon: 'info',
            showCancelButton: true,
            confirmButtonText: 'Ödemeyi Onayla',
            cancelButtonText: 'Vazgeç',
            confirmButtonColor: '#10b981',
            preConfirm: () => {
                const hesapId = document.getElementById('payHesapId').value;
                const payTutar = document.getElementById('payTutar').value;
                const payTarih = document.getElementById('payTarih').value;
                const payTanim = document.getElementById('payTanim').value;
                
                if (!hesapId) {
                    Swal.showValidationMessage('Lütfen bir kasa/banka hesabı seçin.');
                    return false;
                }
                if (!payTutar || parseFloat(payTutar) <= 0) {
                    Swal.showValidationMessage('Geçerli bir ödeme tutarı girin.');
                    return false;
                }
                if (!payTarih) {
                    Swal.showValidationMessage('Ödeme tarihi boş olamaz.');
                    return false;
                }
                if (!payTanim.trim()) {
                    Swal.showValidationMessage('Açıklama alanı boş olamaz.');
                    return false;
                }
                
                return {
                    hesap_id: parseInt(hesapId),
                    tutar: parseFloat(payTutar),
                    tarih: payTarih,
                    tanim: payTanim
                };
            }
        }).then(async (result) => {
            if (result.isConfirmed) {
                const data = result.value;
                try {
                    const formData = new FormData();
                    formData.append('cari_id', cariId);
                    formData.append('fatura_id', faturaId);
                    formData.append('hesap_id', data.hesap_id);
                    formData.append('tutar', data.tutar);
                    formData.append('tarih', data.tarih);
                    formData.append('tanim', data.tanim);
                    formData.append('tip', tip);
                    
                    const res = await fetch('/api/fatura/ode', {
                        method: 'POST',
                        body: formData
                    });
                    const resJson = await res.json();
                    
                    if (resJson.success) {
                        Swal.fire('Başarılı', 'Ödeme işlemi başarıyla kaydedildi ve hesaplara yansıtıldı.', 'success');
                        if (typeof onComplete === 'function') onComplete();
                    } else {
                        Swal.fire('Hata', resJson.message || 'Ödeme sırasında hata oluştu.', 'error');
                    }
                } catch (e) {
                    Swal.fire('Hata', 'İşlem sunucuya iletilemedi.', 'error');
                }
            }
        });
        
    } catch (e) {
        Swal.fire('Hata', 'Kasa/Banka hesapları yüklenemedi.', 'error');
    }
}
