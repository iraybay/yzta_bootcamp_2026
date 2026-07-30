let allFatura = [];
        let currentTab = 'tumu';
        let allCariler = [];

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
            await fetchCariler();
            await fetchFaturaList();
            
            const params = new URLSearchParams(window.location.search);
            
            if (params.get('type') === 'irsaliye') {
                document.getElementById('tab-tumu').style.display = 'none';
                document.getElementById('tab-satis').style.display = 'none';
                document.getElementById('tab-alis').style.display = 'none';
                document.getElementById('tab-irsaliye').style.display = 'inline-flex';
                
                // Update title & icon indicator dynamically
                const indicator = document.querySelector('.page-indicator');
                if (indicator) {
                    indicator.innerHTML = '<i class="fa-solid fa-truck-fast"></i> İrsaliye & Sevkiyat Takibi';
                }
                document.title = "İrsaliye & Sevkiyat Takibi - Bulutİş ERP";
                
                switchTab('irsaliye');
            } else {
                document.getElementById('tab-irsaliye').style.display = 'none';
                document.getElementById('tab-tumu').style.display = 'inline-flex';
                document.getElementById('tab-satis').style.display = 'inline-flex';
                document.getElementById('tab-alis').style.display = 'inline-flex';
                switchTab('tumu');
            }
            
            if (params.get('action') === 'new') {
                showAddFaturaModal();
            }
        }

        async function fetchCariler() {
            try {
                const res = await fetch('/api/cari/tum-liste');
                const json = await res.json();
                allCariler = json.data || [];
            } catch(e){}
        }

        async function fetchFaturaList() {
            const tbody = document.getElementById('faturaTableBody');
            const start = document.getElementById('startDate').value;
            const end = document.getElementById('endDate').value;
            
            try {
                const url = `/api/fatura/liste?start_date=${start}&end_date=${end}`;
                const res = await fetch(url);
                if (!res.ok) throw new Error();
                const json = await res.json();
                
                allFatura = json.data || [];
                updateMetrics(allFatura);
                filterData();
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4" style="color: var(--danger-color);"><i class="fa-solid fa-triangle-exclamation"></i> Veriler yüklenemedi.</td></tr>`;
            }
        }

        function updateMetrics(list) {
            document.getElementById('metricTotalCount').textContent = list.length;
            
            const totalVol = list.reduce((sum, item) => sum + (item.tutar || 0), 0);
            document.getElementById('metricTotalVolume').textContent = formatCurrency(totalVol);
            
            const unpaid = list.filter(item => item.durum === 'Ödenmedi').length;
            document.getElementById('metricUnpaidCount').textContent = unpaid;
            
            const irsaliyeCount = list.filter(item => item.belge_turu === 'irsaliye' || item.belge_turu === 'irsaliyeli_fatura').length;
            document.getElementById('metricIrsaliyeCount').textContent = irsaliyeCount;
        }

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`tab-${tab}`).classList.add('active');
            
            const btnYeniKayit = document.getElementById('btnYeniKayit');
            if (btnYeniKayit) {
                if (tab === 'tumu') {
                    btnYeniKayit.style.display = 'inline-flex';
                } else {
                    btnYeniKayit.style.display = 'none';
                }
            }
            
            // Dinamik Durum Filtresi Güncelleme
            const durumFilter = document.getElementById('durumFilter');
            const currentFilterVal = durumFilter.value;
            
            if (tab === 'irsaliye') {
                durumFilter.innerHTML = `
                    <option value="tumu">Tüm Durumlar</option>
                    <option value="Bekliyor">Bekliyor (Yolda)</option>
                    <option value="Teslim Edildi">Teslim Edildi</option>
                `;
            } else {
                durumFilter.innerHTML = `
                    <option value="tumu">Tüm Durumlar</option>
                    <option value="Ödendi">Ödendi</option>
                    <option value="Ödenmedi">Ödenmedi</option>
                    <option value="Bekliyor">Bekliyor (Yolda)</option>
                    <option value="Teslim Edildi">Teslim Edildi</option>
                `;
            }
            
            // Eski seçili filtreyi korumaya çalış (eğer yeni listede varsa)
            let exists = Array.from(durumFilter.options).some(opt => opt.value === currentFilterVal);
            if (exists) {
                durumFilter.value = currentFilterVal;
            } else {
                durumFilter.value = 'tumu';
            }
            
            filterData();
        }

        function filterData() {
            const query = document.getElementById('searchFaturaInput').value.toLowerCase().trim();
            const durumVal = document.getElementById('durumFilter').value;
            const params = new URLSearchParams(window.location.search);
            const isIrsaliyeMode = params.get('type') === 'irsaliye';
            
            let filtered = allFatura.filter(item => {
                const matchesQuery = item.tanim.toLowerCase().includes(query);
                const matchesDurum = (durumVal === 'tumu') || (item.durum === durumVal);
                
                // Segregate Waybills (irsaliye) from Invoices (fatura) based on active view mode
                const isWaybill = (item.belge_turu === 'irsaliye' || item.belge_turu === 'irsaliyeli_fatura');
                const matchesMode = isIrsaliyeMode ? isWaybill : !isWaybill;
                
                let matchesTab = true;
                if (currentTab === 'satis') matchesTab = (item.belge_turu === 'satis' || item.belge_turu === 'satis_faturasi');
                else if (currentTab === 'alis') matchesTab = (item.belge_turu === 'alis' || item.belge_turu === 'alis_faturasi');
                else if (currentTab === 'irsaliye') matchesTab = isWaybill;
                
                return matchesQuery && matchesDurum && matchesMode && matchesTab;
            });
            
            renderTable(filtered);
        }

        function renderTable(list) {
            const tbody = document.getElementById('faturaTableBody');
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4">Kriterlere uygun fatura veya irsaliye kaydı bulunamadı.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = '';
            list.forEach(item => {
                const tr = document.createElement('tr');
                
                // Type Badge
                let typeBadge = '';
                if (item.belge_turu === 'satis' || item.belge_turu === 'satis_faturasi') {
                    typeBadge = `<span class="badge-type bg-satis"><i class="fa-solid fa-file-arrow-up"></i> Satış Faturası</span>`;
                } else if (item.belge_turu === 'alis' || item.belge_turu === 'alis_faturasi') {
                    typeBadge = `<span class="badge-type bg-alis"><i class="fa-solid fa-file-arrow-down"></i> Alış Faturası</span>`;
                } else if (item.belge_turu === 'irsaliye') {
                    typeBadge = `<span class="badge-type bg-irsaliye"><i class="fa-solid fa-truck-fast"></i> Sevk İrsaliyesi</span>`;
                } else {
                    typeBadge = `<span class="badge-type bg-irsaliyeli"><i class="fa-solid fa-receipt"></i> İrsaliyeli Fatura</span>`;
                }
                
                // Status Badge
                let stBadge = '';
                if (item.durum === 'Ödendi') {
                    stBadge = `<span class="badge-status st-odendi"><i class="fa-solid fa-check"></i> Ödendi</span>`;
                } else if (item.durum === 'Ödenmedi') {
                    stBadge = `<span class="badge-status st-odenmedi"><i class="fa-solid fa-clock"></i> Ödenmedi</span>`;
                } else if (item.durum === 'Teslim Edildi') {
                    stBadge = `<span class="badge-status st-teslim"><i class="fa-solid fa-box-check"></i> Teslim Edildi</span>`;
                } else {
                    stBadge = `<span class="badge-status st-bekliyor"><i class="fa-solid fa-hourglass-half"></i> Bekliyor / Yolda</span>`;
                }
                
                // Date formatting
                const dParts = item.tarih.split('-');
                const fmtDate = dParts.length === 3 ? `${dParts[2]}.${dParts[1]}.${dParts[0]}` : item.tarih;
                
                // Format Amount
                const tutarDisplay = item.tutar > 0 ? formatCurrency(item.tutar) : '<span style="color: var(--text-light); font-size: 11px;">(Tutar Yok)</span>';
                
                // Action options
                let toggleActionText = item.durum === 'Ödendi' ? 'Ödenmedi İşaretle' : (item.belge_turu === 'irsaliye' ? 'Teslim Edildi Yap' : 'Ödendi İşaretle');
                let nextStatus = item.durum === 'Ödendi' ? 'Ödenmedi' : (item.belge_turu === 'irsaliye' ? 'Teslim Edildi' : 'Ödendi');

                let unvanDisplay = item.cari_ad || 'Genel Cari';
                if (item.cari_id) {
                    unvanDisplay = `<a href="/cari-detay/${item.cari_id}" style="color: var(--primary-color); text-decoration: none;" class="link-hover">${unvanDisplay}</a>`;
                }

                let actionBtnHtml = '';
                if (item.durum === 'Ödenmedi' && item.belge_turu !== 'irsaliye') {
                    const payTip = (item.belge_turu === 'satis' || item.belge_turu === 'satis_faturasi') ? 'gelir' : 'gider';
                    actionBtnHtml = `<button class="action-btn-sm" onclick="showInvoicePaymentPopup(${item.id}, ${item.cari_id}, '${item.belge_no || 'FT-' + item.id}', ${item.tutar}, '${payTip}', () => { fetchFaturaList(); })">Ödeme Yap</button>`;
                } else {
                    actionBtnHtml = `<button class="action-btn-sm" onclick="changeStatus(${item.id}, '${nextStatus}')">${toggleActionText}</button>`;
                }

                tr.innerHTML = `
                    <td><strong>#${item.id}</strong></td>
                    <td><span style="font-family: monospace; font-size: 12px; font-weight: 700; color: var(--primary-color);">${item.belge_no || ('FT-' + item.id)}</span></td>
                    <td><strong style="color: var(--text-primary); font-size: 13px;">${unvanDisplay}</strong></td>
                    <td>${typeBadge}</td>
                    <td><span style="font-size: 12px; color: var(--text-secondary);">${item.aciklama || item.tanim}</span></td>
                    <td><i class="fa-regular fa-calendar" style="opacity: 0.6; margin-right: 4px;"></i>${fmtDate}</td>
                    <td>${stBadge}</td>
                    <td><strong>${tutarDisplay}</strong></td>
                    <td style="text-align: right; white-space: nowrap;">
                        ${actionBtnHtml}
                        <button class="action-btn-del" onclick="deleteRecord(${item.id})"><i class="fa-solid fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function changeStatus(id, newStatus) {
            try {
                const res = await fetch(`/api/fatura/durum-guncelle/${id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ durum: newStatus })
                });
                const json = await res.json();
                if (json.success) {
                    Swal.fire({ icon: 'success', title: 'Güncellendi', text: json.message, timer: 1200, showConfirmButton: false });
                    fetchFaturaList();
                } else {
                    Swal.fire('Hata', json.message || 'Hata oluştu', 'error');
                }
            } catch(e) {
                Swal.fire('Hata', 'Sunucu hatası', 'error');
            }
        }

        async function deleteRecord(id) {
            const confirm = await Swal.fire({
                title: 'Emin misiniz?',
                text: "Bu belge kaydı kalıcı olarak silinecek!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#ef4444',
                confirmButtonText: 'Evet, Sil',
                cancelButtonText: 'İptal'
            });
            if (confirm.isConfirmed) {
                try {
                    const res = await fetch(`/api/fatura/sil/${id}`, { method: 'DELETE' });
                    const json = await res.json();
                    if (json.success) {
                        Swal.fire({ icon: 'success', title: 'Silindi', text: json.message, timer: 1200, showConfirmButton: false });
                        fetchFaturaList();
                    }
                } catch(e) {
                    Swal.fire('Hata', 'Silme başarısız', 'error');
                }
            }
        }

        function showAddFaturaModal() {
            let cariOptionsHtml = `<option value="">-- Cari Ünvan Seçiniz --</option>` + allCariler.map(c => {
                const name = c.ad || c.unvan || '';
                return `<option value="${c.id}">${name}</option>`;
            }).join('');

            if (allCariler.length === 0) {
                cariOptionsHtml = `<option value="">-- Kayıtlı Cari Bulunamadı --</option>`;
            }

            Swal.fire({
                title: 'Yeni Fatura / İrsaliye Kaydı',
                width: '680px',
                html: `
                    <div style="text-align: left; font-size: 13px; max-height: 70vh; overflow-y: auto; padding-right: 6px; overflow-x: hidden;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Belge İşlem Tipi *</label>
                                <select id="swalTip" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; padding: 0 10px; height: 40px; font-size: 13px;">
                                    <option value="satis">Satış Faturası (Gelir)</option>
                                    <option value="alis">Alış Faturası (Gider)</option>
                                    <option value="irsaliye">Sevk İrsaliyesi</option>
                                    <option value="irsaliyeli_fatura">İrsaliyeli Fatura</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Fatura / İrsaliye Seri & No</label>
                                <input type="text" id="swalBelgeNo" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px;" placeholder="Örn: FT-2026-000101">
                            </div>
                        </div>

                        <div style="margin-bottom: 12px;">
                            <label style="display: block; font-weight: 600; margin-bottom: 4px;">Cari Ünvan / Firma (Cari Listesinden) *</label>
                            <select id="swalUnvan" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; padding: 0 10px; height: 40px; font-size: 13px;" onchange="onCariSelectChange(this.value)" required>
                                ${cariOptionsHtml}
                            </select>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Vergi Dairesi</label>
                                <input type="text" id="swalVergiDairesi" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px;" placeholder="Örn: Maslak V.D.">
                            </div>
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Vergi No / TCKN</label>
                                <input type="text" id="swalVergiNo" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px;" placeholder="Örn: 9876543210">
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">E-posta Adresi</label>
                                <input type="email" id="swalEposta" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px;" placeholder="fatura@firma.com">
                            </div>
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Telefon</label>
                                <input type="text" id="swalTelefon" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px;" placeholder="0532 000 00 00">
                            </div>
                        </div>

                        <div style="margin-bottom: 12px;">
                            <label style="display: block; font-weight: 600; margin-bottom: 4px;">Teslimat / Fatura Adresi</label>
                            <input type="text" id="swalAdres" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px;" placeholder="İl, ilçe, cadde, mahalle...">
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Belge Tarihi</label>
                                <input type="date" id="swalTarih" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; padding: 0 10px; height: 40px; font-size: 13px;" value="2026-07-24">
                            </div>
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">İşlem / Ödeme Durumu</label>
                                <select id="swalDurum" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; padding: 0 10px; height: 40px; font-size: 13px;">
                                    <option value="Ödenmedi" selected>Ödenmedi</option>
                                    <option value="Ödendi">Ödendi</option>
                                    <option value="Bekliyor">Bekliyor (Yolda)</option>
                                    <option value="Teslim Edildi">Teslim Edildi</option>
                                </select>
                            </div>
                        </div>

                        <div style="margin-bottom: 12px;">
                            <label style="display: block; font-weight: 600; margin-bottom: 4px;">Mal / Hizmet Kalem Açıklaması</label>
                            <input type="text" id="swalAciklama" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px;" placeholder="Örn: 30 Gün Vadeli Donanım Teslimatı">
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Matrah Tutar (₺)</label>
                                <input type="number" step="0.01" id="swalMatrah" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px;" placeholder="1000.00" oninput="calcSwalTutar()">
                            </div>
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">KDV Oranı</label>
                                <select id="swalKdv" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; padding: 0 10px; height: 40px; font-size: 13px;" onchange="calcSwalTutar()">
                                    <option value="20" selected>%20 KDV</option>
                                    <option value="10">%10 KDV</option>
                                    <option value="1">%1 KDV</option>
                                    <option value="0">%0 (Muaf)</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Genel Toplam (₺)</label>
                                <input type="number" step="0.01" id="swalToplam" class="swal2-input" style="width: 100%; box-sizing: border-box; margin: 0; height: 40px; font-weight: 700; color: #0078d4;" placeholder="1200.00" readonly>
                            </div>
                        </div>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: 'Kayıt Oluştur',
                cancelButtonText: 'İptal',
                confirmButtonColor: '#0078d4',
                didOpen: () => {
                    window.calcSwalTutar = function() {
                        const matrah = parseFloat(document.getElementById('swalMatrah')?.value || 0);
                        const kdv = parseFloat(document.getElementById('swalKdv')?.value || 20);
                        const toplam = matrah + (matrah * kdv / 100);
                        const toplamEl = document.getElementById('swalToplam');
                        if (toplamEl) toplamEl.value = toplam.toFixed(2);
                    };

                    window.onCariSelectChange = function(selectedId) {
                        if (!selectedId) return;
                        const match = allCariler.find(c => (c.id == selectedId));
                        if (match) {
                            if (document.getElementById('swalVergiDairesi')) document.getElementById('swalVergiDairesi').value = match.vergi_dairesi || '';
                            if (document.getElementById('swalVergiNo')) document.getElementById('swalVergiNo').value = match.vergi_no || '';
                            if (document.getElementById('swalEposta')) document.getElementById('swalEposta').value = match.eposta || '';
                            if (document.getElementById('swalTelefon')) document.getElementById('swalTelefon').value = match.telefon || '';
                            
                            const fullAddr = [match.mahalle, match.adres_detay, match.ilce, match.il].filter(Boolean).join(' ');
                            if (document.getElementById('swalAdres')) document.getElementById('swalAdres').value = fullAddr || '';
                        }
                    };
                },
                preConfirm: () => {
                    const tip = document.getElementById('swalTip').value;
                    const cariSelect = document.getElementById('swalUnvan');
                    const cari_id = cariSelect.value;
                    const unvan = cariSelect.options[cariSelect.selectedIndex].text;
                    const belgeNo = document.getElementById('swalBelgeNo').value;
                    const matrah = parseFloat(document.getElementById('swalMatrah').value || 0);
                    const kdv = parseFloat(document.getElementById('swalKdv').value || 20);
                    const tutar = matrah + (matrah * kdv / 100);
                    const tarih = document.getElementById('swalTarih').value;
                    const durum = document.getElementById('swalDurum').value;
                    const aciklama = document.getElementById('swalAciklama').value;

                    if (!cari_id || cari_id.trim() === '') {
                        Swal.showValidationMessage('Cari Seçimi zorunludur.');
                        return false;
                    }
                    if (tip !== 'irsaliye' && matrah <= 0) {
                        Swal.showValidationMessage('Faturalar için tutar girilmesi zorunludur.');
                        return false;
                    }
                    return { tip, cari_id, unvan, belge_no: belgeNo, tutar, tarih, durum, aciklama };
                }
            }).then(async (result) => {
                if (result.isConfirmed) {
                    try {
                        const res = await fetch('/api/fatura/ekle', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(result.value)
                        });
                        const data = await res.json();
                        if (data.success) {
                            Swal.fire('Başarılı', data.message, 'success');
                            fetchFaturaList();
                        } else {
                            Swal.fire('Hata', data.message || 'Bir hata oluştu.', 'error');
                        }
                    } catch (err) {
                        Swal.fire('Hata', 'Sunucu ile iletişim kurulamadı.', 'error');
                    }
                }
            });
        }

        function formatCurrency(val) {
            return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(val);
        }

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