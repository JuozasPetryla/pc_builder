import { categories } from "./constants";
import { useEffect, useRef, useState } from "react";

export function Icon({ name = "build" }) {
  const paths = {
    build:
      "M4 4h16v16H4z M8 8h8v8H8z M9 1v3m6-3v3M9 20v3m6-3v3M1 9h3m-3 6h3m16-6h3m-3 6h3",
    users:
      "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M17 4a4 4 0 0 1 0 8m1 3a4 4 0 0 1 4 4v2",
    account: "M20 21a8 8 0 0 0-16 0 M12 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10",
    logout: "M9 4H4v16h5 M9 12h13m-5-5 5 5-5 5",
    menu: "M3 6h18M3 12h18M3 18h18",
    plus: "M12 4v16M4 12h16",
  };
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] || paths.build} />
    </svg>
  );
}

export function Modal({ title, children, onClose, busy = false }) {
  const ref = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    const dialog = ref.current;
    dialog.showModal();
    return () => {
      dialog.close();
      previous?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby="modal-title"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="modal-heading">
        <h2 id="modal-title">{title}</h2>
        <button
          type="button"
          className="quiet"
          aria-label="Uždaryti"
          disabled={busy}
          onClick={onClose}
        >
          ✕
        </button>
      </div>
      {children}
    </dialog>
  );
}

const schemas = {
  build: [
    ["name", "Pavadinimas", "text", 3, 120],
    ["description", "Aprašymas", "textarea", 0, 2000],
    ["is_public", "Viešas komplektas", "checkbox"],
  ],
  component: [
    ["category", "Kategorija", "select", categories],
    ["manufacturer", "Gamintojas", "text", 2, 80],
    ["model", "Modelis", "text", 2, 120],
    ["description", "Aprašymas", "textarea", 0, 2000],
    ["specifications", "Specifikacijos (JSON objektas)", "json"],
  ],
  offer: [
    ["retailer", "Pardavėjas", "text", 2, 100],
    ["price", "Kaina (€)", "number", 0.01, 99999999.99],
    ["product_url", "Prekės nuoroda", "url", 1, 500],
    ["in_stock", "Yra sandėlyje", "checkbox"],
  ],
  review: [
    ["rating", "Įvertinimas", "range", 1, 5],
    ["comment", "Komentaras", "textarea", 3, 2000],
  ],
  role: [
    [
      "role",
      "Rolė",
      "select",
      {
        user: "Naudotojas",
        moderator: "Moderatorius",
        admin: "Administratorius",
      },
    ],
  ],
};

export function Editor({ kind, initial = {}, onSave, onClose }) {
  const [values, setValues] = useState(() =>
    Object.fromEntries(
      schemas[kind].map(([key, , type, min]) => [
        key,
        type === "json"
          ? JSON.stringify(initial[key] || { socket: "AM5" }, null, 2)
          : (initial[key] ??
            (type === "checkbox"
              ? key === "in_stock"
              : type === "select"
                ? Object.keys(min)[0]
                : type === "range"
                  ? 5
                  : "")),
      ]),
    ),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = { ...values };
      if (kind === "component") {
        try {
          body.specifications = JSON.parse(body.specifications);
        } catch {
          throw new Error(
            'Specifikacijos turi būti taisyklingas JSON objektas, pvz. {"socket":"AM5"}.',
          );
        }
        if (
          !body.specifications ||
          Array.isArray(body.specifications) ||
          typeof body.specifications !== "object" ||
          !Object.keys(body.specifications).length
        )
          throw new Error("Įrašykite bent vieną specifikaciją JSON objekte.");
      }
      if (kind === "review") body.rating = Number(body.rating);
      await onSave(body);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title={initial.id ? "Redaguoti įrašą" : "Naujas įrašas"}
      onClose={onClose}
      busy={busy}
    >
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          {schemas[kind].map(([key, label, type, min, max]) => (
            <label key={key} className={type === "checkbox" ? "check" : ""}>
              <span>
                {label}
                {type === "range" && `: ${values[key]} / 5`}
              </span>
              {type === "select" ? (
                <select
                  value={values[key]}
                  onChange={(e) =>
                    setValues({ ...values, [key]: e.target.value })
                  }
                >
                  {Object.entries(min).map(([value, text]) => (
                    <option key={value} value={value}>
                      {text}
                    </option>
                  ))}
                </select>
              ) : type === "textarea" || type === "json" ? (
                <textarea
                  rows={type === "json" ? 5 : 3}
                  value={values[key]}
                  required={type === "json" || min > 0}
                  minLength={min || undefined}
                  maxLength={max}
                  onChange={(e) =>
                    setValues({ ...values, [key]: e.target.value })
                  }
                  spellCheck={type !== "json"}
                />
              ) : (
                <input
                  type={type}
                  value={type === "checkbox" ? undefined : values[key]}
                  checked={type === "checkbox" ? values[key] : undefined}
                  required={!["checkbox", "range"].includes(type)}
                  min={["number", "range"].includes(type) ? min : undefined}
                  max={["number", "range"].includes(type) ? max : undefined}
                  minLength={["text", "url"].includes(type) ? min : undefined}
                  maxLength={["text", "url"].includes(type) ? max : undefined}
                  step={type === "number" ? "0.01" : undefined}
                  onChange={(e) =>
                    setValues({
                      ...values,
                      [key]:
                        type === "checkbox" ? e.target.checked : e.target.value,
                    })
                  }
                />
              )}
            </label>
          ))}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <div className="actions">
            <button type="button" className="secondary" onClick={onClose}>
              Atšaukti
            </button>
            <button type="submit">{busy ? "Saugoma…" : "Išsaugoti"}</button>
          </div>
        </fieldset>
      </form>
    </Modal>
  );
}

export function Confirmation({ title, message, action, onClose }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <Modal title={title} onClose={onClose} busy={busy}>
      <p>{message}</p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="actions">
        <button className="secondary" disabled={busy} onClick={onClose}>
          Atšaukti
        </button>
        <button
          className="danger"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await action();
            } catch (err) {
              setError(err.message);
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? "Vykdoma…" : "Patvirtinti"}
        </button>
      </div>
    </Modal>
  );
}
