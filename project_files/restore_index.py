import re

with open('templates/index.html', 'r') as f:
    html = f.read()

# Extract the menus from current HTML
cari_menu = re.search(r'(<div class="op-sub-panel dropdown-menu" id="opPanel-cari">.*?</div>)', html, re.DOTALL)
if not cari_menu:
    cari_menu = re.search(r'(<div class="op-sub-panel" id="opPanel-cari">.*?</div>)', html, re.DOTALL)
cari_menu = cari_menu.group(1).replace('dropdown-menu', '').replace('op-sub-panel ', 'op-sub-panel')

kasa_menu = re.search(r'(<div class="op-sub-panel" id="opPanel-kasa">.*?</div>)', html, re.DOTALL).group(1).replace('dropdown-menu', '').replace('op-sub-panel ', 'op-sub-panel')
stok_menu = re.search(r'(<div class="op-sub-panel" id="opPanel-stok">.*?</div>)', html, re.DOTALL).group(1).replace('dropdown-menu', '').replace('op-sub-panel ', 'op-sub-panel')
fatura_menu = re.search(r'(<div class="op-sub-panel" id="opPanel-fatura">.*?</div>)', html, re.DOTALL).group(1).replace('dropdown-menu', '').replace('op-sub-panel ', 'op-sub-panel')

new_operations = f"""        <section class="operations-bar-card" id="operationsBar">
            <div class="operations-tabs">
                <button class="op-tab-btn" onclick="toggleOperationsTab('cari')">
                    <i class="fa-solid fa-users icon-orange"></i> Cari İşlemleri <i class="fa-solid fa-chevron-down arrow"></i>
                </button>
                <button class="op-tab-btn" onclick="toggleOperationsTab('kasa')">
                    <i class="fa-solid fa-vault icon-blue"></i> Kasa & Banka <i class="fa-solid fa-chevron-down arrow"></i>
                </button>
                <button class="op-tab-btn" onclick="toggleOperationsTab('stok')">
                    <i class="fa-solid fa-box-open icon-green"></i> Stok İşlemleri <i class="fa-solid fa-chevron-down arrow"></i>
                </button>
                <button class="op-tab-btn" onclick="toggleOperationsTab('fatura')">
                    <i class="fa-solid fa-file-invoice-dollar icon-purple"></i> Fatura & İrsaliye <i class="fa-solid fa-chevron-down arrow"></i>
                </button>
            </div>
            
            <div class="operations-bar-content" id="operationsContent">
                {cari_menu.strip()}
                {kasa_menu.strip()}
                {stok_menu.strip()}
                {fatura_menu.strip()}
            </div>
        </section>"""

old_section = re.search(r'(<section class="operations-bar-card" id="operationsBar">.*?</section>)', html, re.DOTALL).group(1)
html = html.replace(old_section, new_operations)

with open('templates/index.html', 'w') as f:
    f.write(html)

print("Restored index.html")
