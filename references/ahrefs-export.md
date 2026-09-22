# Ahrefs Export'u: Alma, Okuma, Doğrulama

Veriyi kullanıcı Ahrefs arayüzünden indirip sana iletir. Bu dosya export talimatını,
dosyanın nasıl okunacağını ve neyin doğrulanması gerektiğini anlatır.

## Kullanıcıya verilecek talimat

Tarih aralığı netleştikten sonra:

> 1. **Site Explorer**'a gidin, domaini girip taratın
> 2. Sol menüden **Backlinks** raporunu açın
> 3. **"One link per domain" filtresini açın**
> 4. **Show history** ile tarih aralığını seçin
> 5. **Export** edin ve dosyayı bana iletin

## "One link per domain" neden şart

Disavow kararı domain seviyesinde verilir — `domain:ornek.com` satırı o domainden gelen
tüm linkleri kapsar. Dolayısıyla domain başına bir örnek link analiz için yeterlidir.

Filtre kapalıyken tek bir domainden gelen yüzlerce sitewide link (footer, blogroll,
şablon linki) ayrı satır olarak gelir. Sonuç: dosya gereksiz büyür, aynı domaini defalarca
incelersin ve gerçek domain sayısını göremezsin. Kullanıcı filtreyi açmayı unutmuşsa
`scripts/hazirla.py` aynı kök domainden gelen tekrarları zaten eler, ama bunu fark edersen
kullanıcıya bildir — çünkü Ahrefs filtresiz export'ta satır limitine takılıp profilin bir
kısmını hiç vermemiş olabilir.

## Dosya formatı

Ahrefs export'ları **UTF-16 kodlu ve sekme ayraçlıdır**. UTF-8 varsayıp okumaya çalışırsan
bozuk karakterlerle karşılaşırsın:

```python
import csv
csv.field_size_limit(10 ** 9)
with open(yol, encoding="utf-16", newline="") as f:
    satirlar = list(csv.DictReader(f, delimiter="\t"))
```

veya

```python
pandas.read_csv(yol, encoding="utf-16", sep="\t")
```

`scripts/hazirla.py` bunu kendiliğinden halleder; UTF-16/sekme, UTF-8/virgül ve
UTF-8/sekme kombinasyonlarını sırayla dener, ayrıca `.xlsx` ve `.json` de kabul eder.

## Beklenen sütunlar

Export'taki sütun adları `hazirla.py` içindeki `ALAN_ESLEME` tablosuyla eşlenir. Analiz
için kritik olanlar:

| Export sütunu | Ne işe yarar |
|---|---|
| `Referring page URL` | Zorunlu. Kök domain bundan çıkarılır |
| `Referring page title` | Link satış ağlarının en hızlı teşhis yolu. "Directory Pages Index", "Buy Dofollow Backlinks" gibi başlıklar domaini açmadan ele verir |
| `Anchor` | Alakasız veya aşırı optimize anchor, satın alınmış link sinyalidir |
| `Domain rating` | Tek başına karar vermez, trafikle birlikte okunur |
| `Domain traffic` | **Analizin en kritik sütunu.** Yüksek DR + sıfır organik trafik, link satış ağlarının en güvenilir parmak izidir |
| `Language` | Hedef pazarla alakasız dil, otomatik spam ağı işaretidir (bkz. `--diller`) |
| `External links` | Sayfadaki dış link sayısı yüzlerceyse link çiftliği sayfasıdır |
| `Is spam` | Yardımcı sinyal, karar mercii değil |
| `Page category` | Ahrefs'in AI sınıflandırması; yetişkin içerik ön elemesinde işe yarar |
| `Lost status` / `First seen` | Kayıp linkler disavow gerektirmez ama saldırının zamanlamasını gösterir |

Bir sütun eksikse analiz yine çalışır, sadece o sinyali kullanamazsın. `Domain traffic`
eksikse kullanıcıdan export'u o sütunla tekrar almasını iste — onsuz PBN tespiti ciddi
şekilde zayıflar.

## Dosya geldiğinde doğrula

`hazirla.py` çıktısındaki `toplam_kayit` ve `analiz_edilecek` sayılarını kullanıcıya
bildir. İkisi arasında büyük fark varsa (ör. 5.000 kayıt → 900 domain) "One link per
domain" filtresi kapalı gelmiş demektir; bunu söyle ve gerekirse export'u tekrar istemeyi
öner.

Kayıt sayısı beklenenden çok düşükse (ör. birkaç yüz) tarih aralığı fazla dar seçilmiş ya
da export satır limitine takılmış olabilir.

## Alternatif: Ahrefs MCP ile çekme

Kullanıcı export veremiyorsa ve oturumda Ahrefs MCP varsa veri doğrudan çekilebilir:

```
mcp__ahrefs__site-explorer-all-backlinks(
  target: "ornekmarka.com", mode: "subdomains",
  aggregation: "1_per_domain", history: "since:2025-09-01",
  order_by: "domain_rating_source:desc",
  select: "url_from,title,anchor,domain_rating_source,traffic_domain,traffic,is_spam,
           is_dofollow,tld_class_source,page_category_source,languages,links_external,
           http_code,first_seen_link,is_lost,link_group_count"
)
```

`aggregation: "1_per_domain"` UI'daki "One link per domain" filtresinin, `history:
"since:<tarih>"` ise "Show history" ayarının karşılığıdır.

Bu yolun iki zorluğu var, o yüzden varsayılan değil:

- **Tek çağrı `limit`ten bağımsız olarak ~500 satırda tavan yapar.** Profili tamamlamak
  için sayfalaman gerekir: `order_by` ile DR'ye göre çek, dönen son kaydın DR'sine bak,
  sonra `where: {"and":[{"field":"domain_rating_source","is":["lte", <son_DR>]}]}` ile
  altını iste, iki partiyi `url_from` üzerinden tekilleştirerek birleştir. İkinci parti
  tavanın altında bir sayı döndürdüyse profil tamamlanmış demektir.
- **Büyük yanıtlar bağlama sığmaz** ve otomatik olarak bir dosyaya kaydedilir. Bu aslında
  işine yarar — dosyayı doğrudan `hazirla.py`'a besle. Dosya
  `[{"type":"text","text":"<gerçek json>"}]` sarmalayıcısındadır:

  ```python
  raw = json.load(open(dosya, encoding="utf-8"))
  kayitlar = json.loads(raw[0]["text"])["backlinks"]
  ```

`traffic` ve `traffic_domain` sütunları 10'ar API birimi tüketir; `traffic_domain`
vazgeçilmez olduğu için maliyetine rağmen mutlaka seç. Kalan birimi
`mcp__ahrefs__subscription-info-limits-and-usage` ile, profil büyüklüğünü
`site-explorer-backlinks-stats` ile önceden kontrol edebilirsin.
