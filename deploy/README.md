# Nemokamas publikavimas

Naudojamas vienas Render Docker web service nemokamame plane ir PostgreSQL duomenų bazė Neon Free plane. Render pateikia HTTPS adresą. Jo nemokamas web service užmiega po neveiklos ir pirmas kito lankytojo apsilankymas gali būti lėtas; šis variantas tinka demonstracijai, ne nuolatiniam darbui. Duomenų bazių nemokami limitai ir sąlygos priklauso nuo tiekėjų planų.

## Publikavimas per IaC

Render infrastruktūra aprašyta [render.yaml](../render.yaml), Neon projektas – Terraform faile `deploy/terraform` (Terraform ≥1.14 ir [Neon provider](https://registry.terraform.io/providers/kislerdm/neon/latest)). Reikia Git paskyros ir paskyros kiekvienam debesijos tiekėjui. API raktų nesaugokite Git saugykloje.

1. Įkelkite šį projektą į GitHub, GitLab arba Bitbucket.
2. Neon paskyroje gaukite API raktą ir organizacijos ID. Vietoje `deploy/terraform`:

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   cp credentials.env.example .credentials.env
   ```

   Įrašykite `neon_org_id` į `terraform.tfvars`, o API raktą – į `.credentials.env`. Tada:

   ```bash
   set -a
   source .credentials.env
   set +a
   terraform init
   terraform validate
   terraform apply
   terraform output -raw database_url
   ```

   Paskutinė komanda parodo slaptą duomenų bazės URL. Jį nukopijuokite laikinai, jo nesiųskite ir neįrašykite į Git. Terraform būsena taip pat saugo šį URL ir DB slaptažodį: laikykite `terraform.tfstate` privačiai, padarykite saugią atsarginę kopiją ir niekada jos nekelkite į viešą saugyklą.

3. Render paskyroje pasirinkite **New → Blueprint**, prijunkite saugyklą ir prieš patvirtindami peržiūrėkite planuojamus išteklius. Pradiniame sukūrime Render paprašys `DATABASE_URL` ir `BOOTSTRAP_ADMIN_PASSWORD`. Įveskite ankstesniame žingsnyje gautą URL ir naują stiprų administratoriaus slaptažodį. `JWT_SECRET` Render sugeneruoja automatiškai.
4. Palaukite kol diegimas baigsis, atidarykite `https://<render-service>.onrender.com` ir prisijunkite kaip `pc-admin` su pasirinktu slaptažodžiu. Tada iš `render.yaml` pašalinkite `BOOTSTRAP_ADMIN_USERNAME` ir `BOOTSTRAP_ADMIN_PASSWORD` įrašus, įkelkite pakeitimą į Git ir palaukite diegimo. Po jo Render aplinkos kintamuosiuose ištrinkite abu bootstrap kintamuosius vienu kartu. Įrašykite viešą adresą į savo projekto pastabas.

Po Git pakeitimų Render automatiškai sukuria naują diegimą. DB pakeitimus aplikacija migruoja startavimo metu. Neon duomenų bazė išsaugoma nepriklausomai nuo nemokamo Render proceso užmigimo.

Jei Git saugyklos URL, Neon organizacija ar paskyros dar nesukurtos, pakeiskite tik nurodytus laukus vėliau; nėra saugu paleisti tikrą diegimą su placeholder reikšmėmis. Tiekėjų patvirtinti nemokamo plano apribojimai: [Render Free](https://render.com/docs/free), [Neon planai](https://neon.tech/pricing).

## Vietinis produkcinio vaizdo bandymas

Docker vaizdas ir starto migracijos patikrinami be debesijos paskyrų:

```bash
docker compose -f deploy/compose.test.yaml up --build --wait
curl -fsS http://localhost:8090/healthz
docker compose -f deploy/compose.test.yaml down --volumes
```
