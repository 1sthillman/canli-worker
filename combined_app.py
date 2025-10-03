#!/usr/bin/env python3
"""
PythonAnywhere için Flask ve Worker Birleşik Uygulama
- Flask web sunucusu ve veri çekme işlemi tek bir uygulama içinde
- PythonAnywhere'in "Web" özelliğini kullanarak sürekli çalışır
- Worker thread'i arka planda sürekli veri toplar
- Ücretsiz hesapta bile hiç durmadan çalışır
"""
from flask import Flask, send_file, jsonify, render_template_string
import sqlite3
import requests
import time
import json
import logging
import os
import datetime
import threading
from pathlib import Path

# Log yapılandırması
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename="futbol_app.log",
    filemode="a"
)
logger = logging.getLogger(__name__)

# PythonAnywhere için dosya yolları
HOME = str(Path.home())
DATA_DIR = os.path.join(HOME, "futbol_data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "canli.db")

# SQLite veritabanı yapılandırması
def setup_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    
    # Ana veri tablosu
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
                   
    # Log tablosu
    c.execute("""CREATE TABLE IF NOT EXISTS log(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                   level TEXT,
                   message TEXT)""")
    
    conn.commit()
    return conn

# Flask uygulaması
app = Flask(__name__)

# Veritabanı bağlantısı
conn = setup_db()

# Log fonksiyonu
def log_to_db(level, message):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO log(level, message) VALUES(?, ?)", (level, message))
        conn.commit()
    except Exception as e:
        logger.error(f"Log yazma hatası: {str(e)}")

# Veri çekme fonksiyonu
def get_data():
    """İki API'den veri çeker ve veritabanına kaydeder"""
    logger.info("Veri çekiliyor...")
    log_to_db("INFO", "Veri çekme başlatıldı")
    
    # API istekleri
    headers = {
        "If-Modified-Since": "Sat, 1 Jan 2000 00:00:00 GMT",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        j1 = requests.get("https://sportsbookv2.iddaa.com/sportsbook/events?st=1&type=1&version=0", 
                        headers=headers, timeout=20).json()
        j2 = requests.get("https://www.bilyoner.com/api/v3/mobile/aggregator/gamelist/all/v1?tabType=9999&bulletinType=1&liveEventsEnabledForPreBulletin=true", 
                        headers=headers, timeout=20).json()
        
        # Veri işleme - API yapısını düzeltilmiş şekilde kullan
        sc_dict = j1.get("data", {}).get("sc", {})  # sc bir sözlük
        ev_list = j1.get("data", {}).get("events", [])  # events bir liste
        b_dict = j2.get("events", {})  # bilyoner events bir sözlük
        
        logger.info(f"IDDAA: {len(sc_dict)} maç, {len(ev_list)} event bulundu")
        logger.info(f"BILYONER: {len(b_dict)} etkinlik bulundu")
        log_to_db("INFO", f"IDDAA: {len(sc_dict)} maç, BILYONER: {len(b_dict)} etkinlik")
        
        # Mevcut tarih
        today = datetime.date.today().isoformat()
        
        # Mevcut maç ID'leri
        c = conn.cursor()
        c.execute("SELECT mac_id FROM raw WHERE date(ts) = date('now')")
        existing_ids = set([r[0] for r in c.fetchall()])
        
        # Günlük tabloyu temizle (aynı verileri tekrar tekrar eklememek için)
        if existing_ids:
            c.execute("DELETE FROM raw WHERE date(ts) = date('now')")
            conn.commit()
        
        processed = 0
        for mac_id, sc in sc_dict.items():
            try:
                # Skor bilgisi
                skor = f"{sc['ht']['c']}-{sc['at']['c']}"
                dakika = sc.get("min", "ST")
                
                # Eşleşen event bilgisi
                ev_obj = next((e for e in ev_list if e["i"] == sc["id"]), None)
                if not ev_obj:
                    logger.warning(f"Maç ID {mac_id} için event bulunamadı")
                    continue
                    
                ev = ev_obj["hn"]
                dep = ev_obj["an"]
                oran = "AÇIK" if any(m.get("s") == "1" for m in ev_obj.get("m", [])[:3]) else "KAPALI"
                
                # Bilyoner'den ek bilgiler
                bilyoner_id = str(ev_obj.get("bri", ""))
                b_obj = b_dict.get(bilyoner_id)
                
                if not b_obj:
                    tarih, saat, lig, mbs = today, "", "", ""
                else:
                    tarih = b_obj["esd"].split("T")[0] if "esd" in b_obj else today
                    saat = b_obj.get("strt", "")
                    lig = b_obj.get("lgn", "")
                    mbs = b_obj.get("mbs", "")
                
                # Veritabanına kaydet
                c.execute("INSERT INTO raw(mac_id,ev,dep,skor,dakika,oran,tarih,saat,lig,mbs) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (mac_id, ev, dep, skor, dakika, oran, tarih, saat, lig, mbs))
                processed += 1
                
            except Exception as e:
                logger.error(f"Maç ID {mac_id} işlenirken hata: {str(e)}")
                log_to_db("ERROR", f"Maç ID {mac_id} işlenirken hata: {str(e)}")
        
        # Meta veriyi güncelle
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", 
                  ("last_updated", now))
        c.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", 
                  ("record_count", str(processed)))
        
        conn.commit()
        logger.info(f"{processed} adet maç veritabanına kaydedildi.")
        log_to_db("INFO", f"{processed} adet maç veritabanına kaydedildi")
        
    except Exception as e:
        error_msg = f"Veri çekme hatası: {str(e)}"
        logger.exception(error_msg)
        log_to_db("ERROR", error_msg)
        return False
        
    return True

# Worker thread fonksiyonu
def worker_thread():
    """Arka planda sürekli veri çeken thread"""
    logger.info("Worker thread başlatıldı")
    log_to_db("INFO", "Worker thread başlatıldı")
    
    while True:
        try:
            get_data()
        except Exception as e:
            error_msg = f"Beklenmeyen worker hatası: {str(e)}"
            logger.exception(error_msg)
            log_to_db("ERROR", error_msg)
        
        # Her 60 saniyede bir veri çek
        time.sleep(60)

# Ana sayfa HTML şablonu
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Canlı Futbol Veri Servisi</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            line-height: 1.6;
            color: #333;
        }
        h1 { color: #2c3e50; }
        h2 { color: #3498db; margin-top: 30px; }
        .container { max-width: 1000px; margin: 0 auto; }
        a { 
            color: #3498db; 
            text-decoration: none;
            padding: 10px 15px;
            background: #f8f9fa;
            border-radius: 4px;
            display: inline-block;
            margin: 5px 0;
            border: 1px solid #e9ecef;
        }
        a:hover { background: #e9ecef; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        tr:hover { background-color: #f8f9fa; }
        .status {
            padding: 15px;
            background: #e8f4f8;
            border-radius: 4px;
            margin: 20px 0;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            font-size: 0.9em;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Canlı Futbol Veri Servisi</h1>
        <p>Bu servis, canlı futbol maç verilerini toplar ve sunar.</p>
        
        <div class="status">
            <strong>Son Güncelleme:</strong> {{ last_updated }}<br>
            <strong>Kayıt Sayısı:</strong> {{ record_count }}<br>
            <strong>Servis Durumu:</strong> {{ status }}
        </div>
        
        <h2>Linkler</h2>
        <ul>
            <li><a href="/canli.db">Veritabanını İndir</a></li>
            <li><a href="/api/status">API Durumu (JSON)</a></li>
            <li><a href="/api/matches">Güncel Maçlar (JSON)</a></li>
        </ul>
        
        <h2>Güncel Maçlar</h2>
        <table>
            <tr>
                <th>Ev Sahibi</th>
                <th>Skor</th>
                <th>Deplasman</th>
                <th>Dakika</th>
                <th>Lig</th>
                <th>Tarih/Saat</th>
                <th>Oran</th>
            </tr>
            {% for match in matches %}
            <tr>
                <td>{{ match.ev }}</td>
                <td><strong>{{ match.skor }}</strong></td>
                <td>{{ match.dep }}</td>
                <td>{{ match.dakika }}</td>
                <td>{{ match.lig }}</td>
                <td>{{ match.tarih }} {{ match.saat }}</td>
                <td>{{ match.oran }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <h2>Son Loglar</h2>
        <table>
            <tr>
                <th>Zaman</th>
                <th>Seviye</th>
                <th>Mesaj</th>
            </tr>
            {% for log in logs %}
            <tr>
                <td>{{ log.timestamp }}</td>
                <td>{{ log.level }}</td>
                <td>{{ log.message }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <div class="footer">
            <p>Canlı Futbol Veri Servisi | PythonAnywhere + Streamlit</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Ana sayfa"""
    try:
        c = conn.cursor()
        
        # Meta bilgilerini al
        c.execute("SELECT * FROM meta")
        meta = {row[0]: row[1] for row in c.fetchall()}
        
        last_updated = "Bilinmiyor"
        if "last_updated" in meta:
            try:
                dt = datetime.datetime.fromisoformat(meta["last_updated"])
                last_updated = dt.strftime("%d.%m.%Y %H:%M:%S")
            except:
                last_updated = meta["last_updated"]
        
        record_count = meta.get("record_count", "0")
        
        # Son maçları al
        c.execute("""
            SELECT ev, skor, dep, dakika, lig, tarih, saat, oran 
            FROM raw 
            ORDER BY id DESC LIMIT 20
        """)
        
        matches = []
        for row in c.fetchall():
            matches.append({
                "ev": row[0],
                "skor": row[1],
                "dep": row[2],
                "dakika": row[3],
                "lig": row[4],
                "tarih": row[5],
                "saat": row[6],
                "oran": row[7]
            })
        
        # Son logları al
        c.execute("SELECT timestamp, level, message FROM log ORDER BY id DESC LIMIT 10")
        logs = []
        for row in c.fetchall():
            logs.append({
                "timestamp": row[0],
                "level": row[1],
                "message": row[2]
            })
            
        return render_template_string(
            HTML_TEMPLATE,
            last_updated=last_updated,
            record_count=record_count,
            status="Aktif ✓",
            matches=matches,
            logs=logs
        )
    except Exception as e:
        logger.exception(f"Ana sayfa hatası: {str(e)}")
        return f"Hata: {str(e)}"

@app.route('/canli.db')
def db():
    """Veritabanı indirme endpoint'i"""
    return send_file(DB_FILE, as_attachment=True)

@app.route('/api/status')
def status():
    """API durum bilgisi"""
    try:
        c = conn.cursor()
        
        # Meta bilgilerini al
        c.execute("SELECT * FROM meta")
        meta = {row[0]: row[1] for row in c.fetchall()}
        
        # Kayıt sayısını al
        c.execute("SELECT COUNT(*) FROM raw")
        count = c.fetchone()[0]
        
        # Son log mesajını al
        c.execute("SELECT timestamp, level, message FROM log ORDER BY id DESC LIMIT 1")
        log = c.fetchone()
        last_log = {"timestamp": log[0], "level": log[1], "message": log[2]} if log else None
        
        return jsonify({
            "status": "up",
            "timestamp": datetime.datetime.now().isoformat(),
            "db_file": DB_FILE,
            "record_count": count,
            "last_updated": meta.get("last_updated", "Bilinmiyor"),
            "last_log": last_log
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/api/matches')
def matches():
    """Güncel maçları JSON olarak döndür"""
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM raw ORDER BY id DESC LIMIT 50")
        
        columns = [description[0] for description in c.description]
        result = []
        
        for row in c.fetchall():
            result.append(dict(zip(columns, row)))
        
        return jsonify({
            "count": len(result),
            "timestamp": datetime.datetime.now().isoformat(),
            "matches": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/force-update')
def force_update():
    """Zorla veri güncelleme"""
    try:
        success = get_data()
        return jsonify({
            "status": "success" if success else "error",
            "timestamp": datetime.datetime.now().isoformat(),
            "message": "Veri güncellendi" if success else "Veri güncellenirken hata oluştu"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

# Uygulama başlatma
if __name__ == "__main__":
    # Worker thread'i başlat
    worker = threading.Thread(target=worker_thread, daemon=True)
    worker.start()
    
    # Flask uygulamasını başlat
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
else:
    # WSGI sunucusu tarafından içe aktarıldığında worker'ı başlat
    try:
        # Daha önce worker başlatılmış mı kontrol et
        if not any(t.name == "worker-thread" for t in threading.enumerate()):
            worker = threading.Thread(target=worker_thread, daemon=True, name="worker-thread")
            worker.start()
            logger.info("Worker thread WSGI modunda başlatıldı")
            log_to_db("INFO", "Worker thread WSGI modunda başlatıldı")
    except Exception as e:
        logger.exception(f"Worker thread başlatma hatası: {str(e)}")
        log_to_db("ERROR", f"Worker thread başlatma hatası: {str(e)}")
