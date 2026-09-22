# Playwright ile Domain İnceleme Protokolü

Toxic karar içerikle verilir, metrikle değil — bu yüzden domainleri fiilen açmak akışın
merkezindedir. Bu dosya ziyaretin nasıl yürütüleceğini tanımlar.

## Kimi ziyaret edersin

**Ziyaret edilecekler:**

1. **Gri kovadaki her domain.** Ön sınıflandırmada ne toxic imzasına ne beyaz listeye
   oturmuş olanlar. Asıl iş buradadır.
2. **DR ≥ 30 veya aylık organik trafiği ≥ 10.000 olan her domain** — toxic imzası taşısa
   bile. Buradaki mantık asimetrik risk: güçlü ve meşru bir linki yanlışlıkla disavow
   etmek sıralama kaybettirir, oysa zayıf bir spam linkini bir tur fazla incelemek sadece
   zaman alır. Yanlış pozitifin pahalı olduğu yerde gözle doğrula.

**Ziyaret edilmeyecekler:**

- Beyaz listedeki domainler (`.gov.tr`, `.edu.tr`, bilinen platformlar).
- Aynı ağa ait düşük DR'li seri domainler. 200 tane `seoexpress-*.store` domaini tek bir
  şablondan üretilmiştir; 3-5 örnek açıp ağı teyit et, kalanını imza üzerinden sınıflandır
  ve notlar sütununa "X ağının parçası, örneklem üzerinden sınıflandırıldı" yaz. Her birini
  tek tek açmak ne bilgi katar ne de kararı değiştirir.

## Nasıl ziyaret edersin

Playwright MCP araçlarını kullan. Domain başına iki sayfa yeterlidir: **linkin bulunduğu
sayfa** (`url_from`) ve gerekiyorsa **ana sayfa**. Link sayfası domainin markaya nasıl
baktığını, ana sayfa domainin ne olduğunu gösterir.

Verimli sıra:

1. `browser_navigate` ile `url_from` adresine git
2. `browser_snapshot` ile sayfanın yapısını al — görsel ekran görüntüsünden daha hızlı ve
   metin içeriğini doğrudan okunabilir verir
3. Karar netleşmediyse ana sayfaya git ve tekrar bak

Ekran görüntüsü (`browser_take_screenshot`) yalnızca yetişkin içerik şüphesinde ya da
sayfanın görsel düzeni karar için gerekliyse al — yavaş ve bağlam tüketir.

**Diyalog uyarısı:** Bazı spam siteler JavaScript alert/confirm açar ve bu oturumu
kilitler. Şüpheli bir sayfada beklenmedik davranış görürsen `browser_handle_dialog` ile
kapat, açılmasını tetikleyecek butonlara tıklama.

**Erişilemeyen domainler:** Parked, 404, DNS hatası veya zaman aşımı veren domainler için
tekrar deneme turuna girme. Bunları "Kontrol gerekli" olarak işaretle ve notlar sütununa
durumu yaz ("domain erişilemiyor / parked"). Linkin kendisi hâlâ Ahrefs indeksindeyse ve
domain spam imzası taşıyorsa disavow önerebilirsin, ama gerekçesini belirt.

## Neye bakarsın

Sayfayı açtığında cevaplaman gereken tek soru şu: **bu domain ne için var?**

| Gözlem | Ne anlama gelir |
|---|---|
| Sayfada onlarca alakasız dış link, konu bütünlüğü yok | Link çiftliği → toxic |
| "Backlink paketi", fiyat listesi, Telegram/WhatsApp iletişim | Link satış sitesi → toxic |
| Site bir konuda, ama bu sayfa tamamen başka konuda | Hacklenmiş → toxic |
| Yetişkin içerik, kategori veya ürün | Kritik toxic |
| Otomatik üretilmiş, anlamsız veya çeviri kokan metin | İçerik çiftliği → toxic |
| Markayı mağaza/adres/iletişim olarak listeliyor | Zararsız → temiz |
| Gerçek bir yayın, blog, forum; markadan doğal bağlamda söz ediyor | Temiz |
| Gerçek bir site ama ürün yazısı sponsorlu/PR gibi duruyor | Kontrol gerekli → kullanıcıya sor |

## Ölçek yönetimi

Büyük profillerde ziyaret sayısı yüzleri bulabilir. Şu sırayla ilerle:

1. Önce **yüksek etkili** olanları bitir (DR ve trafik sırasına göre). Bunlar hem karar
   kalitesini en çok etkileyen hem de kullanıcının ilk soracağı domainlerdir.
2. Sonra gri kovayı sırayla işle.
3. Her 20-30 domainde bir ara verip ilerlemeyi kullanıcıya bildir — uzun bir sessizlik
   yerine "80 domainin 30'u incelendi, şu ana kadar 12 disavow önerisi çıktı" demek
   kullanıcının süreci takip etmesini sağlar.

Ziyaret ettiğin her domain için kararını ve tek cümlelik gerekçeni hemen kaydet; hepsini
sona bırakırsan bağlam kaybolur ve notlar sütunu zayıflar.

## Ziyaret sonrası

Karar veremediğin domainleri **toplu halde** kullanıcıya sun. Tek tek sormak yerine
kategorize edilmiş bir liste ver:

> Şu 14 domain için onayınız gerekiyor. Hepsi gerçek yerel haber siteleri ve ürün odaklı
> içerik yayınlamışlar — markanın PR/link building çalışması mı, yoksa sizin dışınızda mı
> yerleşmiş?

Kullanıcı markanın link geçmişini senden iyi bilir; doğru soru çoğu belirsizliği tek
hamlede çözer.
