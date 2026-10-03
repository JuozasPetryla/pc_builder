import { useEffect, useState } from 'react'
import { api } from './api'
import { categories } from './constants'
import { Modal } from './ui'

export default function CatalogPicker({ build, initial, onSave, onClose }) {
  const [category, setCategory] = useState(initial?.category || '')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [page, setPage] = useState({ loading: true })
  const [retry, setRetry] = useState(0)
  const query = new URLSearchParams({ limit: '12', offset: String(offset), q: search, ...(category && { category }) }).toString()
  useEffect(() => {
    let active = true
    api(`/catalog/components?${query}`).then(data => { if (active) setPage({ data, loading: false }) }).catch(err => { if (active) setPage({ error: err.message, loading: false }) })
    return () => { active = false }
  }, [query, retry])
  const used = new Set(build.components.filter(item => item.id !== initial?.id).map(item => item.category))
  function filter(update) { setPage({ loading: true }); setOffset(0); setSelected(null); update() }
  return <Modal title={initial ? 'Pakeisti pasirinktą komponentą' : 'Pasirinkti iš katalogo'} busy={busy} onClose={onClose}>
    <p className="muted">Pasirinkite administratoriaus sukurtą komponentą. Specifikacijos ir pasiūlymai bendri visiems komplektams.</p>
    <fieldset disabled={busy}>
      <label>Ieškoti pagal gamintoją ar modelį<input type="search" value={search} maxLength={120} onChange={e => filter(() => setSearch(e.target.value))} /></label>
      <label>Kategorija<select value={category} onChange={e => filter(() => setCategory(e.target.value))}><option value="">Visos kategorijos</option>{Object.entries(categories).map(([key, name]) => <option value={key} key={key}>{name}</option>)}</select></label>
      {page.loading ? <p role="status" className="loading"><span className="spinner" /> Kraunama…</p> : page.error ? <><p role="alert" className="error">{page.error}</p><button className="secondary" onClick={() => { setPage({ loading: true }); setRetry(retry + 1) }}>Bandyti dar kartą</button></> : <>
        {!page.data.length && <p className="empty">Tinkančių komponentų nėra. Katalogą pildo administratorius.</p>}
        <div className="picker-list">{page.data.map(item => <label key={item.id} className={`picker-option ${used.has(item.category) ? 'unavailable' : ''}`}><input type="radio" name="catalog-component" value={item.id} checked={selected === item.id} disabled={used.has(item.category)} onChange={() => setSelected(item.id)} /><span><strong>{item.manufacturer} {item.model}</strong><small>{categories[item.category]} · {used.has(item.category) ? 'Ši kategorija jau pasirinkta' : `${item.offers.length} pasiūlymai`}</small></span></label>)}</div>
        <div className="pagination"><button className="secondary" disabled={offset === 0} onClick={() => { setPage({ loading: true }); setOffset(offset - 12); setSelected(null) }}>← Ankstesnis</button><span>{offset / 12 + 1}</span><button className="secondary" disabled={page.data.length < 12} onClick={() => { setPage({ loading: true }); setOffset(offset + 12); setSelected(null) }}>Kitas →</button></div>
      </>}
      {error && <p className="error" role="alert">{error}</p>}
      <div className="actions"><button className="secondary" onClick={onClose}>Atšaukti</button><button disabled={!selected || page.loading} onClick={async () => { setBusy(true); setError(''); try { await onSave({ catalog_component_id: selected }) } catch (err) { setError(err.message) } finally { setBusy(false) } }}>{busy ? 'Saugoma…' : initial ? 'Pakeisti' : 'Pridėti į komplektą'}</button></div>
    </fieldset>
  </Modal>
}
