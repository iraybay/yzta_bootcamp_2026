with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/templates/mutabakat_raporu.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"gelecek"', '"gelir"')
content = content.replace('"gidecek"', '"borç"')
content = content.replace("tip === 'gelecek'", "tip === 'gelir'")
content = content.replace('item.tip === \'gelecek\'', 'item.tip === \'gelir\'')
content = content.replace('row-gelecek', 'row-gelir')
content = content.replace('row-gidecek', 'row-borç')
content = content.replace('totalGelecek', 'totalGelir')
content = content.replace('totalGidecek', 'totalBorc')
content = content.replace('toplam_gelecek', 'toplam_gelir')
content = content.replace('toplam_gidecek', 'toplam_borç')
content = content.replace('Gelecek Ödemeler', 'Gelir Ödemeleri')
content = content.replace('Gidecek Ödemeler', 'Borç Ödemeleri')

with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/templates/mutabakat_raporu.html', 'w', encoding='utf-8') as f:
    f.write(content)
