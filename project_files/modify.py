import re
import random

with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/db_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace gelecek -> gelir and gidecek -> borç in odeme_plani tip field
# The tip in odeme_plani table definition
content = content.replace("-- 'gelecek' veya 'gidecek'", "-- 'gelir' veya 'borç'")

# We also need to change the types in get_payment_plan if necessary:
# total_gelecek = sum(r['kalan_tutar'] for r in rows if r['tip'] == 'gelecek')
# total_gidecek = sum(r['kalan_tutar'] for r in rows if r['tip'] == 'gidecek')
content = content.replace("r['tip'] == 'gelecek'", "r['tip'] == 'gelir'")
content = content.replace("r['tip'] == 'gidecek'", "r['tip'] == 'borç'")


def replace_line(match):
    # Match something like: ("Ahmet Yılmaz", 5400.0, "gelecek", "2026-07-20", "Ürün Satış Bedeli", "Bekliyor")
    pre = match.group(1)
    tutar = float(match.group(2))
    tip = match.group(3)
    post = match.group(4)
    
    # modify tip
    if tip == 'gelecek':
        new_tip = 'gelir'
    elif tip == 'gidecek':
        new_tip = 'borç'
    else:
        new_tip = tip
        
    # random variation between -10% and +10%
    variation = random.uniform(0.9, 1.1)
    new_tutar = round(tutar * variation, 2)
    
    return f'{pre}{new_tutar}, "{new_tip}"{post}'

# We need to find the odeme_listesi
# Format: ("Ahmet Yılmaz", 5400.0, "gelecek", "2026-07-20", ...
pattern = re.compile(r'(\(\"[^\"]+\",\s*)([0-9\.]+)(,\s*\")([a-z]+)(\",\s*\"2026-[0-9]{2}-[0-9]{2}\",\s*\"[^\"]+\",\s*\"[^\"]+\"\))')

new_content = pattern.sub(replace_line, content)

with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/db_manager.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print("Modified db_manager.py")
