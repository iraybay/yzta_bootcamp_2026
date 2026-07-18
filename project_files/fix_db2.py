with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/db_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"toplam_gelecek"', '"toplam_gelir"')
content = content.replace('"toplam_gidecek"', '"toplam_borç"')
content = content.replace("total_gelecek", "total_gelir")
content = content.replace("total_gidecek", "total_borç")

with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/db_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
