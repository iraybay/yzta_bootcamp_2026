// Check dark mode state
        if (localStorage.getItem('theme') !== 'light') {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        } else {
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
        }

        window.addEventListener('DOMContentLoaded', () => {
            fetchReportList();
        });

        async function fetchReportList(params = '') {
            const tbody = document.getElementById('reportTableBody');
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4"><i class="fa-solid fa-spinner fa-spin"></i> Veriler getiriliyor...</td></tr>`;
            
            try {
                const response = await fetch(`/api/mutabakat/liste${params}`);
                if (!response.ok) throw new Error();
                const json = await response.json();
                
                // Update metrics summary
                document.getElementById('totalGelir').textContent = formatCurrency(json.toplam_gelir);
                document.getElementById('totalBorc').textContent = formatCurrency(json.toplam_borç);

                document.getElementById('totalOdenen').textContent = formatCurrency(json.toplam_odenen ?? 0);
                
                // Render table
                renderTable(json.liste);
                
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4" style="color: var(--danger-color);"><i class="fa-solid fa-circle-exclamation"></i> Veriler yüklenemedi.</td></tr>`;
            }
        }

        function renderTable(list) {
            const tbody = document.getElementById('reportTableBody');
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4">Filtre kriterlerine uygun ödeme kaydı bulunamadı.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = '';
            list.forEach(item => {
                const tr = document.createElement('tr');
                const isInflow = item.tip === 'gelir';
                
                tr.className = isInflow ? 'row-gelir' : 'row-borc';

                const statusHtml = item.durum === 'Ödendi'
                    ? '<span class="badge-payment" style="background:rgba(16,185,129,0.12);color:var(--green-primary);"><i class="fa-solid fa-circle-check"></i> Ödendi</span>'
                    : (item.durum === 'Kısmi Ödendi'
                       ? '<span class="badge-payment" style="background:rgba(245,158,11,0.12);color:var(--orange-primary);"><i class="fa-solid fa-circle-half-stroke"></i> Kısmi Ödendi</span>'
                       : '<span class="badge-payment" style="background:rgba(100,116,139,0.12);color:var(--text-secondary);"><i class="fa-regular fa-clock"></i> Bekliyor</span>');

                const dateParts = item.tarih.split('-');
                const formattedDate = dateParts.length === 3 ? `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}` : item.tarih;

                const indicator = isInflow ? 'G' : 'B';
                const indicatorColor = isInflow ? 'var(--green-primary)' : 'var(--danger-color)';
                const amountText = `${formatCurrency(item.tutar)} <span style="font-weight:800; color:${indicatorColor}; font-size:11px; margin-left:4px;">${indicator}</span>`;

                tr.innerHTML = `
                    <td><strong>${formattedDate}</strong></td>
                    <td><strong>${item.cari_ad}</strong><br><small style="opacity:.7;">${item.aciklama || ''}</small></td>
                    <td style="font-weight: 700;">${amountText}</td>
                    <td>${statusHtml}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function applyFilters(event) {
            event.preventDefault();
            const start = document.getElementById('startDate').value;
            const end = document.getElementById('endDate').value;
            const type = document.getElementById('typeFilter').value;
            
            const params = new URLSearchParams();
            if (start) params.append('start_date', start);
            if (end) params.append('end_date', end);
            if (type) params.append('tip', type);
            
            fetchReportList(`?${params.toString()}`);
        }

        function clearFilters() {
            document.getElementById('filterForm').reset();
            fetchReportList();
        }

        function formatCurrency(val) {
            return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(val);
        }