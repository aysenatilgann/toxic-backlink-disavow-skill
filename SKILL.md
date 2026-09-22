---
name: toxic-backlink-disavow
description: Bir domainin backlink profilini Ahrefs üzerinden çekip toxic link analizi yapar ve Google Search Console'a yüklenmeye hazır disavow listesi üretir. Domainleri WebFetch ve Playwright ile fiilen inceleyerek içerik ve amaç bazlı karar verir; yalnızca Ahrefs'in "is spam" sütununa veya DR/trafik metriklerine güvenmez. Büyük profillerde incelemeyi Sonnet alt ajanlarına bölerek token maliyetini düşürür. Şu taleplerde mutlaka kullan - "toxic backlink analizi", "disavow listesi hazırla", "zararlı backlinkleri tespit et", "backlink temizliği", "spam link analizi", "disavow dosyası güncelle", "şu domainin backlinklerini incele", "hangi linkleri reddetmeliyiz", "negatif SEO kontrolü", ya da kullanıcı bir Ahrefs backlink export dosyasıyla gelip "bunlardan hangileri zararlı" diye sorduğunda. Kullanıcı "disavow" kelimesini kullanmasa bile backlink profilinin temizlenmesinden bahsediyorsa tetikle.
---

# Toxic Backlink Analizi ve Disavow Listesi Üretimi

Bu skill, bir markanın backlink profilindeki zararlı linkleri tespit edip Google Search
Console'a yüklenebilir bir disavow dosyası üretir.

## Bu işin temel ilkesi

Toxic backlink kararı **içerik ve domainin amacına** göre verilir — metriklere göre değil.
Bu ayrımı içselleştirmen bu skill'in en kritik parçası, çünkü metrik bazlı otomatik
filtreleme hem meşru linkleri yok eder hem de gerçek spam'i kaçırır:

- **DR 0 / trafik 0 olması bir şeyi toxic yapmaz.** Yeni açılmış küçük bir blog, niş bir
  forum ya da yerel bir işletme sitesi anlamlı içerik barındırıyorsa disavow listesine
  alınmaz. Metrik düşüklüğü zarar değil, sadece değer azlığıdır.
- **DR 60 olması bir şeyi güvenli yapmaz.** Link satış ağları kendi aralarında link
  alışverişi yaparak yüksek DR üretir. DR 55-74 arası ama organik trafiği sıfır olan bir
  domain, klasik PBN profilidir.
- **Ahrefs'in `is_spam` sütunu tek başına yeterli değildir.** Yardımcı sinyaldir, karar
  mercii değil. Gerçek spam'in büyük kısmı bu sütunda `false` görünür.

Karar vermenin tek güvenilir yolu domaini açıp ne olduğuna bakmaktır. Bu yüzden akışın
merkezinde domainleri fiilen inceleme adımı vardır.

## Akış

### 1. Başlamadan önce iki şeyi sor

**a) Site hangi ülkede / pazarda hizmet veriyor?** Bu soruyu mutlaka sor ve cevabı almadan
başlama. Dil ve pazar bilgisi olmadan iki yönde birden hata yaparsın:

- Hedef pazarın dilindeki meşru siteleri yabancı sanıp toxic işaretlersin.
- Hedef pazarla hiç ilgisi olmayan dildeki spam'i olağan sanıp kaçırırsın.

Türkiye pazarına hizmet veren bir markaya Çince film sitesinden ya da Endonezyaca haber
sitesinden gelen link, içeriğine bakmaya gerek kalmadan otomatik spam ağı işaretidir.
Aynı link çok dilli global bir marka için olağan olabilir.

Pazar birden fazlaysa (ör. Türkiye + Almanya, ya da global) hepsini al; beklenen dil kümesi
buna göre genişler. Cevabı sınıflandırıcıya `--diller tr,en` biçiminde geçir.

**b) Hangi tarih aralığındaki backlinklerle çalışalım?**

> Son 12 ay, 2025-01-01'den bugüne, ya da tüm zamanlar?

Belirsizse son 12 ayı öner — negatif SEO saldırıları ve satın alınmış spam genelde yakın
dönemde yoğunlaşır, tüm zamanlar ise gereksiz hacim getirir. Bu cevabı sonraki adımda
kullanıcıya vereceğin export talimatında kullanacaksın, o yüzden önce bunu netleştir.

**Mevcut disavow dosyasını bu aşamada isteme.** O, çalışmanın sonunda, kullanıcı önerileri
onayladıktan sonra devreye girer (adım 8).

### 2. Kullanıcıdan Ahrefs export'unu iste

Veriyi kullanıcı indirip sana iletir. Tarih aralığı netleştikten sonra şu talimatı ver:

> Ahrefs'ten export alalım:
> 1. **Site Explorer**'a gidin, domaini girip taratın
> 2. Sol menüden **Backlinks** raporunu açın
> 3. **"One link per domain" filtresini açın** — bu kritik, filtresiz export'ta tek
>    domainden yüzlerce satır gelir ve liste gereksiz şişer
> 4. **Show history** ile tarih aralığını <kullanıcının verdiği aralık> olarak ayarlayın
> 5. **Export** edin ve dosyayı bana iletin

"One link per domain" filtresini ayrıca vurgula. Disavow kararı zaten domain seviyesinde
verildiği için domain başına bir örnek link yeterlidir; filtresiz bir export hem analiz
hacmini katlar hem de aynı domaini defalarca incelemene yol açar.

Dosya geldiğinde okumadan önce formatını kontrol et — Ahrefs export'ları **UTF-16 kodlu ve
sekme ayraçlıdır**. `scripts/hazirla.py` bunu kendiliğinden halleder; elle okuman gerekirse
`references/ahrefs-export.md` dosyasındaki notlara bak.

### 3. Normalize et

`scripts/hazirla.py` Ahrefs çıktısındaki URL'lerden kök domaini çıkarır (Public Suffix List
ile — `.com.tr`, `.co.uk` gibi çok parçalı uzantılar ve `web.app` gibi barındırma alanları
doğru ayrışsın diye) ve aynı kök domainden gelen tekrarları eler.

Bu aşamada `--disavow` parametresini **kullanma**. Mevcut listeyle karşılaştırma sona
bırakıldı; şimdi profilin tamamını analiz ediyorsun.

### 4. Ön sınıflandırma yap

`scripts/siniflandir.py --diller <pazar_dilleri>` bilinen imzalara göre kaba bir ayrım
yapar ve her domaini üç kovadan birine koyar: `toxic-imza`, `beyaz-liste`, `gri`.

Bu **karar değil, önceliklendirmedir**. Amaç inceleme emeğini doğru yere yöneltmek. İmza
listesi, dil değerlendirmesi ve beyaz liste mantığı için `references/siniflandirma.md` oku.

### 5. Domainleri incele

İnceleme üç katmanlıdır; hepsini tek bir araca yıkmak tıkanmaya yol açar:

1. **Başlık ve metadata triyajı** — kimliği tartışmasız platformlar ve başlığı kendini ele
   veren spam burada kesinleşir, açmaya gerek kalmaz.
2. **WebFetch ile toplu inceleme** — triyajdan geçemeyen her domain için varsayılan araç.
   Paralel çağrılabildiği için hızlıdır.
3. **Playwright ile hedefli ziyaret** — 403 dönen önemli domainler, JavaScript ile render
   edilen sayfalar, görsel doğrulama gerektiren yetişkin içerik şüphesi.

**İncelenecek domain sayısı 100'ü aşıyorsa işi Sonnet alt ajanlarına böl.** Bu bir
optimizasyon değil maliyet gereğidir: inceleme adımı tüm çalışmanın token harcamasının
yaklaşık %90'ıdır ve her domain için yapılan iş (sayfayı aç, ne olduğuna bak, tek cümlelik
gerekçe yaz) Sonnet'in rahatça yaptığı türden bir iştir. Bölme kuralları ve alt ajana
verilecek görev metni `references/domain-inceleme.md` dosyasında.

Protokol, hangi soruyu soracağın, erişilemeyen domainlerin nasıl ele alınacağı ve ölçek
yönetimi de aynı dosyada.

Katman 1 sonrası kalan her domaini incele, ayrıca **DR ≥ 30 veya trafiği ≥ 10.000 olan her
domaini** — toxic imzası taşısa bile. Yanlış pozitifin maliyeti asimetriktir: meşru ve
güçlü bir linki yanlışlıkla disavow etmek sıralama kaybettirir, zayıf bir spam linkini bir
tur fazla incelemek sadece zaman alır.

Buna karşılık aynı ağa ait seri domainleri tek tek açma — 200 tane `seoexpress-*.store`
aynı şablondandır; birkaç örnek yeter, kalanını imza üzerinden sınıflandır ve notlar
sütununda belirt.

### 6. Emin olamadıklarını kullanıcıya sor

İnceleme sonrası hâlâ karar veremediğin domainler olacak — özellikle:
- İçeriği anlamlı ama link yerleşimi şüpheli görünenler
- Markanın kendi PR/link building çalışması olabilecek siteler
- Erişilemeyen, parked ya da hata veren domainler (spam ağları hızla kapandığı için bu grup
  beklediğinden kalabalık çıkar)

Bunları toplu halde ve gerekçesiyle sun, tek tek sorup kullanıcıyı yorma. Kullanıcı markanın
link geçmişini senden iyi bilir; "bu sizin çalışmanız mı?" sorusu çoğu belirsizliği tek
hamlede çözer. Cevabı notlar sütununa "kullanıcı teyit etti" diye işle.

### 7. Raporu üret ve onaya sun

`scripts/rapor_uret.py` çalıştır — bu aşamada `--mevcut-disavow` **verme**. Üretilen Excel
raporu, önerilerin kullanıcı tarafından gözden geçirileceği belgedir.

**Excel sütunları**, bu sırada:

| Sütun | İçerik |
|---|---|
| Sayfa URL'i | Linkin bulunduğu tam URL |
| Domain Rating | Ahrefs DR |
| Trafik | Domainin aylık organik trafiği |
| Domain | Yalın kök domain (`www.` ve alt alan adı olmadan) |
| Page Title | Referans sayfanın başlığı |
| Anchor Text | Link metni |
| Önerilen Aksiyon | Disavow / Disavow (kritik) / Temiz / Kontrol gerekli |
| Notlar | Kararın gerekçesi, özellikle emin olmadıklarında |

Notlar sütununu boş bırakma alışkanlığı edinme — kullanıcı bu raporla markaya karşı karar
savunacak ve altı ay sonra "bu domaini neden reddetmiştik?" diye geri dönecek.

Raporu sunarken kategori kırılımını ver ve **kullanıcıdan onay iste**. Onay gelmeden
sonraki adıma geçme; disavow listesi markanın arama görünürlüğünü doğrudan etkileyen bir
dosyadır ve son sözü kullanıcı söyler.

### 8. Onay sonrası: mevcut listeyi al ve final teslimi yap

Kullanıcı önerileri onayladıktan **sonra** mevcut disavow dosyasını iste:

> Onaylanan liste hazır. Search Console > Disavow Links aracından mevcut listeyi indirip
> bana iletir misiniz? Yeni tespitleri onun üzerine ekleyip yüklemeye hazır final dosyayı
> vereceğim.

Dosya geldiğinde `scripts/rapor_uret.py`'ı bu kez `--mevcut-disavow` ile tekrar çalıştır.
Script mevcut listeyi korur, yeni domainleri sonuna ekler ve tekilleştirir — aynı domain iki
kez görünmez.

Final teslimde şunu söyle: mevcut listede kaç domain vardı, kaçı eklendi, toplam kaç oldu.
Dosya düz metindir ve hiçbir düzenleme yapılmadan doğrudan Search Console'a yüklenebilir
olmalıdır.

Mevcut listede olup bu çalışmada "Temiz" çıkan domainler varsa bunu ayrıca bildir — geçmiş
bir çalışmada yanlışlıkla reddedilmiş meşru bir link olabilir ve kullanıcı listeden çıkarmak
isteyebilir. Kendiliğinden çıkarma, kararı ona bırak.

## Sonuçları sunarken

Kullanıcı ajans tarafında çalışıyor ve bu raporu markaya sunacak. Terminal cevabında şunları
ver: kaç domain incelendi, kaç disavow önerisi çıktı, hangi kategorilerde yoğunlaştı, kaç
tanesi için onay bekleniyor. Kategori bazlı kırılım (kaç link satış ağı, kaç hacklenmiş site,
kaç yetişkin içerik) markaya anlatılabilir bir hikâye kurar.

Yetişkin içerikli domainler varsa bunu ayrıca ve net şekilde öne çıkar — marka güvenliği
açısından en kritik bulgudur ve genelde acil aksiyon gerektirir.
