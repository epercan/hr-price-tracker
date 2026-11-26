# Arhitektura sustava

## Cilj

Sustav svaki dan preuzima javne cjenike hrvatskih trgovačkih lanaca, svodi ih na zajednički
oblik i sprema u bazu, čime se s vremenom gradi povijest cijena. Na temelju toga korisnik može
pretraživati proizvode, uspoređivati cijene po trgovinama, pratiti kretanje cijena te provjeriti
je li neka akcija stvarno sniženje.

Preuzimač, parseri i čišćenje podataka vlastiti su kod (bez oslanjanja na postojeće projekte
poput cijene-api).

## Opseg po kontrolnim točkama

| Točka | Sadržaj |
|---|---|
| 1 | Konzum: preuzimanje, parsiranje, čišćenje, SQLite baza, CLI naredbe (`search`, `history`, `compare`, `stats`) |
| 2 | Drugi lanac, povezivanje proizvoda bez barkoda, provjera akcija |
| 3 | Web sučelje (Flask + Chart.js), obavijesti, najjeftinija košarica, statistike |

Izvan opsega: preuzimanje svih ~570 Konzumovih poslovnica (prevelika količina podataka,
~1,4 GB dnevno). Prate se poslovnice odabrane u postavkama, filtrom po gradu ili popisom
šifri. Za početak to je Rijeka: 5 poslovnica (Osječka 71 SUPER, Nikole Tesle 9, Riva 16,
Vatroslava Lisinskog 2 i internet trgovina), sve dostupne dane (~14).

## Izvor podataka: Konzum

- Stranica `https://www.konzum.hr/cjenici?date=YYYY-MM-DD&page=N` sadrži poveznice na CSV
  datoteke, jednu po poslovnici, za zadnjih ~14 dana.
- Naziv datoteke sadrži tip i adresu poslovnice, šifru poslovnice i datum, npr.
  `20261126-SUPER,ŽITNA 1A 10310 IVANIĆ GRAD,0204,113241,26.11.2026, 05-24.CSV`.
- CSV je u UTF-8, ~26 000 redaka i ~2,4 MB po poslovnici. Stupci:
  naziv, šifra, marka, neto količina, jedinica mjere, maloprodajna cijena, poseban oblik prodaje
  (DA/NE), naziv posebnog oblika prodaje, cijena za jedinicu mjere, barkod, bazna cijena.
- Konzum nema zaseban stupac "najniža cijena u 30 dana"; sprema se "bazna cijena", a najniža
  cijena računa se iz vlastite povijesti.

## Tok podataka

```
izvor ──► fetch ──► data/raw/<lanac>/<datum>/*.csv.gz
                         │
                         ▼
                      parse  (parser po lancu → PriceRecord)
                         │
                         ▼
                      clean  (brojevi, jedinice, nazivi, marka/količina iz naziva)
                         │
                         ▼
                      load ──► data/tracker.db (SQLite)
                         │
                ┌────────┴────────┐
                ▼                 ▼
          CLI naredbe        web (točka 3)
```

- Sirovi podaci se spremaju komprimirani i ne mijenjaju se; obrada se može ponoviti bez
  ponovnog preuzimanja (bitno jer lanci brišu cjenike starije od 30 dana).
- Svaki korak se pokreće zasebno (`fetch`, `import`) ili zajedno (`run`).
- Uvoz je idempotentan: tablica `import_log` pamti uvezene datoteke.

## Lanci

Svaki lanac je klasa izvedena iz zajedničke osnovne klase:

- `discover(date)` — vraća popis datoteka (URL, poslovnica, datum) za zadani dan
- `parse(path)` — čita datoteku i vraća zapise u zajedničkom obliku `PriceRecord`

Novi lanac = novi modul + upis u registar lanaca.

## Baza podataka

```
chains ─< stores ─< prices >─ chain_products >─ products
                                     │
                              product_matches
```

- `chains` — lanci
- `stores` — poslovnice (šifra, tip, adresa, grad)
- `chain_products` — proizvod kako ga vodi pojedini lanac (šifra, naziv, marka, neto količina,
  jedinica, barkod, normalizirani naziv, izvučena količina)
- `products` — zajednički (kanonski) proizvod; za sada se povezuje preko barkoda
- `product_matches` — prijedlozi povezivanja bez barkoda s ocjenom i statusom
  (`pending` / `confirmed` / `rejected`); koristi se od točke 2
- `prices` — jedan zapis po danu, poslovnici i proizvodu: cijena, cijena po jedinici, akcija
  (da/ne + naziv), bazna cijena, najniža cijena u 30 dana (ako je lanac objavljuje)
- `import_log` — uvezene datoteke, broj redaka, vrijeme

## Čišćenje

- decimalni zarez/točka → `float`, prazne vrijednosti → `NULL`
- neto količina (`0.25 l`, `1.00 kg`, `500ml`) → količina + osnovna jedinica (l, kg, kom)
- nazivi: višestruki razmaci, velika/mala slova, uklanjanje dijakritika za usporedbu
- izvlačenje marke i količine iz naziva (priprema za povezivanje bez barkoda)

## Tehnologije

| Namjena | Alat |
|---|---|
| jezik | Python 3.12 |
| HTTP | requests |
| HTML | BeautifulSoup |
| CSV | `csv` (standardna biblioteka) |
| baza | SQLite (`sqlite3`), čisti SQL, bez ORM-a |
| CLI | `argparse` |
| postavke | `config.toml` (`tomllib`) |
| paralelno preuzimanje | `concurrent.futures.ThreadPoolExecutor` |
| testovi | pytest |
| automatsko pokretanje | cron |
| web (točka 3) | Flask, Chart.js |

Razmatrano i odbačeno: pandas (nepotrebno težak za čitanje red po red), Scrapy (prevelik alat
za jednu stranicu s poveznicama), PostgreSQL (treba poseban server), spremanje samo promjena
cijena umjesto dnevnih zapisa (ima smisla tek kod velikog broja poslovnica).

## Struktura projekta

```
hr-price-tracker/
├── tracker/
│   ├── __main__.py      CLI
│   ├── config.py
│   ├── fetch.py         preuzimanje
│   ├── chains/
│   │   ├── base.py      osnovna klasa, PriceRecord
│   │   └── konzum.py
│   ├── clean.py
│   ├── db.py            shema i upiti
│   └── load.py          uvoz u bazu
├── tests/
│   └── fixtures/
├── docs/
├── config.toml
├── requirements.txt
└── data/                (ne ide na git)
```
