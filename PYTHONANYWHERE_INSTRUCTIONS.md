# PythonAnywhere'de Sürekli Çalışan Futbol Veri Servisi Kurulumu

Bu belgede, PythonAnywhere'de hiç durmadan sürekli çalışan Futbol Veri Servisi'nin nasıl kurulacağı adım adım anlatılmaktadır.

## 1. PythonAnywhere Hesabı Ayarları

1. [PythonAnywhere](https://www.pythonanywhere.com/) hesabınıza giriş yapın (1sthill)
2. Ücretsiz hesapla bile web uygulaması sürekli çalışacak şekilde ayarlanacaktır

## 2. Gerekli Dosyaları Yükleme

1. **Files** sekmesine tıklayın
2. `futbol_data` dizini oluşturun:
   ```bash
   mkdir ~/futbol_data
   ```
3. `combined_app.py` dosyasını ana dizininize yükleyin:
   - "Upload a file" butonuyla yükleyin veya
   - Bash konsolunda şu komutu çalıştırın:
   ```bash
   wget https://raw.githubusercontent.com/1sthillman/canli-worker/main/combined_app.py
   ```

## 3. Gerekli Kütüphaneleri Yükleme

Bash konsolunda şu komutu çalıştırın:
```bash
pip3 install --user flask requests
```

## 4. Web Uygulaması Yapılandırması

1. **Web** sekmesine tıklayın
2. "Add a new web app" butonuna tıklayın
3. Domain adını onaylayın (otomatik olarak `1sthill.pythonanywhere.com`)
4. **"Manual configuration"** seçin, Python 3.9 veya üstünü seçin
5. Web uygulaması yapılandırma sayfasında:
   - **Source code**: `/home/1sthill/`
   - **Working directory**: `/home/1sthill/`
   - **WSGI configuration file** linkine tıklayın ve açılan dosyada her şeyi silip aşağıdaki kodu yapıştırın:

```python
import sys

# PythonAnywhere'de ana dizininizi ekleyin
path = '/home/1sthill'
if path not in sys.path:
    sys.path.append(path)

from combined_app import app as application
```

6. **"Save"** butonuna tıklayın
7. **"Reload"** butonuna tıklayın

## 5. Servisin Test Edilmesi

1. Tarayıcıda `https://1sthill.pythonanywhere.com` adresine gidin
2. Ana sayfada güncel maçlar ve durum bilgilerini görmelisiniz
3. Veritabanını indirmek için `https://1sthill.pythonanywhere.com/canli.db` adresine gidebilirsiniz
4. API durumunu kontrol etmek için `https://1sthill.pythonanywhere.com/api/status` adresine gidebilirsiniz

## 6. Streamlit Uygulamasını Güncelleme

Streamlit Cloud'da deploy edilmiş uygulamanız için `streamlit_app.py` dosyasını güncellemelisiniz:

1. Veritabanı URL'ini `https://1sthill.pythonanywhere.com/canli.db` olarak ayarlayın
2. GitHub'a push yapın ve Streamlit Cloud'da yeniden deploy edin

## 7. Neden Bu Çözüm Hiç Durmaz?

PythonAnywhere'in ücretsiz planında web uygulamaları 3 ay boyunca hiç ziyaret edilmese bile çalışmaya devam eder. Sadece web uygulamalarında bu süreklilik vardır, ancak **task** ve **console** uygulamalarında yoktur.

Bu çözümde:
1. Flask web uygulaması sürekli çalışır (PythonAnywhere garantisi)
2. Web uygulaması başlatıldığında otomatik olarak worker thread'i de başlatılır
3. Worker thread'i arka planda sürekli veri toplar
4. Web uygulaması yeniden başlatılsa bile worker thread'i otomatik olarak yeniden başlar

## 8. Hata Durumlarını Kontrol Etme

1. Tarayıcıda `https://1sthill.pythonanywhere.com` adresine giderek log kayıtlarını görebilirsiniz
2. PythonAnywhere'de **Logs** sekmesinden error loglarını kontrol edebilirsiniz
3. Zorla veri güncelleme için `https://1sthill.pythonanywhere.com/force-update` adresine gidebilirsiniz

## 9. Sistemi Canlı Tutma

PythonAnywhere ücretsiz hesaplarda web uygulamaları 3 ay boyunca hiç ziyaret edilmezse devre dışı kalabilir. Bu durumu önlemek için:

1. Düzenli olarak web uygulamanızı ziyaret edin (ayda en az bir kez)
2. Veya bir cron job ile web uygulamanızı otomatik olarak ziyaret edecek bir script yazın

## 10. Veritabanı Temizleme

Veritabanı her gün büyüyecektir. Belirli aralıklarla eski verileri temizlemek gerekebilir. Bunun için:

1. `https://1sthill.pythonanywhere.com/api/clean-old-data` adresine giderek 30 günden eski verileri temizleyebilirsiniz
2. Veya yeni bir veritabanı oluşturmak için silebilir ve yeniden başlatabilirsiniz
