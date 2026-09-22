# Domain İnceleme Protokolü

Toxic karar içerikle verilir, metrikle değil — bu yüzden domainlere fiilen bakmak akışın
merkezindedir. Ama "her domaini aç" kuralı 100+ domainlik bir gri kovada tıkanır. Bu dosya
inceleme işini üç katmana bölerek hem doğruluğu hem ölçeklenebilirliği korur.

## Katman 1 — Başlık ve metadata triyajı (araç gerekmez)

Elindeki `title`, `anchor`, `domain`, DR ve trafik verisiyle listeyi bir kez gözden geçir.
Domainlerin önemli bir kısmı buradan kesin olarak sınıflanır ve ziyaret gerektirmez:

**Ziyaretsiz temiz sayılabilecekler** — kimliği tartışmasız platformlar ve kurumlar:
arama motorları (yandex, google), harita servisleri (waze, yango), global pazaryerleri
(lazada, amazon), tanınmış yayınlar (vogue, ulusal gazeteler), AVM siteleri, uygulama
dizinleri, banka/kart kampanya sayfaları. Bunları açmak hiçbir şey öğretmez.

**Ziyaretsiz toxic sayılabilecekler** — başlığı kendini ele verenler:
"Directory Pages Index", "Buy Dofollow Backlinks", "Before Finding SEOExpress.org...",
"Manual Outreach Backlinks to Boost Domain Authority", "Alexa top domain list page 488".
Bir başlık onlarca domainde birebir tekrarlanıyorsa tek bir ağa bakıyorsun demektir.

Triyaj sonrası elinde kalan liste, gerçekten bilgi eksiği olan domainlerdir. Pratikte bu,
başlangıçtaki gri kovanın üçte biri kadar olur.

## Katman 2 — WebFetch ile toplu inceleme

Kalan domainler için varsayılan araç WebFetch'tir. Sayfayı çeker ve sorduğun soruya göre
özetler — ham HTML yerine cevap döndürdüğü için hem hızlıdır hem bağlamı şişirmez, hem de
birden fazla domaini aynı anda paralel sorgulayabilirsin.

Sorduğun soru kararı belirler, o yüzden genel değil spesifik sor:

> Bu site ne için var? Gerçek bir yayın mı yoksa link yerleştirmek için kurulmuş bir site
> mi? Sayfada kaç alakasız dış link var, içerik insan için mi yazılmış? Markadan doğal bir
> bağlamda mı bahsediliyor yoksa zorlama bir link mi? Kumar, yetişkin içerik veya
> SEO/backlink satışı ile ilgili öğe var mı?

Tek seferde 4-5 domaini paralel sorgula. 100 domain bile bu şekilde makul sürede biter.

**Erişilemeyen domainler beklediğinden fazla çıkar.** Spam ağları hızla kurulup kapanır;
404, DNS çözümlenememesi, SSL el sıkışma hatası ve 403 yaygındır. Bunları tekrar deneme
turuna sokma:

- **DNS yok / domain ölü + toxic imza taşıyor** → Disavow, notta "domain ölü" yaz
- **404 / 403 ama domain ayakta, imza yok** → Kontrol gerekli. Erişilemeyen bir domain
  zaten link değeri taşımıyor; acele disavow etmenin kazancı düşük, yanlış pozitif riski
  gerçek. Kullanıcıya sor.
- **Sitenin ana konusuyla alakasız sayfa + 404** → hacklenmiş olma ihtimali yüksek, ama
  doğrulayamadığın için Kontrol gerekli olarak işaretle ve şüpheni notta belirt.

## Katman 3 — Playwright ile hedefli ziyaret

Playwright'ı WebFetch'in yetmediği yerlerde kullan:

- WebFetch 403 döndürdü ama domain önemli (yüksek DR veya trafik)
- Sayfa JavaScript ile render ediliyor, WebFetch boş içerik getiriyor
- Yetişkin içerik şüphesi var ve görsel doğrulama gerekiyor
- Link yerleşiminin sayfadaki konumunu görmen gerekiyor

Kullanım:

1. `browser_navigate` ile git. Dönen yanıt zaten URL, sayfa başlığı ve HTTP durumunu
   verir — çoğu zaman karar için bu kadarı yeter, snapshot'a gerek kalmaz.
2. İçeriği görmen gerekiyorsa `browser_snapshot` al, ama **`filename` parametresiyle
   dosyaya yaz**. Link çiftliği sayfaları binlerce satır döndürür; doğrudan bağlama
   almak oturumu tıkar. Dosyaya yazıp `grep`/`wc` ile analiz et — zaten "kaç dış link
   var" sorusunun cevabı da böyle daha hızlı çıkar.
3. Ekran görüntüsünü yalnızca görsel doğrulama şartsa al.

**Diyalog uyarısı:** Bazı spam siteler JavaScript alert/confirm açar ve oturumu kilitler.
Beklenmedik davranış görürsen `browser_handle_dialog` ile kapat, tetikleyecek butonlara
tıklama.

## 100'den fazla domain varsa: Sonnet alt ajanlarına böl

İnceleme adımı bu çalışmanın token harcamasının yaklaşık %90'ıdır — her domain için bir
sayfa çekilir, okunur ve bir cümle yazılır. Bu iş yargı gerektirir ama derin muhakeme
gerektirmez; Sonnet rahatça yapar. Büyük profillerde bunu ana oturumda yürütmek maliyeti
gereksiz yere katlar.

**Kural:** incelenecek domain sayısı 100'ü aşıyorsa işi `Agent` aracıyla
`model: "sonnet"` alt ajanlarına dağıt.

**Bölme:** her alt ajana 60-80 domain ver. Daha küçük partiler kurulum maliyetini
(görev metni, protokol) gereksiz tekrarlar; daha büyükleri alt ajanın bağlamını doldurur.
Partileri aynı mesajda başlat ki paralel çalışsınlar.

**Partileri anlamlı böl.** Rastgele bölmek yerine aynı ağa ait domainleri tek partide
topla — alt ajan ağı bir kez tanır, kalanını hızla sınıflandırır. Yüksek DR'li domainleri
de kendi partisinde topla; bunlar en dikkatli bakılması gerekenlerdir.

**Alt ajana verilecek görev metni** şu parçaları içermeli:

```
Sana bir backlink domain listesi veriyorum. Her biri için sayfayı inceleyip
toxic olup olmadığına karar ver.

Marka: <marka>  |  Hedef pazar: <ülke>, beklenen diller: <tr,en>
Girdi dosyası: <yol>/parti-N.json
Çıktı dosyası: <yol>/parti-N-karar.json

YÖNTEM
- Her domain için WebFetch ile linkin bulunduğu URL'yi çek ve sor: bu site ne için
  var? Gerçek bir yayın/işletme mi, yoksa link yerleştirmek için mi kurulmuş?
  Sayfada kaç alakasız dış link var? Marka doğal bağlamda mı anılmış?
- 4-5 domaini aynı anda paralel çek.
- 404/DNS/SSL hatası alırsan tekrar deneme; aşağıdaki kurala göre işaretle.
- Aynı başlığı taşıyan seri domainleri tek tek açma; 2-3 örnek yeter, kalanını
  imza üzerinden sınıflandır ve notta belirt.

KARAR KURALLARI
- Karar İÇERİĞE göre verilir, metriğe göre değil. DR 0 / trafik 0 olan anlamlı bir
  site temizdir; DR 60 ama organik trafiği sıfır olan site PBN'dir.
- Link satışı, hacklenmiş site, otomatik içerik çiftliği -> "Disavow"
- Yetişkin içerik veya kumar -> "Disavow (kritik)"
- Markayı listeleyen site (AVM, rehber, kupon, uygulama dizini) -> "Temiz"
- Gerçek yayın/işletme, marka doğal bağlamda anılmış -> "Temiz"
- Ölü domain + toxic imza -> "Disavow"
- Erişilemiyor ama imza yok, ya da PR/satın alınmış link şüphesi -> "Kontrol gerekli"

ÇIKTI
Girdideki her kayda "aksiyon" ve "notlar" alanlarını ekleyip aynı JSON yapısında
çıktı dosyasına yaz. "notlar" tek cümlelik gerekçe olmalı ve ne gördüğünü
söylemeli ("DR 61 ama trafik sıfır, sayfa bir link satış dizini" gibi) - kullanıcı
bu notla markaya karşı kararı savunacak.

Bitirince sadece şunu bildir: kaç domain işledin, aksiyon dağılımı ne oldu,
hangi domainler için kullanıcı onayı gerekiyor.
```

Alt ajanların çıktılarını topladıktan sonra tek dosyada birleştir ve **kendin bir geçiş
yap**: "Kontrol gerekli" işaretlenenleri ve yüksek DR'li "Disavow" kararlarını gözden
geçir. Alt ajan kararlarını körlemesine kabul etme — nihai sorumluluk sende, özellikle
yanlış pozitifin pahalı olduğu yüksek DR'li domainlerde.

Yetişkin içerik tespitlerini de ayrıca doğrula; bu kategori markaya acil olarak
raporlanacağı için yanlış alarm vermek güven kaybettirir.

## Kimi incelemek zorundasın

Katman 1 sonrası kalan her domain, artı şu ikisi:

- **DR ≥ 30 veya aylık organik trafiği ≥ 10.000 olan her domain** — toxic imzası taşısa
  bile. Buradaki mantık asimetrik risk: güçlü ve meşru bir linki yanlışlıkla disavow etmek
  sıralama kaybettirir, oysa zayıf bir spam linkini bir tur fazla incelemek sadece zaman
  alır.
- **Sitenin konusuyla uyuşmayan sayfa barındıran her domain** — hacklenmiş site tespitinin
  tek yolu budur ve metrikten görünmez.

Buna karşılık aynı ağa ait seri domainleri tek tek açma. 200 tane `seoexpress-*.store`
aynı şablondan üretilmiştir; 3-5 örnek açıp ağı teyit et, kalanını imza üzerinden
sınıflandır ve notlar sütununa "X ağının parçası, örneklem üzerinden sınıflandırıldı" yaz.

## Neye bakarsın

Sayfayı açtığında cevaplaman gereken tek soru: **bu domain ne için var?**

| Gözlem | Ne anlama gelir |
|---|---|
| Onlarca alakasız dış link, konu bütünlüğü yok | Link çiftliği → toxic |
| "Backlink paketi", fiyat listesi, Telegram/WhatsApp iletişim | Link satış sitesi → toxic |
| Site bir konuda ama bu sayfa tamamen başka konuda | Hacklenmiş → toxic |
| Yetişkin içerik, kategori veya ürün | Kritik toxic |
| Otomatik üretilmiş, anlamsız veya çeviri kokan metin | İçerik çiftliği → toxic |
| Account Suspended / parked / domain satılık | Ölü spam ağı → toxic (imza varsa) |
| Markayı mağaza, adres, iletişim olarak listeliyor | Zararsız → temiz |
| Gerçek yayın, blog veya forum; markadan doğal bağlamda söz ediyor | Temiz |
| Gerçek site ama ürün yazısı sponsorlu/PR gibi duruyor | Kontrol gerekli → kullanıcıya sor |

## Ölçek yönetimi

Yüksek etkili domainlerle başla (DR ve trafik sırasına göre) — hem karar kalitesini en çok
etkileyen hem de kullanıcının ilk soracağı domainler onlardır. Her 20-30 domainde bir
ilerlemeyi bildir; uzun sessizlik yerine "80 domainin 30'u incelendi, 12 disavow önerisi
çıktı" demek kullanıcının süreci takip etmesini sağlar.

İncelediğin her domain için kararını ve tek cümlelik gerekçeni hemen kaydet. Hepsini sona
bırakırsan bağlam kaybolur ve notlar sütunu zayıflar — oysa kullanıcı raporu o sütun için
okuyacak.

## İnceleme sonrası

Karar veremediklerini **toplu halde** kullanıcıya sun. Tek tek sormak yerine kategorize
edilmiş bir liste ver:

> Şu 13 domain gerçek Türk güzellik/moda sitesi ve hepsinde ürün odaklı yazı içine marka
> linki yerleştirilmiş — tipik PR/satın alınmış link profili. Bunlar sizin çalışmanız mı?

Kullanıcı markanın link geçmişini senden iyi bilir; doğru soru çoğu belirsizliği tek
hamlede çözer. Cevabı aldığında notlar sütununa "kullanıcı teyit etti" diye işle — altı ay
sonra aynı soru tekrar sorulduğunda cevap raporda durur.
