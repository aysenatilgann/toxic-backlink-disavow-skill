---
name: toxic-backlink-disavow
description: Bir domainin backlink profilini Ahrefs üzerinden çekip toxic link analizi yapar ve Google Search Console'a yüklenmeye hazır disavow listesi üretir. Domainleri WebFetch ve Playwright ile fiilen inceleyerek içerik ve amaç bazlı karar verir; yalnızca Ahrefs'in "is spam" sütununa veya DR/trafik metriklerine güvenmez. Mevcut disavow dosyasıyla kesişim kontrolü yaparak aynı domainin listede tekrarlanmasını engeller. Şu taleplerde mutlaka kullan - "toxic backlink analizi", "disavow listesi hazırla", "zararlı backlinkleri tespit et", "backlink temizliği", "spam link analizi", "disavow dosyası güncelle", "şu domainin backlinklerini incele", "hangi linkleri reddetmeliyiz", "negatif SEO kontrolü", ya da kullanıcı bir Ahrefs backlink export dosyasıyla gelip "bunlardan hangileri zararlı" diye sorduğunda. Kullanıcı "disavow" kelimesini kullanmasa bile backlink profilinin temizlenmesinden bahsediyorsa tetikle.
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

### 1. Başlamadan önce kullanıcıdan iki şey al

**a) Tarih aralığı.** Ahrefs'in `history` parametresi hangi tarihten itibaren kaybolan
linklerin de rapora dahil edileceğini belirler. Kullanıcıya sor:

> Hangi tarihten itibaren gelen backlinklerle çalışalım? (ör. son 12 ay, 2025-01-01'den
> bugüne, ya da tüm zamanlar)

Belirsizse son 12 ayı öner — negatif SEO saldırıları ve satın alınmış spam genelde yakın
dönemde yoğunlaşır, tüm zamanlar ise gereksiz hacim getirir.

**b) Mevcut disavow dosyası.** Bu adımı atlama. Kullanıcıdan Search Console'daki güncel
disavow dosyasını istemelisin:

> Search Console > Disavow Links aracından mevcut listeyi indirip bana iletir misin?
> (Yoksa ilk disavow çalışması olarak ilerleyebiliriz.)

Sebebi: mevcut listede zaten olan bir domaini tekrar analiz etmek hem boşa iş hem de
teslim dosyasında aynı domainin iki-üç kez görünmesine yol açar. Kesişim kontrolünü
**analiz başlamadan** yap, böylece inceleme emeğini de gereksiz domainlerde harcamazsın.

### 2. Ahrefs'ten veriyi çek

Parametreler ve `select` listesi için `references/ahrefs-cekme.md` dosyasını oku. Özet:
`aggregation: "1_per_domain"` (UI'daki "One link per domain" filtresinin karşılığı),
`mode: "subdomains"`, `history: "since:<tarih>"`.

### 3. Normalize et ve kesişimi düş

`scripts/hazirla.py` bunu yapar: Ahrefs çıktısındaki URL'lerden kök domaini çıkarır
(Public Suffix List ile — `.com.tr`, `.co.uk` gibi çok parçalı uzantılar ve `web.app`
gibi barındırma alanları doğru ayrışsın diye), mevcut disavow listesiyle karşılaştırır,
zaten kapsanmış olanları ayırır.

Kullanıcıya kaç domainin zaten listede olduğunu ve kaç yeni domainin analiz edileceğini
söyle. Bu, çalışmanın ölçeğini baştan görmesini sağlar.

### 4. Ön sınıflandırma yap

`scripts/siniflandir.py` bilinen imzalara göre kaba bir ayrım yapar ve her domaini üç
kovadan birine koyar: `toxic-imza`, `beyaz-liste`, `gri`.

Bu **karar değil, önceliklendirmedir**. Amaç inceleme emeğini doğru yere yöneltmek. İmza listesi ve beyaz liste mantığı için `references/siniflandirma.md` oku.

### 5. Domainleri incele

İnceleme üç katmanlıdır; hepsini tek bir araca yıkmak tıkanmaya yol açar:

1. **Başlık ve metadata triyajı** — listeyi bir kez gözden geçir. Kimliği tartışmasız
   platformlar (arama motorları, tanınmış yayınlar, AVM siteleri) ve başlığı kendini ele
   veren spam ("Directory Pages Index", "Buy Dofollow Backlinks") burada kesinleşir.
   Bunları açmak hiçbir şey öğretmez.
2. **WebFetch ile toplu inceleme** — triyajdan geçemeyen her domain için varsayılan araç.
   Sayfayı çekip sorduğun soruya cevap verir; paralel çağırabildiğin için 100 domain bile
   makul sürede biter.
3. **Playwright ile hedefli ziyaret** — WebFetch'in yetmediği yerler: 403 dönen önemli
   domainler, JavaScript ile render edilen sayfalar, görsel doğrulama gerektiren yetişkin
   içerik şüphesi.

Protokol, hangi soruyu soracağın, erişilemeyen domainlerin nasıl ele alınacağı ve ölçek
yönetimi için `references/domain-inceleme.md` oku.

Katman 1 sonrası kalan her domaini incele, ayrıca **DR ≥ 30 veya trafiği ≥ 10.000 olan
her domaini** — toxic imzası taşısa bile. Yanlış pozitifin maliyeti burada asimetriktir:
meşru ve güçlü bir linki yanlışlıkla disavow etmek sıralama kaybettirir, zayıf bir spam
linkini bir tur fazla incelemek sadece zaman alır.

Buna karşılık aynı ağa ait seri domainleri tek tek açma — 200 tane `seoexpress-*.store`
aynı şablondandır; birkaç örnek yeter, kalanını imza üzerinden sınıflandır ve notlar
sütununda belirt.

### 6. Emin olamadıklarını kullanıcıya sor

İnceleme sonrası hâlâ karar veremediğin domainler olacak — özellikle:
- İçeriği anlamlı ama link yerleşimi şüpheli görünenler (ör. konuyla alakasız bir haber
  sitesinde ürün odaklı bir yazı)
- Markanın kendi PR/link building çalışması olabilecek siteler
- Erişilemeyen, parked ya da hata veren domainler (spam ağları hızla kapandığı için bu
  grup beklediğinden kalabalık çıkar)

Bunları toplu halde ve gerekçesiyle sun, tek tek sorup kullanıcıyı yorma. Kullanıcı
markanın link geçmişini senden iyi bilir; "bu sizin çalışmanız mı?" sorusu çoğu belirsizliği
tek hamlede çözer.

### 7. Çıktıları üret

`scripts/rapor_uret.py` iki dosya üretir. Sütun yapısı ve disavow formatı için scripti
çalıştırman yeterli; detay `references/ciktilar.md` dosyasında.

**Excel raporu** — şu sütunlarla, bu sırada:

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
savunacak. "DR 61 ama organik trafiği sıfır, sayfa başlığı 'Directory Pages Index', link
satış dizini" gibi tek cümlelik bir gerekçe, listedeki her satırı denetlenebilir kılar.

**GSC'ye yüklenmeye hazır disavow dosyası** — mevcut liste + yeni tespitler birleşik,
düz metin, `domain:` formatında. Bu teslim setinin son adımıdır ve kullanıcının hiçbir
düzenleme yapmadan doğrudan Search Console'a yükleyebilmesi gerekir.

## Sonuçları sunarken

Kullanıcı ajans tarafında çalışıyor ve bu raporu markaya sunacak. Terminal cevabında
şunları ver: kaç domain incelendi, kaçı zaten listedeydi, kaç yeni disavow önerisi çıktı,
hangi kategorilerde yoğunlaştı, kaç tanesi için onayı bekleniyor. Kategori bazlı kırılım
(kaç tane link satış ağı, kaç tane hacklenmiş site, kaç tane yetişkin içerik) markaya
anlatılabilir bir hikâye kurar.

Yetişkin içerikli domainler varsa bunu ayrıca ve net şekilde öne çıkar — marka güvenliği
açısından en kritik bulgudur ve genelde acil aksiyon gerektirir.
