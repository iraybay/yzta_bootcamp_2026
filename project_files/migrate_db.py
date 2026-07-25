import sqlite3

def migrate():
    conn = sqlite3.connect('bulutis.db')
    cursor = conn.cursor()
    
    # 1. Add columns to fatura_irsaliye
    try:
        cursor.execute("ALTER TABLE fatura_irsaliye ADD COLUMN cari_id INTEGER")
        print("Added cari_id to fatura_irsaliye")
    except Exception as e:
        print("cari_id exists:", e)
        
    try:
        cursor.execute("ALTER TABLE fatura_irsaliye ADD COLUMN belge_no TEXT")
        print("Added belge_no to fatura_irsaliye")
    except Exception as e:
        print("belge_no exists:", e)
        
    try:
        cursor.execute("ALTER TABLE fatura_irsaliye ADD COLUMN belge_turu TEXT")
        print("Added belge_turu to fatura_irsaliye")
    except Exception as e:
        print("belge_turu exists:", e)
        
    # 2. Add column to kasa_banka_islem
    try:
        cursor.execute("ALTER TABLE kasa_banka_islem ADD COLUMN fatura_id INTEGER")
        print("Added fatura_id to kasa_banka_islem")
    except Exception as e:
        print("fatura_id exists:", e)
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
