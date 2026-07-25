from repositories.db_core import get_db_connection
import datetime

def add_fatura_record(unvan, tutar, tip):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye")
    f_count = cursor.fetchone()[0] + 109
    prefix = "FT-2026-S" if tip == 'satis' else "FT-2026-A"
    fatura_no = f"{prefix}{f_count:05d}"
    
    log_tanim = f"{fatura_no} - {unvan} Faturası Düzenlendi"
    cursor.execute("INSERT INTO fatura_irsaliye (tanim, tutar, durum, tarih) VALUES (?, ?, 'Ödenmedi', '2026-07-18')", 
                   (log_tanim, tutar))
    
    conn.commit()
    conn.close()

def get_fatura_irsaliye_list(start_date=None, end_date=None, durum=None, tip=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih FROM fatura_irsaliye WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND tarih >= ?"
        params.append(start_date)
    if end_date:
        query += " AND tarih <= ?"
        params.append(end_date)
    if durum and durum != 'tumu':
        query += " AND durum = ?"
        params.append(durum)
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    
    result = []
    for r in rows:
        tanim = r['tanim']
        tutar = float(r['tutar'] or 0)
        
        belge_turu_db = r['belge_turu']
        belge_no_db = r['belge_no']
        
        if belge_turu_db:
            belge_turu = belge_turu_db
            if belge_turu == 'irsaliye': belge_label = "Sevk İrsaliyesi"
            elif belge_turu == 'alis_faturasi': belge_label = "Alış Faturası"
            elif belge_turu == 'irsaliyeli_fatura': belge_label = "İrsaliyeli Fatura"
            else: belge_label = "Satış Faturası"
        else:
            if "Sevk İrsaliyesi" in tanim or "IR-" in tanim or "Sevkiyat" in tanim:
                belge_turu = "irsaliye"
                belge_label = "Sevk İrsaliyesi"
            elif "Alış" in tanim or "A00" in tanim:
                belge_turu = "alis"
                belge_label = "Alış Faturası"
            elif "İrsaliyeli" in tanim or "IF-" in tanim:
                belge_turu = "irsaliyeli_fatura"
                belge_label = "İrsaliyeli Fatura"
            else:
                belge_turu = "satis"
                belge_label = "Satış Faturası"
                
        if tip and tip != 'tumu':
            if tip == 'irsaliye' and belge_turu not in ['irsaliye', 'irsaliyeli_fatura']:
                continue
            elif tip == 'satis' and belge_turu not in ['satis', 'satis_faturasi']:
                continue
            elif tip == 'alis' and belge_turu not in ['alis', 'alis_faturasi']:
                continue

        belge_no = belge_no_db if belge_no_db else f"DOC-{r['id']:04d}"
        unvan = "Genel Cari"
        aciklama = tanim

        if " — " in tanim:
            parts = tanim.split(" — ", 1)
            if not belge_no_db: belge_no = parts[0].strip()
            rest = parts[1].strip()
            if " | " in rest:
                sub_parts = rest.split(" | ", 1)
                unvan = sub_parts[0].strip()
                aciklama = sub_parts[1].strip()
            else:
                unvan = rest
                aciklama = rest
        elif " - " in tanim:
            parts = tanim.split(" - ", 1)
            if not belge_no_db: belge_no = parts[0].strip()
            rest = parts[1].strip()
            if " | " in rest:
                sub_parts = rest.split(" | ", 1)
                unvan = sub_parts[0].strip()
                aciklama = sub_parts[1].strip()
            else:
                unvan = rest
                aciklama = rest
        
        r['cari_id'] = r['cari_id']

        r['belge_no'] = belge_no
        r['unvan'] = unvan
        r['aciklama'] = aciklama
        r['belge_turu'] = belge_turu
        r['belge_label'] = belge_label
        result.append(r)
        
    conn.close()
    return result

def add_fatura_irsaliye_full(cari_id, unvan, belge_no, tutar, tip, durum, tarih, aciklama=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM fatura_irsaliye")
    count = cursor.fetchone()[0] + 115
    
    if tip == 'irsaliye':
        prefix = "IR-2026-"
        label = "Sevk İrsaliyesi"
        belge_turu = "irsaliye"
    elif tip == 'alis':
        prefix = "FT-2026-A"
        label = "Alış Faturası"
        belge_turu = "alis_faturasi"
    elif tip == 'irsaliyeli_fatura':
        prefix = "IF-2026-"
        label = "İrsaliyeli Fatura"
        belge_turu = "irsaliyeli_fatura"
    else:
        prefix = "FT-2026-S"
        label = "Satış Faturası"
        belge_turu = "satis_faturasi"
        
    code = belge_no if belge_no else f"{prefix}{count:05d}"
    detail_aciklama = aciklama if aciklama else label
    log_tanim = f"{code} — {unvan} | {detail_aciklama}"
        
    cursor.execute("INSERT INTO fatura_irsaliye (cari_id, belge_no, belge_turu, tanim, tutar, durum, tarih) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (cari_id, code, belge_turu, log_tanim, float(tutar), durum, tarih))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_fatura_status(fatura_id, yeni_durum):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE fatura_irsaliye SET durum = ? WHERE id = ?", (yeni_durum, fatura_id))
    conn.commit()

def delete_fatura_record(fatura_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fatura_irsaliye WHERE id = ?", (fatura_id,))
    conn.commit()
    conn.close()

