import { test, expect } from "@playwright/test";

const password = "Browser-test-password-42";
const unique = (prefix) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
const dialog = (page) => page.getByRole("dialog");
const section = (page, name) =>
  page
    .locator("section.collection")
    .filter({ has: page.getByRole("heading", { name, exact: true }) });
async function save(page) {
  await dialog(page)
    .getByRole("button", { name: "Išsaugoti", exact: true })
    .click();
  await expect(dialog(page)).toHaveCount(0);
}
async function confirm(page) {
  await dialog(page).getByRole("button", { name: "Patvirtinti" }).click();
  await expect(dialog(page)).toHaveCount(0);
}
async function login(page, username, secret = password) {
  await page.goto("/");
  await page.getByLabel("Naudotojo vardas").fill(username);
  await page.getByLabel("Slaptažodis", { exact: true }).fill(secret);
  await page.getByRole("button", { name: "Prisijungti", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Komplektų erdvė" }),
  ).toBeVisible();
}
async function newBuild(page, name) {
  await section(page, "Komplektai")
    .getByRole("button", { name: "Pridėti" })
    .click();
  await dialog(page).getByLabel("Pavadinimas").fill(name);
  await dialog(page)
    .getByLabel("Aprašymas")
    .fill("Naršyklės integracinis bandymas");
  await dialog(page).getByLabel("Viešas komplektas").check();
  await save(page);
  // Test databases can contain many builds; open the created resource by its real API ID.
  const id = await page.evaluate(async (name) => {
    const tokens = JSON.parse(sessionStorage.getItem("pc-builder-session"));
    for (let offset = 0; ; offset += 200) {
      const response = await fetch(
        `/api/v1/builds?limit=200&offset=${offset}`,
        { headers: { Authorization: `Bearer ${tokens.access_token}` } },
      );
      const builds = await response.json();
      const found = builds.find((build) => build.name === name);
      if (found) return found.id;
      if (builds.length < 200) throw new Error("Created build not found");
    }
  }, name);
  await page.goto(`/#/builds/${id}`);
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  return id;
}
async function newCatalogComponent(page, model) {
  await page.getByRole("link", { name: "Katalogas" }).click();
  await section(page, "Komponentų katalogas")
    .getByRole("button", { name: "Pridėti" })
    .click();
  await dialog(page).getByLabel("Kategorija").selectOption("cpu");
  await dialog(page).getByLabel("Gamintojas").fill("AMD");
  await dialog(page).getByLabel("Modelis", { exact: true }).fill(model);
  await dialog(page)
    .getByLabel("Specifikacijos (JSON objektas)")
    .fill('{"socket":"AM5","cores":8}');
  await save(page);
  await page.getByRole("link", { name: "Komplektai" }).click();
}
async function selectComponent(page, model) {
  await section(page, "Komponentai")
    .getByRole("button", { name: "Pridėti iš katalogo" })
    .click();
  if (model) await dialog(page).getByRole("searchbox").fill(model);
  const options = dialog(page).locator(".picker-option:not(.unavailable)");
  const option = model ? options.filter({ hasText: model }).first() : options.first();
  const title = await option.locator("strong").innerText();
  await option.locator("input").check();
  await dialog(page).getByRole("button", { name: "Pridėti į komplektą" }).click();
  await expect(dialog(page)).toHaveCount(0);
  return title;
}

test("registration, CRUD, refresh, validation, sharing route and mobile navigation", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("dialog", () => {
    throw new Error("Native alert/confirm is forbidden");
  });
  const username = unique("browser");
  await page.goto("/");
  await expect(
    page.getByRole("img", { name: /Kompiuterio korpuso/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Neturite paskyros/ }).click();
  await page.getByLabel("Naudotojo vardas").fill(username);
  await page.getByLabel("Slaptažodis", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Registruotis", exact: true }).click();
  await expect(
    page.getByText("Paskyra sukurta.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Prisijungti", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Komplektų erdvė" }),
  ).toBeVisible();
  const name = unique("Testinis komplektas");
  const buildId = await newBuild(page, name);
  await page
    .locator(".detail-header")
    .getByRole("button", { name: "Redaguoti", exact: true })
    .click();
  await dialog(page).getByLabel("Aprašymas").fill("Atnaujintas aprašymas");
  await save(page);
  await expect(
    page.getByText("Atnaujintas aprašymas", { exact: true }),
  ).toBeVisible();
  const selectedPart = await selectComponent(page);
  const components = section(page, "Komponentai");
  await components
    .getByRole("button", { name: "Keisti pasirinkimą", exact: true })
    .click();
  await expect(dialog(page)).toContainText(
    "Pasirinkite administratoriaus sukurtą komponentą",
  );
  await page.keyboard.press("Escape");
  await components.getByRole("button", { name: "Peržiūrėti" }).click();
  await expect(
    page.getByRole("heading", { name: selectedPart }),
  ).toBeVisible();
  await expect(page.locator("dd").filter({ hasText: /^12$/ })).toBeVisible();
  await expect(
    section(page, "Pardavėjų pasiūlymai").getByRole("button", {
      name: "Pridėti",
    }),
  ).toHaveCount(0);
  await page.goto(`/#/builds/${buildId}`);
  const reviews = section(page, "Atsiliepimai");
  await reviews.getByRole("button", { name: "Pridėti" }).click();
  await dialog(page)
    .getByLabel("Komentaras")
    .fill("Puikus testinis komplektas");
  await dialog(page).getByRole("slider").fill("4");
  await save(page);
  await reviews.getByRole("button", { name: "Peržiūrėti" }).click();
  await expect(dialog(page).getByText("4 / 5", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await reviews.getByRole("button", { name: "Redaguoti" }).click();
  await dialog(page).getByLabel("Komentaras").fill("Atnaujintas atsiliepimas");
  await save(page);
  await reviews.getByRole("button", { name: "Pašalinti" }).click();
  await confirm(page);
  await expect(reviews.getByText("Atnaujintas atsiliepimas")).toHaveCount(0);
  await page
    .locator(".detail-header")
    .getByRole("button", { name: username })
    .click();
  await expect(dialog(page)).toContainText(username);
  await page.keyboard.press("Escape");
  const before = await page.evaluate(
    () =>
      JSON.parse(sessionStorage.getItem("pc-builder-session")).refresh_token,
  );
  await page.evaluate(() => {
    const pair = JSON.parse(sessionStorage.getItem("pc-builder-session"));
    pair.access_token = "expired";
    sessionStorage.setItem("pc-builder-session", JSON.stringify(pair));
  });
  await page.reload();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  const after = await page.evaluate(
    () =>
      JSON.parse(sessionStorage.getItem("pc-builder-session")).refresh_token,
  );
  expect(after).not.toBe(before);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("navigation")).toBeHidden();
  await page.getByRole("button", { name: "Meniu", exact: true }).click();
  await expect(page.getByRole("navigation")).toBeVisible();
  await page.getByRole("button", { name: "Atnaujinti sesiją" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Sesijos žetonai atnaujinti." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Meniu", exact: true }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({ path: "test-results/mobile.png", fullPage: true });
  await section(page, "Komponentai")
    .getByRole("button", { name: "Pašalinti" })
    .click();
  await confirm(page);
  await page
    .locator(".detail-header")
    .getByRole("button", { name: "Pašalinti" })
    .click();
  await confirm(page);
  await expect(
    page.getByRole("heading", { name: "Komplektų erdvė" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Meniu", exact: true }).click();
  await page.getByRole("button", { name: "Atsijungti" }).click();
  await expect(
    page.getByRole("heading", { name: "Sveiki sugrįžę" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("admin manages offers, roles, blocking and deletion through modal forms", async ({
  page,
  request,
}) => {
  test.skip(
    !process.env.E2E_ADMIN_USERNAME || !process.env.E2E_ADMIN_PASSWORD,
    "Provide a disposable test administrator",
  );
  const targetName = unique("managed");
  const created = await request.post("/api/v1/auth/register", {
    data: { username: targetName, password },
  });
  expect(created.status()).toBe(201);
  await login(
    page,
    process.env.E2E_ADMIN_USERNAME,
    process.env.E2E_ADMIN_PASSWORD,
  );
  const model = unique("Admin CPU");
  await newCatalogComponent(page, model);
  const buildId = await newBuild(page, unique("Admin build"));
  await selectComponent(page, model);
  await section(page, "Komponentai")
    .getByRole("button", { name: "Peržiūrėti" })
    .click();
  const offers = section(page, "Pardavėjų pasiūlymai");
  await offers.getByRole("button", { name: "Pridėti" }).click();
  await dialog(page).getByLabel("Pardavėjas").fill("Testinė parduotuvė");
  await dialog(page).getByLabel("Kaina (€)").fill("199.99");
  await dialog(page)
    .getByLabel("Prekės nuoroda")
    .fill("https://example.com/test");
  await save(page);
  await offers.getByRole("button", { name: "Peržiūrėti" }).click();
  await expect(dialog(page)).toContainText("Testinė parduotuvė");
  await page.keyboard.press("Escape");
  await offers.getByRole("button", { name: "Redaguoti" }).click();
  await dialog(page).getByLabel("Kaina (€)").fill("189.99");
  await dialog(page).getByLabel("Yra sandėlyje").uncheck();
  await save(page);
  await expect(
    offers.getByRole("article").getByText("Nėra sandėlyje", { exact: true }),
  ).toBeVisible();
  await offers.getByRole("button", { name: "Pašalinti" }).click();
  await confirm(page);
  await page.goto(`/#/builds/${buildId}`);
  await page
    .locator(".detail-header")
    .getByRole("button", { name: "Pašalinti" })
    .click();
  await confirm(page);
  await page.getByRole("link", { name: "Naudotojai", exact: true }).click();
  const users = section(page, "Naudotojai");
  let target = users
    .locator("article")
    .filter({
      has: page.getByRole("heading", { name: targetName, exact: true }),
    });
  await expect(users.locator(".pagination")).toBeVisible();
  while (!(await target.count())) {
    await users.getByRole("button", { name: "Kitas →" }).click();
    await expect(users.locator(".loading")).toHaveCount(0);
  }
  await target.getByRole("button", { name: "Profilis" }).click();
  await expect(dialog(page)).toContainText(targetName);
  await page.keyboard.press("Escape");
  await target.getByRole("button", { name: "Keisti rolę" }).click();
  await dialog(page)
    .getByRole("combobox", { name: "Rolė", exact: true })
    .selectOption("moderator");
  await save(page);
  await expect(users.locator(".pagination")).toBeVisible();
  while (!(await target.count())) {
    await users.getByRole("button", { name: "Kitas →" }).click();
    await expect(users.locator(".loading")).toHaveCount(0);
  }
  await expect(target).toContainText("moderator");
  await target.getByRole("button", { name: "Blokuoti", exact: true }).click();
  await confirm(page);
  await expect(users.locator(".pagination")).toBeVisible();
  while (!(await target.count())) {
    await users.getByRole("button", { name: "Kitas →" }).click();
    await expect(users.locator(".loading")).toHaveCount(0);
  }
  await expect(target).toContainText("Užblokuotas");
  await target.getByRole("button", { name: "Atblokuoti", exact: true }).click();
  await confirm(page);
  await expect(users.locator(".pagination")).toBeVisible();
  while (!(await target.count())) {
    await users.getByRole("button", { name: "Kitas →" }).click();
    await expect(users.locator(".loading")).toHaveCount(0);
  }
  await target.getByRole("button", { name: "Pašalinti" }).click();
  await confirm(page);
  await expect(target).toHaveCount(0);
});
