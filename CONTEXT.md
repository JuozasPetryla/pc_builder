# Įgyvendinimo kontekstas

- Sukurta Docker Compose aplinka: React/Nginx, FastAPI ir PostgreSQL.
- Realizuota tiksliai 15 dokumentuotų REST operacijų komponentams, komplektams, suderinamumui, kainai ir atsiliepimams.
- Pridėtos Alembic migracijos: `0001_schema` kuria schemą, `0002_seed` įrašo prasmingus demonstracinius duomenis.
- API konteineris prieš startą automatiškai vykdo `alembic upgrade head`.
- OpenAPI pasiekiama per `/api/openapi.json`, Swagger per `/api/docs`; statinė kopija yra `api/openapi.json`.
- Postman/Newman kolekcija patikrina visus metodus bei 201, 204, 400, 404 ir 422 atsakymus; paleidimas: `docker compose --profile demo run --rm demo`.
- Docker testų paleidimas: `docker compose --profile test run --build --rm api-test`.
- Sąmoningai neįgyvendinta autentifikacija ir detalus teisių valdymas; `owner_name` bei `is_public` palikti kitam etapui.
