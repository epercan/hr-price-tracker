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

Postavke (grad, broj dana, putanje) nalaze se u `config.toml`.

## Testovi

```bash
pytest
```
