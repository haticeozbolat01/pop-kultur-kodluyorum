# Netflix İzleme Panom (Streamlit)

**Netflix İzleme Geçmişi Panosu 2** yazısının uygulaması. Kendi Netflix izleme geçmişini yükleyip tıklanabilir bir panoya çevirir.

## Çalıştırmak

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tarayıcıda açılan sayfaya Netflix'ten indirdiğin `NetflixViewingHistory.csv` dosyasını yükle. Dosya yüklemezsen pano hayali bir örnek veriyle açılır.

Dosyan hiçbir yere kaydedilmez; uygulama onu yalnızca açık olan oturumda işler. Ham CSV dosyanı herkese açık bir yere yükleme.
