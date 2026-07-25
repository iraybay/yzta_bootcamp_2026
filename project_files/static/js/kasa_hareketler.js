let allTransactions = [];

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

        function fmt(d) {
            if (!d) return '';
            const p = d.split('-');
            return p.length === 3 ? `${p[2]}.${p[1]}.${p[0]}` : d;
        }

        window.addEventListener('DOMContentLoaded', () => {
            const btn = document.getElementById('themeToggleBtn');
            if (document.body.classList.contains('dark-mode')) {
                if (btn) btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            } else {
                if (btn) btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
            }
            document.getElementById('startDate').value = '2026-05-15';
            document.getElementById('endDate').value = '2026-07-18';
            fetchTransactions();
        });

        async function fetchTransactions() {
            const start = document.getElementById('startDate').value;
            const end   = document.getElementById('endDate').value;
            const type  = document.getElementById('accountTypeFilter').value;
            document.getElementById('dateRangeText').textContent = `${fmt(start)} - ${fmt(end)}`;
            try {
                const res  = await fetch(`/api/kasa-banka/hareketler?start_date=${start}&end_date=${end}&tur=${type}`);
                if (!res.ok) throw new Error();
                const json = await res.json();
                allTransactions = json.liste;

                document.getElementById('totalGiris').textContent = formatCurrency(json.total_giris);
                document.getElementById('totalCikis').textContent = formatCurrency(json.total_cikis);

                const nd = document.getElementById('netDenge');
                const sign = json.net_denge >= 0 ? '+' : '';
                nd.textContent = sign + formatCurrency(json.net_denge);
                nd.className = `value ${json.net_denge >= 0 ? 'val-positive' : 'val-negative'}`;

                renderTable(allTransactions);
            } catch {
                document.getElementById('islemTableBody').innerHTML =
                    `<tr><td colspan="5" class="text-center py-4" style="color:var(--danger-color);"><i class="fa-solid fa-circle-exclamation"></i> Veriler yüklenemedi.</td></tr>`;
            }
        }

        function renderTable(list) {
            const tbody = document.getElementById('islemTableBody');
            document.getElementById('islemCount').textContent = list.length;
            if (!list.length) {
                tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4">Filtrelere uygun hareket bulunamadı.</td></tr>`;
                return;
            }
            tbody.innerHTML = '';
            list.forEach(item => {
                const isGiris = item.tip === 'giris';
                const colorClass = isGiris ? 'val-positive' : 'val-negative';
                const sign = isGiris ? '+' : '-';
                const isKasa = item.hesap_tur === 'kasa';
                const typeClass = isKasa ? 'bg-kasa' : 'bg-banka';
                const typeLabel = isKasa ? 'Kasa' : 'Banka';
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${fmt(item.tarih)}</strong></td>
                    <td><strong>${item.tanim}</strong></td>
                    <td>
                        <span class="badge-type ${typeClass}" style="margin-right:6px;">${typeLabel}</span>
                        <span style="font-weight:600;">${item.hesap_ad}</span>
                    </td>
                    <td><strong>${item.doviz_turu || 'TRY'}</strong></td>
                    <td class="${colorClass}">${sign}${formatCurrency(item.tutar, item.doviz_turu)}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function filterLocal() {
            const q = document.getElementById('searchInput').value.toLowerCase();
            renderTable(allTransactions.filter(i =>
                i.tanim.toLowerCase().includes(q) || i.hesap_ad.toLowerCase().includes(q)
            ));
        }

        function formatCurrency(val, currency = 'TRY') {
            return new Intl.NumberFormat('tr-TR', { style: 'currency', currency }).format(val);
        }