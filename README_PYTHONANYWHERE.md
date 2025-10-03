# PythonAnywhere Kurulum Talimatları

Bu belge, Canlı Futbol Veri Toplama Servisi'nin PythonAnywhere üzerinde nasıl kurulacağını adım adım anlatır.

## 1. PythonAnywhere Hesabı Oluşturma

1. [PythonAnywhere](https://www.pythonanywhere.com/)'e gidin
2. Ücretsiz bir hesap oluşturun
3. Giriş yapın

## 2. Dosyaları Yükleme

1. PythonAnywhere kontrol panelinde **Files** sekmesine tıklayın
2. `futbol_data` adında bir klasör oluşturun:
   ```
   mkdir ~/futbol_data
   ```
3. Dosyaları yükleyin:
   - `pythonanywhere_worker.py` dosyasını ana dizine yükleyin
   - `pythonanywhere_flask.py` dosyasını ana dizine yükleyin

## 3. Flask Web Uygulaması Kurulumu

1. **Web** sekmesine tıklayın
2. **Add a new web app** düğmesine tıklayın
3. **Manual configuration** seçin
4. Python sürümünü seçin (Python 3.10 önerilen)
5. **Code** bölümünde:
   - Source code: `/home/KULLANICIADI/pythonanywhere_flask.py`
   - Working directory: `/home/KULLANICIADI/`
   - WSGI yapılandırma dosyasını aşağıdaki gibi düzenleyin:

```python
# +++++++++++ FLASK ++++++++++++++
import sys
path = '/home/KULLANICIADI'
if path not in sys.path:
    sys.path.append(path)

from pythonanywhere_flask import app as application
```

6. **Save** düğmesine tıklayın ve web uygulamasını yeniden başlatın

## 4. Always-on Task Kurulumu

1. **Tasks** sekmesine tıklayın
2. **Schedule a new task** bölümüne gidin
3. **Command** alanına şu komutu yazın:
   ```
   python3 ~/pythonanywhere_worker.py
   ```
4. "Schedule" olarak "Always-on task (requires paid account)" seçin
   - Not: Ücretsiz hesapta bu seçenek olmayabilir, bu durumda ücretli hesaba yükseltmeniz gerekebilir
5. Alternatif olarak, ücretsiz hesapta saatlik çalışacak şekilde ayarlayabilirsiniz:
   ```
   00 * * * *
   ```
   Bu her saatin başında çalışacaktır.

## 5. Streamlit Uygulamasını Güncelleme

Streamlit uygulamasındaki DB_URL değişkenini PythonAnywhere URL'inize göre güncelleyin:

```python
# Veritabanı URL'i
DB_URL = "https://KULLANICIADI.pythonanywhere.com/canli.db"
```

## 6. Maintenance

- PythonAnywhere ücretsiz hesaplarda 3 ay kullanılmayan web uygulamaları devre dışı kalabilir
- Web uygulamanızı aktif tutmak için düzenli olarak kontrol edin
- Veritabanı her gün büyüyecektir, zaman zaman temizlemeniz gerekebilir

## Alternatif: Oracle Cloud Free Tier

Eğer PythonAnywhere "Always-on task" için ücretli hesap gerektiriyorsa, Oracle Cloud Free Tier kullanabilirsiniz:

1. [Oracle Cloud](https://www.oracle.com/cloud/free/) hesabı oluşturun
2. "Always Free" VM oluşturun (2 adet ücretsiz VM sunuyor)
3. Bu repo'daki dosyaları VM'e klonlayın
4. `worker.py` dosyasını systemd servisi olarak ayarlayın
