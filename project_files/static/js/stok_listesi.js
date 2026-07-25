let allStok = [];
        let allHareketler = [];
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

        window.onload = async function() {
            const btn = document.getElementById('themeToggleBtn');
            if (document.body.classList.contains('dark-mode')) {
                if (btn) btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            } else {
                if (btn) btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
            }
            
            await fetchStokList();
            
            const params = new URLSearchParams(window.location.search);
            if (params.get('action') === 'new') {
                showAddStokModal();
            } else if (params.get('tab') === 'hareketler') {
                switchTab('hareketler');
            }
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
            document.getElementById('metricTotalProducts').textContent = allStok.length;
            const totalQty = allStok.reduce((sum, item) => sum + (item.adet || 0), 0);
            document.getElementById('metricTotalQty').textContent = totalQty;
            const critical = allStok.filter(item => item.adet < 10).length;
            document.getElementById('metricCritical').textContent = critical;
        }

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`tab-${tab}`).classList.add('active');
            
            const btnYeni = document.getElementById('btnYeniStok');
            const btnSayim = document.getElementById('btnSayimFisi');
            
            if (tab === 'hareketler') {
                btnYeni.style.display = 'none';
                btnSayim.style.display = 'inline-flex';
                document.getElementById('tableHeader').innerHTML = `
                    <th>Tarih</th>
                    <th>Fiş No</th>
                    <th>Ürün</th>
                    <th>İşlem Tipi</th>
                    <th>Miktar</th>
                    <th>Açıklama</th>
                `;
                fetchHareketler();
            } else {
                btnYeni.style.display = 'inline-flex';
                btnSayim.style.display = 'none';
                document.getElementById('tableHeader').innerHTML = `
                    <th>ID</th>
                    <th>Ürün Adı</th>
                    <th>Kategori</th>
                    <th>Stok Miktarı</th>
                    <th style="text-align: right;">İşlemler</th>
                `;
                filterData();
            }
        }

        function filterData() {
            if (currentTab === 'hareketler') return; 
            
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            
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
                let color = item.tip === 'giris' || item.tip === 'sayim_fazlasi' ? 'var(--green-primary)' : 'var(--danger-color)';
                let sign = item.tip === 'giris' || item.tip === 'sayim_fazlasi' ? '+' : '-';
                
                tr.innerHTML = `
                    <td>${item.tarih}</td>
                    <td><span style="font-family: monospace; color: var(--primary-color); font-weight:700;">${item.fis_no}</span></td>
                    <td><strong>${item.stok_ad}</strong></td>
                    <td>${item.tip.toUpperCase()}</td>
                    <td><strong style="color: ${color}; font-size:14px;">${sign}${item.miktar}</strong></td>
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
                                    <option value="sayim_fazlasi">Sayım Fazlası (Stok Artır)</option>
                                    <option value="fire">Fire / Zayi (Stok Düş)</option>
                                    <option value="giris">Manuel Giriş</option>
                                    <option value="cikis">Manuel Çıkış</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 4px; font-weight:600;">Miktar *</label>
                                <input id="swalMiktar" type="number" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;" value="1">
                            </div>
                        </div>
                        
                        <label style="display: block; margin-bottom: 4px; font-weight:600;">Açıklama</label>
                        <input id="swalAciklama" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0 0 12px 0; height: 40px;" placeholder="Örn: Yıl sonu sayım eksik/fazlası">
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'Fişi İşle',
                cancelButtonText: 'İptal',
                preConfirm: () => {
                    return {
                        stok_id: document.getElementById('swalStokId').value,
                        tip: document.getElementById('swalTip').value,
                        miktar: document.getElementById('swalMiktar').value,
                        aciklama: document.getElementById('swalAciklama').value
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