# Gaziantep Kentsel Isı Adası — Bir Hipotezin Testi

> **Durum: Durduruldu.** Proje, belediyeye "ağaçlandırma bütçesi önce hangi mahalleye?" sorusunda yardım edecek bir karar aracı olarak başladı. Temel varsayımı, yani "yeşil mahalleler daha serin" fikri, ölçülen veriyle doğrulanamadı. Bu depo, bu sonuca nasıl varıldığını gösteriyor.

## Amaç

Uydudan ölçülen yüzey sıcaklığı, yeşillik ve nüfus bilgisini mahalle düzeyinde birleştirmek ve ağaçlandırma için şeffaf bir öncelik sırası çıkarmak. Ana şart şuydu: **her rakam bir uydu sahnesine ve tarihe izlenebilmeli; hiçbir sonuç varsayıma dayanmamalı.**

Bu yüzden ürünü kurmadan önce iki dur/devam kontrolü tanımlandı:

| Kontrol | Soru | Ölçüt |
|---|---|---|
| (a) Tutarlılık | Mahallelerin sıcaklık sıralaması günden güne aynı mı kalıyor? | Medyan Spearman ρ ≥ 0,7 |
| (b) İlişki | Yeşil oranı yüksek mahalleler daha serin mi? | Eğimin %95 güven aralığı tamamen 0'ın altında |

## Veri

| Veri | Kaynak |
|---|---|
| Yüzey sıcaklığı ve NDVI | Landsat 8/9 Collection 2 Level-2, Microsoft Planetary Computer (STAC). 2025 Haziran–Ağustos, bulut < %10; 31 sahne, 19 gün. Liste: [`data/sonuc/sahneler.csv`](data/sonuc/sahneler.csv) |
| Mahalle sınırları | OpenStreetMap, Geofabrik Türkiye kopyası (17 Kasım 2026). 9 ilçede 745 mahalle. **Resmî sınır değildir.** |
| Arazi örtüsü | ESA WorldCover 2021 v200 (10 m) |

Çalışma alanı: kent merkezi kutusu (37,25–37,50 D; 36,98–37,15 K), içindeki **132 mahalle** (Şahinbey 88, Şehitkamil 44).

Uydu, **yüzey** sıcaklığını ölçer; bu, hava sıcaklığı değildir. Ölçüm saati yerel saatle yaklaşık 11.00'dir.

## Bulgular

**(a) Tutarlılık: GEÇTİ.** 19 günün 361 gün çiftinde mahalle sıralamasının medyan korelasyonu ρ = 0,90 (en düşük 0,72). Kentin tamamını gören 7 günde ρ = 0,95. Yani ölçüm sağlam: mahallelerin sıcak ya da serin çıkması tesadüf değil.

**(b) Yeşil–sıcaklık ilişkisi: KALDI.**

| Analiz (132 mahalle, 7 gün medyanı) | Sonuç |
|---|---|
| Mahalle NDVI ↔ yüzey sıcaklığı | ρ = **+0,42**; NDVI 0,1 artınca **+1,2 °C** [%95 GA +0,6, +1,9] |
| Yalnızca yapılaşmış pikseller (WorldCover) | ρ = +0,40; +1,2 °C [+0,6, +1,7] |
| Ağaç örtüsü oranı ↔ sıcaklık | Anlamlı ilişki yok (GA 0'ı içeriyor) |
| **Çıplak arazi + kuru çayır oranı ↔ sıcaklık** | **ρ = +0,75** |

**Yorum.** Gaziantep'te yaz gündüzü en sıcak yüzeyler beton değil, kent çeperindeki **çıplak, kuru arazi**. Tamamen yapılaşmış merkez mahalleler (Yeşilevler, İstiklal, 60. Yıl, İnönü…) en serin grupta yer alıyor. Yarı kurak iklimlerde gündüz görülen bu durum literatürde "yüzey kentsel serinlik adası" olarak biliniyor. Mahalle düzeyindeki NDVI, gerçek yeşilliği kurumuş otlu boş araziden ayıramadı. Kentteki ağaç örtüsü de çok düşük olduğu için (çoğu mahallede %0–12) ağacın etkisi bu ölçekte ölçülemedi.

Bu nedenle "ağaçlandırma önceliği" ürünü savunulabilir bir temele oturtulamadı ve proje durduruldu. Farklı değişkenler deneyip ilişki aramaya devam etmek, sonuca uydurma riski taşıdığı için bilinçli olarak yapılmadı.

## Sınırlılıklar

- Landsat'ın termal ölçümü 100 m çözünürlüktedir (30 m'ye yeniden örneklenir). Çeperdeki yapı pikselleri, yanlarındaki arazinin ısısını da içerebilir.
- Yalnızca gündüz ölçümü vardır. Kentsel ısı adası etkisi geceleri daha belirgin olabilir; bu çalışmada test edilmedi.
- OSM mahalle sınırları resmî değildir.

## Yeniden üretme

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest tests
```

Geofabrik'ten `turkey-latest.osm.pbf` dosyasını `data/ham/` klasörüne indirdikten sonra betikleri sırayla çalıştırın:

| Betik | Ne yapar |
|---|---|
| `pipeline/01_mahalleler.py` | OSM dosyasından ilçe ve mahalle sınırlarını çıkarır |
| `pipeline/02_sahneler.py` | Landsat sahne listesini oluşturur |
| `pipeline/03_lst_ndvi.py` | Sahne başına mahalle sıcaklık ve NDVI medyanlarını hesaplar |
| `pipeline/04_kontrol.py` | Dur/devam kontrolleri (a) ve (b) |
| `pipeline/05_yapilasmis_deneme.py` | Yapılaşmış alan maskesiyle ek deneme |

Tasarım belgesi ve uygulama planı [`docs/superpowers/`](docs/superpowers/) klasöründedir.


