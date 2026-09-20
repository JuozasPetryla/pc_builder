# Projektas „PC Builder“


## Turinys

1. [Sprendžiamo uždavinio aprašymas](#1-sprendžiamo-uždavinio-aprašymas)
   1. [Sistemos paskirtis](#11-sistemos-paskirtis)
   2. [Funkciniai reikalavimai](#12-funkciniai-reikalavimai)
2. [Sistemos architektūra](#2-sistemos-architektūra)
3. [Realizuota programavimo aplinka](#realizuota-programavimo-aplinka)

## 1. Sprendžiamo uždavinio aprašymas

### 1.1. Sistemos paskirtis

Projekto tikslas – palengvinti vartotojams patiems sustatyti savo kompiuterį, suteikiant galimybe išsirinkti detales patiems bei patikrinti jų suderinamumą.

Veikimo principas – platformą sudaro dvi dalys: internetinė aplikacija, kuria naudosis žmonės, norintys susistatyti savo kompiuterį bei aplikacijų programavimo sąsaja (angl. Trump. API).

Naudotojas platforma galės naudotis neprisiregistravęs: pasirinkti kompiuterio dalis, sudaryti komplektą, patikrinti dalių suderinamumą, kainą ir įsigijimo vietas. Prisiregistravęs naudotojas papildomai galės išsaugoti ir viešai paskelbti savo sukurtus komplektus. Kitų naudotojų paskelbtus komplektus bus galima peržiūrėti, vertinti ir komentuoti. Administratorius galės tvarkyti kompiuterių detalių katalogus, administruoti registruotų naudotojų komplektus, komentarus bei atlikti visas funkcijas ką galės atlikti registruotas naudotojas.

### 1.2. Funkciniai reikalavimai

Toliau pateiktas pradinis viso projekto planas. Šiame etape įgyvendintas API;
faktiškai veikiančios operacijos ir Build hierarchija aprašytos skyriuje
„Realizuoti API metodai“. Frontend ir autentifikacija palikti kitam etapui.

#### Neregistruotas sistemos naudotojas galės

1. Peržiūrėti platformos reprezentacinį puslapį;
2. Registruotis ir prisijungti prie internetinės aplikacijos;
3. Peržiūrėti kompiuterio dalių katalogą;
4. Sudaryti asmeninio kompiuterio komplektą;
5. Patikrinti pasirinktų dalių suderinamumą;
6. Peržiūrėti komplekto kainą ir dalių įsigijimo vietas;

#### Registruotas sistemos naudotojas galės

1. Prisijungti ir atsijungti nuo internetinės aplikacijos;
2. Atlikti visas neregistruotam naudotojui prieinamas funkcijas;
3. Išsaugoti sudarytą kompiuterio komplektą;
4. Redaguoti ir pašalinti savo išsaugotus komplektus;
5. Viešai paskelbti savo sudarytą komplektą;
6. Dalintis paskelbto komplekto nuoroda;
7. Vertinti kitų naudotojų paskelbtus komplektus;
8. Komentuoti kitų naudotojų paskelbtus komplektus;
9. Redaguoti ir pašalinti savo komentarus;
10. Peržiūrėti komplektą sudariusio naudotojo viešą informaciją.

#### Administratorius galės

1. Tvarkyti kompiuterio dalių katalogą;
2. Šalinti netinkamus viešai paskelbtus komplektus;
3. Šalinti netinkamus komentarus;
4. Blokuoti arba šalinti taisykles pažeidžiančius naudotojus.

## 2. Sistemos architektūra

Sistemos sudedamosios dalys:

- Kliento pusė (angl. Front-End) – naudojant React;
- Serverio pusė (angl. Back-End) – naudojant Python FastAPI. Duomenų bazė – PostgreSQL.

Numatytas sistemos talpinimas AWS VPS serveryje, atskiruose Docker konteineriuose,
naudojant HTTPS. PC Builder API vykdo mainus su duomenų baze per SQLAlchemy ORM.
Toliau aprašyta įgyvendinta vietinė Docker Compose aplinka.

---

## Realizuota programavimo aplinka

Projektą sudaro trys pagrindiniai Docker konteineriai:

- `web` – React aplikacija, sukompiliuota su Vite ir pateikiama per Nginx;
- `api` – FastAPI REST sąsaja, naudojanti SQLAlchemy ORM ir Alembic migracijas;
- `db` – PostgreSQL duomenų bazė su išliekančiu Docker volume.

Papildomi `demo` ir `api-test` profiliai skirti greitai atsiskaitymo demonstracijai ir testams.

### Paleidimas

Reikalingi tik Docker ir Docker Compose:

```bash
cp .env.example .env
docker compose up --build --detach --wait
```

Paleidus pasiekiama:

- internetinė aplikacija – <http://localhost:8080>;
- Swagger UI – <http://localhost:8000/api/docs>;
- ReDoc – <http://localhost:8000/api/redoc>;
- OpenAPI JSON – <http://localhost:8000/api/openapi.json>;
- statinė OpenAPI kopija – [`api/openapi.json`](api/openapi.json).

Išsamus API naudojimo vadovas su užklausų pavyzdžiais: [`api/README.md`](api/README.md).

### Realizuoti API metodai

API turi 20 operacijų: komplektų, jų komponentų, komponentų pardavėjų pasiūlymų
ir atsiliepimų CRUD bei LIST. Visų lentelėje nurodytų kelių pradžia — `/api/v1`.

| Resursas | LIST `GET` ir CREATE `POST` | READ `GET`, UPDATE `PUT`, DELETE `DELETE` |
|---|---|---|
| Komplektas | `/builds` | `/builds/{build_id}` |
| Komponentas | `/builds/{build_id}/components` | `/components/{component_id}` |
| Pasiūlymas | `/builds/{build_id}/components/{component_id}/offers` | `/offers/{offer_id}` |
| Atsiliepimas | `/builds/{build_id}/reviews` | `/reviews/{review_id}` |

Privaloma hierarchija prasideda nuo **Build**:

```text
Build (1) ── (N) Component (1) ── (N) RetailOffer
    └─────── (N) Review
```

`components.build_id` ir `retail_offers.component_id` yra privalomi išoriniai
raktai. Jungiamoji `build_components` lentelė pašalinta: N:M ryšio nebėra.
Komponentas yra konkretaus komplekto dalies įrašas, todėl tas pats fizinis modelis
skirtinguose komplektuose saugomas atskirai, su atskirais pasiūlymais.
Kategorija (`cpu`, `gpu`, `memory` ir kt.) yra komponento laukas, ne atskira esybė.
Komplekte gali būti vienas kiekvienos kategorijos komponentas.

Pavyzdys, apimantis visus tris hierarchijos lygius:

```http
GET /api/v1/builds/1/components/1/offers
```

Sąrašai ir kūrimas naudoja įdėtinius kolekcijų URL. Pasiūlymų kolekcijos metodai
grąžina `404`, jei komponentas nepriklauso URL nurodytam komplektui.
Individualiems GET, PUT ir DELETE pakanka `/components/{component_id}` arba
`/offers/{offer_id}`: tėvai nustatomi pagal duomenų bazės ryšius, jų ID kartoti nereikia.
Tai nekeičia privalomos 1:N hierarchijos; `links` pateikia nuorodas į tėvus.
Seni įdėtiniai individualių komponentų ir pasiūlymų URL nebepalaikomi.

Komplektas kuriamas tik su jo metaduomenimis; komponentas sukuriamas per
`POST /builds/{build_id}/components`, pasiūlymas — per komponento `/offers`.
Senas `component_ids` priskyrimo būdas nebepalaikomas. Komponento `PUT`
keičia tik komponento laukus ir išsaugo jo pasiūlymus; pasiūlymai turi savo CRUD.
Komponento perkelti į kitą komplektą per `PUT` negalima.
Ištrynus komplektą ištrinami jo komponentai, jų pasiūlymai ir atsiliepimai.
Kitų komplektų įrašai nekeičiami.

Sudėtinis panaudojimo atvejis — `GET /builds/{build_id}`: vienas atsakymas
sujungia komplektą, komponentus, jų pasiūlymus ir atsiliepimus.

Visų esybių atsakymai turi `links.self` ir susijusių API resursų nuorodas.
Komplekto `links.components` veda į jo komponentus, komponento `links.offers`
— į trijų lygių pasiūlymų URL. Pasiūlymas turi nuorodas į save, komponentą ir
komplektą. Nuorodos yra santykinės serverio šaknies atžvilgiu.
Atskiras `product_url` laukas skirtas pardavėjo svetainei.

Visi keturi sąrašai turi `limit` (1–200, numatyta 100), `offset`
(0–2147483647) ir filtrą:

| Sąrašas | Filtras |
|---|---|
| Komplektai | `public_only=true` |
| Komplekto komponentai | `category=cpu` |
| Komponento pasiūlymai | `in_stock=true` arba `false` |
| Komplekto atsiliepimai | `rating=1..5` |

Sėkmingas `POST` grąžina `201`, skaitymas ir atnaujinimas — `200`,
`DELETE` — `204` be kūno. Neegzistuojantis arba nurodytai apimčiai
nepriklausantis resursas grąžina `404`. Pasikartojanti komponento kategorija
komplekte arba pardavėjas prie komponento — `409`.
Netinkamas payload, nežinomi laukai, per didelis `offset`, ilgesnė nei
500 simbolių pardavėjo nuoroda, nulinis simbolis ar `NaN`/`Infinity` —
`422`. Validacijos klaidos pateikia `loc`, `msg`, `type`.
Užklausos ir atsakymai su turiniu naudoja `application/json`.

### Duomenų bazė ir migracijos

API konteineris prieš paleidimą vykdo `alembic upgrade head`.

- `0001_schema` sukuria pradinę schemą.
- `0002_seed` įrašo pradinius prasmingus demonstracinius duomenis.
- `0003_builds` pakeičia bendrus katalogo ryšius į komponentų priklausomybę
  komplektui. Pirmajam komplektui išsaugomi originalūs komponentų ir pasiūlymų ID;
  kitiems sukuriamos nepriklausomos kopijos su tais pačiais duomenimis.
  Nepriskirti komponentai išsaugomi atskiruose juodraštiniuose komplektuose.
  Komplektų ir atsiliepimų kiekis papildomas iki mažiausiai 5.

Naujoje DB po migracijų yra 5 komplektai, 40 jiems priklausančių komponentų,
80 pardavėjų pasiūlymų ir 5 atsiliepimai. Tai 9 komponentų modelių įrašai
skirtinguose komplektuose. Kainos ir `example.com` nuorodos yra demonstracinės.

Esamai DB atnaujinti:

```bash
docker compose up --build --detach --wait api
```

DB ištrinti nereikia. Prieš esamos DB migravimą išsaugokite atsarginę kopiją:
`0003_builds` yra vienkryptė migracija. Vėliau savarankiškai pakeistų komponentų
ir kainų automatinis sujungimas į seną bendrą katalogą galėtų prarasti duomenis,
todėl grįžimui naudojama prieš migraciją išsaugota DB kopija.

Migracijų būseną galima patikrinti:

```bash
docker compose exec api alembic current
docker compose exec api alembic history
```

### Greita atsiskaitymo demonstracija

[Postman kolekcija](postman/PC_Builder_API.postman_collection.json) apima visas
20 operacijų. Ji sukuria du komplektus ir to paties modelio komponentus juose,
patikrina jų nepriklausomumą, trijų lygių apimtį, hypermedia, filtravimą,
puslapiavimą, sudėtinį atsakymą bei `404`, `409`, `422` scenarijus.
Laikini įrašai pašalinami; kolekcija nepriklauso nuo konkrečių pradinių ID.

```bash
docker compose --profile demo run --rm demo
```

Automatiniai API testai:

```bash
docker compose --profile test run --build --rm api-test
```

Testai naudoja izoliuotą atmintinę SQLite DB. Jie tikrina ir patį 1:N modelį,
netinkamų tėvinių ID atmetimą kolekcijų operacijoms, trumpus individualių objektų URL, kopijų nepriklausomumą,
šalinimo ryšius ir Postman aprėptį. Newman patikra vykdoma su PostgreSQL.

Trumpiniai: `make up`, `make demo`, `make test`.
`make reset` pašalina DB volume ir atkuria pradinius duomenis; paprastam
atnaujinimui šios komandos nereikia.

Sustabdyti aplikaciją, išsaugant DB:

```bash
docker compose down
```
