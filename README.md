# PC Builder

Kompiuterių komplektų REST API: FastAPI, PostgreSQL ir JWT autentifikacija. React frontend – pradinė struktūra. Bendras dalių katalogas ir suderinamumo tikrinimas dar neįgyvendinti.

## Rolės

Svečio režimo nėra. Registracija suteikia `user` rolę; teisės tikrinamos pagal rolę ir įrašo savininko ID.

| Rolė | Teisės |
|---|---|
| `user` | Skaityti viešą turinį, kurti ir viešinti savo komplektus, tvarkyti jų komponentus, rašyti atsiliepimus matomuose komplektuose ir tvarkyti savo atsiliepimus. |
| `moderator` | Visos `user` teisės ir svetimų viešų komplektų bei jų komentarų šalinimas. |
| `admin` | Visos `moderator` teisės, pardavėjų pasiūlymų valdymas matomuose komplektuose, kitų naudotojų blokavimas, atblokavimas, šalinimas ir rolių keitimas. |

Nė viena rolė negali redaguoti svetimų komplektų ar komentarų ir skaityti svetimų privačių komplektų. Administratorius negali pakeisti savo rolės, blokuoti ar pašalinti savo paskyros.

## Paleidimas

Reikia Docker ir Docker Compose.

```bash
cp .env.example .env
# .env nustatykite JWT_SECRET – bent 32 simbolių atsitiktinę paslaptį.
docker compose up --build --detach --wait
```

- Aplikacija: <http://localhost:8080>
- Swagger: <http://localhost:8000/api/docs>
- [API dokumentacija](api/README.md)

Pirmo administratoriaus sukūrimas:

```bash
docker compose exec api python -m scripts.create_admin
```

Migracijos vykdomos automatiškai. Prieš atnaujindami esamą DB išsaugokite jos kopiją: `0003_builds` migracija vienkryptė.

## Testai

```bash
docker compose --profile test run --build --rm api-test
```
