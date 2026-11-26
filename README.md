# hr-price-tracker

Sustav za prikupljanje, analizu i usporedbu cijena proizvoda u hrvatskim trgovačkim lancima.
Svaki dan preuzima javno objavljene cjenike, svodi ih na zajednički oblik i sprema u SQLite
bazu, čime se gradi povijest cijena. Nad tim podacima moguće je pretraživati proizvode,
uspoređivati cijene po poslovnicama i pratiti kretanje cijena kroz vrijeme.

Projekt iz kolegija Skriptni jezici. Opis arhitekture nalazi se u [docs/arhitektura.md](docs/arhitektura.md).

## Instalacija

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Postavke (grad, broj dana, putanje) nalaze se u `config.toml`. Trenutno se prate
Konzumove poslovnice u Rijeci.

## Korištenje

```bash
python -m tracker fetch            # preuzmi cjenike (data/raw/)
python -m tracker import           # uvezi preuzete cjenike u bazu (data/tracker.db)
python -m tracker run              # fetch + import

python -m tracker search trajno mlijeko dukat
python -m tracker history 3850102019526     # šifra proizvoda ili barkod
python -m tracker compare 3850102019526
python -m tracker stats
```

Primjer:

```
$ python -m tracker history 3850102019526
Datum       Min     Max     Akcija
----------  ------  ------  ------
2026-11-12  2,49 €  2,49 €  da
...
2026-11-17  3,49 €  3,49 €
...
2026-11-24  2,49 €  3,49 €  da
2026-11-25  2,49 €  2,49 €  da
```

Ponovno pokretanje `fetch` i `import` ne duplicira podatke: već preuzete datoteke se
preskaču, a uvezene se pamte u tablici `import_log`.

## Automatsko pokretanje

Cjenici se objavljuju svako jutro do 8 sati. Za dnevno preuzimanje dodati u `crontab -e`:

```
0 9 * * * /putanja/do/hr-price-tracker/scripts/daily.sh
```

Ispis se sprema u `data/daily.log`.

## Testovi

```bash
pytest
```
