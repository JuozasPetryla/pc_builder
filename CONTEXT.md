# Įgyvendinimo kontekstas

- Docker Compose: React/Nginx, FastAPI ir PostgreSQL. Frontend yra pradinė struktūra.
- Privaloma hierarchija: Build (1) → (N) Component (1) → (N) RetailOffer. N:M jungiamoji lentelė pašalinta; category yra komponento laukas.
- 20 REST operacijų: komplektų, jų komponentų, pasiūlymų ir atsiliepimų CRUD/LIST.
- Sąrašai ir kūrimas naudoja įdėtines kolekcijas: /api/v1/builds/{build_id}/components ir /api/v1/builds/{build_id}/components/{component_id}/offers. Pasiūlymų kolekcija tikrina komponento priklausomybę komplektui. Individualūs GET/PUT/DELETE: /api/v1/components/{component_id} ir /api/v1/offers/{offer_id}; tėvai nustatomi iš DB, hierarchija nesikeičia.
- Visi sąrašai puslapiuojami ir filtruojami; visos esybės turi links. Komplekto atsakymas sujungia komponentus, jų pasiūlymus ir atsiliepimus.
- Migracijos: 0001_schema, 0002_seed, 0003_builds. Naujoje DB: 5 komplektai, 40 komponentų įrašų, 80 pasiūlymų, 5 atsiliepimai.
- 0003_builds išsaugo esamus komplektus ir nukopijuoja bendrus komponentus su pasiūlymais. Atšaukimui reikalinga prieš migraciją išsaugota DB kopija.
- API paleidimas automatiškai vykdo alembic upgrade head.
- Swagger: /api/docs; OpenAPI: /api/openapi.json ir api/openapi.json.
- Postman/Newman: docker compose --profile demo run --rm demo.
- API testai: docker compose --profile test run --build --rm api-test.
- JWT: PyJWT HS256, Argon2, 15 min. access, vienkartinė refresh rotacija, 7 dienų DB sesijos, logout iškart atšaukia access ir refresh.
- Rolės user/moderator/admin; savininko ID ir privataus komplekto patikros visuose hierarchijos keliuose. Registracija visada user; admin kuriamas scripts.create_admin.
- Migracija 0004_auth: users, auth_sessions, builds.owner_id, reviews.author_id. Seni NULL savininkai negali būti perimami; viešą turinį gali šalinti moderator/admin. JWT_SECRET privalomas.
- 10 papildomų auth/naudotojų metodų; vardai ir savininko ID POST/PUT įvestyje nepriimami.

- 0005_user_status: paskyrų blokavimas; admin sąrašas, blokavimas / atblokavimas ir šalinimas; prisijungusiems viešas profilis (ID, vardas). Šalinimas išsaugo anonimizuotą turinį. Svečio nėra: visi domeno metodai reikalauja prisijungimo.
- user tvarko savo turinį; moderator/admin gali papildomai šalinti svetimą viešą turinį, bet negali jo redaguoti ar skaityti svetimų privačių komplektų. Tik admin valdo paskyras, roles ir matomų komplektų pasiūlymus. Bendras katalogas neįgyvendintas; komponentus tvarko komplekto savininkas.
