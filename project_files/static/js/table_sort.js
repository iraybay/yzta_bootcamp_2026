document.addEventListener('DOMContentLoaded', () => {
    window.activeSortConfigs = {}; // Store { colIndex: number, asc: boolean } per tbody

    function getCellValue(tr, idx) {
        let text = tr.children[idx].innerText || tr.children[idx].textContent;
        // Basic cleanups for parsing
        text = text.replace(/₺/g, '').replace(/\./g, '').replace(/,/g, '.').trim();
        // Return number if valid, else string
        let num = parseFloat(text);
        return isNaN(num) ? text.toLowerCase() : num;
    }

    function sortTable(tbody, colIndex, asc) {
        if (!tbody || tbody.children.length === 0) return;
        
        // Skip sort if it's an empty message row
        if (tbody.children.length === 1 && tbody.children[0].children.length === 1 && tbody.children[0].children[0].colSpan > 1) {
            return;
        }

        let rows = Array.from(tbody.children);
        rows.sort((a, b) => {
            const v1 = getCellValue(a, colIndex);
            const v2 = getCellValue(b, colIndex);
            if (v1 === v2) return 0;
            if (asc) return v1 > v2 ? 1 : -1;
            else return v1 < v2 ? 1 : -1;
        });

        // Append rows back
        rows.forEach(tr => tbody.appendChild(tr));
    }

    window.bindSortHeaders = function() {
        const tables = document.querySelectorAll('table');
        tables.forEach((table, tableIndex) => {
            const headers = table.querySelectorAll('th.sortable');
            if (headers.length === 0) return;
            
            const tbody = table.querySelector('tbody');
            if (!tbody) return;
            
            // Assign a unique ID to tbody if it doesn't have one
            if (!tbody.id) {
                tbody.id = 'tableBody-' + tableIndex;
            }

            headers.forEach((th, idx) => {
                // Remove old event listener if exists to prevent duplicates on re-bind
                const newTh = th.cloneNode(true);
                th.parentNode.replaceChild(newTh, th);
                
                // Find actual visual index since there might be non-sortable columns before it
                let colIndex = Array.from(newTh.parentNode.children).indexOf(newTh);
                
                newTh.style.cursor = 'pointer';
                newTh.addEventListener('click', () => {
                    const asc = !newTh.classList.contains('asc');
                    
                    // Reset all other headers in this table
                    const allHeaders = newTh.parentNode.querySelectorAll('th.sortable');
                    allHeaders.forEach(h => {
                        h.classList.remove('asc', 'desc');
                        let icon = h.querySelector('i');
                        if(icon) icon.className = 'fa-solid fa-sort';
                    });
                    
                    // Set current header class
                    newTh.classList.add(asc ? 'asc' : 'desc');
                    let icon = newTh.querySelector('i');
                    if(icon) {
                        icon.className = asc ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down';
                    }

                    // Save config and sort
                    window.activeSortConfigs[tbody.id] = { colIndex: colIndex, asc: asc };
                    
                    // Temporarily disconnect observer to prevent infinite loops during manual sort
                    if (window.tableObservers && window.tableObservers[tbody.id]) {
                        window.tableObservers[tbody.id].disconnect();
                    }
                    
                    sortTable(tbody, colIndex, asc);
                    
                    // Reconnect observer
                    if (window.tableObservers && window.tableObservers[tbody.id]) {
                        window.tableObservers[tbody.id].observe(tbody, { childList: true });
                    }
                });
            });
        });
    };

    // Setup observers to re-sort automatically when renderTable runs
    window.tableObservers = {};
    function setupObservers() {
        const tables = document.querySelectorAll('table');
        tables.forEach((table) => {
            if (!table.querySelector('th.sortable')) return;
            
            const tbody = table.querySelector('tbody');
            if (!tbody || !tbody.id) return;
            
            const observer = new MutationObserver((mutations) => {
                let shouldSort = false;
                for (let m of mutations) {
                    if (m.addedNodes.length > 0) {
                        shouldSort = true;
                        break;
                    }
                }
                
                if (shouldSort && window.activeSortConfigs[tbody.id]) {
                    const config = window.activeSortConfigs[tbody.id];
                    
                    // Disconnect while sorting to prevent loop
                    observer.disconnect();
                    
                    sortTable(tbody, config.colIndex, config.asc);
                    
                    // Reconnect
                    observer.observe(tbody, { childList: true });
                }
            });
            
            observer.observe(tbody, { childList: true });
            window.tableObservers[tbody.id] = observer;
        });
    }

    bindSortHeaders();
    setupObservers();
});
