# Sınıflandırma: Ne Toxic, Ne Değil

Bu dosya ön sınıflandırmanın mantığını ve karar kriterlerini tanımlar. Ön sınıflandırma
bir **önceliklendirme aracıdır** — Playwright ziyaretlerini doğru yere yöneltmek içindir,
tek başına karar mercii değildir.

## Kesin toxic kategorileri

### 1. SEO / backlink satış siteleri

Tek işi link satmak olan domainler. Marka ile hiçbir konusal ilişkisi yoktur, linkiniz
oraya satın alınarak ya da otomatik olarak yerleştirilmiştir.

Başlık ve içerik imzaları:
- "Directory Pages Index", "Domain List Page", "Most Visited Website List"
- "Buy Dofollow Backlinks", "High DA Guest Post", "PBN Links", "Niche Edit"
- "Link Building Service", "Increase Domain Rating", "Trust Flow"
- Telegram/iletişim çağrıları: `@SEO_...`, `t.me/...`, "TG @..."

Domain imzaları: adında `seo`, `link`, `rank`, `backlink`, `boost`, `guestpost` geçen ve
uzantısı `.shop`, `.store`, `.site`, `.click`, `.agency`, `.online` olanlar. Bu ağlar
yüzlerce domaini aynı şablonla ürettiği için başlıkları da birbirinin aynısıdır — aynı
başlığın onlarca domainde tekrarlandığını görürsen tek bir ağa bakıyorsun demektir.

Metrik imzası: **DR 40-75 arası ama organik trafiği sıfır.** Bu kombinasyon neredeyse
istisnasız PBN'dir. Gerçek bir sitenin DR'si yükseldikçe trafiği de yükselir.

### 2. Yetişkin içerikli domainler — en kritik kategori

Cinsel içerik, kategori ya da ürün barındıran her domain toxic'tir ve marka güvenliği
açısından acil aksiyon gerektirir. Diğer kategorilerden farklı olarak bunlar yalnızca SEO
riski değil, itibar riskidir — raporda ayrıca öne çıkarılmalıdır.

İmzalar: domain adında veya sayfa başlığında `porn`, `sex`, `seks`, `sikiş`, `escort`,
`eskort`, `erotik`, `travesti`, `fetish`, `xxx`, `nude`, `webcam`, `+18`. Ahrefs'in
`page_category_source` alanı `/Adult` yolunu içeriyorsa da işaretle.

Türkçe kelimelerde yanlış pozitife dikkat: "gecelik", "iç giyim", "sütyen", "mayo" gibi
kelimeler tekstil markaları için tamamen meşru ürün terimleridir. Kelime kökü eşleşmesi
yerine bağlama bak — "gecelik modelleri" bir ürün sayfasıdır, toxic değildir.

Ayrıca link satış ağları sıklıkla "Best SEO Backlinks for Escort in ..." gibi başlıklar
kullanır; bunlar aslında 1. kategoridir ama yetişkin içerik bağlamı taşıdığı için aynı
aciliyetle ele alınır.

### 3. Hacklenmiş domainler

Meşru bir sitenin ele geçirilip gizli link enjekte edilmiş hali. Domain düzgün görünür
ama belirli dizinlerde alakasız spam sayfaları barındırır.

İmzalar:
- Başlıkta arşiv/kategori kalıpları: `seo_linkk_order Archives`, `links-dealer`,
  `masslinker`, `SEO CARTEL`, `Dark Side Links`
- Sitenin ana diliyle alakasız içerik (bir Alman kuaför sitesinde Türkçe SEO sayfası)
- Sitenin konusuyla tamamen alakasız enjekte içerik (bir sanat derneği sitesinde sigorta
  ya da kripto yazısı)
- Rastgele üretilmiş alt alan adları: `xk7d92.ornekdomain.com`

Hacklenmiş siteler disavow edilir — site sahibinin kötü niyeti olmasa da link zararlıdır.
Notlar sütununda "hacklenmiş, muhtemelen site sahibinin haberi yok" diye belirtmek,
markanın outreach yapmak isterse yolunu açık bırakır.

### 4. Otomatik içerik ve korsan içerik çiftlikleri

Hedef pazarla alakasız dilde, otomatik üretilmiş içerik barındıran domainler. Türk
markalarına gelen Çince film/dizi siteleri, Endonezyaca "Situs Berita" spam siteleri,
"Encyclopedia Q&A" tipi üretilmiş sayfalar bu gruba girer.

İmza: `languages` alanı hedef pazarla uyumsuz + domain rastgele karakterlerden oluşuyor
(`xho6dj.info`, `ocs1lp.asia`) + uzantı `.xyz`, `.asia`, `.info`, `.site`.

## Zararsız kategoriler — disavow edilmez

### Marka listeleme ve dizin siteleri

Markayı listeleyen, mağaza/adres/iletişim bilgisi veren siteler zararsızdır. Bunlar
markanın doğal dijital ayak izidir:

- AVM siteleri ("Mağazalar" sayfasında markanın yer alması)
- Şirket/firma rehberleri, iş ilanı siteleri, franchise portalları
- Logo/marka varlığı siteleri, teknoloji stack analiz siteleri
- İndirim kuponu ve kampanya siteleri
- Wikipedia, Google Play, App Store gibi platformlar

Bu sitelerin DR'si veya trafiği düşük olabilir — fark etmez. İçerik meşru ve amaç
listelemeyse disavow listesine alınmaz.

### Asla disavow edilmeyecekler

Bu gruplar ön sınıflandırmada otomatik olarak beyaz listeye alınır:

1. `.gov.tr`, `.edu.tr`, `.gov`, `.edu` uzantıları ve `tld_class_source` değeri `gov`
   veya `edu` olan her domain
2. Bilinen dizinler ve platformlar (Wikipedia, Google, Apple, LinkedIn, resmi kurum
   siteleri, KAP gibi düzenleyici platformlar)
3. AVM ve marka siteleri
4. **Markanın kendi link building çalışmaları** — bunu sen bilemezsin, kullanıcıya sor.
   Türk yerel haber sitelerinde yayınlanmış ürün odaklı içerikler tipik olarak satın
   alınmış PR link'leridir; markanın kendi çalışması olabilir. Karar vermeden önce
   kullanıcıya toplu halde sun.

## Karar matrisi

Kararı verirken sırayla şunu sor:

1. **Domainin var oluş amacı ne?** Link satmak ya da spam üretmekse → toxic. Gerçek bir
   iş, yayın, topluluk ya da hizmetse → devam et.
2. **İçerik anlamlı mı?** İnsan için yazılmış, konusu tutarlı bir site mi? Evet ise DR ve
   trafik sıfır olsa bile disavow etme.
3. **Link bağlamı makul mü?** Marka doğal bir şekilde mi anılmış, yoksa alakasız bir
   metne zorla mı yerleştirilmiş?
4. **Metrikler ne diyor?** Bu en son sorulur ve yalnızca 1-3 arası cevaplar belirsizse
   ağırlık taşır.

Metriklerin tek başına anlamı olmadığını gösteren tipik kombinasyonlar:

| DR | Trafik | İçerik | Karar |
|---|---|---|---|
| 0 | 0 | Anlamlı yerel işletme sitesi | Temiz — disavow etme |
| 61 | 0 | "Directory Pages Index" | Disavow |
| 44 | 12.000 | Yerel haber sitesi, ürün yazısı | Kontrol gerekli — markanın PR çalışması olabilir |
| 0 | 0 | `seoexpress-pbn-team.store` | Disavow |
| 97 | 3.6 milyar | Wikipedia | Temiz |

## Önerilen aksiyon değerleri

Excel raporunda "Önerilen Aksiyon" sütunu şu dört değerden birini alır:

- **Disavow (kritik)** — yetişkin içerik. Acil, ayrıca raporlanır.
- **Disavow** — link satış ağı, hacklenmiş site, içerik çiftliği.
- **Kontrol gerekli** — karar verilemedi, kullanıcı onayı bekleniyor. Gerekçe notlar
  sütununda açıklanır.
- **Temiz** — disavow edilmez.
