# Ahrefs'ten Backlink Verisini Çekme

Ahrefs MCP'nin `site-explorer-all-backlinks` aracı, Site Explorer arayüzündeki Backlinks
raporunun birebir karşılığıdır. Aşağıdaki parametreler UI'daki filtrelerle eşleşir.

## Parametre karşılıkları

| UI'daki ayar | API parametresi |
|---|---|
| "One link per domain" filtresi açık | `aggregation: "1_per_domain"` |
| Domain girip subdomain'leri de dahil etme | `mode: "subdomains"` |
| "Show history" + tarih seçimi | `history: "since:YYYY-MM-DD"` |
| History kapalı (sadece canlı linkler) | `history: "live"` |
| Tüm zamanlar | `history: "all_time"` |

`aggregation: "1_per_domain"` kritik — bu olmadan tek bir domainden gelen yüzlerce link
ayrı satır olarak gelir ve hem analiz hacmi şişer hem de API birimi boşa gider. Disavow
kararı zaten domain seviyesinde verildiği için domain başına bir örnek link yeterlidir.

`history` parametresi yalnızca başlangıç tarihi alır, aralık almaz. Kullanıcı "2025 Ocak
ile 2025 Haziran arası" gibi kapalı bir aralık isterse `since:2025-01-01` ile çekip
`first_seen_link` alanı üzerinden sonradan filtrele.

## Örnek çağrı

```
mcp__ahrefs__site-explorer-all-backlinks(
  target: "ornekmarka.com",
  mode: "subdomains",
  aggregation: "1_per_domain",
  history: "since:2025-09-01",
  limit: 2000,
  order_by: "domain_rating_source:desc",
  select: "url_from,title,anchor,name_source,root_name_source,domain_rating_source,
           url_rating_source,traffic_domain,traffic,is_spam,is_dofollow,is_nofollow,
           is_content,tld_class_source,page_type_source,page_category_source,
           languages,links_external,http_code,first_seen_link,is_lost,link_group_count"
)
```

`select` içinde satır sonu kullanma — tek satır, virgülle ayrılmış olmalı. Yukarıdaki
okunabilirlik içindir.

## Kolon seçimi ve maliyet

Bazı kolonlar ek API birimi tüketir. Çalışmanın boyutu büyükse bunu hesaba kat:

- `traffic` ve `traffic_domain` — her biri 10 birim
- `refdomains_source`, `refdomains_source_domain`, `class_c` — her biri 5 birim

`traffic_domain` toxic analizi için vazgeçilmez: yüksek DR + sıfır organik trafik
kombinasyonu link satış ağlarının en güvenilir parmak izidir, o yüzden maliyetine rağmen
mutlaka seç. `refdomains_*` ve `class_c` kolonlarını ise analizde gerçekten kullanmayacaksan
seçme.

Kalan çalışma birimini `mcp__ahrefs__subscription-info-limits-and-usage` ile kontrol
edebilirsin; büyük bir profil çekmeden önce bakmak, işin ortasında limite takılmaktan iyidir.

## Analizde işe yarayan kolonlar ve neden

| Kolon | Ne işe yarar |
|---|---|
| `title` | Link satış ağlarının en hızlı teşhis yolu. "Directory Pages Index", "Buy Dofollow Backlinks", "seo_linkk_order Archives" gibi başlıklar domaini açmadan ele verir. |
| `anchor` | Alakasız veya aşırı optimize anchor (para anahtar kelimesi, yabancı dil, marka dışı) satın alınmış link sinyalidir. |
| `traffic_domain` | DR ile birlikte okunur. Yüksek DR + sıfır trafik = PBN. |
| `page_type_source` / `page_category_source` | Ahrefs'in AI sınıflandırması. Yetişkin içerik, kumar, dizin sayfası tespitinde ön eleme sağlar. |
| `languages` | Hedef pazarla alakasız dil (ör. Türk markasına Çince/Endonezce sayfadan link) otomatik spam ağı işaretidir. |
| `links_external` | Sayfadaki dış link sayısı çok yüksekse (yüzlerce) link çiftliği sayfasıdır. |
| `tld_class_source` | `gov` ve `edu` sınıfı domainleri beyaz listeye almak için. |
| `is_lost` | Kaybolmuş linkler disavow gerektirmez ama negatif SEO saldırısının zamanlamasını gösterir. |
| `link_group_count` | Aynı domainden kaç link geldiği. Tek domainden yüzlerce link sitewide footer/blogroll link'idir. |

## Veri gelmezse

`limit` varsayılanı 1000'dir; büyük profillerde bunu yükselt. API tek seferde çok büyük
yanıt döndüremiyorsa `order_by: "domain_rating_source:desc"` ile sayfalara böl ve
`where` filtresiyle DR aralıklarına ayırarak çek.

Kullanıcı Ahrefs MCP'ye erişemiyorsa ya da UI'dan export etmeyi tercih ediyorsa, manuel
export dosyası da kabul edilir. Ahrefs export'ları **UTF-16 kodlu ve sekme ayraçlı**
gelir — `pandas.read_csv(path, encoding="utf-16", sep="\t")` ya da
`csv.reader(open(path, encoding="utf-16"), delimiter="\t")` ile okunur. UTF-8 varsayıp
okumaya çalışırsan bozuk karakterlerle karşılaşırsın.
