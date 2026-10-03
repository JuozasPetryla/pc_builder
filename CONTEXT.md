# Įgyvendinimo kontekstas

- Docker Compose vietinei aplinkai: React/Nginx, FastAPI ir PostgreSQL. Vieno Docker vaizdo produkcinis startas aprašytas deploy/Dockerfile.
- Pradinės REST dalys teikia komplektų, pasirinkimų, pasiūlymų ir atsiliepimų CRUD/LIST; bendro katalogo CRUD turi atskirus API kelius.
- Domeno modelis: Build → Component (komplekto pasirinkimas) → CatalogComponent (bendra katalogo dalis) → RetailOffer; Build → Review. Katalogo CRUD: /api/v1/catalog/components, tik administratorius rašo; naudotojas komplektui pasirenka esamą ID per /api/v1/builds/{build_id}/components. Katalogo pasiūlymai: /api/v1/catalog/components/{id}/offers; keitimai iškart matomi komplektuose. Individualus pasirinkimo CRUD: /api/v1/components/{id}; pasiūlymai: /api/v1/offers/{id}.
- Visi sąrašai puslapiuojami ir filtruojami; visos esybės turi links. Komplekto atsakymas sujungia komponentus, jų pasiūlymus ir atsiliepimus.
- Migracijos: 0001_schema–0007_shared_catalog. Naujoje DB: 5 komplektai, 40 pasirinkimų/katalogo komponentų ir 80 pasiūlymų, 5 atsiliepimai.
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
- user tvarko savo turinį; moderator/admin gali papildomai šalinti svetimą viešą turinį, bet negali jo redaguoti ar skaityti svetimų privačių komplektų. Tik admin valdo paskyras, roles ir bendrą katalogą/pasiūlymus.

- 0006_timestamps: builds/components/retail_offers created_at ir updated_at sulyginti su ORM (timestamp with time zone), senas datas interpretuojant kaip UTC. Auth datos nekeičiamos.
- 0007_shared_catalog: katalogo dalys atskirtos nuo komplektų pasirinkimų; esami įrašai išsaugomi, privačių dalių duomenys neviešinami.
- Funkciniai reikalavimai: FUNKCINIAI_REIKALAVIMAI.md; atskirai pažymėtos dar neįgyvendintos funkcijos.

- Sąsaja: web/src/App.jsx (ekranai ir sąrašai), ui.jsx (modalai ir formos), api.js (JSON klientas, sessionStorage, viena bendra refresh operacija ir vienas užklausos pakartojimas po 401). Hash nuorodos į komplektus ir komponentus.
- Vietiniai SVG ir Montserrat šriftai; CSS breakpoint 1050 / 700 px, hamburgeris, animacijos ir reduced-motion.
- Frontend patikros: npm run lint, npm test, npm run build; Playwright npm run test:e2e su veikiančia testine aplikacija.
- Publikavimas: Render Blueprint (nemokamas web) ir Neon Terraform (PostgreSQL), instrukcijos deploy/README.md. Paskyros ir repo URL pateikiami kaip naudotojo vietiniai nustatymai; viešas URL dar nepatvirtintas.
- Reikalavimų ir sąsajos veiksmų atitiktis: REIKALAVIMU_PATIKRA.md. Pirminis PDF laikomas istorine ataskaita, dabartinę realizaciją aprašo Markdown dokumentai.
