# Canlı Futbol Veri Toplama Servisi

Bu repo, canlı futbol maçlarının skorlarını ve oranlarını API'lerden çekip depolayan bir servisi içerir. Bu servis, [canli-dash](https://github.com/1sthillman/canli-dash) uygulamasıyla birlikte çalışır.

## 🔍 Özellikler

- **API Veri Çekme**: İddaa ve Bilyoner API'lerinden saniyede bir veri çekme
- **Veri Depolama**: SQLite veritabanında saklama
- **REST API**: Veri erişimi için basit HTTP endpointleri
- **Kalıcı Disk**: Render.com'un kalıcı diskinde veri saklama
- **7/24 Çalışma**: Sürekli çalışan background worker

## 🛠️ Kurulum

### Yerel Geliştirme

1. Gereksinimleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

2. Uygulamayı çalıştırın:
   ```bash
   python worker.py
   ```

### Docker İle Çalıştırma

```bash
docker build -t canli-worker .
docker run -d -p 10000:10000 -v ./data:/data --name canli-worker canli-worker
```

## 🚀 Render.com Deployment

1. [Render.com](https://render.com)'a giriş yapın
2. "New" -> "Background Worker" seçin
3. GitHub repo olarak bu repo'yu seçin
4. "Add a Persistent Disk" seçeneğini işaretleyin:
   - Boyut: 1 GB
   - Mount Path: `/data`
5. Environment Variable ekleyin:
   - `PORT`: `10000` 
6. "Create Background Worker" butonuna tıklayın

## 📡 API Endpoints

- `GET /`: Ana sayfa
- `GET /canli.db`: SQLite veritabanını indirme
- `GET /health`: Sağlık kontrolü

## 📋 Notlar

- Servis, İddaa ve Bilyoner'in API yapılarına bağımlıdır. API yapıları değişirse kod güncellenmelidir.
- Veritabanı dosyası sürekli büyür, belirli aralıklarla temizleme gerekebilir.
