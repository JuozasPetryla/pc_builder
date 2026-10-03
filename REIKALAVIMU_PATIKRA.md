# Sąsajos reikalavimų patikra

| Pateiktas reikalavimas | Įgyvendinimas |
|---|---|
| CRUD bent trims objektams | Komplektų pasirinkimai, katalogo komponentai, pasiūlymai ir atsiliepimai. Katalogą keičia administratorius, naudotojai renkasi jo įrašus. |
| Visi realizuoti API metodai | Visos 37 operacijos dokumentuotos sąsajoje/API; žr. lentelę žemiau. |
| Registracija, prisijungimas, žetonų atnaujinimas | Registracijos / prisijungimo forma, automatinė vienkartinė refresh rotacija po `401`, rankinis sesijos atnaujinimas ir atsijungimas. |
| Bent 4 įvesties elementų tipai | Teksto ir slaptažodžio laukai, `textarea`, `select`, `checkbox`, kainos `number` su žingsniu, įvertinimo `range`. |
| JSON duomenys | API grąžina JSON; sėkmingas DELETE ir logout – `204` be turinio. React apdoroja duomenis, o ne serverio HTML formas. |
| Prisitaikantys paveikslėliai, vektorinės meniu ikonėlės | Vietinė SVG iliustracija keičia dydį pagal langą; meniu naudoja inline SVG ikonėles. |
| Header, footer, modaliniai langai | Bendras header ir footer; kūrimas, redagavimas, šalinimas ir blokavimo patvirtinimas – native `dialog` su fokuso grąžinimu ir Escape. |
| Animacijos | Krovimo indikatorius, kortelių ir modalinių langų atsiradimas, mygtukų užvedimo efektai; atsižvelgiama į `prefers-reduced-motion`. |
| Vieninga CSS stilistika, nestandartinis šriftas | Tamsi paletė su mėtiniu akcentu; vietinis Montserrat su OFL licencija. |
| Grįžtamasis ryšys be naršyklės alert | Sėkmės, klaidų, validavimo ir krovimo būsenos; ARIA status / alert sritys, be `window.alert` ir `window.confirm`. |
| Responsive ir hamburgeris | 1050 ir 700 px lūžio taškai, prisitaikantys tinkleliai, mobilus išskleidžiamas meniu. |
| Publikavimas internete | Render Blueprint nemokamam web servisui ir Terraform valdomai Neon DB. **Dar nepublikuota:** reikia saugyklos, paskyrų ir API rakto. |

## API operacijų vietos sąsajoje

| Operacijos | Vieta |
|---|---|
| 5 komplektų LIST / CRUD | „Komplektai“ → Pridėti / Peržiūrėti / Redaguoti / Pašalinti. |
| 5 komponentų LIST / CRUD | Atidarytas komplektas → „Komponentai“; atskiras komponento ekranas. |
| 5 pasiūlymų LIST / CRUD | Atidarytas komponentas → „Pardavėjų pasiūlymai“; keitimas administratoriui. |
| 5 katalogo komponento operacijos + pasiūlymų LIST / CREATE | Meniu „Katalogas“; administratorius tvarko bendrus įrašus ir pasiūlymus. |
| 5 atsiliepimų LIST / CRUD | Atidarytas komplektas → „Atsiliepimai“. |
| Register, login | Pradinis neprisijungusio lankytojo puslapis. |
| Refresh, logout, me | Meniu: „Atnaujinti sesiją“, „Atsijungti“, naudotojo vardas; refresh vyksta ir automatiškai. |
| Viešas naudotojo profilis | Komplekto / atsiliepimo autorius arba administratoriaus sąrašo „Profilis“. |
| Naudotojų LIST, status, DELETE, role | Administratoriaus meniu „Naudotojai“. |

Visi sąrašai turi puslapiavimą; domeno sąrašai turi API palaikomus filtrus. Individuali peržiūra ir redagavimo formos įkėlimas kviečia individualius GET metodus.

## Pakartojama patikra

Paleidimo ir automatinių testų komandos pateiktos [README](README.md). API testai tikrina CRUD, hierarchiją, roles, privatumą ir sesijas; kliento testai – refresh lenktynes ir klaidų apdorojimą; Playwright – naudotojo ir administratoriaus veiksmų sekas su tikra API, modalines formas ir mobilų meniu.

Patikros vykdymo komandos pateiktos pagrindiniame README. Publikavimo URL dar nėra, nes saugyklos ir debesijos paskyros nebuvo pateiktos.

Prieš pateikiant darbą patikrinkite viešą URL iš kito tinklo. Automatinis dalių suderinamumo tikrinimas nėra įgyvendintas.
