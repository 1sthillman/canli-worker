#!/usr/bin/env python3
"""
PythonAnywhere için Futbol Veri Toplama Scripti
Bu script, 'Always-on task' olarak çalıştırılarak sürekli veri toplar.
"""
import sqlite3
import requests
import time
import json
import logging
import os
import datetime
from pathlib import Path

# Log yapılandırması
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename="futbol_worker.log",  # Log dosyası
    filemode="a"
)
logger = logging.getLogger(__name__)

# PythonAnywhere için dosya yolları
HOME = str(Path.home())
DATA_DIR = os.path.join(HOME, "futbol_data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "canli.db")

# SQLite veritabanı yapılandırması
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Tablo oluştur (yoksa)
c.execute("""CREATE TABLE IF NOT EXISTS raw(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               ts TEXT DEFAULT CURRENT_TIMESTAMP,
               mac_id TEXT,
               ev TEXT,
               dep TEXT,
               skor TEXT,
               dakika TEXT,
               oran TEXT,
               tarih TEXT,
               saat TEXT,
               lig TEXT,
               mbs TEXT)""")

# Meta veri tablosu
c.execute("""CREATE TABLE IF NOT EXISTS meta(
               key TEXT PRIMARY KEY,
               value TEXT)""")
conn.commit()

def get_data():
    """İki API'den veri çeker ve veritabanına kaydeder"""
    logger.info("Veri çekiliyor...")
    
    # API istekleri
    headers = {
        "If-Modified-Since": "Sat, 1 Jan 2000 00:00:00 GMT",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        j1 = requests.get("https://sportsbookv2.iddaa.com/sportsbook/events?st=1&type=1&version=0", 
                        headers=headers, timeout=10).json()
        j2 = requests.get("https://www.bilyoner.com/api/v3/mobile/aggregator/gamelist/all/v1?tabType=9999&bulletinType=1&liveEventsEnabledForPreBulletin=true", 
                        headers=headers, timeout=10).json()
        
        # Veri işleme
        sc_list = j1.get("data", {}).get("sc", [])
        ev_list = j1.get("data", {}).get("events", [])
        b_list = j2.get("events", [])
        
        # Mevcut maç ID'leri
        c.execute("SELECT mac_id FROM raw WHERE tarih = date('now')")
        existing_ids = set([r[0] for r in c.fetchall()])
        
        # Günlük tabloyu temizle (aynı verileri tekrar tekrar eklememek için)
        if existing_ids:
            c.execute("DELETE FROM raw WHERE tarih = date('now')")
            conn.commit()
        
        processed = 0
        for sc in sc_list:
            mac_id = sc["id"]
            skor = f"{sc['ht']['c']}-{sc['at']['c']}"
            dakika = sc.get("min", "ST")
            
            # Eşleşen event bilgisi
            ev_obj = next((e for e in ev_list if e["i"] == mac_id), None)
            if not ev_obj:
                continue
                
            ev = ev_obj["hn"]
            dep = ev_obj["an"]
            oran = "AÇIK" if any(m.get("s") == "1" for m in ev_obj.get("m", [])[:3]) else "KAPALI"
            
            # Bilyoner'den ek bilgiler
            b_obj = next((b for b in b_list if b.get("brdId") == ev_obj.get("bri")), None)
            if not b_obj:
                tarih, saat, lig, mbs = "", "", "", ""
            else:
                tarih = b_obj["esd"].split("T")[0] if "esd" in b_obj else datetime.date.today().isoformat()
                saat = b_obj.get("strt", "")
                lig = b_obj.get("lgn", "")
                mbs = b_obj.get("mbs", "")
            
            # Veritabanına kaydet
            c.execute("INSERT INTO raw(mac_id,ev,dep,skor,dakika,oran,tarih,saat,lig,mbs) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (mac_id, ev, dep, skor, dakika, oran, tarih, saat, lig, mbs))
            processed += 1
        
        # Meta veriyi güncelle
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", 
                  ("last_updated", now))
        c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", 
                  ("record_count", str(processed)))
        
        conn.commit()
        logger.info(f"{processed} adet maç veritabanına kaydedildi.")
        
    except Exception as e:
        logger.exception(f"Veri çekme hatası: {str(e)}")
        return False
        
    return True

def main_loop():
    """Ana döngü fonksiyonu"""
    logger.info("Worker servisi başlatıldı.")
    
    while True:
        try:
            get_data()
        except Exception as e:
            logger.exception(f"Beklenmeyen hata: {str(e)}")
        
        # Web sunucu için ek iş yapmaya gerek yok, veritabanını doğrudan erişilebilir kılabiliriz
        # PythonAnywhere'de /home/username/ altındaki dosyalar username.pythonanywhere.com/ 
        # üzerinden erişilebilir olacak
        
        time.sleep(60)  # 60 saniyede bir güncelle

if __name__ == "__main__":
    main_loop()
