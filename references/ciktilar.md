# Teslim Seti

`scripts/rapor_uret.py` üç dosya üretir. Girdi olarak, her kayıtta karar ve gerekçe
bulunan bir JSON listesi bekler:

```json
[
  {
    "url": "https://ornek.com/sayfa",
    "domain": "ornek.com",
    "baslik": "Sayfa başlığı",
    "anchor": "Link metni",
    "dr": 61.0,
    "trafik_domain": 0,
    "kategori": "link-satis",
    "aksiyon": "Disavow",
    "notlar": "DR 61 ama organik trafiği sıfır; sayfa bir link satış dizini."
  }
]
```

Çalıştırma:

```bash
python scripts/rapor_uret.py \
  --kararlar kararlar.json \
  --out teslim/ \
  --marka "Marka Adı" \
  --mevcut-disavow mevcut-disavow.txt
```

## 1. Excel raporu

`<marka>-toxic-backlink-raporu.xlsx` — iki sayfa.

**"Toxic Backlink Analizi" sayfası**, sekiz sütun, bu sırada: Sayfa URL'i, Domain Rating,
Trafik, Domain, Page Title, Anchor Text, Önerilen Aksiyon, Notlar.

Satırlar aksiyon önceliğine göre sıralanır — kritik olanlar en üstte. Kullanıcı dosyayı
açtığında acil aksiyon gerektiren yetişkin içerikli domainleri hemen görür, aşağı
kaydırmak zorunda kalmaz. "Önerilen Aksiyon" hücreleri renk kodludur ve sütunlara filtre
uygulanmıştır.

**"Özet" sayfası** aksiyon dağılımını ve tespit kategorisi kırılımını verir. Bu, markaya
sunum yaparken doğrudan kullanılabilecek tablodur.

## 2. Birleşik disavow dosyası

`<marka>-disavow-BIRLESIK.txt` — mevcut liste + yeni tespitler, `domain:` formatında,
tekilleştirilmiş. Teslim setinin son adımı budur ve kullanıcının hiçbir düzenleme
yapmadan doğrudan Search Console'a yükleyebilmesi gerekir.

Dosyanın başında yorum satırları olarak güncelleme tarihi ve sayım özeti bulunur —
Google `#` ile başlayan satırları yok sayar, dolayısıyla yükleme için sorun çıkarmaz ama
dosyayı sonradan açan biri neye baktığını anlar.

Mevcut listedeki sıralama korunur, yeni domainler sona eklenir. Böylece kullanıcı iki
sürümü karşılaştırdığında farkı kolayca görür.

## 3. Yalnızca yeni eklenenler

`<marka>-disavow-YENI.txt` — bu çalışmada eklenen domainler. Markaya "bu ay şunları
ekledik" demek ya da değişikliği onaya sunmak için kullanılır.

## Notlar sütunu hakkında

Bu sütunu boş bırakma alışkanlığı edinme. Kullanıcı bu raporla markaya karşı karar
savunacak ve altı ay sonra "bu domaini neden reddetmiştik?" sorusuyla geri dönecek.

İyi bir not tek cümlede kararın dayanağını verir:

- "DR 61 ama organik trafiği sıfır, başlık 'Directory Pages Index' — link satış dizini."
- "Meşru bir sanat derneği sitesi, ancak /wp-content altına SEO spam sayfaları enjekte
  edilmiş; hacklenmiş, site sahibinin haberi olmayabilir."
- "Gerçek yerel haber sitesi, ürün odaklı içerik sponsorlu görünüyor — markanın PR
  çalışması olup olmadığı teyit edilmeli."
- "seoexpress ağının parçası, örneklem üzerinden sınıflandırıldı."

Emin olmadığın durumlarda bunu açıkça yaz. "Kontrol gerekli" aksiyonu ile birlikte net
bir soru içeren not, kullanıcının tek bakışta karar vermesini sağlar.
