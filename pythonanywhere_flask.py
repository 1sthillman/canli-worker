"""
PythonAnywhere için Flask web uygulaması
Veritabanına web üzerinden erişim sağlar
"""
from flask import Flask, send_file
import os
from pathlib import Path

app = Flask(__name__)

# PythonAnywhere için dosya yolları
HOME = str(Path.home())
DATA_DIR = os.path.join(HOME, "futbol_data")
DB_FILE = os.path.join(DATA_DIR, "canli.db")

@app.route('/')
def home():
    """Ana sayfa"""
    return """
    <html>
        <head>
            <title>Canlı Futbol Veri Servisi</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #333; }
                .container { max-width: 800px; margin: 0 auto; }
                a { color: #0066cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Canlı Futbol Veri Servisi</h1>
                <p>Bu servis, canlı futbol maç verilerini toplar ve sunar.</p>
                <p><a href="/canli.db">Veritabanını İndir</a></p>
            </div>
        </body>
    </html>
    """

@app.route('/canli.db')
def db():
    """Veritabanı indirme endpoint'i"""
    return send_file(DB_FILE, as_attachment=True)

@app.route('/health')
def health():
    """Sağlık kontrolü"""
    import json
    return json.dumps({"status": "up"})

if __name__ == '__main__':
    app.run(debug=True)
