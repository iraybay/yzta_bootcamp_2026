let allBanka = [];

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
            fetchBankaList();
        }

        async function fetchBankaList() {
            const tbody = document.getElementById('bankaTableBody');
            try {
                const res = await fetch('/api/kasa-banka/hesaplar?tur=banka');
                if (!res.ok) throw new Error();
                const json = await res.json();
                
                allBanka = json.data;
                renderTable(allBanka);
                updateMetrics(allBanka);
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4" style="color: var(--danger-color);"><i class="fa-solid fa-triangle-exclamation"></i> Veriler yüklenemedi.</td></tr>`;
            }
        }

        function updateMetrics(list) {
            document.getElementById('totalBankaCount').textContent = list.length;
            const totalVal = list.reduce((sum, item) => sum + item.bakiye, 0);
            document.getElementById('totalBankaBalance').textContent = formatCurrency(totalVal, 'TRY');
            
            const creds = list.map(item => item.kredibilite || 'A');
            const bestCred = creds.includes('A+') ? 'A+' : (creds.includes('A') ? 'A' : (creds.includes('B') ? 'B' : '-'));
            document.getElementById('maxBankaKredibilite').textContent = bestCred;
        }

        function renderTable(list) {
            const tbody = document.getElementById('bankaTableBody');
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4">Kayıtlı banka hesabı bulunamadı.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = '';
            list.forEach(c => {
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
                    <td><strong>#${c.id}</strong></td>
                    <td><strong class="link-hover">${c.ad}</strong></td>
                    <td><strong>${c.sube || '-'}</strong></td>
                    <td>
                        <div style="font-size: 13px; font-weight: 600;">${c.hesap_no || '-'}</div>
                        <div class="iban-cell">${c.iban || '-'}</div>
                    </td>
                    <td>${kredBadge}</td>
                    <td class="${balClass}">${prefix}${formatCurrency(c.bakiye, c.doviz_turu)}</td>
                `;
                tr.onclick = () => { location.href = `/banka-detay/${c.id}`; };
                tbody.appendChild(tr);
            });
        }

        function filterBankaList() {
            const query = document.getElementById('searchBankaInput').value.toLowerCase().trim();
            const filtered = allBanka.filter(c => 
                c.ad.toLowerCase().includes(query) || 
                (c.sube && c.sube.toLowerCase().includes(query))
            );
            renderTable(filtered);
        }

        function showAddBankaModal() {
            Swal.fire({
                title: 'Yeni Banka Hesabı Ekle',
                html: `
                    <div style="text-align: left; font-size: 13px;">
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; font-weight: 600; margin-bottom: 4px;">Banka Tanımı / Adı *</label>
                            <input type="text" id="swalAd" class="swal2-input" style="width: 90%; margin: 0;" placeholder="Örn: Akbank Ticari">
                        </div>
                        <div style="margin-bottom: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Şube *</label>
                                <input type="text" id="swalSube" class="swal2-input" style="width: 85%; margin: 0;" placeholder="Örn: Maslak">
                            </div>
                            <div>
                                <label style="display: block; font-weight: 600; margin-bottom: 4px;">Para Birimi</label>
                                <select id="swalDoviz" class="swal2-input" style="width: 90%; margin: 0; padding: 0 10px; height: 44px; font-size: 13px;">
                                    <option value="TRY">TRY (₺)</option>
                                    <option value="USD">USD ($)</option>
                                    <option value="EUR">EUR (€)</option>
                                </select>
                            </div>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; font-weight: 600; margin-bottom: 4px;">Hesap No *</label>
                            <input type="text" id="swalHesapNo" class="swal2-input" style="width: 90%; margin: 0;" placeholder="Örn: 4480-129033">
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; font-weight: 600; margin-bottom: 4px;">IBAN *</label>
                            <input type="text" id="swalIban" class="swal2-input" style="width: 90%; margin: 0; font-family: monospace;" placeholder="TR...">
                        </div>
                        <div style="margin-bottom: 10px;">
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
                `,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Hesap Ekle',
                cancelButtonText: 'İptal',
                confirmButtonColor: '#0078d4',
                preConfirm: () => {
                    const ad = document.getElementById('swalAd').value;
                    const sube = document.getElementById('swalSube').value;
                    const doviz_turu = document.getElementById('swalDoviz').value;
                    const hesap_no = document.getElementById('swalHesapNo').value;
                    const iban = document.getElementById('swalIban').value;
                    const kredibilite = document.getElementById('swalKredibilite').value;
                    
                    if (!ad || !ad.trim()) {
                        Swal.showValidationMessage('Banka Adı alanı zorunludur.');
                        return false;
                    }
                    if (!sube || !sube.trim()) {
                        Swal.showValidationMessage('Şube alanı zorunludur.');
                        return false;
                    }
                    if (!hesap_no || !hesap_no.trim()) {
                        Swal.showValidationMessage('Hesap No alanı zorunludur.');
                        return false;
                    }
                    if (!iban || !iban.trim()) {
                        Swal.showValidationMessage('IBAN alanı zorunludur.');
                        return false;
                    }
                    return { ad, tur: 'banka', sube, doviz_turu, hesap_no, iban, kredibilite };
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
                            Swal.fire('Başarılı', 'Banka hesabı başarıyla eklendi.', 'success');
                            fetchBankaList();
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