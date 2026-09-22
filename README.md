# toxic-backlink-disavow

Bir domainin backlink profilini Ahrefs üzerinden çekip toxic link analizi yapan ve Google
Search Console'a yüklenmeye hazır disavow listesi üreten [Claude Code](https://claude.com/claude-code)
skill'i.

## Neden

Toxic backlink kararı içerik ve domainin amacına göre verilir — metriğe göre değil.
Metrik bazlı otomatik filtreleme iki yönde de hata yapar: DR 0 / trafik 0 olan meşru bir
yerel işletme sitesini reddeder, DR 61 ama organik trafiği sıfır olan bir link satış
ağını kaçırır. Ahrefs'in `is spam` sütunu da yardımcı bir sinyaldir, karar mercii değil —
gerçek spam'in büyük kısmı o sütunda `false` görünür.

Bu skill bu yüzden domainleri fiilen inceleyerek karar verir — başlık triyajı, WebFetch
ile toplu inceleme ve gerektiğinde Playwright ziyareti.

## Akış

1. **Tarih aralığı sorulur** — hangi dönemden itibaren gelen backlinklerle çalışılacağı
2. **Mevcut disavow dosyası istenir** — analiz başlamadan kesişim kontrolü yapılır, böylece
   aynı domain listede tekrarlanmaz ve zaten reddedilmiş domainlere zaman harcanmaz
3. **Ahrefs'ten veri çekilir** — `aggregation: 1_per_domain`, `mode: subdomains`,
   `history: since:<tarih>` (Site Explorer arayüzündeki "One link per domain" + "Show
   history" ayarlarının birebir karşılığı)
4. **Ön sınıflandırma** — domainler toxic-imza / beyaz-liste / gri kovalarına ayrılır.
   Bu bir karar değil, inceleme emeğini doğru yere yöneltmek için önceliklendirmedir
5. **Katmanlı inceleme** — önce başlık/metadata triyajı (kimliği tartışmasız platformlar ve
   başlığı kendini ele veren spam burada kesinleşir), sonra kalanlar için WebFetch ile toplu
   inceleme, Playwright ise 403 dönen / JavaScript ile render edilen / görsel doğrulama
   gerektiren sayfalara ayrılır. Triyaj sonrası kalan her domain, artı DR ≥ 30 veya trafiği
   ≥ 10.000 olan her domain (toxic imzası taşısa bile) incelenir
6. **Belirsizler kullanıcıya sorulur** — toplu ve gerekçeli olarak
7. **Teslim seti üretilir**

## Tespit kategorileri

| Kategori | Örnek imzalar |
|---|---|
| Yetişkin içerik — **kritik** | Marka güvenliği riski, ayrıca raporlanır |
| SEO / backlink satış siteleri | "Directory Pages Index", "Buy Dofollow Backlinks", `seo*.shop`, yüksek DR + sıfır trafik |
| Hacklenmiş domainler | `seo_linkk_order Archives`, sitenin konusuyla alakasız enjekte sayfalar |
| Otomatik / korsan içerik çiftlikleri | Hedef pazarla alakasız dil, rastgele alt alan adları |

**Asla disavow edilmeyenler:** `.gov.tr` / `.edu.tr`, bilinen platform ve dizinler, AVM ve
marka listeleme siteleri, markanın kendi link building çalışmaları.

## Çıktılar

- `<marka>-toxic-backlink-raporu.xlsx` — Sayfa URL'i, Domain Rating, Trafik, Domain, Page
  Title, Anchor Text, Önerilen Aksiyon, Notlar sütunlarıyla; kritik satırlar üstte, renk
  kodlu, filtreli. Ayrıca kategori kırılımı veren bir Özet sayfası
- `<marka>-disavow-BIRLESIK.txt` — mevcut liste + yeni tespitler, tekilleştirilmiş,
  doğrudan Search Console'a yüklenebilir
- `<marka>-disavow-YENI.txt` — yalnızca bu çalışmada eklenenler

## Kurulum

```bash
git clone https://github.com/<kullanici>/toxic-backlink-disavow-skill.git \
  ~/.claude/skills/toxic-backlink-disavow
```

Claude Code'u yeniden başlatın; skill `/toxic-backlink-disavow` olarak görünür ve "toxic
backlink analizi", "disavow listesi hazırla" gibi taleplerde kendiliğinden devreye girer.

## Gereksinimler

- **Ahrefs MCP** — backlink verisini çekmek için. Alternatif olarak Site Explorer'dan
  alınmış manuel export dosyası da kabul edilir (UTF-16, sekme ayraçlı)
- **WebFetch** — domain incelemelerinin büyük kısmı için
- **Playwright MCP** — 403 dönen, JavaScript ile render edilen veya görsel doğrulama
  gerektiren sayfalar için
- **Python paketleri:** `tldextract`, `openpyxl`

```bash
pip install tldextract openpyxl
```

`tldextract` domain çıkarımını Public Suffix List üzerinden yapar; `.com.tr` ve `.co.uk`
gibi çok parçalı uzantılar ile `web.app` gibi barındırma alanları düz string kesmeyle
doğru ayrışmaz.

## Yapı

```
toxic-backlink-disavow/
├── SKILL.md                          Ana iş akışı
├── references/
│   ├── ahrefs-cekme.md               API parametreleri, kolon seçimi ve maliyeti
│   ├── siniflandirma.md              Toxic kategorileri, beyaz liste, karar matrisi
│   ├── domain-inceleme.md            Katmanlı inceleme protokolü ve ölçek yönetimi
│   └── ciktilar.md                   Teslim seti formatı
└── scripts/
    ├── hazirla.py                    Normalize + mevcut disavow kesişimi
    ├── siniflandir.py                İmza bazlı ön sınıflandırma
    └── rapor_uret.py                 Excel + birleşik disavow dosyası
```

Scriptler tek başına da çalışır:

```bash
python scripts/hazirla.py --backlinks export.csv --disavow mevcut.txt --out calisma/
python scripts/siniflandir.py --girdi calisma/yeni.json --out calisma/
python scripts/rapor_uret.py --kararlar calisma/kararlar.json --out teslim/ \
  --marka "Marka Adı" --mevcut-disavow mevcut.txt
```
