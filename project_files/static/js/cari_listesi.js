let allCariler = [];

        // Check if dark mode is active from localStorage
        if (localStorage.getItem('theme') !== 'light') {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        } else {
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
        }

        // Fetch data on load
        window.addEventListener('DOMContentLoaded', async () => {
            await fetchMetrics();
            await fetchCariList();
        });

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/dashboard');
                if (!res.ok) throw new Error();
                const data = await res.json();
                
                document.getElementById('totalMusteri').textContent = data.cari.musteri_sayisi;
                document.getElementById('totalTedarikci').textContent = data.cari.tedarikci_sayisi;
                
                const net = data.cari.toplam_alacak - data.cari.toplam_borc;
                const netEl = document.getElementById('netDenge');
                netEl.textContent = formatCurrency(net);
                if (net >= 0) {
                    netEl.className = 'value bal-positive';
                } else {
                    netEl.className = 'value bal-negative';
                }
            } catch (err) {
                console.error("Metrikler yüklenirken hata oluştu:", err);
            }
        }

        async function fetchCariList() {
            const tbody = document.getElementById('cariTableBody');
            try {
                const res = await fetch('/api/cari/tum-liste');
                if (!res.ok) throw new Error();
                const json = await res.json();
                
                allCariler = json.data;
                renderTable(allCariler);
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4" style="color: var(--danger-color);"><i class="fa-solid fa-triangle-exclamation"></i> Veriler yüklenemedi.</td></tr>`;
            }
        }

        function renderTable(list) {
            const tbody = document.getElementById('cariTableBody');
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4">Kayıtlı cari bulunamadı.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = '';
            list.forEach(c => {
                const tr = document.createElement('tr');
                const isMusteri = c.tip === 'musteri';
                const typeLabel = isMusteri ? 'Müşteri' : 'Tedarikçi';
                const typeClass = isMusteri ? 'bg-musteri' : 'bg-tedarikci';
                const balClass = isMusteri ? 'bal-positive' : 'bal-negative';
                const prefix = isMusteri ? '+' : '-';
                
                // Determine credibility styling
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
                
                const balVal = c.bakiye || 0;
                // If it is musteri (customer), alacak is positive bakiye. If tedarikci (supplier), borc is negative bakiye.
                // In SAP terms, positive balance = G (Gelir/Receivable), negative balance = B (Borç/Payable)
                const isPositive = balVal >= 0;
                const indicator = isPositive ? 'G' : 'B';
                const indicatorColor = isPositive ? 'var(--green-primary)' : 'var(--danger-color)';
                const formattedBakiyeText = `${formatCurrency(Math.abs(balVal))} <span style="font-weight:800; color:${indicatorColor}; font-size:11px; margin-left:4px;">${indicator}</span>`;
                
                tr.innerHTML = `
                    <td><strong>#${c.id}</strong></td>
                    <td><a href="/cari-detay/${c.id}" class="link-hover" style="color: var(--primary-color); text-decoration: none; font-weight: 700;">${c.ad}</a></td>
                    <td><span class="badge-type ${typeClass}">${typeLabel}</span></td>
                    <td>${kredBadge}</td>
                    <td>${c.yetkili_kisi || '-'}</td>
                    <td>${c.telefon || '-'}</td>
                    <td style="font-weight: 700;">${formattedBakiyeText}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function filterCariList() {
            const query = document.getElementById('searchCariInput').value.toLowerCase().trim();
            const typeFilter = document.getElementById('filterCariType').value;
            
            const filtered = allCariler.filter(c => {
                const nameMatch = c.ad.toLowerCase().startsWith(query);
                const yetkiliMatch = c.yetkili_kisi && c.yetkili_kisi.toLowerCase().startsWith(query);
                const matchesSearch = nameMatch || yetkiliMatch;
                
                const matchesType = typeFilter === 'all' || c.tip === typeFilter;
                return matchesSearch && matchesType;
            });
            
            // Sort by ID ASC
            filtered.sort((a, b) => a.id - b.id);
            
            renderTable(filtered);
        }

        function showCariDetail(id) {
            const c = allCariler.find(item => item.id === id);
            if (!c) return;
            
            const isMusteri = c.tip === 'musteri';
            const typeLabel = isMusteri ? 'Müşteri' : 'Tedarikçi';
            
            // Construct full address representation
            let fullAddress = '';
            if (c.mahalle || c.ilce || c.il) {
                fullAddress += `${c.mahalle || ''} ${c.ilce || ''} / ${c.il || ''}`.trim();
            }
            if (c.adres_detay) {
                fullAddress += (fullAddress ? ', ' : '') + c.adres_detay;
            }
            if (!fullAddress) fullAddress = '-';
            
            Swal.fire({
                title: `Cari Hesap Detay Kartı`,
                html: `
                    <div style="text-align: left; font-size: 13px; line-height: 1.8; color: var(--text-primary);">
                        <p style="border-bottom: 1px solid var(--border-color); padding-bottom: 6px; margin-bottom: 8px; font-size: 14px;">
                            <strong>Cari Ünvanı:</strong> ${c.ad}
                        </p>
                        <p><strong>Cari Tipi:</strong> ${typeLabel}</p>
                        <p><strong>Cari Grubu / Sektör:</strong> ${c.cari_grubu || '-'}</p>
                        <p><strong>Vergi No / TC Kimlik:</strong> ${c.vergi_no || '-'}</p>
                        <p><strong>Vergi Dairesi:</strong> ${c.vergi_dairesi || '-'}</p>
                        <p><strong>Yetkili Kişi:</strong> ${c.yetkili_kisi || '-'}</p>
                        <p><strong>E-Posta Adresi:</strong> ${c.eposta || '-'}</p>
                        <p><strong>Telefon Numarası:</strong> ${c.telefon || '-'}</p>
                        <p><strong>Açık Adres:</strong> ${fullAddress}</p>
                        <p style="border-top: 1px solid var(--border-color); padding-top: 8px; margin-top: 8px; font-size: 14px;">
                            <strong>Devir Bakiyesi / Limit:</strong> 
                            <span style="font-weight: bold; color: ${isMusteri ? 'var(--green-primary)' : 'var(--danger-color)'}">
                                ${isMusteri ? '+' : '-'}${formatCurrency(c.limit_val)}
                            </span>
                        </p>
                    </div>
                `,
                icon: 'info',
                confirmButtonColor: '#0078d4'
            });
        }

        function formatCurrency(val) {
            return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(val);
        }