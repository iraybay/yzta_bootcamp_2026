let allStok = [];
        let allHareketler = [];
        let allCariler = [];
        let currentTab = 'stoklar';

        function toggleTheme() {
            const body = document.body;
            const btn = document.getElementById('themeToggleBtn');
            if (body.classList.contains('dark-mode')) {
                body.classList.remove('dark-mode');
                body.classList.add('light-mode');
                if (btn) btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
                localStorage.setItem('theme', 'light');
            } else {
                body.classList.remove('light-mode');
                body.classList.add('dark-mode');
                if (btn) btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
                localStorage.setItem('theme', 'dark');
            }
        }

        async function fetchCariler() {
            try {
                const res = await fetch('/api/cari/tum-liste');
                const json = await res.json();
                allCariler = json.data || [];
            } catch(e){}
        }

        window.onload = async function() {
            const btn = document.getElementById('themeToggleBtn');
            if (document.body.classList.contains('dark-mode')) {
                if (btn) btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            } else {
                if (btn) btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
            }
            await fetchCariler();
            
            const params = new URLSearchParams(window.location.search);
            const isHareket = (params.get('tab') === 'hareketler');
            
            // Set page indicator dynamically
            const indicator = document.querySelector('.page-indicator');
            if (indicator) {
                if (isHareket) {
                    indicator.innerHTML = '<i class="fa-solid fa-truck-moving"></i> Stok Hareketleri';
                } else {
                    indicator.innerHTML = '<i class="fa-solid fa-boxes-stacked"></i> Stok Kartları';
                }
            }
            
            if (isHareket) {
                switchTab('hareketler');
            } else {
                await fetchStokList();
                if (params.get('action') === 'new') {
                    showAddStokModal();
                }
            }
            
            // Otomatik günlük stok raporu tetikleyici
            setTimeout(() => {
                const inputEl = document.getElementById('stokAiQuestionInput');
                if(inputEl) {
                    inputEl.value = "Sistemdeki kritik stokları listele ve bana günlük rapor olarak sun.";
                    askStokAi(true);
                }
            }, 800);
        }

        async function fetchStokList() {
            try {
                const res = await fetch('/api/stok/liste');
                const json = await res.json();
                allStok = json.data || [];
                updateMetrics();
                filterData();
            } catch(e) {
                console.error("Stok liste hatası", e);
            }
        }

        async function fetchHareketler() {
            try {
                const res = await fetch('/api/stok/hareketler');
                const json = await res.json();
                allHareketler = json.data || [];
                renderHareketler(allHareketler);
            } catch(e) {
                console.error("Hareketler liste hatası", e);
            }
        }

        function updateMetrics() {
            const elTotalProducts = document.getElementById('metricTotalProducts');
            if (elTotalProducts) elTotalProducts.textContent = allStok.length;
            
            const elTotalQty = document.getElementById('metricTotalQty');
            if (elTotalQty) {
                const totalQty = allStok.reduce((sum, item) => sum + (item.adet || 0), 0);
                elTotalQty.textContent = totalQty;
            }
            
            const elCritical = document.getElementById('metricCritical');
            if (elCritical) {
                const critical = allStok.filter(item => item.adet < 10).length;
                elCritical.textContent = critical;
            }
        }

        function switchTab(tab) {
            currentTab = tab;
            
            // Update tabs UI
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            const elTab = document.getElementById(`tab-${tab}`);
            if (elTab) elTab.classList.add('active');
            
            const btnYeni = document.getElementById('btnYeniStok');
            const btnSayim = document.getElementById('btnSayimFisi');
            const dateWrapper = document.getElementById('dateFilterWrapper');
            
            if (tab === 'hareketler') {
                if (btnYeni) btnYeni.style.display = 'none';
                if (btnSayim) btnSayim.style.display = 'inline-flex';
                if (dateWrapper) dateWrapper.style.display = 'flex';
                
                const dataTable = document.getElementById('dataTable');
                if (dataTable) dataTable.className = 'history-table';
                
                const elHeader = document.getElementById('tableHeader');
                if (elHeader) {
                    elHeader.innerHTML = `
                        <th>Tarih</th>
                        <th>Fiş No</th>
                        <th>Ürün</th>
                        <th>İşlem Tipi</th>
                        <th>Miktar</th>
                        <th>İrsaliye</th>
                        <th>Açıklama</th>
                    `;
                }
                fetchHareketler();
            } else {
                if (btnYeni) btnYeni.style.display = 'inline-flex';
                if (btnSayim) btnSayim.style.display = 'none';
                if (dateWrapper) dateWrapper.style.display = 'none';
                
                const dataTable = document.getElementById('dataTable');
                if (dataTable) dataTable.className = 'data-table';
                
                const elHeader = document.getElementById('tableHeader');
                if (elHeader) {
                    elHeader.innerHTML = `
                        <th>ID</th>
                        <th>Ürün Adı</th>
                        <th>Kategori</th>
                        <th>Stok Miktarı</th>
                        <th style="text-align: right;">İşlemler</th>
                    `;
                }
                filterData();
            }
        }

        function filterData() {
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            
            if (currentTab === 'hareketler') {
                const sDateVal = document.getElementById('startDate').value;
                const eDateVal = document.getElementById('endDate').value;
                const sDate = sDateVal ? new Date(sDateVal) : null;
                const eDate = eDateVal ? new Date(eDateVal) : null;
                
                let filtered = allHareketler.filter(item => {
                    // Text match
                    const matchText = 
                        (item.stok_ad && item.stok_ad.toLowerCase().includes(query)) ||
                        (item.fis_no && item.fis_no.toLowerCase().includes(query)) ||
                        (item.tip && item.tip.toLowerCase().includes(query)) ||
                        (item.irsaliye_no && item.irsaliye_no.toLowerCase().includes(query));
                        
                    // Date match
                    let matchDate = true;
                    if (sDate || eDate) {
                        const itemD = new Date(item.tarih);
                        if (sDate && itemD < sDate) matchDate = false;
                        if (eDate && itemD > eDate) matchDate = false;
                    }
                    
                    return matchText && matchDate;
                });
                renderHareketler(filtered);
                return;
            }
            
            let filtered = allStok.filter(item => {
                const matchesQuery = item.ad.toLowerCase().includes(query) || (item.kategori && item.kategori.toLowerCase().includes(query));
                const isCritical = item.adet < 10;
                
                if (currentTab === 'kritik') return matchesQuery && isCritical;
                return matchesQuery;
            });
            
            renderTable(filtered);
        }

        function renderTable(list) {
            const tbody = document.getElementById('tableBody');
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 30px;">Kayıt bulunamadı.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = '';
            list.forEach(item => {
                const tr = document.createElement('tr');
                const isCrit = item.adet < 10;
                const adetClass = isCrit ? 'stok-warning' : 'stok-ok';
                const warnIcon = isCrit ? '<i class="fa-solid fa-circle-exclamation" style="margin-left:6px;"></i>' : '';
                
                tr.innerHTML = `
                    <td><strong>#${item.id}</strong></td>
                    <td><strong style="color: var(--text-primary); font-size: 13px;">${item.ad}</strong></td>
                    <td><span class="badge-cat">${item.kategori || 'Genel'}</span></td>
                    <td><span class="${adetClass}" style="font-size:14px;">${item.adet}</span> ${warnIcon}</td>
                    <td style="text-align: right;">
                        <button class="action-btn-sm" onclick="editStok(${item.id})"><i class="fa-solid fa-pen"></i> Düzenle</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function renderHareketler(list) {
            const tbody = document.getElementById('tableBody');
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 30px;">Depo hareketi bulunamadı.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = '';
            list.forEach(item => {
                const tr = document.createElement('tr');
                
                // Color, sign, and text mapping for transaction type
                let typeText = '';
                let typeClass = '';
                let color = '';
                let sign = '';
                
                if (item.tip === 'giris') {
                    typeText = 'Giriş';
                    typeClass = 'tag-green';
                    color = 'var(--green-primary)';
                    sign = '+';
                } else if (item.tip === 'cikis') {
                    typeText = 'Çıkış';
                    typeClass = 'tag-orange';
                    color = 'var(--danger-color)';
                    sign = '-';
                } else if (item.tip === 'sayim_fazlasi') {
                    typeText = 'Sayım fazlası';
                    typeClass = 'tag-purple';
                    color = 'var(--green-primary)';
                    sign = '+';
                } else if (item.tip === 'fire') {
                    typeText = 'Fire';
                    typeClass = 'tag-blue';
                    color = 'var(--danger-color)';
                    sign = '-';
                } else {
                    typeText = item.tip;
                    typeClass = 'tag-gray';
                    color = 'var(--text-secondary)';
                    sign = '';
                }
                
                // Format date as DD.MM.YYYY
                let formattedDate = item.tarih;
                if (item.tarih) {
                    const parts = item.tarih.split('-');
                    if (parts.length === 3) {
                        formattedDate = `${parts[2]}.${parts[1]}.${parts[0]}`;
                    }
                }
                
                let irsaliyeDisplay = '-';
                if (item.irsaliye_id) {
                    irsaliyeDisplay = `<a href="/fatura-irsaliye?type=irsaliye" style="color: var(--primary-color); font-weight:700; text-decoration:none;"><i class="fa-solid fa-truck-fast" style="opacity:0.7; margin-right:4px;"></i>${item.irsaliye_no || 'Sevkiyat'}</a>`;
                }
                
                tr.innerHTML = `
                    <td><strong>${formattedDate}</strong></td>
                    <td><span style="font-family: monospace; color: var(--primary-color); font-weight:700;">${item.fis_no}</span></td>
                    <td><strong>${item.stok_ad}</strong></td>
                    <td><span class="tile-tag ${typeClass}" style="text-transform: none;">${typeText}</span></td>
                    <td><strong style="color: ${color}; font-size:14px;">${sign}${item.miktar}</strong></td>
                    <td>${irsaliyeDisplay}</td>
                    <td style="color: var(--text-secondary);">${item.aciklama || ''}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function showAddStokModal() {
            Swal.fire({
                title: 'Yeni Stok Kartı Ekle',
                html: `
                    <div style="text-align: left; font-size: 13px;">
                        <label style="display: block; margin-bottom: 4px; font-weight:600;">Ürün Adı *</label>
                        <input id="swalUrunAd" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;">
                        
                        <label style="display: block; margin-bottom: 4px; font-weight:600;">Kategori</label>
                        <input id="swalKategori" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;" placeholder="Örn: Hırdavat, Gıda, Elektronik">
                        
                        <label style="display: block; margin-bottom: 4px; font-weight:600;">Açılış Stok Miktarı</label>
                        <input id="swalAdet" type="number" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;" value="0">
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'Kaydet',
                cancelButtonText: 'İptal',
                preConfirm: () => {
                    return {
                        ad: document.getElementById('swalUrunAd').value,
                        kategori: document.getElementById('swalKategori').value,
                        adet: document.getElementById('swalAdet').value
                    }
                }
            }).then(async (res) => {
                if (res.isConfirmed && res.value.ad) {
                    try {
                        const response = await fetch('/api/stok/ekle', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(res.value)
                        });
                        const data = await response.json();
                        if (data.success) {
                            Swal.fire('Başarılı!', 'Ürün eklendi', 'success');
                            fetchStokList();
                        } else {
                            Swal.fire('Hata', data.message || 'Eklenemedi', 'error');
                        }
                    } catch(e) {
                        Swal.fire('Hata', 'Sunucu hatası', 'error');
                    }
                }
            });
        }

        function showSayimFisiModal() {
            let options = allStok.map(s => `<option value="${s.id}">${s.ad} (Mevcut: ${s.adet})</option>`).join('');
            
            Swal.fire({
                title: 'Depo Sayım / Düzeltme Fişi',
                html: `
                    <div style="text-align: left; font-size: 13px;">
                        <label style="display: block; margin-bottom: 4px; font-weight:600;">Ürün Seçin *</label>
                        <select id="swalStokId" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px; font-size:13px; padding:0 10px;">
                            ${options}
                        </select>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap:12px;">
                            <div>
                                <label style="display: block; margin-bottom: 4px; font-weight:600;">İşlem Tipi *</label>
                                <select id="swalTip" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px; font-size:13px; padding:0 10px;">
                                    <option value="sayim_fazlasi">Sayım fazlası (Stok artır)</option>
                                    <option value="fire">Fire / zayi (Stok düş)</option>
                                    <option value="giris">Manuel giriş</option>
                                    <option value="cikis">Manuel çıkış (Sevkiyat)</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 4px; font-weight:600;">Miktar *</label>
                                <input id="swalMiktar" type="number" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;" value="1">
                            </div>
                        </div>
                        
                        <div id="swalCariWrapper" style="display: none; margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 4px; font-weight:600;">İlişkili Cari (Müşteri) *</label>
                            <select id="swalCariId" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px; font-size:13px; padding:0 10px;">
                                ${allCariler.map(c => `<option value="${c.id}">${c.ad} (${c.tip === 'musteri' ? 'Müşteri' : 'Tedarikçi'})</option>`).join('')}
                            </select>
                        </div>
                        
                        <label style="display: block; margin-bottom: 4px; font-weight:600;">Açıklama</label>
                        <input id="swalAciklama" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;" placeholder="Örn: Yıl sonu sayım eksik/fazlası">
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'Fişi İşle',
                cancelButtonText: 'İptal',
                didOpen: () => {
                    const selectTip = document.getElementById('swalTip');
                    const cariWrapper = document.getElementById('swalCariWrapper');
                    
                    const toggleCari = () => {
                        if (selectTip.value === 'cikis') {
                            cariWrapper.style.display = 'block';
                        } else {
                            cariWrapper.style.display = 'none';
                        }
                    };
                    
                    selectTip.addEventListener('change', toggleCari);
                    toggleCari();
                },
                preConfirm: () => {
                    const tip = document.getElementById('swalTip').value;
                    return {
                        stok_id: document.getElementById('swalStokId').value,
                        tip: tip,
                        miktar: document.getElementById('swalMiktar').value,
                        aciklama: document.getElementById('swalAciklama').value,
                        cari_id: tip === 'cikis' ? document.getElementById('swalCariId').value : null
                    }
                }
            }).then(async (res) => {
                if (res.isConfirmed && res.value.stok_id && res.value.miktar) {
                    try {
                        const response = await fetch('/api/stok/hareket-ekle', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(res.value)
                        });
                        const data = await response.json();
                        if (data.success) {
                            Swal.fire('Başarılı!', 'Hareket işlendi ve stok güncellendi', 'success');
                            fetchStokList();
                            if (currentTab === 'hareketler') fetchHareketler();
                        } else {
                            Swal.fire('Hata', data.message || 'İşlenemedi', 'error');
                        }
                    } catch(e) {
                        Swal.fire('Hata', 'Sunucu hatası', 'error');
                    }
                }
            });
        }

        function editStok(id) {
            const stok = allStok.find(s => s.id === id);
            if (!stok) return;
            
            Swal.fire({
                title: 'Stok Kalemi Düzenle',
                html: `
                    <div style="text-align: left; font-size: 13px;">
                        <label style="display: block; margin-bottom: 4px; font-weight:600;">Ürün Adı *</label>
                        <input id="swalUrunAd" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;" value="${stok.ad}">
                        <label style="display: block; margin-bottom: 4px; font-weight:600;">Kategori</label>
                        <input id="swalKategori" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;" value="${stok.kategori}">
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'Kaydet',
                cancelButtonText: 'İptal',
                preConfirm: () => {
                    return {
                        id: stok.id,
                        ad: document.getElementById('swalUrunAd').value,
                        kategori: document.getElementById('swalKategori').value
                    }
                }
            }).then(async (res) => {
                if (res.isConfirmed && res.value.ad) {
                    try {
                        const response = await fetch('/api/stok/duzenle', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(res.value)
                        });
                        const data = await response.json();
                        if (data.success) {
                            Swal.fire('Başarılı!', 'Ürün güncellendi', 'success');
                            fetchStokList();
                        } else {
                            Swal.fire('Hata', data.message || 'Güncellenemedi', 'error');
                        }
                    } catch(e) {
                        Swal.fire('Hata', 'Sunucu hatası', 'error');
                    }
                }
            });
        }

        let stokAiChatHistory = [];
        
        async function askStokAi(isInitialReport = false) {
            const inputEl = document.getElementById('stokAiQuestionInput');
            const question = inputEl.value.trim();
            if (!question) return;
            
            inputEl.value = '';
            
            const historyContainer = document.getElementById('aiChatHistory');
            const reportContainer = document.getElementById('aiInsightReport');
            const reportContent = document.getElementById('aiInsightReportContent');
            const ratingDiv = document.getElementById('aiInsightRating');
            
            if (!isInitialReport) {
                historyContainer.style.display = 'block';
                // Append user question
                const userMsg = document.createElement('div');
                userMsg.className = 'ai-chat-msg user';
                userMsg.innerHTML = `<i class="fa-solid fa-user" style="opacity:0.7; font-size: 14px; margin-top:2px;"></i> <div style="flex:1;">${question}</div>`;
                historyContainer.appendChild(userMsg);
            } else {
                if (ratingDiv) ratingDiv.style.display = 'block';
            }
            
            // Append loading
            const loadingMsg = document.createElement('div');
            loadingMsg.className = 'ai-chat-msg ai loading';
            loadingMsg.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles fa-bounce" style="color:var(--primary-color); font-size: 14px; margin-top:2px;"></i> <div style="flex:1;">Analiz ediliyor, lütfen bekleyin...</div>`;
            
            if (!isInitialReport) {
                historyContainer.appendChild(loadingMsg);
                historyContainer.scrollTop = historyContainer.scrollHeight;
            }
            
            try {
                const response = await fetch('/api/ai/stok-sor', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        soru: question,
                        history: stokAiChatHistory
                    })
                });
                
                const data = await response.json();
                
                if (!isInitialReport) {
                    historyContainer.removeChild(loadingMsg);
                } else {
                    if (ratingDiv) ratingDiv.style.display = 'none';
                    document.getElementById('aiInsightsList').style.display = 'none';
                }
                
                if (data.success) {
                    stokAiChatHistory.push({"role": "user", "content": question});
                    stokAiChatHistory.push({"role": "model", "content": data.cevap});
                    
                    if (isInitialReport) {
                        reportContent.innerHTML = data.cevap.replace(/\n/g, '<br>');
                        reportContainer.style.display = 'block';
                    } else {
                        const aiMsg = document.createElement('div');
                        aiMsg.className = 'ai-chat-msg ai';
                        aiMsg.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles" style="color:var(--primary-color); font-size: 14px; margin-top:2px;"></i> <div style="flex:1; line-height:1.5;">${data.cevap.replace(/\n/g, '<br>')}</div>`;
                        historyContainer.appendChild(aiMsg);
                    }
                } else {
                    if (!isInitialReport) {
                        const errMsg = document.createElement('div');
                        errMsg.className = 'ai-chat-msg ai';
                        errMsg.style.color = '#ef4444';
                        errMsg.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div>Hata: ${data.message}</div>`;
                        historyContainer.appendChild(errMsg);
                    }
                }
                
                if (!isInitialReport) {
                    historyContainer.scrollTop = historyContainer.scrollHeight;
                }
            } catch (error) {
                if (historyContainer.contains(loadingMsg)) {
                    historyContainer.removeChild(loadingMsg);
                }
                const errMsg = document.createElement('div');
                errMsg.className = 'ai-chat-msg ai';
                errMsg.style.color = '#ef4444';
                errMsg.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div>Bağlantı hatası oluştu. Lütfen tekrar deneyin.</div>`;
                historyContainer.appendChild(errMsg);
            }
        }