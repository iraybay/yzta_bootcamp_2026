import re

with open('templates/index.html', 'r') as f:
    html = f.read()

# We want to replace the whole operationsBar section.
# First, extract the content of each ul.op-vertical-menu to reuse.
cari_menu = re.search(r'(<div class="op-sub-panel" id="opPanel-cari">.*?</div>)', html, re.DOTALL).group(1)
kasa_menu = re.search(r'(<div class="op-sub-panel" id="opPanel-kasa">.*?</div>)', html, re.DOTALL).group(1)
stok_menu = re.search(r'(<div class="op-sub-panel" id="opPanel-stok">.*?</div>)', html, re.DOTALL).group(1)
fatura_menu = re.search(r'(<div class="op-sub-panel" id="opPanel-fatura">.*?</div>)', html, re.DOTALL).group(1)

# Remove the arrows
cari_menu = re.sub(r'<i class="fa-solid fa-chevron-right menu-arrow"></i>', '', cari_menu)
kasa_menu = re.sub(r'<i class="fa-solid fa-chevron-right menu-arrow"></i>', '', kasa_menu)
stok_menu = re.sub(r'<i class="fa-solid fa-chevron-right menu-arrow"></i>', '', stok_menu)
fatura_menu = re.sub(r'<i class="fa-solid fa-chevron-right menu-arrow"></i>', '', fatura_menu)

new_operations = f"""        <section class="operations-bar-card" id="operationsBar">
            <div class="operations-tabs" style="display: flex; gap: 12px; flex-wrap: wrap;">
                
                <div class="dropdown-wrapper" style="position: relative;">
                    <button class="op-tab-btn" onclick="toggleOperationsTab('cari')">
                        <i class="fa-solid fa-users icon-orange"></i> Cari İşlemleri <i class="fa-solid fa-chevron-down arrow"></i>
                    </button>
                    {cari_menu.strip()}
                </div>

                <div class="dropdown-wrapper" style="position: relative;">
                    <button class="op-tab-btn" onclick="toggleOperationsTab('kasa')">
                        <i class="fa-solid fa-vault icon-blue"></i> Kasa & Banka <i class="fa-solid fa-chevron-down arrow"></i>
                    </button>
                    {kasa_menu.strip()}
                </div>

                <div class="dropdown-wrapper" style="position: relative;">
                    <button class="op-tab-btn" onclick="toggleOperationsTab('stok')">
                        <i class="fa-solid fa-box-open icon-green"></i> Stok İşlemleri <i class="fa-solid fa-chevron-down arrow"></i>
                    </button>
                    {stok_menu.strip()}
                </div>

                <div class="dropdown-wrapper" style="position: relative;">
                    <button class="op-tab-btn" onclick="toggleOperationsTab('fatura')">
                        <i class="fa-solid fa-file-invoice-dollar icon-purple"></i> Fatura & İrsaliye <i class="fa-solid fa-chevron-down arrow"></i>
                    </button>
                    {fatura_menu.strip()}
                </div>

            </div>
        </section>"""

# Replace in html
old_section = re.search(r'(<section class="operations-bar-card" id="operationsBar">.*?</section>)', html, re.DOTALL).group(1)
html = html.replace(old_section, new_operations)

with open('templates/index.html', 'w') as f:
    f.write(html)

print("Rewrote index.html")
