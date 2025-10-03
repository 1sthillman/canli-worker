#!/usr/bin/env python3
import sqlite3, requests, time, json, logging, os
from flask import Flask, send_file
import threading

# Kalıcı disk yapılandırması
DB_FILE = "/data/canli.db"
os.makedirs("/data", exist_ok=True)

# Log yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLite veritabanı yapılandırması
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
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
                tarih = b_obj["esd"].split("T")[0] if "esd" in b_obj else ""
                saat = b_obj.get("strt", "")
                lig = b_obj.get("lgn", "")
                mbs = b_obj.get("mbs", "")
            
            # Veritabanına kaydet
            c.execute("INSERT INTO raw(mac_id,ev,dep,skor,dakika,oran,tarih,saat,lig,mbs) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (mac_id, ev, dep, skor, dakika, oran, tarih, saat, lig, mbs))
            processed += 1
        
        conn.commit()
        logger.info(f"{processed} adet maç veritabanına kaydedildi.")
    except Exception as e:
        logger.exception(f"Veri çekme hatası: {str(e)}")
        
def main_loop():
    """Ana döngü fonksiyonu, sürekli çalışır"""
    logger.info("Worker servisi başlatıldı.")
    while True:
        try:
            get_data()
        except Exception as e:
            logger.exception(f"Beklenmeyen hata: {str(e)}")
        time.sleep(1)  # 1 saniye bekle

# Flask web sunucusu
app = Flask(__name__)

@app.route("/")
def home():
    """Ana sayfa"""
    return "Canlı Futbol Veri Servisi"

@app.route("/canli.db")
def db():
    """Veritabanı indirme endpoint'i"""
    return send_file(DB_FILE, as_attachment=True)

@app.route("/health")
def health():
    """Sağlık kontrolü"""
    return {"status": "up", "timestamp": time.time()}

if __name__ == "__main__":
    # Ana döngüyü ayrı bir thread'de başlat
    threading.Thread(target=main_loop, daemon=True).start()
    
    # Flask sunucusunu başlat
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
