let allKasa = [];

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

        window.onload = function() {
            const btn = document.getElementById('themeToggleBtn');
            if (document.body.classList.contains('dark-mode')) {
                if (btn) btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            } else {
                if (btn) btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
            }
            fetchKasaList();
        }

        async function fetchKasaList() {
            const tbody = document.getElementById('kasaTableBody');
            try {
                const res = await fetch('/api/kasa-banka/hesaplar?tur=kasa');
                if (!res.ok) throw new Error();
                const json = await res.json();
                
                allKasa = json.data;
                renderTable(allKasa);
                updateMetrics(allKasa);
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4" style="color: var(--danger-color);"><i class="fa-solid fa-triangle-exclamation"></i> Veriler yüklenemedi.</td></tr>`;
            }
        }

        function updateMetrics(list) {
            document.getElementById('totalKasaCount').textContent = list.length;
            const totalVal = list.reduce((sum, item) => sum + item.bakiye, 0);
            document.getElementById('totalKasaBalance').textContent = formatCurrency(totalVal, 'TRY');
            
            const creds = list.map(item => item.kredibilite || 'A');
            const bestCred = creds.includes('A+') ? 'A+' : (creds.includes('A') ? 'A' : (creds.includes('B') ? 'B' : '-'));
            document.getElementById('maxKasaKredibilite').textContent = bestCred;
        }

        function renderTable(list) {
            const tbody = document.getElementById('kasaTableBody');
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4">Kayıtlı kasa hesabı bulunamadı.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = '';
            list.forEach((c, idx) => {
                const tr = document.createElement('tr');
                const isPositive = c.bakiye >= 0;
                const balClass = isPositive ? 'bal-positive' : 'bal-negative';
                const prefix = isPositive ? '+' : '';
                
                const k = c.kredibilite || 'A';
                let kredBadge = '';
                if (k === 'A+') {
                    kredBadge = `<span class="badge-type" style="background: rgba(16, 185, 129, 0.12); color: var(--success-color); border: 1px solid rgba(16, 185, 129, 0.2);">${k}</span>`;
                } else if (k === 'A') {
                    kredBadge = `<span class="badge-type" style="background: rgba(0, 120, 212, 0.12); color: var(--primary-color); border: 1px solid rgba(0, 120, 212, 0.2);">${k}</span>`;
                } else if (k === 'B') {
                    kredBadge = `<span class="badge-type" style="background: rgba(245, 158, 11, 0.12); color: var(--warning-color); border: 1px solid rgba(245, 158, 11, 0.2);">${k}</span>`;
                } else {
                    kredBadge = `<span class="badge-type" style="background: rgba(239, 68, 68, 0.12); color: var(--danger-color); border: 1px solid rgba(239, 68, 68, 0.2);">${k}</span>`;
                }
                
                tr.innerHTML = `
                    <td><strong>#${idx + 1}</strong></td>
                    <td><strong class="link-hover">${c.ad}</strong></td>
                    <td><span class="badge-type bg-kasa">Kasa Tipi</span></td>
                    <td><strong>${c.doviz_turu || 'TRY'}</strong></td>
                    <td>${kredBadge}</td>
                    <td class="${balClass}">${prefix}${formatCurrency(c.bakiye, c.doviz_turu)}</td>
                `;
                tr.onclick = () => { location.href = `/kasa-detay/${c.id}`; };
                tbody.appendChild(tr);
            });
        }

        function filterKasaList() {
            const query = document.getElementById('searchKasaInput').value.toLowerCase().trim();
            const filtered = allKasa.filter(c => c.ad.toLowerCase().includes(query));
            renderTable(filtered);
        }

        function showAddKasaModal() {
            Swal.fire({
                title: 'Yeni Kasa Tanımla',
                html: `
                    <div style="text-align: left; font-size: 13px;">
                        <div style="margin-bottom: 12px;">
                            <label style="display: block; font-weight: 600; margin-bottom: 4px;">Kasa Tanımı / Adı *</label>
                            <input type="text" id="swalAd" class="swal2-input" style="width: 90%; margin: 0;" placeholder="Örn: Merkez Kasa">
                        </div>
                        <div style="margin-bottom: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Para Birimi</label>
                                <select id="swalDoviz" class="swal2-input" style="width: 90%; margin: 0; padding: 0 10px; height: 44px; font-size: 13px;">
                                    <option value="TRY">TRY (₺)</option>
                                    <option value="USD">USD ($)</option>
                                    <option value="EUR">EUR (€)</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Kredibilite</label>
                                <select id="swalKredibilite" class="swal2-input" style="width: 90%; margin: 0; padding: 0 10px; height: 44px; font-size: 13px;">
                                    <option value="A+">A+</option>
                                    <option value="A" selected>A</option>
                                    <option value="B">B</option>
                                    <option value="C">C</option>
                                    <option value="D">D</option>
                                </select>
                            </div>
                        </div>
                    </div>
                `,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Kasa Tanımla',
                cancelButtonText: 'İptal',
                confirmButtonColor: '#0078d4',
                preConfirm: () => {
                    const ad = document.getElementById('swalAd').value;
                    const doviz_turu = document.getElementById('swalDoviz').value;
                    const kredibilite = document.getElementById('swalKredibilite').value;
                    
                    if (!ad || !ad.trim()) {
                        Swal.showValidationMessage('Kasa Adı alanı zorunludur.');
                        return false;
                    }
                    return { ad, tur: 'kasa', doviz_turu, kredibilite };
                }
            }).then(async (result) => {
                if (result.isConfirmed) {
                    try {
                        const res = await fetch('/api/kasa-banka/hesap-ekle', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(result.value)
                        });
                        const data = await res.json();
                        if (data.success) {
                            Swal.fire('Başarılı', 'Kasa hesabı başarıyla tanımlandı.', 'success');
                            fetchKasaList();
                        } else {
                            Swal.fire('Hata', data.message || 'Bir hata oluştu.', 'error');
                        }
                    } catch (err) {
                        Swal.fire('Hata', 'Sunucu ile iletişim kurulamadı.', 'error');
                    }
                }
            });
        }

        function formatCurrency(val, currency = 'TRY') {
            return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: currency }).format(val);
        }