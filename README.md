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

2.1. pav. Pavaizduota kuriamos sistemos diagrama. Sistemos talpinimui yra naudojamas AWS VPS serveris. Kiekviena sistemos dalis yra diegiama tame pačiame serveryje, atskiruose Docker konteineriuose. Internetinė aplikacija pasiekiama per HTTPS. Šios sistemos veikimui yra reikalingas PC Builder API, kuris pasiekiamas per aplikacijų programavimo sąsają. Pats Pharma API vykdo mainus su duomenų baze ir tam naudoja SQLAlchemy ORM.

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

### Realizuoti API metodai

Swagger dokumentacijoje metodai aiškiai atskirti į keturias grupes. Trys pagrindiniai
taikomosios srities objektai turi po penkis metodus: keturias CRUD operacijas ir
vieną sąrašo operaciją. Papildoma komponentų ir specifikacijų grupė skirta
komplekto komponentų priskyrimui, administravimui ir suderinamumui.

| Nr. | Metodas | Kelias | Paskirtis | Sėkmės kodas |
|---:|---|---|---|---:|
| 1 | `GET` | `/api/v1/components` | Gauti ir filtruoti komponentų katalogą | 200 |
| 2 | `POST` | `/api/v1/components` | Sukurti komponentą su pardavėjų pasiūlymais | 201 |
| 3 | `GET` | `/api/v1/components/{component_id}` | Gauti komponentą | 200 |
| 4 | `PUT` | `/api/v1/components/{component_id}` | Pilnai atnaujinti komponentą | 200 |
| 5 | `DELETE` | `/api/v1/components/{component_id}` | Pašalinti komponentą | 204 |
| 6 | `GET` | `/api/v1/builds` | Gauti komplektus, kainas ir suderinamumą | 200 |
| 7 | `POST` | `/api/v1/builds` | Sukurti komplektą | 201 |
| 8 | `GET` | `/api/v1/builds/{build_id}` | Gauti komplektą | 200 |
| 9 | `PUT` | `/api/v1/builds/{build_id}` | Pilnai atnaujinti komplektą | 200 |
| 10 | `DELETE` | `/api/v1/builds/{build_id}` | Pašalinti komplektą | 204 |
| 11 | `GET` | `/api/v1/components/{component_id}/offers` | Gauti komponento pardavėjų pasiūlymų sąrašą | 200 |
| 12 | `POST` | `/api/v1/components/{component_id}/offers` | Sukurti komponento pardavėjo pasiūlymą | 201 |
| 13 | `GET` | `/api/v1/offers/{offer_id}` | Gauti pardavėjo pasiūlymą | 200 |
| 14 | `PUT` | `/api/v1/offers/{offer_id}` | Pilnai atnaujinti pardavėjo pasiūlymą | 200 |
| 15 | `DELETE` | `/api/v1/offers/{offer_id}` | Pašalinti pardavėjo pasiūlymą | 204 |
| 16 | `GET` | `/api/v1/builds/{build_id}/reviews` | Gauti konkretaus komplekto atsiliepimų sąrašą | 200 |
| 17 | `POST` | `/api/v1/builds/{build_id}/reviews` | Sukurti atsiliepimą | 201 |
| 18 | `GET` | `/api/v1/reviews/{review_id}` | Gauti atsiliepimą | 200 |
| 19 | `PUT` | `/api/v1/reviews/{review_id}` | Pilnai atnaujinti atsiliepimą | 200 |
| 20 | `DELETE` | `/api/v1/reviews/{review_id}` | Pašalinti atsiliepimą | 204 |

Hierarchinis `GET /api/v1/builds/{build_id}` atsakymas pateikia struktūrą
`komplektas → komponentas → pardavėjo pasiūlymas`. Komponento `category` nusako
tipą (`cpu`, `gpu`, `memory` ir kt.), o jo `offers` lauke pateikiamos parduotuvės,
kainos ir įsigijimo nuorodos.

Užklausos ir atsakymai su turiniu naudoja `application/json`; sėkmingi `DELETE` grąžina `204 No Content` be atsakymo kūno. Neegzistuojantis resursas grąžina `404`, struktūriškai blogas payload – `422`, o semantiškai neteisingas komplektas (dvi tos pačios kategorijos dalys) – `400`.

### Duomenų bazė ir migracijos

API konteineris kiekvieno paleidimo metu saugiai vykdo:

```bash
alembic upgrade head
```

Migracija `0001_schema` sukuria DB schemą, indeksus, išorinius raktus ir apribojimus. Migracija `0002_seed` prideda devynis realistiškus komponentus, po du pardavėjų pasiūlymus, suderinamą ir tyčia nesuderinamą komplektą bei atsiliepimus.

Migracijų būseną galima patikrinti:

```bash
docker compose exec api alembic current
docker compose exec api alembic history
```

Norint visiškai atkurti pradinius demonstracinius duomenis:

```bash
docker compose down --volumes
docker compose up --build --detach --wait
```

### Greita atsiskaitymo demonstracija

Postman kolekcija yra [`postman/PC_Builder_API.postman_collection.json`](postman/PC_Builder_API.postman_collection.json). Visus metodus ir privalomus klaidų scenarijus galima paleisti viena komanda:

```bash
docker compose --profile demo run --rm demo
```

Trumpinys tai pačiai komandai: `make demo`. Paleidimui taip pat galima naudoti `make up`, testams – `make test`, o pradinei DB būsenai atkurti – `make reset`.

Kolekcija vykdo API operacijas ir papildomus `404`, `422` bei `400` scenarijus.
Sukurti laikini duomenys kolekcijos pabaigoje pašalinami, todėl ją galima kartoti.

Automatiniai API testai vykdomi izoliuotame konteineryje:

```bash
docker compose --profile test run --build --rm api-test
```

Sustabdyti aplikaciją, išsaugant DB duomenis:

```bash
docker compose down
```
