# API

Bazinis kelias: `/api/v1`. Vietinė Swagger dokumentacija: `http://localhost:8000/api/docs`; ReDoc: `/api/redoc`; statinė OpenAPI schema – [openapi.json](openapi.json). Paleidimo ir testų komandos pateiktos [pagrindiniame README](../README.md).

## Domenas ir prieiga

```text
Build → Component pasirinkimas → CatalogComponent → RetailOffer
   └── Review
```

Administratorius kuria ir redaguoja bendrą katalogą; naudotojas komplektui pasirenka katalogo įrašą, o ne kuria naują dalį. Katalogo specifikacijų ir pasiūlymų pakeitimai iškart matomi visuose jį naudojančiuose komplektuose. Viename komplekte gali būti po vieną pasirinkimą iš kiekvienos dalies kategorijos. Komplektų, atsiliepimų ir naudotojų privatumo bei rolių taisyklės tikrinamos serveryje.

Visiems keliams žemiau pridėkite `/api/v1`. Domeno ir naudotojų API reikia `Authorization: Bearer <access_token>`.

| Išteklius | Sąrašas / kūrimas | Skaitymas / pakeitimas / šalinimas |
|---|---|---|
| Komplektai | `/builds` | `/builds/{build_id}` |
| Komplekto pasirinkimai | `/builds/{build_id}/components` | `/components/{component_id}` |
| Bendras katalogas | `/catalog/components` | `/catalog/components/{component_id}` |
| Katalogo pasiūlymai | `/catalog/components/{component_id}/offers` | `/offers/{offer_id}` |
| Komplekto atsiliepimai | `/builds/{build_id}/reviews` | `/reviews/{review_id}` |

Sąrašo ir kūrimo metodai yra `GET` / `POST`; atskiro įrašo metodai `GET` / `PUT` / `DELETE`. Katalogo ir jo pasiūlymų keitimas leidžiamas tik administratoriui. Komplekto pasirinkimo POST turinys yra `{"catalog_component_id": 12}`. Komponento ištrynimas pašalina pasirinkimą tik iš vieno komplekto; katalogo dalies pašalinti negalima, kol ji naudojama.

Katalogo dalies sukūrimo pavyzdys (admin):

```json
{"category":"cpu","manufacturer":"AMD","model":"Ryzen 7 7800X3D","description":"Procesorius","specifications":{"socket":"AM5","cores":8}}
```

Pasiūlymo turinys: `{"retailer":"Parduotuvė","price":"299.99","product_url":"https://example.com/item","in_stock":true}`. Kaina teigiama, iki 2 skaitmenų po kablelio; URL turi būti HTTP(S). PUT visiškai pakeičia laukus. Sėkmingas DELETE grąžina `204` be turinio. `409` reiškia kategorijos/pardavėjo konfliktą ar naudojamos katalogo dalies ribojimą; neteisingas turinys grąžina `422`.

Sąrašai palaiko `limit` (1–200, numatytasis 100), `offset` (numatytasis 0), ir pagal kelią filtrus: `public_only`, `category`, kataloge `q`, pasiūlymuose `in_stock`, atsiliepimuose `rating`. Visos sėkmingos reikšmės ir klaidos grąžinamos JSON formatu, išskyrus `204`.

## Sesija ir administravimas

| Metodas | Kelias | Pastaba |
|---|---|---|
| POST | `/auth/register` | Sukuria tik `user` rolę |
| POST | `/auth/login` | Grąžina access ir refresh žetonus |
| POST | `/auth/refresh` | Vieną kartą pakeičia refresh žetoną |
| POST | `/auth/logout` | Atšaukia dabartinę sesiją |
| GET | `/auth/me` | Dabartinė paskyra |
| GET | `/users` | Tik admin |
| GET | `/users/{user_id}` | Vieša profilio dalis |
| PUT | `/users/{user_id}/role` | Tik admin; atšaukia paskyros sesijas |
| PUT | `/users/{user_id}/status` | Tik admin; blokavimas atšaukia sesijas |
| DELETE | `/users/{user_id}` | Tik admin; turinys anonimizuojamas |

Pirmą administratorių vietinėje aplinkoje sukuria `docker compose exec api python -m scripts.create_admin`. Publikavimo aplinka jį sukuria vieną kartą iš `BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD`; sėkmingai prisijungę pašalinkite šiuos kintamuosius. `JWT_SECRET` turi būti bent 32 atsitiktiniai simboliai.

## OpenAPI ir testai

Po API pakeitimų specifikaciją atnaujinkite iš `api` katalogo:

```bash
JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')" python -m scripts.export_openapi
```

Postman kolekcija yra `postman/PC_Builder_API.postman_collection.json`. API testai: `docker compose --profile test run --build --rm api-test`.
