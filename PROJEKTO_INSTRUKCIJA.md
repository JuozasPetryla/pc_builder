# Projekto instrukcija

## Paleidimas

Reikia Docker ir Docker Compose.

```bash
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_hex(32))'
# Gautą reikšmę įrašykite į .env JWT_SECRET; pakeiskite POSTGRES_PASSWORD.
docker compose up --build --detach --wait
```

Jei aplikacija jau veikė prieš kodo pakeitimus, pakartokite šią komandą, kad būtų perkurti API ir sąsajos vaizdai, tada atnaujinkite naršyklės puslapį.

Jei `.env` jau yra, jo neperrašykite. Atnaujindami esamą DB nekeiskite jos slaptažodžio vien `.env` faile: PostgreSQL inicializavimo kintamieji galioja tik naujam DB tomui.

- Aplikacija: <http://localhost:8080>
- Swagger: <http://localhost:8080/api/docs>
- Tiesioginis API: <http://localhost:8000/api/v1>

Migracijos vykdomos automatiškai. Prieš atnaujindami esamą DB išsaugokite jos kopiją: `0003_builds` ir `0007_shared_catalog` migracijos vienkryptės. `docker compose down` išsaugo duomenis; `down --volumes` juos pašalina.

Pirmą administratorių sukurkite interaktyviai:

```bash
docker compose exec api python -m scripts.create_admin
```

Naršyklėje registruokitės ir prisijunkite. Administratorius meniu **Katalogas** sukuria komponentus ir jų pardavėjų pasiūlymus. Naudotojas sukuria komplektą, jį atidaro ir pasirenka komponentus iš katalogo. Administratorius valdo paskyras meniu **Naudotojai**. Pradiniai demonstraciniai komplektai nėra naujai užregistruoto naudotojo nuosavybė.

Sesija saugoma konkrečios naršyklės kortelės `sessionStorage`. Gavęs `401`, klientas vieną kartą atnaujina abu žetonus ir pakartoja užklausą. Meniu **Atnaujinti sesiją** leidžia tai atlikti rankiniu būdu. Viešo komplekto nuorodos gavėjas turi prisijungti.

## Rolės

| Rolė | Teisės |
|---|---|
| `user` | Skaityti katalogą ir viešą turinį; tvarkyti savo komplektus, jų katalogo pasirinkimus ir savo atsiliepimus matomuose komplektuose. |
| `moderator` | Papildomai šalinti svetimus viešus komplektus ir jų atsiliepimus. |
| `admin` | Papildomai tvarkyti bendrą komponentų katalogą ir pasiūlymus, kitų naudotojų roles, blokavimą ir paskyrų šalinimą. |

Svečio režimo nėra. Nė viena rolė negali skaityti svetimų privačių komplektų ar redaguoti svetimų komplektų ir atsiliepimų. Administratorius negali keisti savo rolės, blokuoti ar pašalinti savo paskyros.

## Sąsajos kūrimas be perkompiliavimo

Pirma paleiskite konteinerius. Atskirame terminale, turint Node.js 22.12 ar naujesnę versiją:

```bash
cd web
npm ci
npm run dev
```

Atidarykite terminale nurodytą adresą (paprastai `http://localhost:5173`). Vite persiunčia `/api` užklausas į `http://127.0.0.1:8000`; pakeitus `API_PORT`, atnaujinkite `web/vite.config.js`. Docker versiją atnaujina `docker compose up --build --detach --wait`.

## Patikros

```bash
docker compose --profile test run --build --rm api-test
cd web
npm ci
npm run lint
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Naršyklės testams aplikacija turi veikti `http://localhost:8080` (kitam adresui nustatykite `E2E_BASE_URL`). Testuokite atskiroje testinėje DB: testai sukuria paskyras ir turinį. Administravimo scenarijui reikalingi `E2E_ADMIN_USERNAME` ir `E2E_ADMIN_PASSWORD` aplinkos kintamieji su testinės administratoriaus paskyros duomenimis; be jų scenarijus praleidžiamas.

## Publikavimas ir dokumentacija

- [Publikavimas su Render, Neon ir IaC](deploy/README.md)
- [API dokumentacija](api/README.md)
- [Funkciniai reikalavimai ir likusios ribos](FUNKCINIAI_REIKALAVIMAI.md)
- [Reikalavimų patikra ir API veiksmų vietos sąsajoje](REIKALAVIMU_PATIKRA.md)
- [Projekto ataskaita](README.md)

Automatinis dalių suderinamumo tikrinimas ir viso komplekto kainos skaičiavimas dar neįgyvendinti.
