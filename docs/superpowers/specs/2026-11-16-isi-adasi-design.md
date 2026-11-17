# Gaziantep Kentsel Isı Adası — Belediye Karar Destek Aracı (Tasarım)

Tarih: 16 Kasım 2026 · Etkinlik: HASAT-13 Proje Pazarı (HKÜ, 25–26 Kasım 2026)
Poster teslimi: **22 Kasım 2026 Pazar 23.59**, hasat13@hku.edu.tr
Tema: İklim değişikliğiyle mücadele · Akıllı şehirler ve sürdürülebilir yaşam alanları

> İşaretler: **[karar]** = kullanıcı karar verdi. **[öneri]** = Claude önerdi, kullanıcı değiştirebilir.

## 1. Niyet ve neden

SolarAI projesi internetten toplanmış verilere ve varsayımlara dayanıyordu. Bu proje bunun tersi olsun: **ölçülmüş, resmî ve herkesin tekrar indirip kontrol edebileceği verilerle** belediyenin gerçek bir sorusuna cevap versin:

> "Ağaçlandırma/gölgelik bütçesi önce hangi mahalleye gitmeli?"

Araç; uydudan ölçülen yüzey sıcaklığını, yeşil alan oranını ve nüfusu mahalle düzeyinde birleştirir. Bunları şeffaf bir kuralla sıraya dizer ve kuralın ağırlıkları değiştiğinde sıranın ne kadar değiştiğini gösterir.

Başarı ölçütü: Jüri (Gaziantep Ticaret Odası, HKÜ Teknoloji Transfer Ofisi) bir rakamı sorduğunda, ekip o rakamın hangi uydu sahnesinden, hangi tarihten ve hangi hesapla geldiğini gösterebilmeli.

## 2. Hedefler, hedef olmayanlar, anti-hedefler

**Hedefler**
- Kent merkezindeki her mahalle için yaz yüzey sıcaklığı (LST), yeşil oranı ve nüfus değerlerini üretmek.
- Bu değerleri **kaynağıyla birlikte** (sahne kimliği + tarih) içeren küçük bir sonuç dosyası oluşturmak.
- Streamlit uygulaması geliştirmek: harita, tıklanınca açılan mahalle kartı, öncelik listesi, ağırlık kaydırıcıları ve duyarlılık göstergesi.
- 50×70 cm poster için rakam ve görsel üretmek.

**Hedef olmayanlar**
- Hava sıcaklığı tahmini yapmamak. Uydu **yüzey** sıcaklığını ölçer; bu ayrım her yerde doğru adlandırılır.
- "X ağaç dikersen Y °C düşer" gibi **nedensellik iddiası** veya müdahale simülasyonu yapmamak.
- Gerçek zamanlı ya da günlük güncellenen bir sistem kurmamak (yıllık yeniden hesaplama yeterli).
- Bütün il kapsamında analiz yapmamak (kırsal mahalleler kapsam dışında).

**Anti-hedefler** (çalışsa bile başarısızlık sayılır)
- Kaynağı gösterilemeyen tek bir rakam.
- Tek bir güne dayanan "en sıcak mahalle" iddiası.
- Ağırlıklar biraz değişince tamamen alt üst olan bir listeyi "kesin öncelik" diye sunmak.
- Ekibin anlatamadığı kod. HASAT şartnamesi özgün çalışma istiyor.

## 3. Kısıtlar

- Süre: Posterin 22 Kasım'a kadar hazır olması gerekiyor. Uygulama fuar günü (25 Kasım) çalışıyor olmalı.
- Maliyet: Ücretsiz ve hesap gerektirmeyen veri kaynakları kullanılacak.
- Barındırma: Streamlit Community Cloud kullanılacak. CPU için ayrı `app/requirements.txt` gerekli; uygulama ağır raster işlemi yapmamalı, sadece önceden hesaplanmış sonuç dosyasını okumalı.
- Ortam: Windows 10, Python 3.13. Kurulacak paketler: rasterio, rioxarray, geopandas, pystac-client, planetary-computer.
- Öğrenme: Kullanıcı her adımı anlayarak ilerlemek istiyor. Kod küçük, okunur ve anlatılabilir parçalar halinde yazılacak.

## 4. Yaklaşımlar (Approaches)

| | Yol | Artı | Eksi |
|---|---|---|---|
| **A** | **Python veri hattı** (STAC → rasterio/geopandas) → küçük sonuç dosyası → **Streamlit** uygulaması | Her adım kodda görünür ve GitHub'da tekrarlanabilir. Hesap gerektirmez. Ağır iş bir kez yerelde yapılır, uygulama hafif kalır. Ekip daha önce Streamlit yayınlamış. | Raster işlemeyi (projeksiyon, maskeleme, bölgesel istatistik) öğrenmek gerekir. Windows'ta kurulum zahmetli olabilir. |
| B | **Google Earth Engine** (bulutta hesap) → dışa aktarım → web uygulaması | Hesaplama hızlı ve veri kataloğu hazır. | Google hesabı ve proje kaydı gerekir. Hesap bulutta olduğu için hesabın içi daha az görünür ve platforma bağımlılık oluşur. "Kendi bilgi ve becerimiz" savunması zayıflar. |
| C | **QGIS ile elle analiz** → statik poster ve harita | Kod yok, hızlı ilk sonuç alınır. | Tekrarlanamaz (tıklama dizisi), etkileşimli karar aracı yok, duyarlılık analizi zor. Ürün değil, rapor olur. |

**Seçilen: A [karar].** Kullanıcının ana şartı "havada sonuç istemiyorum" olduğu için her rakamın izlenebilir ve tekrar üretilebilir olması gerekiyor. Bunu en iyi A sağlar. Betikler herkese açık; veri herkese açık bir katalogdan geliyor; aynı komutla aynı sonuç alınıyor. B'nin hızı bu ölçekte (yaklaşık 2 ilçe, yaklaşık 15 sahne) gerekli değil. C ise karar aracı üretmiyor.

## 5. Savunulabilirlik çerçevesi [karar]

Üç katman var. Her katman bir öncekine dayanır ve iddiaları birbirinden ayrı tutulur.

1. **Ölçüm.** Her mahalle için yaz LST'si ve yeşil oranı hesaplanır. Tek bir güne değil, **10–15 bulutsuz yaz gününün medyanına** dayanılır. Günler arası tutarlılık sayıyla verilir (sıra korelasyonu).
2. **İlişki.** Mahalleler genelinde yeşil oranı ile LST arasındaki ilişki ölçülür ve **güven aralığıyla** verilir. Kontrol değişkenleri rakım ve merkeze uzaklıktır. Dil şöyle olur: "yeşil oranı yüksek mahalleler ortalamada X °C daha serin *yüzey* sıcaklığına sahip". Nedensellik iddiası yoktur.
3. **Önceliklendirme.** Şeffaf ağırlıklı bir karar kuralı kullanılır ve **duyarlılık analizi** yapılır. Bu katman "doğru cevap" değil, "şu önceliklere göre şu sıra" der.

## 6. Veri

| Veri | Kaynak | Not |
|---|---|---|
| Yüzey sıcaklığı | Landsat 8/9 Collection 2 Level-2 (`landsat-c2-l2`), `lwir11` (ST_B10) | 30 m (termal 100 m'den yeniden örneklenmiş). Kelvin = DN × 0.00341802 + 149.0, sonra °C'ye çevrilir. Bulut/gölge `qa_pixel` ile maskelenir. 2025 Haziran–Ağustos, bulut < %10 → 29 sahne (16 Kasım'da doğrulandı). |
| Yeşil oranı | Aynı Landsat sahnelerinden NDVI (`red`, `nir08`) **[öneri]** | Aynı gün ve aynı piksel ızgarası kullanıldığı için LST ile tutarlıdır. Sentinel-2 (10 m, `B04`/`B08`) daha ince bir yeşil oranı için isteğe bağlıdır. |
| Mahalle sınırları | OSM Overpass, `admin_level=8` (Gaziantep'te 745 mahalle) | Resmî değildir. Örnek mahallelerle kontrol edilecek ve posterde "OSM sınırları, resmî değil" diye belirtilecek. Overpass isteğinde User-Agent başlığı zorunludur. |
| Nüfus | TÜİK ADNKS mahalle nüfusu | **Erişim doğrulanmadı.** Dur/devam kontrolü (c) bunu doğrulayacak. Yaş dağılımı (yaşlı/çocuk) bulunursa eklenecek. |
| Rakım | Copernicus DEM GLO-30 (`cop-dem-glo-30`, Planetary Computer) **[öneri]** | Kontrol değişkeni. |
| Hassas noktalar | OSM okul/hastane (`amenity=school/hospital`) **[öneri, isteğe bağlı]** | Mahalle başına sayı. |

Erişim: Planetary Computer STAC (`https://planetarycomputer.microsoft.com/api/stac/v1`) hesap gerektirmez. Dosyaları okumak için `planetary_computer.sign` ile SAS imzası alınır.

**Çalışma alanı [öneri]:** Şahinbey ve Şehitkamil'in kentsel mahalleleri. Kırsal mahallelerin elenmesi için basit ve açıklanabilir bir kural kullanılacak (ör. mahalle alanının en az %X'i yapılaşmış ya da nüfus yoğunluğu eşiğin üstünde). Eşik, veriye bakıldıktan sonra kullanıcıyla belirlenecek.

## 7. Aşama 0 — Dur/devam kontrolleri (planın ilk işi)

Projeye gömülmeden önce aşağıdaki kontroller yapılacak. Biri tutmazsa **durup kullanıcıyla konuşulacak**.

| Kontrol | Yöntem | Geçme ölçütü **[öneri]** |
|---|---|---|
| (a) Günler arası tutarlılık | Farklı yaz günlerinin LST haritalarından mahalle ortalamaları alınır. Gün çiftleri için Spearman sıra korelasyonu hesaplanır. | Çiftlerin medyanı ρ ≥ 0.7 |
| (b) Yeşil–sıcaklık ilişkisi | Mahalle medyan NDVI ile medyan LST arasında Spearman ilişkisi ve basit regresyon eğimi ile %95 güven aralığı hesaplanır. | Eğim negatif ve güven aralığı 0'ı içermiyor |
| (c) Nüfus verisi | TÜİK ADNKS'den Şahinbey ve Şehitkamil mahalle nüfusları indirilir, OSM mahalle adlarıyla eşleştirilir. | Kentsel mahallelerin ≥ %90'ı eşleşiyor |

## 8. Sistem parçaları

```
pipeline/            (yerelde, bir kez çalışır)
  01_mahalleler.py   OSM → mahalle sınırları (GeoPackage)
  02_sahneler.py     STAC araması → sahne listesi (CSV: id, tarih, bulut)
  03_lst_ndvi.py     her sahne: maske + LST + NDVI → mahalle istatistikleri
  04_birlestir.py    sahneler arası medyan + nüfus + rakım → sonuç dosyası
  05_analiz.py       tutarlılık, ilişki + güven aralığı, poster grafikleri
data/sonuc/          küçük sonuç dosyası (GeoJSON/GeoParquet) + sahneler.csv
app/                 Streamlit (sadece sonuç dosyasını okur)
  app.py, requirements.txt
```

**Sonuç dosyası (mahalle başına) [öneri]:** ad, ilçe, geometri, LST medyanı, LST günler arası değişkenliği, NDVI medyanı, yeşil oranı, nüfus, (yaşlı/çocuk oranı), rakım, merkeze uzaklık, kullanılan sahne sayısı. Ayrıca `sahneler.csv` içinde her sahnenin kimliği, tarihi ve bulut oranı bulunur. Böylece her rakam tarih ve sahneye kadar izlenebilir.

**Uygulama:**
- Harita: mahalleler LST'ye veya öncelik puanına göre renklendirilir.
- Mahalle kartı (tıklanınca): LST, yeşil oranı, nüfus, kent içindeki sırası, kullanılan sahne tarihleri.
- Öncelik listesi ve kaydırıcılar: puan = Σ ağırlık × normalize edilmiş gösterge. Göstergeler: ısı, yeşil eksikliği, nüfus, isteğe bağlı olarak hassas grup ve okul/hastane. Normalizasyon yöntemi **[öneri]** mahalleler arası yüzdelik sıradır; anlatması kolay ve aykırı değerlere dayanıklıdır.
- Duyarlılık: (1) mevcut ağırlıklarla varsayılan ağırlıklar arasında ilk 10'un ortaklığı; (2) **[öneri]** rastgele ağırlıklarla 1000 deneme yapılır ve her mahallenin ilk 10'a girme sıklığı gösterilir. Böylece "hangi ağırlıkla bakarsan bak, şu mahalleler hep öncelikli" denebilir.
- Yan özellik (isteğe bağlı): vatandaş için "mahallem ne kadar sıcak" görünümü.
- Her ekranda "Yüzey sıcaklığı (uydu), hava sıcaklığı değildir" notu yer alır.

## 9. Builder'a bırakılanlar

- Kütüphane sürümleri ve Windows kurulum yolu (pip wheel'leri yeterli olmalı).
- Projeksiyon: UTM 37N (EPSG:32637) önerilir.
- Bölgesel istatistik ayrıntıları: piksel merkezi mi, alan ağırlıklı mı; çok küçük mahallelerde minimum piksel sayısı.
- Grafik stili.

## 10. Açık konular (sonra kullanıcıdan)

- Ekip üyeleri, iletişim bilgileri, grup temsilcisi, danışman (poster ve e-posta konusu için gerekli).
- Kırsal/kentsel eleme eşiği (veri görüldükten sonra).
- Varsayılan ağırlıklar (ekip kararı; belki belediye bakışıyla gerekçelendirilecek).
