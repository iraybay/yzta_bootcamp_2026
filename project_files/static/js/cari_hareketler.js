if (localStorage.getItem('theme') !== 'light') {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        } else {
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
        }

        function formatDateText(dateStr) {
            if (!dateStr) return '';
            const parts = dateStr.split('-');
            if (parts.length === 3) {
                return `${parts[2]}.${parts[1]}.${parts[0]}`;
            }
            return dateStr;
        }

        window.addEventListener('DOMContentLoaded', () => {
            // Set default date range to the beginning of this month to today
            document.getElementById('startDateIslem').value = "2026-01-01";
            document.getElementById('endDateIslem').value = "2026-07-30";
            fetchRecentTransactions();
        });

        async function fetchRecentTransactions() {
            try {
                const startDate = document.getElementById('startDateIslem').value;
                const endDate = document.getElementById('endDateIslem').value;
                
                // Show date range in title
                const startFormatted = formatDateText(startDate);
                const endFormatted = formatDateText(endDate);
                document.getElementById('dateRangeText').textContent = `${startFormatted} - ${endFormatted}`;

                const response = await fetch(`/api/cari/hareketler?start_date=${startDate}&end_date=${endDate}`);
                if (!response.ok) throw new Error();
                const json = await response.json();
                
                // Update metrics summary
                document.getElementById('totalAlacak').textContent = formatCurrency(json.total_alacak);
                document.getElementById('totalBorc').textContent = formatCurrency(json.total_borc);
                
                const netVal = json.net_denge;
                const netEl = document.getElementById('netDurum');
                netEl.textContent = formatCurrency(netVal);
                if (netVal >= 0) {
                    netEl.className = 'value val-green';
                } else {
                    netEl.className = 'value val-red';
                }
                
                // Update count badge
                document.getElementById('islemCount').textContent = json.liste.length;
                
                // Render table
                renderTable(json.liste);
                
            } catch (err) {
                const tbody = document.getElementById('islemTableBody');
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4" style="color: var(--danger-color);"><i class="fa-solid fa-circle-exclamation"></i> Veriler yüklenemedi.</td></tr>`;
            }
        }

        function renderTable(list) {
            const tbody = document.getElementById('islemTableBody');
            if (!list || list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4">Herhangi bir cari işlem kaydı bulunamadı.</td></tr>`;
                return;
            }
            
            // To calculate a true running net balance, sort the filtered items chronologically first (oldest to newest)
            const chronologicalList = [...list].sort((a, b) => {
                if (a.tarih !== b.tarih) return a.tarih.localeCompare(b.tarih);
                return a.id - b.id;
            });
            
            let runningBalance = 0;
            const computedItems = chronologicalList.map(item => {
                const isAlacak = item.tip === 'alacak';
                if (isAlacak) {
                    runningBalance += item.tutar;
                } else {
                    runningBalance -= item.tutar;
                }
                return { ...item, runningBakiye: runningBalance };
            });
            
            // Reverse back to newest first for UI presentation
            const displayList = computedItems.reverse();
            
            tbody.innerHTML = '';
            displayList.forEach(item => {
                const tr = document.createElement('tr');
                const isAlacak = item.tip === 'alacak';
                
                // Format Date representation YYYY-MM-DD -> DD.MM.YYYY
                const dateParts = item.tarih.split('-');
                const formattedDate = dateParts.length === 3 ? `${dateParts[2]}.${dateParts[1]}.${dateParts[0]}` : item.tarih;
                
                // Calculate Vade / Son Gün (e.g. 30 days term limit for invoices based on cari role)
                const isInvoice = item.tanim.toLowerCase().includes("faturası");
                let vadeText = '-';
                let odemeText = '-';
                let isDelayed = false;
                
                if (isInvoice) {
                    const transDate = new Date(item.tarih);
                    const dueDate = new Date(transDate);
                    dueDate.setDate(dueDate.getDate() + 30);
                    
                    const dd = String(dueDate.getDate()).padStart(2, '0');
                    const mm = String(dueDate.getMonth() + 1).padStart(2, '0');
                    const yyyy = dueDate.getFullYear();
                    vadeText = `${dd}.${mm}.${yyyy}`;
                    
                    if (item.odeme_tarihi) {
                        const actualPayDate = new Date(item.odeme_tarihi);
                        const pd = String(actualPayDate.getDate()).padStart(2, '0');
                        const pm = String(actualPayDate.getMonth() + 1).padStart(2, '0');
                        const py = actualPayDate.getFullYear();
                        const formattedPayDate = `${pd}.${pm}.${py}`;
                        
                        if (actualPayDate > dueDate) {
                            // Paid late
                            odemeText = `<span style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger-color); color: var(--danger-color); padding: 4px 10px; border-radius: 4px; font-weight:800; font-size:11px;"><i class="fa-solid fa-clock"></i> Ödendi: ${formattedPayDate}</span>`;
                            isDelayed = true;
                        } else {
                            // Paid timely (Yeşil Ödendi badge)
                            odemeText = `<span style="background: rgba(16, 185, 129, 0.12); border: 1px solid var(--green-primary); color: var(--green-primary); padding: 4px 10px; border-radius: 4px; font-weight:800; font-size:11px;"><i class="fa-regular fa-calendar-check"></i> Ödendi: ${formattedPayDate}</span>`;
                        }
                    } else {
                        const todayLimit = new Date('2026-07-30');
                        if (dueDate < todayLimit) {
                            odemeText = `<span style="background: rgba(239, 68, 68, 0.15); border: 1px solid var(--danger-color); color: var(--danger-color); padding: 4px 10px; border-radius: 4px; font-weight:800; font-size:11px;"><i class="fa-solid fa-circle-exclamation"></i> Ödenmedi</span>`;
                            isDelayed = true;
                        } else {
                            // Unpaid but within term limit (Sarı Bekliyor badge)
                            odemeText = `<span style="background: rgba(245, 158, 11, 0.1); border: 1px solid var(--warning-color); color: var(--warning-color); padding: 4px 10px; border-radius: 4px; font-weight:800; font-size:11px;"><i class="fa-regular fa-clock"></i> Bekliyor</span>`;
                        }
                    }
                } else {
                    vadeText = formattedDate;
                    odemeText = `<span style="background: rgba(16, 185, 129, 0.12); border: 1px solid var(--green-primary); color: var(--green-primary); padding: 4px 10px; border-radius: 4px; font-weight:800; font-size:11px;"><i class="fa-solid fa-circle-check"></i> Ödendi: ${formattedDate}</span>`;
                }
                
                let rowBg = "";
                let rowColor = "";
                if (isDelayed) {
                    rowBg = "rgba(239, 68, 68, 0.06)";
                    rowColor = "var(--danger-color)";
                } else if (isInvoice && item.odeme_tarihi) {
                    rowBg = "rgba(16, 185, 129, 0.03)";
                }
                
                if (rowBg) {
                    tr.style.background = rowBg;
                }
                if (rowColor) {
                    tr.style.color = rowColor;
                }
                
                // Render single Tutar column with B/G indicator standard
                const indicator = isAlacak ? 'G' : 'B';
                const indicatorColor = isAlacak ? 'var(--green-primary)' : 'var(--danger-color)';
                const amountText = `${formatCurrency(item.tutar)} <span style="font-weight:800; color:${indicatorColor}; font-size:11px; margin-left:4px;">${indicator}</span>`;
                
                tr.innerHTML = `
                    <td><strong>#${item.id}</strong></td>
                    <td style="${isDelayed ? 'color: var(--danger-color);' : ''}"><strong>${formattedDate}</strong></td>
                    <td style="${isDelayed ? 'color: var(--danger-color);' : ''}"><strong>${item.tanim}</strong></td>
                    <td style="${isDelayed ? 'color: var(--danger-color);' : ''}"><strong>${vadeText}</strong></td>
                    <td>${odemeText}</td>
                    <td style="font-weight: 700;">${amountText}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function formatCurrency(val) {
            return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(val);
        }