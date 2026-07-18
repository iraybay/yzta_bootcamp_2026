import re
import random

with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/db_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Let's just recreate the odeme_listesi block
original_list = [
    ('Ahmet Yılmaz', 5400.0, 'gelecek', '2026-07-20', 'Ürün Satış Bedeli', 'Bekliyor'),
    ('Ayşe Kaya', 3200.0, 'gelecek', '2026-07-22', 'Hizmet Bedeli Tahsilatı', 'Bekliyor'),
    ('TeknoMarket A.Ş.', 15000.0, 'gelecek', '2026-07-25', 'Yarı Yıl Hak Edişi', 'Kısmi Ödendi'),
    ('Vural İnşaat Ltd.', 40000.0, 'gelecek', '2026-07-30', 'Şantiye Destek Bedeli', 'Bekliyor'),
    ('Zeynep Şahin', 1250.0, 'gelecek', '2026-08-02', 'Danışmanlık Hizmeti', 'Bekliyor'),
    ('Caner Demir', 9800.0, 'gelecek', '2026-08-05', 'Malzeme Satışı', 'Bekliyor'),
    ('Öztürk Gıda', 14000.0, 'gelecek', '2026-08-10', 'Toptan Gıda Satış Bedeli', 'Bekliyor'),
    ('Akdeniz Lojistik', 38000.0, 'gelecek', '2026-08-15', 'Taşıma Hizmet Bedeli', 'Bekliyor'),
    ('Elif Çelik', 4300.0, 'gelecek', '2026-08-18', 'Tasarım Proje Tahsilatı', 'Bekliyor'),
    ('Yıldız Mobilya', 28900.0, 'gelecek', '2026-08-22', 'Ofis Mobilyaları Satışı', 'Bekliyor'),
    ('Maslak Yazılım', 35000.0, 'gelecek', '2026-08-25', 'Yazılım Geliştirme Bedeli', 'Kısmi Ödendi'),
    ('Beta Kimya', 19200.0, 'gelecek', '2026-08-28', 'Kimyasal Madde Satışı', 'Bekliyor'),
    ('Mavi Mimarlık', 24000.0, 'gelecek', '2026-09-02', 'Proje Çizim Bedeli', 'Bekliyor'),
    ('Kaan Arslan', 7200.0, 'gelecek', '2026-09-05', 'Montaj Hizmet Tahsilatı', 'Bekliyor'),
    ('Ahmet Yılmaz', 4500.0, 'gelecek', '2026-09-10', 'Ek Sipariş Ödemesi', 'Bekliyor'),
    ('TeknoMarket A.Ş.', 30000.0, 'gelecek', '2026-09-15', 'Donanım Teslimat Bedeli', 'Bekliyor'),
    ('Vural İnşaat Ltd.', 80000.0, 'gelecek', '2026-09-25', '2. Etap Hak Ediş Ödemesi', 'Bekliyor'),
    ('Öztürk Gıda', 20000.0, 'gelecek', '2026-10-01', 'Gıda Sevkiyat Ödemesi', 'Bekliyor'),
    ('Akdeniz Lojistik', 40000.0, 'gelecek', '2026-10-10', 'Lojistik Destek Tahsilatı', 'Bekliyor'),
    ('Yıldız Mobilya', 15000.0, 'gelecek', '2026-10-15', 'Ekipman Satış Bakiyesi', 'Bekliyor'),
    ('Maslak Yazılım', 30000.0, 'gelecek', '2026-10-20', 'Bakım Anlaşması Bedeli', 'Bekliyor'),
    ('Beta Kimya', 10000.0, 'gelecek', '2026-10-25', 'Laboratuvar Malzeme Satışı', 'Bekliyor'),
    ('Mavi Mimarlık', 30000.0, 'gelecek', '2026-11-02', 'Rölöve Çalışması Tahsilatı', 'Bekliyor'),
    ('Caner Demir', 5000.0, 'gelecek', '2026-11-10', 'Yedek Parça Satış Bedeli', 'Bekliyor'),
    ('Ayşe Kaya', 3000.0, 'gelecek', '2026-11-15', 'Eğitim Hizmet Tahsilatı', 'Bekliyor'),
    ('Doruk Toptan Gıda', 5000.0, 'gidecek', '2026-07-21', 'Toptan Ürün Tedarik Ödemesi', 'Bekliyor'),
    ('Çelik Hırdavat', 4900.0, 'gidecek', '2026-07-24', 'Şantiye Malzeme Faturası', 'Bekliyor'),
    ('Global Enerji A.Ş.', 37000.0, 'gidecek', '2026-07-28', 'Fabrika Elektrik Faturası', 'Kısmi Ödendi'),
    ('Alfa Ambalaj', 13000.0, 'gidecek', '2026-08-01', 'Koli ve Ambalaj Malzemesi', 'Bekliyor'),
    ('Mega Kağıtçılık', 6000.0, 'gidecek', '2026-08-04', 'Ofis Kırtasiye Alımları', 'Bekliyor'),
    ('Kuzey Tekstil', 14500.0, 'gidecek', '2026-08-08', 'Kumaş Tedarik Ödemesi', 'Bekliyor'),
    ('Ege Elektrik', 8700.0, 'gidecek', '2026-08-12', 'Trafo Bakım Bedeli', 'Bekliyor'),
    ('Hilal Demir Sanayi', 45000.0, 'gidecek', '2026-08-20', 'Demir Profil Alım Bedeli', 'Bekliyor'),
    ('Doruk Toptan Gıda', 10000.0, 'gidecek', '2026-08-25', 'Aylık Gıda Alım Faturası', 'Bekliyor'),
    ('Çelik Hırdavat', 4000.0, 'gidecek', '2026-09-01', 'El Aletleri Tedarik Faturası', 'Bekliyor'),
    ('Global Enerji A.Ş.', 30000.0, 'gidecek', '2026-09-08', 'Aylık Tesis Enerji Gideri', 'Bekliyor'),
    ('Alfa Ambalaj', 10000.0, 'gidecek', '2026-09-12', 'Paketleme Malzemesi Alımı', 'Bekliyor'),
    ('Mega Kağıtçılık', 6000.0, 'gidecek', '2026-09-18', 'Matbaa Baskı İşleri Ödemesi', 'Bekliyor'),
    ('Kuzey Tekstil', 20000.0, 'gidecek', '2026-09-22', 'İplik ve Kumaş Siparişi', 'Bekliyor'),
    ('Ege Elektrik', 8000.0, 'gidecek', '2026-10-02', 'Pano Kurulum Hakedişi', 'Bekliyor'),
    ('Hilal Demir Sanayi', 50000.0, 'gidecek', '2026-10-08', 'Sac Levha Sipariş Bakiyesi', 'Bekliyor'),
    ('Global Enerji A.Ş.', 25000.0, 'gidecek', '2026-10-15', 'Enerji Dağıtım Hakedişi', 'Bekliyor'),
    ('Kuzey Tekstil', 15000.0, 'gidecek', '2026-10-22', 'Kışlık Ürün Ham Hammaddesi', 'Bekliyor'),
    ('Doruk Toptan Gıda', 8000.0, 'gidecek', '2026-11-01', 'Market Reyon Siparişi', 'Bekliyor'),
    ('Çelik Hırdavat', 3000.0, 'gidecek', '2026-11-05', 'Kaynak Malzemeleri Faturası', 'Bekliyor'),
    ('Alfa Ambalaj', 8000.0, 'gidecek', '2026-11-12', 'Etiket ve Kutu Alımı', 'Bekliyor'),
    ('Mega Kağıtçılık', 5000.0, 'gidecek', '2026-11-18', 'Arşiv Klasörleri Alımı', 'Bekliyor'),
    ('Ege Elektrik', 5000.0, 'gidecek', '2026-11-20', 'Aydınlatma Sistemleri Faturası', 'Bekliyor'),
    ('Hilal Demir Sanayi', 20000.0, 'gidecek', '2026-11-25', 'Kaynak Telleri Sevkiyatı', 'Bekliyor'),
    ('Global Enerji A.Ş.', 20000.0, 'gidecek', '2026-11-28', 'Trafo Yenileme Ödemesi', 'Bekliyor')
]

# Write a clean replacement string
replacement = "        odeme_listesi = [\n"
for item in original_list:
    tip = 'gelir' if item[2] == 'gelecek' else 'borç'
    new_tutar = round(item[1] * random.uniform(0.9, 1.1), 2)
    replacement += f'            ("{item[0]}", {new_tutar}, "{tip}", "{item[3]}", "{item[4]}", "{item[5]}"),\n'
replacement = replacement.rstrip(",\n") + "\n        ]\n"

# In lines, find the start and end of odeme_listesi
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "odeme_listesi = [" in line:
        start_idx = i
    if start_idx != -1 and i > start_idx:
        # Before the failure, we had lines starting with "            (" and ending with "],"
        # But wait, because it failed, my previous script completely messed up the odeme_listesi block
        if "        # Calculate dynamic remaining outstanding balance" in line:
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + [replacement] + lines[end_idx:]
    with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/db_manager.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Recovered db_manager.py")
else:
    print("Could not find block boundaries")
