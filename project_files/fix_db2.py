import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_manager_path = os.path.join(BASE_DIR, 'db_manager.py')

with open(db_manager_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"toplam_gelecek"', '"toplam_gelir"')
content = content.replace('"toplam_gidecek"', '"toplam_borç"')
content = content.replace("total_gelecek", "total_gelir")
content = content.replace("total_gidecek", "total_borç")

with open(db_manager_path, 'w', encoding='utf-8') as f:
    f.write(content)
