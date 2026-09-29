# 1. Sistemos aprašymas

## 1.1. Sistemos paskirtis

Projekto tikslas – palengvinti naudotojams asmeninio kompiuterio komplektavimą, suteikiant galimybę pasirinkti dalis, patikrinti jų suderinamumą ir peržiūrėti kainas bei įsigijimo vietas.

Sistemą sudaro dvi dalys: internetinė aplikacija, kuria naudosis kompiuterį norintys susikomplektuoti žmonės, ir aplikacijų programavimo sąsaja (API).

Komplektavimo ir bendruomenės funkcijomis galės naudotis tik prisijungę naudotojai. Naudotojas galės išsaugoti savo komplektus, juos redaguoti, pašalinti ir paskelbti viešai. Viešai paskelbti komplektai bus matomi kitiems prisijungusiems naudotojams, kurie galės juos peržiūrėti, vertinti ir komentuoti. Privatūs komplektai bus pasiekiami tik jų savininkams.

Sistemoje numatytos trys rolės: registruotas naudotojas (`user`), moderatorius (`moderator`) ir administratorius (`admin`). Moderatorius prižiūrės viešą naudotojų turinį. Administratorius papildomai tvarkys dalių katalogą, pardavėjų pasiūlymus, naudotojų paskyras ir roles.

## 1.2. Funkciniai reikalavimai

**Neprisijungęs sistemos lankytojas galės:**

1. Peržiūrėti platformos reprezentacinį puslapį;
2. Registruotis sistemoje;
3. Prisijungti prie internetinės aplikacijos.

Neprisijungęs lankytojas negalės naudotis komplektavimo, komplektų peržiūros, vertinimo ar komentavimo funkcijomis. Atskiras svečio režimas nenumatytas.

**Registruotas ir prisijungęs naudotojas (`user`) galės:**

1. Atsijungti nuo internetinės aplikacijos;
2. Peržiūrėti kompiuterio dalių katalogą;
3. Sudaryti asmeninio kompiuterio komplektą ir tvarkyti jame pasirinktas dalis;
4. Patikrinti pasirinktų dalių suderinamumą;
5. Peržiūrėti komplekto kainą, dalių kainas ir jų įsigijimo vietas;
6. Išsaugoti sudarytą kompiuterio komplektą;
7. Peržiūrėti, redaguoti ir pašalinti savo išsaugotus komplektus;
8. Paskelbti savo komplektą viešai arba vėl padaryti jį privatų;
9. Dalintis viešai paskelbto komplekto nuoroda; gavėjas komplektą galės peržiūrėti prisijungęs;
10. Peržiūrėti kitų naudotojų viešai paskelbtus komplektus;
11. Vertinti ir komentuoti matomus komplektus, įskaitant kitų naudotojų viešai paskelbtus komplektus;
12. Redaguoti ir pašalinti savo atsiliepimus matomuose komplektuose;
13. Peržiūrėti komplekto autoriaus viešą informaciją – naudotojo identifikatorių ir vardą.

**Moderatorius (`moderator`) galės:**

1. Atlikti visas registruotam naudotojui prieinamas funkcijas;
2. Šalinti netinkamus kitų naudotojų viešai paskelbtus komplektus;
3. Šalinti netinkamus kitų naudotojų komentarus viešai paskelbtuose komplektuose.

**Administratorius (`admin`) galės:**

1. Atlikti visas moderatoriui prieinamas funkcijas;
2. Tvarkyti kompiuterio dalių katalogą – pridėti, redaguoti ir pašalinti dalių įrašus;
3. Tvarkyti pardavėjų pasiūlymus – pardavėjus, kainas, įsigijimo nuorodas ir prekių prieinamumą;
4. Peržiūrėti naudotojų sąrašą, jų roles ir blokavimo būsenas;
5. Blokuoti taisykles pažeidžiančius naudotojus ir juos atblokuoti;
6. Pašalinti taisykles pažeidžiančių naudotojų paskyras;
7. Keisti kitų naudotojų roles į `user`, `moderator` arba `admin`.

**Bendrosios prieigos ir duomenų valdymo taisyklės:**

1. Registruojantis automatiškai suteikiama `user` rolė; naudotojas negali pats pasirinkti aukštesnių teisių;
2. Veiksmai leidžiami pagal naudotojo rolę ir konkretaus įrašo savininko ar autoriaus identifikatorių;
3. Nė viena rolė negali redaguoti svetimo komplekto, jo komponentų ar komentaro;
4. Nė viena rolė negali peržiūrėti ar šalinti svetimo privataus komplekto ir jo turinio;
5. Moderatorius negali valdyti naudotojų paskyrų, rolių, katalogo ar pardavėjų pasiūlymų;
6. Administratorius negali keisti savo rolės, blokuoti ar pašalinti savo paskyros;
7. Užblokavus paskyrą nutraukiamos visos jos prisijungimo sesijos; užblokuotas naudotojas negali prisijungti. Atblokavus būtina prisijungti iš naujo;
8. Pakeitus naudotojo rolę nutraukiamos visos jo prisijungimo sesijos;
9. Pašalinus paskyrą jos komplektai ir atsiliepimai išsaugomi be ryšio su paskyra, su autoriaus žyma „Pašalintas naudotojas“. Privatūs komplektai netampa vieši;
10. Pašalinus komplektą pašalinami jo komponentai, jų pasiūlymai ir komplekto atsiliepimai. Pašalinus komponentą pašalinami jo pasiūlymai.

## 1.3. Dabartinio įgyvendinimo ribos

Šiame dokumente aprašyti visos sistemos funkciniai reikalavimai. Dabartinė realizacija dar neapima visų jų:

- API įgyvendintos registracijos, prisijungimo, atsijungimo, trijų rolių, nuosavybės, privatumo, paskyrų administravimo, komplektų, komponentų, pasiūlymų ir atsiliepimų valdymo funkcijos;
- Bendras dalių katalogas dar neįgyvendintas. Dabartiniai komponentai priklauso konkrečiam komplektui ir yra tvarkomi jo savininko. Būsimo bendro katalogo įrašus tvarkys tik administratorius;
- Pasiūlymus ir kainas dabar gali keisti tik administratorius, tik jam matomuose komplektuose. Svetimų privačių komplektų pasiūlymai jam neprieinami;
- Dalių suderinamumo tikrinimas ir bendros komplekto kainos apskaičiavimas dar neįgyvendinti; API pateikia atskirų dalių pardavėjų pasiūlymus;
- Atsiliepimą šiuo metu sudaro kartu pateikiamas 1–5 balų įvertinimas ir tekstinis komentaras;
- Internetinė naudotojo sąsaja yra pradinė struktūra. API galimybės pasiekiamos per Swagger ar kitą API klientą; komplektavimo sąsaja ir dalijimosi nuorodomis funkcija internetinėje aplikacijoje dar numatytos įgyvendinti.
