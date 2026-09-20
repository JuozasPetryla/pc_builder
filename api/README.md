# PC Builder API naudojimas

Vietinis serveris: `http://localhost:8000`; API bazinis kelias: `/api/v1`.
[Swagger UI](http://localhost:8000/api/docs), [ReDoc](http://localhost:8000/api/redoc)
ir [statinė OpenAPI specifikacija](openapi.json) aprašo įvesties ir atsakymų schemas.
Paleidimo, migracijų ir testavimo instrukcijos yra [projekto README](../README.md).

## Hierarchija

```text
Build (1) ── (N) Component (1) ── (N) RetailOffer
    └─────── (N) Review
```

Kompiuterio komplektas yra aukščiausio lygio objektas. Komponentas priklauso
vienam komplektui, pasiūlymas — vienam komponentui. Tas pats aparatūros modelis
skirtinguose komplektuose saugomas kaip atskiri komponentai su atskirais pasiūlymais.
`category` yra komponento laukas, ne atskiras objektas. Naudotojų esybės nėra.

Įdėtiniai URL naudojami sąrašams ir kūrimui: jie nurodo kolekciją, su kuria dirbama.
Pasiūlymų kolekcijos URL tikrinama, ar komponentas priklauso nurodytam komplektui;
jei ne, grąžinama `404`. Taip išlaikomas kriterijų reikalaujamas trijų lygių metodas.
Individualaus objekto GET, PUT ir DELETE pakanka vieno unikalaus ID; tėvai nustatomi
iš duomenų bazės. Trumpesni URL nekeičia 1:N ryšių ar kaskadinio šalinimo.

## Visi prieigos taškai

Prie lentelės kelių pridėkite `/api/v1`. Kiekviena eilutė apima penkias operacijas,
iš viso — 20. PATCH metodų nėra.

| Objektas | LIST GET / CREATE POST | READ GET / UPDATE PUT / DELETE |
|---|---|---|
| Komplektas | `/builds` | `/builds/{build_id}` |
| Komponentas | `/builds/{build_id}/components` | `/components/{component_id}` |
| Pasiūlymas | `/builds/{build_id}/components/{component_id}/offers` | `/offers/{offer_id}` |
| Atsiliepimas | `/builds/{build_id}/reviews` | `/reviews/{review_id}` |

Visų vaikinių objektų individualūs metodai naudoja trumpus URL.
Globalūs kolekcijų `/components`, `/offers`, `/categories` keliai nepalaikomi.
Ankstesni ilgi individualių komponentų ir pasiūlymų URL pašalinti, be aliasų;
naudokite naujus kelius arba atsakymo `links.self`.

## Sukūrimo pavyzdys

Toliau pateiktus JSON siųskite su `Content-Type: application/json`.
ID imkite iš kiekvieno `201` atsakymo `id` lauko, o ne iš pradinių duomenų.

1. `POST /api/v1/builds`:

   ```json
   {"name":"1440p Gaming PC","owner_name":"Juozas","description":"Komplektas žaidimams","is_public":true}
   ```

2. `POST /api/v1/builds/{build_id}/components`:

   ```json
   {"category":"cpu","manufacturer":"AMD","model":"Ryzen 7 7800X3D","description":"8 branduolių procesorius","specifications":{"socket":"AM5","cores":8,"tdp_w":120}}
   ```

3. `POST /api/v1/builds/{build_id}/components/{component_id}/offers`:

   ```json
   {"retailer":"Pavyzdinė parduotuvė","price":"299.99","product_url":"https://example.com/products/ryzen-7-7800x3d","in_stock":true}
   ```

4. Papildomai, `POST /api/v1/builds/{build_id}/reviews`:

   ```json
   {"author_name":"Mantas","rating":5,"comment":"Tinkamas komplektas 1440p žaidimams."}
   ```

URL ir kaina yra demonstraciniai. `price` priima JSON skaičių arba dešimtainę eilutę;
atsakyme grąžinama eilutė. Kaina turi būti teigiama, iki 10 skaitmenų iš viso
ir iki 2 po kablelio. `product_url` turi būti HTTP arba HTTPS URL (iki 500 simbolių).

Komponento `specifications` turi būti netuščias JSON objektas. Konkrečių raktų pagal
kategoriją API nereikalauja. Kategorijos: `cpu`, `motherboard`, `memory`, `gpu`,
`storage`, `psu`, `case`, `cooler`.

Viename komplekte leidžiamas vienas komponentas kiekvienai kategorijai.
Vienam komponentui leidžiamas vienas pasiūlymas kiekvienam `retailer`.
Pakartojus šias reikšmes to paties tėvo apimtyje gaunamas `409`.

## Skaitymas, sudėtinis resursas ir hypermedia

`GET /api/v1/builds/{build_id}` grąžina komplekto laukus, `components` su jų
`offers`, `reviews`, laiko žymas ir `links`. Naujas komplektas turi tuščius vaikų masyvus.
Komponento atsakyme taip pat yra `build_id` ir `offers`; pasiūlymo — `component_id`;
atsiliepimo — `build_id`. Tikslios visų atsakymų schemos pateiktos OpenAPI.

`links` reikšmės yra nuorodos nuo serverio šaknies, pavyzdžiui:

```json
{"self":"/api/v1/offers/3","component":"/api/v1/components/2","build":"/api/v1/builds/1"}
```

Šie ID iliustraciniai. Prie nuorodos pridėkite serverio adresą, bet ne antrą `/api/v1`.
Komplektas pateikia `self`, `components`, `reviews`; komponentas — `self`, `build`,
`offers`; pasiūlymas — `self`, `component`, `build`; atsiliepimas — `self`, `build`.

## Puslapiavimas ir filtravimas

Visi keturi LIST metodai grąžina JSON masyvą, surikiuotą pagal ID didėjimo tvarka.
Nėra `total` ar `next` apvalkalo. `limit` numatyta 100, leidžiama 1–200;
`offset` numatyta 0, leidžiama 0–2147483647. Už sąrašo ribų grąžinamas `[]`.

| Sąrašas | Filtras | Praleidus filtrą |
|---|---|---|
| Komplektai | `public_only=true` | Visi komplektai; `false` taip pat reiškia visus |
| Komponentai | `category=cpu` | Visos kategorijos tame komplekte |
| Pasiūlymai | `in_stock=true` arba `false` | Visi to komponento pasiūlymai |
| Atsiliepimai | `rating=5` (1–5) | Visi to komplekto atsiliepimai |

Pavyzdys: `GET /api/v1/builds/{build_id}/components/{component_id}/offers?in_stock=true&limit=5&offset=0`.
Kitam puslapiui naudokite `offset=5`. Puslapiavimas neapriboja sudėtinio atsakymo
viduje esančių vaikų masyvų; jiems naudokite atitinkamus LIST metodus.

## Atnaujinimas ir šalinimas

PUT naudoja tokią pačią įvesties schemą kaip POST ir visiškai pakeičia redaguojamus
objekto laukus. Privalomus laukus reikia pateikti iš naujo. Praleisti neprivalomi
laukai atkuriami į numatytąsias reikšmes (`description=null`, `is_public=false`,
`in_stock=true`, priklausomai nuo objekto).

Nesiųskite viso GET atsakymo kaip PUT turinio: `id`, tėvų ID, laiko žymos,
`links`, vaikų masyvai ir kiti schemoje nenumatyti laukai atmetami su `422`.
`component_ids` nebepalaikomas. Tėvas nustatomas pagal kūrimo URL ir nekeičiamas PUT.
Komplekto PUT nekeičia vaikų; komponento PUT nekeičia jo pasiūlymų.

DELETE komplektui pašalina ir jo komponentus, jų pasiūlymus bei atsiliepimus.
DELETE komponentui pašalina ir jo pasiūlymus. Kitų komplektų duomenys nepaveikiami.
Sėkmingas DELETE grąžina `204` be turinio; pakartotinis to paties ID šalinimas — `404`.

## Klaidos ir prieigos ribos

| Kodas | Reikšmė |
|---|---|
| 200 | Sėkmingas GET arba PUT; JSON atsakymas |
| 201 | Sukurtas objektas; JSON atsakymas su `id` |
| 204 | Objektas pašalintas; tuščias atsakymas |
| 404 | Objektas nerastas arba neatitinka URL hierarchijos |
| 409 | Pasikartojanti kategorija komplekte arba pardavėjas komponente |
| 422 | Netinkamas užklausos turinys, kelio arba užklausos parametrai |

404 ir 409 formatas: `{"detail":"Klaidos paaiškinimas."}`.
422 formato pavyzdys (konkretus tekstas priklauso nuo klaidos):

```json
{"detail":[{"loc":["body","name"],"msg":"Field required","type":"missing"}]}
```

Autentifikacija ir autorizacija dar neįgyvendintos. `owner_name` ir `author_name`
yra tekstinės žymos, ne naudotojų paskyros. `is_public=false` neapsaugo nuo skaitymo
ar keitimo. Šis API nėra paruoštas neapsaugotam viešam diegimui.

## Dokumentacijos atnaujinimas ir bandymai

Iš `api` katalogo, aplinkoje su projekto Python priklausomybėmis:

```bash
python -m scripts.export_openapi
```

Tai atnaujina `api/openapi.json` pagal aplikacijos maršrutus ir schemas.
Swagger ir ReDoc naudoja paleistos aplikacijos specifikaciją; statinio failo
pakeitimas neatnaujina jau veikiančio seno konteinerio. Aplikacijos atnaujinimą
atlikite pagal pagrindinį README, įskaitant atsarginę kopiją prieš vienkryptę migraciją.

[Postman rinkinys](../postman/PC_Builder_API.postman_collection.json) apima visas
20 operacijų. Jis sukuria savo testinius objektus ir juos šalina — vykdykite testavimo
aplinkoje. Automatizuotas paleidimas iš projekto šaknies:

```bash
docker compose --profile demo run --rm demo
```
