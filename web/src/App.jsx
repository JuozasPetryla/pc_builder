import CatalogPicker from "./CatalogPicker";
import { categories } from "./constants";
import { useEffect, useState } from "react";
import { api, hasSession, refreshSession, setSession } from "./api";
import { Confirmation, Editor, Icon, Modal } from "./ui";

const PAGE_SIZE = 12;
const names = {
  build: "Komplektai",
  component: "Komponentai",
  catalog: "Komponentų katalogas",
  offer: "Pardavėjų pasiūlymai",
  review: "Atsiliepimai",
  user: "Naudotojai",
};
const money = (value) =>
  new Intl.NumberFormat("lt-LT", { style: "currency", currency: "EUR" }).format(
    value,
  );
const go = (path) => {
  window.location.hash = path;
};

function useResource(path, revision = 0) {
  const [state, setState] = useState({ loading: true });
  useEffect(() => {
    let active = true;
    api(path)
      .then((data) => {
        if (active) setState({ data, loading: false });
      })
      .catch((error) => {
        if (active) setState({ error: error.message, loading: false });
      });
    return () => {
      active = false;
    };
  }, [path, revision]);
  return state;
}

function Loading() {
  return (
    <p className="loading" role="status">
      <span className="spinner" /> Kraunama…
    </p>
  );
}
function ErrorMessage({ message }) {
  return (
    <p className="error" role="alert">
      {message}
    </p>
  );
}

function Auth({ onLogin }) {
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    const form = new FormData(event.currentTarget);
    const body = {
      username: form.get("username"),
      password: form.get("password"),
    };
    try {
      if (register) {
        await api("/auth/register", "POST", body, false);
        setRegister(false);
        setNotice("Paskyra sukurta. Prisijunkite su pasirinktais duomenimis.");
      } else {
        setSession(await api("/auth/login", "POST", body, false));
        await onLogin();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="landing">
      <div>
        <p className="eyebrow">Nuo idėjos iki komplekto</p>
        <h1>
          Tavo kitas PC.
          <br />
          <em>Tavo pasirinkimai.</em>
        </h1>
        <p className="lead">
          Sudėk komponentus į vieną vietą, peržiūrėk pardavėjų pasiūlymus ir
          pasidalink savo komplektu su bendruomene.
        </p>
        <img
          className="hero-image"
          src="/pc-build.svg"
          width="620"
          height="400"
          alt="Kompiuterio korpuso, procesoriaus ir vaizdo plokštės iliustracija"
        />
        <div className="features">
          <span>01 / Komplektuok</span>
          <span>02 / Palygink kainas</span>
          <span>03 / Dalinkis</span>
        </div>
      </div>
      <div className="panel auth">
        <p className="eyebrow">PC Builder bendruomenė</p>
        <h2>{register ? "Sukurti paskyrą" : "Sveiki sugrįžę"}</h2>
        <p className="muted">
          Prisijunkite, kad matytumėte komplektus ir išsaugotumėte savo idėjas.
        </p>
        <form onSubmit={submit}>
          <fieldset disabled={busy}>
            <label>
              Naudotojo vardas
              <input
                name="username"
                autoComplete="username"
                required
                minLength={3}
                maxLength={80}
                pattern="[a-zA-Z0-9_.\-]+"
                title="3–80 lotyniškų raidžių, skaitmenų arba simbolių _ . -"
              />
            </label>
            <label>
              Slaptažodis
              <input
                name="password"
                type="password"
                autoComplete={register ? "new-password" : "current-password"}
                required
                minLength={8}
                maxLength={128}
              />
            </label>
            {register && (
              <p className="muted">
                Slaptažodis: bent 8 simboliai. Naudotojo vardui naudokite
                lotyniškas raides, skaitmenis, tašką, brūkšnį arba pabraukimą.
              </p>
            )}
            {error && <ErrorMessage message={error} />}
            {notice && (
              <p role="status" className="success">
                {notice}
              </p>
            )}
            <button className="full" type="submit">
              {busy ? "Palaukite…" : register ? "Registruotis" : "Prisijungti"}
            </button>
            <button
              className="quiet full"
              type="button"
              onClick={() => {
                setRegister(!register);
                setError("");
                setNotice("");
              }}
            >
              {register
                ? "Jau turite paskyrą? Prisijunkite"
                : "Neturite paskyros? Registruokitės"}
            </button>
          </fieldset>
        </form>
      </div>
    </section>
  );
}

function Collection({
  kind,
  path,
  revision,
  user,
  build,
  onCreate,
  onEdit,
  onDelete,
  onRead,
  onProfile,
  onStatus,
  onRole,
}) {
  const [offset, setOffset] = useState(0);
  const [filter, setFilter] = useState("");
  const query = `${path}?limit=${PAGE_SIZE}&offset=${offset}${filter ? `&${filter}` : ""}`;
  const [retry, setRetry] = useState(0);
  const canCreate =
    kind === "build" ||
    (kind === "catalog" && user.role === "admin") ||
    kind === "review" ||
    (kind === "component" && build?.owner_id === user.id) ||
    (kind === "offer" && user.role === "admin");
  const options = {
    build: [["public_only=true", "Tik vieši"]],
    catalog: Object.entries(categories).map(([value, text]) => [`category=${value}`, text]),
    component: Object.entries(categories).map(([value, text]) => [
      `category=${value}`,
      text,
    ]),
    offer: [
      ["in_stock=true", "Yra sandėlyje"],
      ["in_stock=false", "Nėra sandėlyje"],
    ],
    review: [5, 4, 3, 2, 1].map((n) => [`rating=${n}`, `${n} / 5`]),
  };
  return (
    <section className="collection">
      <div className="section-heading">
        <h2>{names[kind]}</h2>
        <div className="toolbar">
          {options[kind] && (
            <label className="filter">
              <span className="sr-only">Filtruoti: {names[kind]}</span>
              <select
                value={filter}
                onChange={(e) => {
                  setFilter(e.target.value);
                  setOffset(0);
                }}
              >
                <option value="">Visi</option>
                {options[kind].map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          )}
          {canCreate && (
            <button onClick={() => onCreate(kind, path)}>
              <Icon name="plus" /> {kind === "component" ? "Pridėti iš katalogo" : "Pridėti"}
            </button>
          )}
        </div>
      </div>
      <CollectionResults
        key={`${query}:${revision}:${retry}`}
        {...{
          query,
          kind,
          user,
          build,
          onEdit,
          onDelete,
          onRead,
          onProfile,
          onStatus,
          onRole,
        }}
        onRetry={() => setRetry(retry + 1)}
        offset={offset}
        setOffset={setOffset}
      />
    </section>
  );
}

function CollectionResults({
  query,
  kind,
  user,
  build,
  onEdit,
  onDelete,
  onRead,
  onProfile,
  onStatus,
  onRole,
  onRetry,
  offset,
  setOffset,
}) {
  const { data, loading, error } = useResource(query);
  if (loading) return <Loading />;
  if (error)
    return (
      <>
        <ErrorMessage message={error} />
        <button className="secondary" onClick={onRetry}>
          Bandyti dar kartą
        </button>
      </>
    );
  return (
    <>
      {!data.length && (
        <div className="empty">
          {kind === "component"
            ? "Komplekte dar nėra komponentų. Pasirinkite juos iš katalogo."
            : kind === "catalog"
              ? "Katalogas tuščias. Jį gali papildyti administratorius."
              : "Įrašų nėra. Pridėkite naują įrašą arba pakeiskite filtrą."}
        </div>
      )}
      <div className={kind === "build" ? "cards" : "records"}>
        {data.map((item) => {
          const own =
            kind === "build"
              ? item.owner_id === user.id
              : kind === "review"
                ? item.author_id === user.id
                : build?.owner_id === user.id;
          const editable = ["offer", "catalog"].includes(kind) ? user.role === "admin" : own;
          const removable =
            editable ||
            (["build", "review"].includes(kind) &&
              ["admin", "moderator"].includes(user.role) &&
              (kind === "build" ? item.is_public : build?.is_public));
          return (
            <article className={`panel record ${kind}`} key={item.id}>
              {kind === "build" && (
                <>
                  <div className="card-top">
                    <Icon />
                    <span className="badge">
                      {item.is_public ? "Viešas" : "Privatus"}
                    </span>
                  </div>
                  <h3>
                    <button
                      className="text-button"
                      onClick={() => go(`/builds/${item.id}`)}
                    >
                      {item.name}
                    </button>
                  </h3>
                  <p className="description">
                    {item.description || "Aprašymas dar nepateiktas."}
                  </p>
                  <p className="muted">
                    {item.components.length} komponentai · {item.reviews.length}{" "}
                    atsiliepimai
                  </p>
                  <Author
                    id={item.owner_id}
                    name={item.owner_name}
                    onProfile={onProfile}
                  />
                </>
              )}
              {["component", "catalog"].includes(kind) && (
                <>
                  <span className="badge">{categories[item.category]}</span>
                  <h3>
                    <button
                      className="text-button"
                      onClick={() =>
                        go(kind === "catalog" ? `/catalog/${item.id}` : `/builds/${build.id}/components/${item.id}`)
                      }
                    >
                      {item.manufacturer} {item.model}
                    </button>
                  </h3>
                  <p>{item.description}</p>
                  <p className="muted">
                    {item.offers.length} pardavėjų pasiūlymai
                  </p>
                </>
              )}
              {kind === "offer" && (
                <>
                  <h3>{item.retailer}</h3>
                  <p className="price">{money(item.price)}</p>
                  <p className="muted">
                    {item.in_stock ? "Yra sandėlyje" : "Nėra sandėlyje"}
                  </p>
                  {/^https?:\/\//i.test(item.product_url) && (
                    <a
                      href={item.product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Pardavėjo svetainė ↗
                    </a>
                  )}
                </>
              )}
              {kind === "review" && (
                <>
                  <span
                    className="rating"
                    aria-label={`Įvertinimas ${item.rating} iš 5`}
                  >
                    {"★".repeat(item.rating)}
                    {"☆".repeat(5 - item.rating)}
                  </span>
                  <p className="description">{item.comment}</p>
                  <Author
                    id={item.author_id}
                    name={item.author_name}
                    onProfile={onProfile}
                  />
                </>
              )}
              {kind === "user" ? (
                <>
                  <h3>{item.username}</h3>
                  <p>
                    <span className="badge">{item.role}</span>{" "}
                    {item.is_blocked ? "Užblokuotas" : "Aktyvus"}
                  </p>
                  <div className="actions">
                    <button
                      className="secondary"
                      onClick={() => onProfile(item.id)}
                    >
                      Profilis
                    </button>
                    {item.id !== user.id && (
                      <>
                        <button
                          className="secondary"
                          onClick={() => onRole(item)}
                        >
                          Keisti rolę
                        </button>
                        <button
                          className="secondary"
                          onClick={() => onStatus(item)}
                        >
                          {item.is_blocked ? "Atblokuoti" : "Blokuoti"}
                        </button>
                        <button
                          className="danger subtle"
                          onClick={() => onDelete(kind, item)}
                        >
                          {kind === "component" ? "Pašalinti iš komplekto" : "Pašalinti"}
                        </button>
                      </>
                    )}
                  </div>
                </>
              ) : (
                <div className="actions">
                  <button
                    className="secondary"
                    onClick={() => onRead(kind, item)}
                  >
                    Peržiūrėti
                  </button>
                  {editable && (
                    <button
                      className="secondary"
                      onClick={() => onEdit(kind, item)}
                    >
                      {kind === "component" ? "Keisti pasirinkimą" : "Redaguoti"}
                    </button>
                  )}
                  {removable && (
                    <button
                      className="danger subtle"
                      onClick={() => onDelete(kind, item)}
                    >
                      {kind === "component" ? "Pašalinti iš komplekto" : "Pašalinti"}
                    </button>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </div>
      <div className="pagination">
        <button
          className="secondary"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
        >
          ← Ankstesnis
        </button>
        <span>Puslapis {offset / PAGE_SIZE + 1}</span>
        <button
          className="secondary"
          disabled={data.length < PAGE_SIZE}
          onClick={() => setOffset(offset + PAGE_SIZE)}
        >
          Kitas →
        </button>
      </div>
    </>
  );
}

function Author({ id, name, onProfile }) {
  return id ? (
    <button className="author text-button" onClick={() => onProfile(id)}>
      <Icon name="account" /> {name}
    </button>
  ) : (
    <span className="muted">{name}</span>
  );
}

function BuildPage({ id, componentId, revision, actions, user }) {
  const { data: build, loading, error } = useResource(`/builds/${id}`);
  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  if (componentId)
    return (
      <ComponentPage
        key={componentId}
        {...{ build, componentId, revision, actions, user }}
      />
    );
  const own = build.owner_id === user.id;
  return (
    <>
      <button className="quiet" onClick={() => go("/builds")}>
        ← Visi komplektai
      </button>
      <section className="detail-header panel">
        <div>
          <p className="eyebrow">
            {build.is_public ? "Viešas komplektas" : "Privatus komplektas"}
          </p>
          <h1>{build.name}</h1>
          <p className="description">{build.description}</p>
          <Author
            id={build.owner_id}
            name={build.owner_name}
            onProfile={actions.onProfile}
          />
        </div>
        <div className="actions">
          {own && (
            <button onClick={() => actions.onEdit("build", build)}>
              Redaguoti
            </button>
          )}
          {(own || (build.is_public && user.role !== "user")) && (
            <button
              className="danger subtle"
              onClick={() => actions.onDelete("build", build)}
            >
              Pašalinti
            </button>
          )}
          {build.is_public && (
            <button
              className="secondary"
              onClick={() => actions.share(build.id)}
            >
              Kopijuoti nuorodą
            </button>
          )}
        </div>
      </section>
      <Collection
        key={`components:${revision}`}
        kind="component"
        path={`/builds/${id}/components`}
        {...{ revision, user, build }}
        {...actions}
      />
      <Collection
        key={`reviews:${revision}`}
        kind="review"
        path={`/builds/${id}/reviews`}
        {...{ revision, user, build }}
        {...actions}
      />
    </>
  );
}

function ComponentPage({ build, componentId, revision, actions, user }) {
  const {
    data: component,
    loading,
    error,
  } = useResource(`/components/${componentId}`);
  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  if (component.build_id !== build.id)
    return <ErrorMessage message="Komponentas nepriklauso šiam komplektui." />;
  return (
    <>
      <button className="quiet" onClick={() => go(`/builds/${build.id}`)}>
        ← {build.name}
      </button>
      <section className="panel detail-header">
        <div>
          <p className="eyebrow">{categories[component.category]}</p>
          <h1>
            {component.manufacturer} {component.model}
          </h1>
          <p className="description">{component.description}</p>
          <dl className="specs">
            {Object.entries(component.specifications).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>
                  {typeof value === "object"
                    ? JSON.stringify(value)
                    : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
        {build.owner_id === user.id && (
          <div className="actions">
            <button onClick={() => actions.onEdit("component", component)}>
              Redaguoti
            </button>
            <button
              className="danger subtle"
              onClick={() => actions.onDelete("component", component)}
            >
              Pašalinti
            </button>
          </div>
        )}
      </section>
      <Collection
        kind="offer"
        path={`/catalog/components/${component.catalog_component_id}/offers`}
        {...{ revision, user, build }}
        {...actions}
      />
    </>
  );
}

function ReadModal({ kind, item, onClose }) {
  return (
    <Modal
      title={
        kind === "review"
          ? "Atsiliepimas"
          : kind === "offer"
            ? "Pardavėjo pasiūlymas"
            : "Naudotojo profilis"
      }
      onClose={onClose}
    >
      {kind === "review" ? (
        <>
          <p className="rating">{item.rating} / 5</p>
          <p className="description">{item.comment}</p>
          <p>
            {item.author_name} ·{" "}
            {new Date(item.created_at).toLocaleDateString("lt-LT")}
          </p>
        </>
      ) : kind === "offer" ? (
        <>
          <h3>{item.retailer}</h3>
          <p className="price">{money(item.price)}</p>
          <p>{item.in_stock ? "Yra sandėlyje" : "Nėra sandėlyje"}</p>
          {/^https?:\/\//i.test(item.product_url) && (
            <a
              href={item.product_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Atidaryti prekės nuorodą ↗
            </a>
          )}
        </>
      ) : (
        <dl className="specs">
          <div>
            <dt>Naudotojas</dt>
            <dd>{item.username}</dd>
          </div>
          <div>
            <dt>ID</dt>
            <dd>{item.id}</dd>
          </div>
          {item.role && (
            <div>
              <dt>Rolė</dt>
              <dd>{item.role}</dd>
            </div>
          )}
        </dl>
      )}
    </Modal>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(hasSession);
  const [route, setRoute] = useState(
    window.location.hash.slice(1) || "/builds",
  );
  const [revision, setRevision] = useState(0);
  const [modal, setModal] = useState(null);
  const [notice, setNotice] = useState(null);
  const [menu, setMenu] = useState(false);
  const [busy, setBusy] = useState(false);
  function notify(message, error = false) {
    setNotice({ message, error });
  }
  useEffect(() => {
    const change = () => {
      setRoute(window.location.hash.slice(1) || "/builds");
      setMenu(false);
      setModal(null);
    };
    const expired = () => {
      setUser(null);
      setModal(null);
      setNotice({
        message: "Sesija pasibaigė. Prisijunkite iš naujo.",
        error: true,
      });
    };
    window.addEventListener("hashchange", change);
    window.addEventListener("session-expired", expired);
    let active = true;
    if (hasSession())
      api("/auth/me")
        .then((value) => {
          if (active) setUser(value);
        })
        .catch((err) => {
          if (active) setNotice({ message: err.message, error: true });
        })
        .finally(() => {
          if (active) setBooting(false);
        });
    return () => {
      active = false;
      window.removeEventListener("hashchange", change);
      window.removeEventListener("session-expired", expired);
    };
  }, []);
  const close = () => setModal(null);
  function changed(message) {
    setRevision((v) => v + 1);
    close();
    notify(message);
  }
  const endpoint = (kind, item) =>
    `/${{ build: "builds", component: "components", catalog: "catalog/components", offer: "offers", review: "reviews", user: "users" }[kind]}/${item.id}`;
  async function safely(action) {
    setBusy(true);
    try {
      await action();
    } catch (error) {
      notify(error.message, true);
    } finally {
      setBusy(false);
    }
  }
  const actions = {
    onCreate: (kind, path) => kind === "component"
      ? safely(async () => setModal({ type: "select", path, build: await api(path.replace(/\/components$/, "")) }))
      : setModal({ type: "edit", kind, path }),
    onEdit: (kind, item) =>
      safely(async () => {
        const latest = await api(endpoint(kind, item));
        if (kind === "component") {
          setModal({ type: "select", path: endpoint(kind, item), initial: latest, build: await api(`/builds/${latest.build_id}`) });
          return;
        }
        setModal({
          type: "edit",
          kind,
          item: latest,
          path: endpoint(kind, item),
        });
      }),
    onDelete: (kind, item) =>
      setModal({
        type: "confirm",
        title: "Pašalinti įrašą?",
        message:
          kind === "build"
            ? "Bus pašalintas komplektas, jo pasirinkimai ir atsiliepimai. Bendras katalogas ir pasiūlymai išliks."
            : kind === "component"
              ? "Komponentas bus pašalintas tik iš šio komplekto. Katalogo įrašas ir jo pasiūlymai išliks."
              : kind === "user"
                ? "Paskyra ir jos sesijos bus pašalintos. Turinys liks su anonimizuotu autoriumi."
                : "Įrašas bus pašalintas. Veiksmo atšaukti negalima.",
        action: async () => {
          await api(endpoint(kind, item), "DELETE");
          if (kind === "build" && route.startsWith(`/builds/${item.id}`))
            go("/builds");
          if (kind === "catalog" && route === `/catalog/${item.id}`) go("/catalog");
          if (kind === "component" && route.endsWith(`/components/${item.id}`))
            go(`/builds/${item.build_id}`);
          changed("Įrašas pašalintas.");
        },
      }),
    onRead: (kind, item) =>
      kind === "catalog" ? go(`/catalog/${item.id}`) : kind === "build"
        ? go(`/builds/${item.id}`)
        : kind === "component"
          ? go(`/builds/${item.build_id}/components/${item.id}`)
          : safely(async () =>
              setModal({
                type: "read",
                kind,
                item: await api(endpoint(kind, item)),
              }),
            ),
    onProfile: (id) =>
      safely(async () =>
        setModal({
          type: "read",
          kind: "user",
          item: await api(`/users/${id}`),
        }),
      ),
    onRole: (item) =>
      setModal({
        type: "edit",
        kind: "role",
        item,
        path: `/users/${item.id}/role`,
      }),
    onStatus: (item) =>
      setModal({
        type: "confirm",
        title: item.is_blocked
          ? "Atblokuoti naudotoją?"
          : "Blokuoti naudotoją?",
        message: item.is_blocked
          ? "Naudotojas vėl galės prisijungti."
          : "Visos naudotojo sesijos bus nutrauktos.",
        action: async () => {
          await api(`/users/${item.id}/status`, "PUT", {
            is_blocked: !item.is_blocked,
          });
          changed("Naudotojo būsena atnaujinta.");
        },
      }),
    share: (id) =>
      safely(async () => {
        await navigator.clipboard.writeText(
          `${window.location.origin}/#/builds/${id}`,
        );
        notify("Komplekto nuoroda nukopijuota. Gavėjas turės prisijungti.");
      }),
  };
  const catalogMatch = route.match(/^\/catalog\/(\d+)$/);
  const match = route.match(/^\/builds\/(\d+)(?:\/components\/(\d+))?$/);
  return (
    <>
      <a
        className="skip-link"
        href="#main"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main").focus();
        }}
      >
        Pereiti prie turinio
      </a>
      <header>
        <div className="header-inner">
          <a className="brand" href="#/builds">
            <span className="brand-icon">
              <Icon />
            </span>
            PC<span>Builder</span>
          </a>
          {user && (
            <>
              <button
                className="hamburger secondary"
                aria-label="Meniu"
                aria-expanded={menu}
                aria-controls="navigation"
                onClick={() => setMenu(!menu)}
              >
                <Icon name="menu" />
              </button>
              <nav
                id="navigation"
                className={menu ? "open" : ""}
                aria-label="Pagrindinis meniu"
              >
                <a
                  href="#/builds"
                  aria-current={
                    route.startsWith("/builds") ? "page" : undefined
                  }
                >
                  <Icon /> Komplektai
                </a>
                <a href="#/catalog" aria-current={route.startsWith("/catalog") ? "page" : undefined}><Icon /> Katalogas</a>
                {user.role === "admin" && (
                  <a
                    href="#/users"
                    aria-current={route === "/users" ? "page" : undefined}
                  >
                    <Icon name="users" /> Naudotojai
                  </a>
                )}
                <button
                  className="quiet"
                  disabled={busy}
                  onClick={() =>
                    safely(async () => {
                      setModal({
                        type: "read",
                        kind: "user",
                        item: await api("/auth/me"),
                      });
                      setMenu(false);
                    })
                  }
                >
                  <Icon name="account" /> {user.username}
                </button>
                <button
                  className="quiet"
                  disabled={busy}
                  onClick={() =>
                    safely(async () => {
                      await refreshSession();
                      notify("Sesijos žetonai atnaujinti.");
                    })
                  }
                >
                  <Icon name="account" /> Atnaujinti sesiją
                </button>
                <button
                  className="quiet"
                  disabled={busy}
                  onClick={() =>
                    safely(async () => {
                      await api("/auth/logout", "POST");
                      setSession(null);
                      setUser(null);
                      close();
                      setMenu(false);
                      notify("Atsijungėte.");
                      go("/builds");
                    })
                  }
                >
                  <Icon name="logout" /> Atsijungti
                </button>
              </nav>
            </>
          )}
        </div>
      </header>
      <main id="main" className="shell" tabIndex="-1">
        {notice && (
          <div
            className={`notice ${notice.error ? "error" : "success"}`}
            role={notice.error ? "alert" : "status"}
          >
            <span>{notice.message}</span>
            <button
              className="quiet"
              aria-label="Uždaryti pranešimą"
              onClick={() => setNotice(null)}
            >
              ✕
            </button>
          </div>
        )}
        {busy && <Loading />}
        {booting ? (
          <Loading />
        ) : !user ? (
          <Auth
            onLogin={async () => {
              setUser(await api("/auth/me"));
              notify("Sėkmingai prisijungėte.");
            }}
          />
        ) : route === "/users" && user.role === "admin" ? (
          <>
            <p className="eyebrow">Administravimas</p>
            <h1>Naudotojų valdymas</h1>
            <Collection
              key="users"
              kind="user"
              path="/users"
              {...{ user, revision }}
              {...actions}
            />
          </>
        ) : route === "/catalog" ? (
          <><p className="eyebrow">Bendri komponentai</p><h1>Komponentų katalogas</h1><p className="lead">Administratorius pildo katalogą. Savo komplekte pasirinkite norimus komponentus iš šio sąrašo.</p><Collection key="catalog" kind="catalog" path="/catalog/components" {...{ user, revision }} {...actions} /></>
        ) : catalogMatch ? (
          <CatalogPage key={`${route}:${revision}`} id={catalogMatch[1]} {...{ user, revision, actions }} />
        ) : match ? (
          <BuildPage
            key={`${route}:${revision}`}
            id={match[1]}
            componentId={match[2]}
            {...{ user, revision, actions }}
          />
        ) : (
          <>
            <div className="workspace-heading">
              <div>
                <p className="eyebrow">Tavo idėjos. Bendruomenės patirtis.</p>
                <h1>Komplektų erdvė</h1>
                <p className="lead">Atrask viešus komplektus ir kurk savąjį.</p>
              </div>
              <img
                src="/pc-build.svg"
                width="620"
                height="400"
                alt="Kompiuterio komponentų iliustracija"
              />
            </div>
            <Collection
              key="builds"
              kind="build"
              path="/builds"
              {...{ user, revision }}
              {...actions}
            />
          </>
        )}
      </main>
      <footer>
        <a className="brand" href="#/builds">
          PC<span>Builder</span>
        </a>
        <p>Komplektuok. Palygink. Dalinkis.</p>
        <a href="/api/docs" target="_blank" rel="noopener noreferrer">
          API dokumentacija ↗
        </a>
      </footer>
      {modal?.type === "edit" && (
        <Editor
          key={`${modal.kind}:${modal.item?.id || "new"}`}
          kind={modal.kind === "catalog" ? "component" : modal.kind}
          initial={modal.item}
          onClose={close}
          onSave={async (body) => {
            const saved = await api(modal.path, modal.item ? "PUT" : "POST", body);
            changed("Pakeitimai išsaugoti.");
            if (modal.kind === "build" && !modal.item) go(`/builds/${saved.id}`);
          }}
        />
      )}
      {modal?.type === "select" && <CatalogPicker build={modal.build} initial={modal.initial} onClose={close} onSave={async body => { await api(modal.path, modal.initial ? "PUT" : "POST", body); changed("Komplekto komponentas pasirinktas."); }} />}
      {modal?.type === "confirm" && <Confirmation {...modal} onClose={close} />}
      {modal?.type === "read" && <ReadModal {...modal} onClose={close} />}
    </>
  );
}

function CatalogPage({ id, revision, actions, user }) {
  const { data: item, loading, error } = useResource(`/catalog/components/${id}`);
  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  return <><button className="quiet" onClick={() => go('/catalog')}>← Katalogas</button><section className="panel detail-header"><div><p className="eyebrow">{categories[item.category]}</p><h1>{item.manufacturer} {item.model}</h1><p className="description">{item.description}</p><dl className="specs">{Object.entries(item.specifications).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd></div>)}</dl></div>{user.role === 'admin' && <div className="actions"><button onClick={() => actions.onEdit('catalog', item)}>Redaguoti kataloge</button><button className="danger subtle" onClick={() => actions.onDelete('catalog', item)}>Pašalinti iš katalogo</button></div>}</section><Collection kind="offer" path={`/catalog/components/${id}/offers`} {...{ revision, user }} {...actions} /></>;
}
