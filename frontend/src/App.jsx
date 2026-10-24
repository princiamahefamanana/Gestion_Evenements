import { lazy, Suspense, useState } from 'react'
import './App.css'
import About from './About.jsx'

const API_BASE = import.meta.env.PROD ? '' : `http://${window.location.hostname}:8000`
const ReservationStatusChart = lazy(() => import('./ReservationStatusChart.jsx'))

function DashboardChart({ reservations }) {
  return (
    <Suspense fallback={<section className="panel reservation-chart-card" aria-busy="true"><h2>Chargement du graphique…</h2></section>}>
      <ReservationStatusChart reservations={reservations} />
    </Suspense>
  )
}

function ActionIcon({ name }) {
  const paths = {
    edit: <><path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z" /></>,
    delete: <><path d="M3 6h18" /><path d="M8 6V4h8v2" /><path d="m19 6-1 14H6L5 6" /><path d="M10 11v5M14 11v5" /></>,
    print: <><path d="M6 9V3h12v6" /><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" /><path d="M6 14h12v7H6z" /></>,
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    cancel: <><circle cx="12" cy="12" r="9" /><path d="m9 9 6 6m0-6-6 6" /></>,
    availability: <><path d="M12 3v9" /><path d="M7.05 5.05a7 7 0 1 0 9.9 0" /></>,
    send: <><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></>,
  }

  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}

const definitions = {
  clients: {
    title: 'Clients',
    endpoint: '/api/clients/',
    columns: [['nom', 'Nom'], ['email', 'E-mail'], ['telephone', 'Téléphone']],
    fields: [
      { name: 'nom', label: 'Nom complet', required: true },
      { name: 'email', label: 'E-mail', type: 'email', required: true },
      { name: 'telephone', label: 'Téléphone (10 chiffres)', type: 'tel', required: true, minLength: 10, maxLength: 10, pattern: '[0-9]{10}' },
    ],
    initial: { nom: '', email: '', telephone: '' },
  },
  espaces: {
    title: 'Espaces',
    endpoint: '/api/espaces/',
    columns: [['nom', 'Nom'], ['adresse', 'Adresse'], ['capacite', 'Capacité'], ['tarif_horaire', 'Tarif / heure'], ['disponible', 'Disponibilité']],
    fields: [
      { name: 'nom', label: 'Nom de l’espace', required: true },
      { name: 'adresse', label: 'Adresse', required: true },
      { name: 'capacite', label: 'Capacité (minimum 80 personnes)', type: 'number', min: 80, required: true },
      { name: 'tarif_horaire', label: 'Tarif horaire minimum 100 000 Ar', type: 'number', min: 100000, step: '0.01', required: true },
      { name: 'description', label: 'Description', type: 'textarea' },
      { name: 'disponible', label: 'Disponible à la réservation', type: 'checkbox' },
    ],
    initial: { nom: '', adresse: '', capacite: 80, tarif_horaire: 100000, description: '', disponible: true },
  },
  types: {
    title: 'Types d’événements',
    endpoint: '/api/types-evenements/',
    columns: [['nom', 'Type d’événement'], ['description', 'Description']],
    fields: [
      { name: 'nom', label: 'Type d’événement', required: true },
      { name: 'description', label: 'Description', type: 'textarea' },
    ],
    initial: { nom: '', description: '' },
  },
  reservations: {
    title: 'Réservations',
    endpoint: '/api/reservations/',
    columns: [
      ['type_evenement_nom', 'Événement'],
      ['client_nom', 'Client'],
      ['espace_nom', 'Espace'],
      ['date_debut', 'Début'],
      ['date_fin', 'Fin'],
      ['nombre_invites', 'Invités'],
      ['montant_total', 'Montant estimé'],
      ['statut_display', 'Statut'],
    ],
    fields: [
      { name: 'client', label: 'Client', type: 'select', source: 'clients', value: 'id', text: 'nom', required: true, staffOnly: true },
      { name: 'espace', label: 'Espace', type: 'select', source: 'espaces', value: 'id', text: (item) => `${item.nom} — ${Number(item.tarif_horaire).toLocaleString('fr-FR')} Ar/heure`, required: true },
      { name: 'type_evenement', label: 'Type d’événement', type: 'select', source: 'types', value: 'id', text: 'nom', required: true },
      { name: 'date_debut', label: 'Date et heure de début', type: 'datetime-local', required: true },
      { name: 'date_fin', label: 'Date et heure de fin', type: 'datetime-local', required: true },
      { name: 'nombre_invites', label: 'Nombre d’invités (minimum 10)', type: 'number', min: 10, required: true },
      { name: 'statut', label: 'Statut', type: 'select', options: [['pending', 'En attente'], ['confirmed', 'Confirmée'], ['cancelled', 'Annulée'], ['completed', 'Terminée']], staffOnly: true },
    ],
    initial: { client: '', espace: '', type_evenement: '', date_debut: '', date_fin: '', nombre_invites: 10, statut: 'pending' },
  },
  paiements: {
    title: 'Paiements',
    endpoint: '/api/paiements/',
    columns: [['reservation_resume', 'Réservation'], ['montant', 'Montant'], ['mode_paiement', 'Mode'], ['statut_display', 'Statut'], ['reference', 'Référence'], ['envoye_admin', 'Transmission']],
    fields: [
      { name: 'reservation', label: 'Réservation', type: 'select', source: 'reservations', value: 'id', text: (item) => `${item.type_evenement_nom} — ${item.espace_nom} (#${item.id})`, required: true },
      { name: 'montant', label: 'Montant calculé selon la réservation', type: 'number', readOnly: true },
      { name: 'mode_paiement', label: 'Mode de paiement', type: 'select', options: [['cash', 'Espèces'], ['transfer', 'Virement'], ['card', 'Carte bancaire']] },
      { name: 'statut', label: 'Statut', type: 'select', options: [['pending', 'En attente'], ['paid', 'Payé'], ['cancelled', 'Annulé']], staffOnly: true },
      { name: 'reference', label: 'Référence de paiement', staffOnly: true },
    ],
    initial: { reservation: '', montant: '', mode_paiement: 'cash', statut: 'pending', reference: '' },
  },
  utilisateurs: {
    title: 'Utilisateurs',
    endpoint: '/api/auth/users/',
    columns: [['username', 'Nom d’utilisateur'], ['email', 'E-mail'], ['role', 'Rôle'], ['phone', 'Téléphone']],
    fields: [
      { name: 'username', label: 'Nom d’utilisateur', required: true, minLength: 3, pattern: '.*[^0-9].*', title: 'Le nom d’utilisateur ne peut pas être composé uniquement de chiffres.' },
      { name: 'email', label: 'E-mail', type: 'email', required: true },
      { name: 'first_name', label: 'Prénom', minLength: 3 },
      { name: 'last_name', label: 'Nom de famille', minLength: 3 },
      { name: 'role', label: 'Rôle', type: 'select', options: [['participant', 'Client'], ['organizer', 'Gestionnaire'], ['admin', 'Administrateur']] },
      { name: 'phone', label: 'Téléphone (10 chiffres)', type: 'tel', required: true, minLength: 10, maxLength: 10, pattern: '[0-9]{10}' },
      { name: 'password', label: 'Mot de passe', type: 'password', required: true, createOnly: true },
    ],
    initial: { username: '', email: '', first_name: '', last_name: '', role: 'organizer', phone: '', password: '' },
  },
}

const navigation = [
  ['dashboard', 'Tableau de bord'],
  ['reservations', 'Réservations'],
  ['espaces', 'Espaces'],
  ['types', 'Types d’événements'],
  ['clients', 'Clients'],
  ['paiements', 'Paiements'],
]

function cookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? match[1] : ''
}

async function apiRequest(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const csrfToken = cookie('csrftoken')
  if (csrfToken) headers['X-CSRFToken'] = csrfToken
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...options,
    headers,
  })
  const text = await response.text()
  const payload = text ? JSON.parse(text) : null
  if (!response.ok) {
    const detail = payload?.detail
      || Object.values(payload || {}).flat(Infinity).find((value) => typeof value === 'string')
      || 'Une erreur est survenue.'
    throw new Error(detail)
  }
  return payload
}

function asList(payload) {
  return Array.isArray(payload) ? payload : payload?.results || []
}

async function fetchAllPages(path) {
  const items = []
  let nextPath = path
  while (nextPath) {
    const payload = await apiRequest(nextPath)
    items.push(...asList(payload))
    if (!payload?.next) break
    const nextUrl = new URL(payload.next, API_BASE)
    nextPath = `${nextUrl.pathname}${nextUrl.search}`
  }
  return items
}

function localDateTime(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

function AuthPanel({ onLogin, onRegistered, onAbout, error, setError }) {
  const params = new URLSearchParams(window.location.search)
  const [mode, setMode] = useState(() => params.has('uid') && params.has('token') ? 'reset' : 'login')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [login, setLogin] = useState({ username: '', password: '' })
  const [register, setRegister] = useState({ username: '', email: '', password: '' })
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const submit = async (event, request) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      await request()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-card">
        <div className="brand-block">
          <div className="brand-mark">E</div>
          <div><p className="eyebrow">ESPACE ÉVÉNEMENTIEL</p><h1>Réservez votre salle</h1></div>
        </div>
        {mode === 'login' && (
          <form className="login-form" onSubmit={(event) => submit(event, async () => {
            await apiRequest('/api/auth/csrf/')
            const user = await apiRequest('/api/auth/login/', { method: 'POST', body: JSON.stringify(login) })
            onLogin(user)
          })}>
            <h2>Connexion</h2>
            <label>Nom d’utilisateur<input autoComplete="username" required value={login.username} onChange={(e) => setLogin({ ...login, username: e.target.value })} /></label>
            <label>Mot de passe<input type="password" autoComplete="current-password" required value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })} /></label>
            <button disabled={busy}>{busy ? 'Connexion…' : 'Se connecter'}</button>
            <div className="auth-actions">
              <button type="button" className="text-action" onClick={() => { setMode('forgot'); setError('') }}>Mot de passe oublié ?</button>
              <button type="button" className="text-action" onClick={() => { setMode('register'); setError('') }}>Créer un compte</button>
            </div>
          </form>
        )}
        {mode === 'register' && (
          <form className="login-form" onSubmit={(event) => submit(event, async () => {
            await apiRequest('/api/auth/csrf/')
            const user = await apiRequest('/api/auth/register/', { method: 'POST', body: JSON.stringify(register) })
            onRegistered(user)
          })}>
            <h2>Créer un compte client</h2>
            <label>Nom d’utilisateur<input autoComplete="username" minLength={3} maxLength={150} pattern=".*[^0-9].*" title="Le nom d’utilisateur ne peut pas être composé uniquement de chiffres." required value={register.username} onChange={(e) => setRegister({ ...register, username: e.target.value })} /></label>
            <label>E-mail<input type="email" autoComplete="email" required value={register.email} onChange={(e) => setRegister({ ...register, email: e.target.value })} /></label>
            <label>Mot de passe<input type="password" autoComplete="new-password" required value={register.password} onChange={(e) => setRegister({ ...register, password: e.target.value })} /></label>
            <button disabled={busy}>{busy ? 'Création…' : 'Créer mon compte'}</button>
            <button type="button" className="text-action" onClick={() => { setMode('login'); setError('') }}>Retour à la connexion</button>
          </form>
        )}
        {mode === 'forgot' && (
          <form className="login-form" onSubmit={(event) => submit(event, async () => {
            const result = await apiRequest('/api/auth/password-reset/', { method: 'POST', body: JSON.stringify({ email }) })
            setMessage(result.detail)
          })}>
            <h2>Mot de passe oublié</h2>
            <p>Indiquez l’adresse e-mail de votre compte.</p>
            <label>E-mail<input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
            <button disabled={busy}>{busy ? 'Envoi…' : 'Envoyer le lien'}</button>
            <button type="button" className="text-action" onClick={() => { setMode('login'); setError('') }}>Retour à la connexion</button>
          </form>
        )}
        {mode === 'reset' && (
          <form className="login-form" onSubmit={(event) => submit(event, async () => {
            const result = await apiRequest('/api/auth/password-reset/confirm/', {
              method: 'POST',
              body: JSON.stringify({ uid: params.get('uid'), token: params.get('token'), new_password: password }),
            })
            window.history.replaceState({}, '', window.location.pathname)
            setMode('login')
            setMessage(result.detail)
          })}>
            <h2>Nouveau mot de passe</h2>
            <label>Mot de passe<input type="password" autoComplete="new-password" required value={password} onChange={(e) => setPassword(e.target.value)} /></label>
            <button disabled={busy}>{busy ? 'Enregistrement…' : 'Réinitialiser'}</button>
          </form>
        )}
        {error && <p className="alert error" role="alert">{error}</p>}
        {message && <p className="alert success" role="status">{message}</p>}
        {onAbout && (
          <p className="login-about">
            <button type="button" className="text-action" onClick={onAbout}>À propos</button>
          </p>
        )}
      </section>
    </main>
  )
}

function App() {
  const [user, setUser] = useState(null)
  const [active, setActive] = useState('dashboard')
  const [data, setData] = useState({ clients: [], espaces: [], types: [], reservations: [], paiements: [], utilisateurs: [] })
  const [dashboard, setDashboard] = useState({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [, setNotice] = useState('')
  const [form, setForm] = useState(null)
  const [query, setQuery] = useState('')
  const [searchDraft, setSearchDraft] = useState('')
  const [printError, setPrintError] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [showAbout, setShowAbout] = useState(false)

  const staff = user?.role === 'admin' || user?.role === 'organizer' || user?.is_superuser
  const loadData = async (currentUser) => {
    const keys = ['clients', 'espaces', 'types', 'reservations', 'paiements']
    const results = await Promise.all(keys.map((key) => fetchAllPages(definitions[key].endpoint)))
    const next = Object.fromEntries(keys.map((key, index) => [key, results[index]]))
    if (currentUser.role === 'admin' || currentUser.is_superuser) {
      next.utilisateurs = await fetchAllPages('/api/auth/users/')
    }
    const summary = await apiRequest('/api/tableau-de-bord/')
    setData(next)
    setDashboard(summary)
  }

  const authenticate = async (currentUser, successMessage) => {
    setUser(currentUser)
    setError('')
    setNotice(successMessage)
    setBusy(true)
    try {
      await loadData(currentUser)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const logout = async () => {
    setBusy(true)
    try {
      await apiRequest('/api/auth/logout/', { method: 'POST' })
      setUser(null)
      setData({ clients: [], espaces: [], types: [], reservations: [], paiements: [], utilisateurs: [] })
      setDashboard({})
      setNotice('Vous êtes déconnecté.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const config = definitions[active]
  const records = active === 'utilisateurs' ? data.utilisateurs : data[active] || []
  const filtered = records
  const mayCreate = staff
    ? active !== 'clients'
    : ['reservations', 'paiements'].includes(active)

  const navigateTo = (key) => {
    setActive(key)
    setQuery('')
    setSearchDraft('')
    setForm(null)
    setError('')
    setPrintError('')
    setMenuOpen(false)
  }

  const startCreate = () => {
    if (!config) return
    const initial = { ...config.initial }
    if (active === 'reservations') {
      initial.client = data.clients.find((client) => client.user === user.id)?.id || data.clients[0]?.id || ''
      initial.espace = data.espaces.find((espace) => espace.disponible)?.id || ''
      initial.type_evenement = data.types[0]?.id || ''
      const start = new Date()
      start.setDate(start.getDate() + 1)
      start.setHours(10, 0, 0, 0)
      const end = new Date(start)
      end.setHours(end.getHours() + 4)
      initial.date_debut = localDateTime(start)
      initial.date_fin = localDateTime(end)
    }
    if (active === 'paiements') {
      const eligibleReservations = data.reservations.filter((reservation) => ['pending', 'confirmed'].includes(reservation.statut))
      const reservation = eligibleReservations[0]
      initial.reservation = reservation?.id || ''
      initial.montant = reservation?.montant_total || ''
    }
    setForm({ id: null, values: initial })
    setError('')
  }

  const startEdit = (record) => {
    if (!config) return
    if (!staff && active === 'reservations' && record.statut !== 'pending') return
    if (!staff && active === 'paiements') return
    if (!staff && active !== 'reservations' && active !== 'clients') return
    const values = { ...record }
    delete values.password
    for (const field of config.fields) {
      if (field.type === 'datetime-local' && values[field.name]) {
        values[field.name] = localDateTime(new Date(values[field.name]))
      }
    }
    setForm({ id: record.id, values })
    setError('')
  }

  const saveRecord = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      let payload = { ...form.values }
      for (const field of config.fields) {
        if (field.staffOnly && !staff) delete payload[field.name]
      }
      if (active === 'reservations') {
        delete payload.statut
        delete payload.client
      }
      if (active === 'paiements' && form.id) {
        payload = { reference: form.values.reference, statut: form.values.statut }
      } else if (active === 'paiements' && !staff) {
        payload = {
          reservation: form.values.reservation,
          mode_paiement: form.values.mode_paiement,
        }
      }
      if (active === 'reservations' && staff && form.id) {
        delete payload.type_evenement
        delete payload.date_debut
        delete payload.date_fin
        delete payload.espace
        delete payload.nombre_invites
      }
      if (active === 'utilisateurs' && form.id && !payload.password) {
        delete payload.password
      }
      if (form.id) {
        await apiRequest(`${config.endpoint}${form.id}/`, { method: 'PATCH', body: JSON.stringify(payload) })
      } else {
        await apiRequest(config.endpoint, { method: 'POST', body: JSON.stringify(payload) })
      }
      setForm(null)
      await loadData(user)
      if (form.id || !staff) {
        setNotice(form.id ? 'Les modifications ont été enregistrées.' : 'La nouvelle entrée a été créée.')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const deleteRecord = async (record) => {
    if (!staff && (active !== 'reservations' || record.statut !== 'pending')) return
    const reservationName = active === 'reservations'
      ? `la réservation « ${record.type_evenement_nom} — ${record.client_nom} »`
      : `« ${record.nom || record.type_evenement_nom || record.username || 'cette entrée'} »`
    const paymentWarning = active === 'reservations' && staff
      ? ' Les paiements associés seront également supprimés.'
      : ''
    if (!window.confirm(`Supprimer ${reservationName} ?${paymentWarning}`)) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await apiRequest(`${config.endpoint}${record.id}/`, { method: 'DELETE' })
      await loadData(user)
      setNotice('L’entrée a été supprimée.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const toggleSpaceAvailability = async (space) => {
    const nextAvailability = !space.disponible
    const message = nextAvailability
      ? `Rendre « ${space.nom} » disponible pour les nouvelles réservations ?`
      : `Rendre « ${space.nom} » indisponible pour les nouvelles réservations ?`
    if (!window.confirm(message)) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await apiRequest(`${definitions.espaces.endpoint}${space.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ disponible: nextAvailability }),
      })
      await loadData(user)
      setNotice(nextAvailability ? 'La salle est maintenant disponible.' : 'La salle est maintenant indisponible.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const searchRecords = async (event) => {
    event.preventDefault()
    if (!config) return
    const term = searchDraft.trim()
    setBusy(true)
    setError('')
    try {
      const path = term ? `${config.endpoint}?q=${encodeURIComponent(term)}` : config.endpoint
      const found = await fetchAllPages(path)
      if (active === 'utilisateurs') {
        setData((current) => ({ ...current, utilisateurs: found }))
      } else {
        setData((current) => ({ ...current, [active]: found }))
      }
      setQuery(term)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const clearSearch = async () => {
    setSearchDraft('')
    setQuery('')
    if (!config) return
    setBusy(true)
    setError('')
    try {
      const found = await fetchAllPages(config.endpoint)
      if (active === 'utilisateurs') {
        setData((current) => ({ ...current, utilisateurs: found }))
      } else {
        setData((current) => ({ ...current, [active]: found }))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const cancelReservation = async (record) => {
      setBusy(true)
      setError('')
      setNotice('')
      try {
        await apiRequest(`${config.endpoint}${record.id}/cancel/`, { method: 'POST', body: '{}' })
        await loadData(user)
        setNotice('La réservation a été annulée.')
      } catch (err) {
        setError(err.message)
      } finally {
        setBusy(false)
      }
  }

  const sendPayment = async (payment) => {
    setBusy(true)
    setError('')
    try {
      await apiRequest(`${config.endpoint}${payment.id}/send/`, { method: 'POST', body: '{}' })
      await loadData(user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const cancelPayment = async (payment) => {
    setBusy(true)
    setError('')
    try {
      await apiRequest(`${config.endpoint}${payment.id}/cancel/`, { method: 'POST', body: '{}' })
      await loadData(user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const printPayment = (payment) => {
      const printWindow = window.open('', '_blank', 'width=760,height=650')
      if (!printWindow) {
        setPrintError('Autorisez les fenêtres contextuelles pour imprimer le reçu.')
        return
      }
      setPrintError('')
      const escapeHtml = (value) => String(value ?? '—').replace(/[&<>"']/g, (character) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      })[character])
      const rows = [
        ['Référence du paiement', payment.reference || `PAY-${payment.id}`],
        ['Réservation', payment.reservation_resume],
        ['Montant', `${Number(payment.montant).toLocaleString('fr-FR')} Ar`],
        ['Mode de paiement', { cash: 'Espèces', transfer: 'Virement', card: 'Carte bancaire' }[payment.mode_paiement] || payment.mode_paiement],
        ['Statut', payment.statut_display],
        ['Date', new Date(payment.date_paiement).toLocaleString('fr-FR')],
      ]
      printWindow.document.write(`<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Reçu de paiement — PDF</title><style>@page{size:A4;margin:20mm}body{font:16px Arial,sans-serif;color:#18313b;margin:48px}h1{color:#0f766e}p{color:#64748b}.receipt{max-width:600px;margin:auto}.row{display:flex;justify-content:space-between;gap:20px;padding:14px 0;border-bottom:1px solid #dbe4e8}.row span{color:#64748b}.total{font-size:1.2rem;font-weight:bold}@media print{body{margin:0}}</style></head><body><main class="receipt"><h1>Espace événementiel</h1><p>Reçu de paiement</p>${rows.map(([label, value], index) => `<div class="row ${index === 2 ? 'total' : ''}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join('')}<p>Merci pour votre réservation.</p></main><script>window.addEventListener('load',()=>window.print())</script></body></html>`)
      printWindow.document.close()
  }

  const printClient = (client) => {
    const printWindow = window.open('', '_blank', 'width=760,height=650')
    if (!printWindow) {
      setPrintError('Autorisez les fenêtres contextuelles pour imprimer la fiche client.')
      return
    }
    setPrintError('')
    const escapeHtml = (value) => String(value ?? '—').replace(/[&<>"']/g, (character) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    })[character])
    const reservations = data.reservations.filter((reservation) => reservation.client === client.id)
    const reservationRows = reservations.map((reservation) => (
      `<tr><td>${escapeHtml(reservation.type_evenement_nom)}</td><td>${escapeHtml(reservation.espace_nom)}</td><td>${escapeHtml(new Date(reservation.date_debut).toLocaleString('fr-FR'))}</td><td>${escapeHtml(reservation.statut_display)}</td></tr>`
    )).join('')
    const reservationContent = reservations.length
      ? `<table><thead><tr><th>Événement</th><th>Espace</th><th>Date de début</th><th>Statut</th></tr></thead><tbody>${reservationRows}</tbody></table>`
      : '<p>Aucune réservation enregistrée.</p>'
    printWindow.document.write(`<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Fiche client — ${escapeHtml(client.nom)}</title><style>@page{size:A4;margin:20mm}body{font:16px Arial,sans-serif;color:#18313b;margin:48px}h1{color:#0f766e}h2{margin-top:32px}p{color:#64748b}.client-details{line-height:1.8}table{width:100%;border-collapse:collapse;text-align:left}th,td{padding:10px 8px;border-bottom:1px solid #dbe4e8}th{color:#64748b}@media print{body{margin:0}}</style></head><body><main><h1>Espace événementiel</h1><p>Fiche client</p><section class="client-details"><p><strong>Nom :</strong> ${escapeHtml(client.nom)}</p><p><strong>E-mail :</strong> ${escapeHtml(client.email)}</p><p><strong>Téléphone :</strong> ${escapeHtml(client.telephone)}</p></section><h2>Réservations</h2>${reservationContent}</main><script>window.addEventListener('load',()=>window.print())</script></body></html>`)
    printWindow.document.close()
  }

  const fieldValue = (field, value, disabled = false) => {
    if (field.type === 'checkbox') return <input type="checkbox" checked={Boolean(value)} onChange={(event) => setForm({ ...form, values: { ...form.values, [field.name]: event.target.checked } })} />
    if (field.type === 'textarea') return <textarea required={field.required} value={value ?? ''} onChange={(event) => setForm({ ...form, values: { ...form.values, [field.name]: event.target.value } })} />
    if (field.type === 'datetime-local') {
      const [date = '', time = ''] = (value ?? '').split('T')
      const updateDateTimePart = (part, nextValue) => {
        const nextParts = { date, time, [part]: nextValue }
        setForm({
          ...form,
          values: {
            ...form.values,
            [field.name]: nextParts.date && nextParts.time ? `${nextParts.date}T${nextParts.time}` : '',
          },
        })
      }
      return (
        <span className="date-time-inputs">
          <input aria-label={`${field.label} — date`} type="date" required={field.required} disabled={disabled} value={date} onChange={(event) => updateDateTimePart('date', event.target.value)} />
          <input aria-label={`${field.label} — heure`} type="time" required={field.required} disabled={disabled} value={time} onChange={(event) => updateDateTimePart('time', event.target.value)} />
        </span>
      )
    }
    if (field.type === 'select') {
      const choices = (field.options || data[field.source] || [])
        .filter((choice) => user.is_superuser || field.name !== 'role' || choice[0] !== 'admin')
        .filter((choice) => !(active === 'utilisateurs' && field.name === 'role' && choice[0] === 'participant'))
        .filter((choice) => staff || field.source !== 'espaces' || choice.disponible)
        .filter((choice) => staff || field.source !== 'reservations' || ['pending', 'confirmed'].includes(choice.statut))
      return (
        <select required={field.required} disabled={disabled || (staff && active === 'reservations' && Boolean(form.id) && field.name === 'type_evenement')} value={value ?? ''} onChange={(event) => {
          const selectedValue = event.target.value
          const values = { ...form.values, [field.name]: selectedValue }
          if (active === 'paiements' && field.name === 'reservation') {
            values.montant = data.reservations.find((reservation) => String(reservation.id) === selectedValue)?.montant_total || ''
          }
          setForm({ ...form, values })
        }}>
          {field.name !== 'statut' && <option value="">Sélectionner</option>}
          {choices.map((choice) => (
            <option key={choice[field.value || '0']} value={choice[field.value || '0']}>
              {field.text ? (typeof field.text === 'function' ? field.text(choice) : choice[field.text]) : choice[1]}
            </option>
          ))}
        </select>
      )
    }
    return <input type={field.type || 'text'} min={field.min} minLength={field.minLength} maxLength={field.maxLength} pattern={field.pattern} step={field.step} required={field.required} disabled={disabled} readOnly={field.readOnly} value={value ?? ''} onChange={(event) => setForm({ ...form, values: { ...form.values, [field.name]: event.target.value } })} />
  }

  const renderCell = (record, key) => {
    const value = record[key]
    if (key === 'envoye_admin') return value ? 'Envoyé à l’admin' : 'Pas encore envoyé'
    if (typeof value === 'boolean') return value ? 'Disponible' : 'Indisponible'
    if (key === 'date_debut' || key === 'date_fin') {
      if (!value) return '—'
      const date = new Date(value)
      if (active === 'reservations' && !staff) {
        return (
          <span className="reservation-date-time">
            <span>{date.toLocaleDateString('fr-FR')}</span>
            <span>{date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</span>
          </span>
        )
      }
      return date.toLocaleString('fr-FR')
    }
    if (key === 'tarif_horaire' || key === 'montant_total' || key === 'montant') {
      return value == null ? '—' : `${Number(value).toLocaleString('fr-FR')} Ar`
    }
    if (key === 'mode_paiement') return { cash: 'Espèces', transfer: 'Virement', card: 'Carte bancaire' }[value] || value || '—'
    return value || '—'
  }

  const heading = active === 'dashboard' && staff
    ? 'Vue d’ensemble'
    : active === 'dashboard'
      ? 'Tableau de bord'
    : active === 'apropos'
      ? 'À propos'
    : active === 'utilisateurs'
      ? 'Utilisateurs'
      : active === 'espaces' && staff
        ? 'Gestion des espaces'
        : config?.title

  if (!user) {
    if (showAbout) return <About standalone onBack={() => setShowAbout(false)} />
    return <AuthPanel onLogin={(value) => authenticate(value, '')} onRegistered={(value) => authenticate(value, 'Votre compte client est prêt.')} onAbout={() => setShowAbout(true)} error={error} setError={setError} />
  }

  return (
    <div className="app-shell">
      <aside id="main-navigation" className={`sidebar${menuOpen ? ' is-open' : ''}`}>
        <div className="brand-header">
          <div className="brand-mark">E</div>
          <div><strong>Espace événementiel</strong><small>Gestion des salles</small></div>
        </div>
        <nav className="nav-list" aria-label="Navigation principale">
          {navigation.map(([key, title]) => (
            <button key={key} type="button" className={`nav-item ${active === key ? 'active' : ''}`} onClick={() => navigateTo(key)}>
              {title}
            </button>
          ))}
          {user.role === 'admin' || user.is_superuser ? (
            <button type="button" className={`nav-item ${active === 'utilisateurs' ? 'active' : ''}`} onClick={() => navigateTo('utilisateurs')}>
              Utilisateurs
            </button>
          ) : null}
             <button type="button" className={`nav-item ${active === 'apropos' ? 'active' : ''}`} onClick={() => navigateTo('apropos')}>
            À propos
          </button>
        </nav>
        <div className="sidebar-user">
          <strong>{user.username}</strong>
          <small>{staff ? 'Administrateur' : 'Client'}</small>
          <button type="button" className="logout-button" onClick={logout} disabled={busy}>Déconnexion</button>
        </div>
      </aside>
      {menuOpen && <button type="button" className="sidebar-backdrop" aria-label="Fermer le menu" onClick={() => setMenuOpen(false)} />}

      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-heading">
            <div><p className="eyebrow">GESTION DES ÉVÉNEMENTS</p><h1>{heading}</h1></div>
          </div>
          <div className="topbar-actions">
            {config && mayCreate && <button type="button" className="primary-button" onClick={startCreate} disabled={busy}>{active === 'reservations' && !staff ? 'Réserver un espace' : `Ajouter ${active === 'espaces' ? 'un espace' : active === 'types' ? 'un type' : active === 'paiements' ? 'un paiement' : active === 'utilisateurs' ? 'un utilisateur' : 'une réservation'}`}</button>}
            <button
              type="button"
              className="menu-toggle"
              aria-label={menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
              aria-expanded={menuOpen}
              aria-controls="main-navigation"
              onClick={() => setMenuOpen((open) => !open)}
            >
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                {menuOpen ? <path d="m6 6 12 12M18 6 6 18" /> : <path d="M4 6h16M4 12h16M4 18h16" />}
              </svg>
            </button>
          </div>
        </header>
        {error && <p className="alert error" role="alert">{error}</p>}
        {printError && <p className="alert error" role="alert">{printError}</p>}

        {busy && <p className="loading-note">Chargement…</p>}
        {active === 'dashboard' && staff && (
          <section className="admin-dashboard">
            <div className="stats-grid admin-stats-grid">
              <article className="stat-card admin-stat-card stat-tone-violet">
                <span>Total des salles</span>
                <strong>{Number(dashboard.total_espaces ?? 0).toLocaleString('fr-FR')}</strong>
                <small>Espaces enregistrés</small>
              </article>
              <article className="stat-card admin-stat-card stat-tone-green">
                <span>Salles disponibles</span>
                <strong>{Number(dashboard.espaces_disponibles ?? 0).toLocaleString('fr-FR')}</strong>
                <small>Ouvertes aux réservations</small>
              </article>
              <article className="stat-card admin-stat-card stat-tone-amber">
                <span>À confirmer</span>
                <strong>{Number(dashboard.reservations_en_attente ?? 0).toLocaleString('fr-FR')}</strong>
                <small>Réservations en attente</small>
              </article>
              <article className="stat-card admin-stat-card stat-tone-blue">
                <span>Clients</span>
                <strong>{Number(dashboard.total_clients ?? 0).toLocaleString('fr-FR')}</strong>
                <small>Comptes clients</small>
              </article>
            </div>

            <DashboardChart reservations={data.reservations} />

            <div className="admin-dashboard-grid">
              <section className="panel admin-content-card admin-room-card">
                <div className="admin-card-heading">
                  <div><span className="admin-card-kicker">VOTRE ÉTABLISSEMENT</span><h2>Espaces & disponibilités</h2></div>
                  <button type="button" className="admin-link-button" onClick={() => setActive('espaces')}>Voir tout <span aria-hidden="true">→</span></button>
                </div>
                {data.espaces.length ? (
                  <div className="admin-room-list">
                    {data.espaces.slice(0, 4).map((space) => (
                      <article className="admin-room-row" key={space.id}>
                        <span className="admin-room-icon" aria-hidden="true">⌂</span>
                        <span className="admin-room-info"><strong>{space.nom}</strong><small>{space.capacite} personnes · {space.adresse}</small></span>
                        <span className={`admin-status ${space.disponible ? 'is-available' : 'is-unavailable'}`}><i />{space.disponible ? 'Disponible' : 'Indisponible'}</span>
                        <button type="button" className={`icon-action ${space.disponible ? 'danger-action' : 'edit-action'}`} aria-label={space.disponible ? 'Désactiver' : 'Réactiver'} title={space.disponible ? 'Désactiver' : 'Réactiver'} onClick={() => toggleSpaceAvailability(space)} disabled={busy}><ActionIcon name="availability" /></button>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="admin-empty-state"><span className="admin-empty-icon" aria-hidden="true">⌂</span><strong>Votre première salle vous attend</strong><p>Ajoutez un espace pour commencer à recevoir des réservations.</p><button className="admin-link-button" type="button" onClick={() => { setActive('espaces'); setForm({ id: null, values: { ...definitions.espaces.initial } }) }}>Créer un espace <span aria-hidden="true">→</span></button></div>
                )}
              </section>

              <section className="panel admin-content-card admin-activity-card">
                <div className="admin-card-heading">
                  <div><span className="admin-card-kicker">SUIVI</span><h2>Réservations récentes</h2></div>
                  <button type="button" className="admin-link-button" onClick={() => setActive('reservations')}>Tout voir <span aria-hidden="true">→</span></button>
                </div>
                {data.reservations.length ? (
                  <div className="admin-reservation-list">
                    {data.reservations.slice(0, 4).map((reservation) => (
                      <article className="admin-reservation-row" key={reservation.id}>
                        <span className="admin-reservation-date">{new Date(reservation.date_debut).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })}</span>
                        <span className="admin-reservation-info"><strong>{reservation.type_evenement_nom}</strong><small>{reservation.client_nom} · {reservation.espace_nom}</small></span>
                        <span className={`admin-status-pill status-${reservation.statut}`}>{reservation.statut_display}</span>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="admin-activity-empty"><span aria-hidden="true">▣</span><p>Aucune réservation pour le moment.</p></div>
                )}
              </section>
            </div>
          </section>
        )}

        {active === 'dashboard' && !staff && (
          <section className="dashboard">
            <div className="stats-grid">
              {(staff ? [
                ['Clients', dashboard.total_clients, 'stat-tone-blue'],
                ['Espaces', dashboard.total_espaces, 'stat-tone-violet'],
                ['Types d’événements', dashboard.total_types_evenements, 'stat-tone-cyan'],
                ['Réservations', dashboard.total_reservations, 'stat-tone-indigo'],
                ['En attente', dashboard.reservations_en_attente, 'stat-tone-amber'],
                ['Confirmées', dashboard.reservations_confirmees, 'stat-tone-green'],
                ['Paiements reçus', dashboard.paiements_recus, 'stat-tone-rose'],
              ] : [
                ['Mes réservations', dashboard.total_reservations, 'stat-tone-violet'],
                ['En attente', dashboard.reservations_en_attente, 'stat-tone-amber'],
                ['Confirmées', dashboard.reservations_confirmees, 'stat-tone-green'],
                ['Paiements reçus', dashboard.paiements_recus, 'stat-tone-blue'],
              ]).map(([label, number, tone]) => <article className={`stat-card ${tone}`} key={label}><span>{label}</span><strong>{number ?? 0}</strong></article>)}
            </div>
            <DashboardChart reservations={data.reservations} />
            <section className="panel"><div className="panel-heading"><div><p className="eyebrow">VOS ÉVÉNEMENTS</p><h2>Types proposés</h2></div><button className="text-action" type="button" onClick={() => setActive('types')}>Voir les types</button></div><div className="type-grid">{data.types.map((item) => <article className="type-card" key={item.id}><span className="type-icon">✦</span><h3>{item.nom}</h3><p>{item.description || 'Un espace adapté à votre événement.'}</p></article>)}</div></section>
          </section>
        )}

                {active === 'apropos' && <About />}

        {active !== 'dashboard' && active !== 'apropos' && (
          <section className="panel data-panel">
            <div className="module-header">
              <div><p className="eyebrow">ESPACE ÉVÉNEMENTIEL</p><h2>{heading}</h2></div>
              <form className="search-form" onSubmit={searchRecords}>
                <input className="search-input" type="search" placeholder="Nom, date, statut…" aria-label="Rechercher dans la liste" value={searchDraft} onChange={(event) => setSearchDraft(event.target.value)} />
                <button type="submit" className="icon-action search-action" aria-label="Rechercher" title="Rechercher" disabled={busy}><ActionIcon name="search" /></button>
                {query && <button type="button" className="icon-action search-action" aria-label="Effacer la recherche" title="Effacer la recherche" onClick={clearSearch} disabled={busy}><ActionIcon name="cancel" /></button>}
              </form>
            </div>
            {form && config && (
              <form className="crud-form" onSubmit={saveRecord}>
                <div className="form-title"><h3>{form.id ? 'Modifier' : 'Nouvelle'} entrée</h3><button type="button" className="close-button" onClick={() => setForm(null)} aria-label="Fermer">×</button></div>
                {active === 'espaces' && <p className="form-help">Tarif minimum : 100 000 Ar par heure. La capacité minimale est de 80 personnes.</p>}
                {active === 'utilisateurs' && !form.id && <p className="form-help">Créez un compte avec nom d’utilisateur, e-mail, mot de passe et rôle. Les clients créent leur compte eux-mêmes avant de réserver un espace. Seul un superutilisateur peut créer un compte Administrateur.</p>}
                {config.fields.filter((field) => {
                  if (active === 'paiements' && form.id) return staff && ['reference', 'statut'].includes(field.name)
                  return (!field.staffOnly || staff) && (!field.createOnly || !form.id)
                }).map((field) => (
                  <label className={field.type === 'textarea' ? 'wide-field' : ''} key={field.name}>
                    {field.label}{fieldValue(
                      field,
                      form.values[field.name],
                      active === 'reservations'
                        && staff
                        && Boolean(form.id)
                        && ['date_debut', 'date_fin', 'espace', 'nombre_invites'].includes(field.name),
                    )}
                  </label>
                ))}
                {active === 'paiements' && !form.id && !staff && <p className="form-help">Le montant est calculé automatiquement selon le tarif horaire et la durée. L’administrateur choisira le statut après réception du paiement.</p>}
                {active === 'paiements' && form.id && staff && <p className="form-help">Le montant est calculé automatiquement et ne peut pas être modifié. Vous pouvez mettre à jour le statut et la référence.</p>}
                {active === 'reservations' && <p className="form-help">{staff && form.id ? 'L’espace, les dates, les heures, le nombre d’invités et le type d’événement choisis par le client ne peuvent pas être modifiés.' : 'Le montant estimé est calculé automatiquement selon la durée et le tarif horaire de l’espace. La réservation sera envoyée à l’équipe pour confirmation.'}</p>}
                <div className="form-actions"><button type="button" className="secondary-button" onClick={() => setForm(null)}>Annuler</button><button className="primary-button" disabled={busy}>{busy ? 'Validation…' : active === 'paiements' && !staff && !form.id ? 'Valider' : 'Enregistrer'}</button></div>
              </form>
            )}
            <div className={`table-wrapper${active === 'reservations' && !staff ? ' client-reservations-table' : ''}`}><table className="data-table"><thead><tr>{config.columns.map(([, label]) => <th key={label}>{label}</th>)}{(staff || active === 'reservations' || active === 'clients' || active === 'paiements') && <th>Actions</th>}</tr></thead><tbody>
              {filtered.map((record) => {
                const clientProfile = active === 'clients' && !staff && record.user === user.id
                const ownPendingReservation = active === 'reservations' && !staff && record.statut === 'pending'
                const ownCancellableReservation = active === 'reservations' && !staff && ['pending', 'confirmed'].includes(record.statut)
                const showActions = staff || clientProfile || ownPendingReservation || ownCancellableReservation || active === 'paiements'
                return (
                  <tr key={record.id}>
                    {config.columns.map(([key, label]) => <td key={key} data-label={label}>{renderCell(record, key)}</td>)}
                    {(staff || active === 'reservations' || active === 'clients' || active === 'paiements') && <td className="row-actions" data-label="Actions">
                      {staff && active !== 'clients' && !(active === 'utilisateurs' && record.role === 'participant') && <button type="button" className="icon-action edit-action" aria-label={active === 'paiements' ? 'Ajouter ou modifier la référence' : 'Modifier'} title={active === 'paiements' ? 'Ajouter ou modifier la référence' : 'Modifier'} onClick={() => startEdit(record)}><ActionIcon name="edit" /></button>}
                      {staff && active === 'espaces' && <button type="button" className={`icon-action ${record.disponible ? 'danger-action' : 'edit-action'}`} aria-label={record.disponible ? 'Désactiver' : 'Réactiver'} title={record.disponible ? 'Désactiver' : 'Réactiver'} onClick={() => toggleSpaceAvailability(record)} disabled={busy}><ActionIcon name="availability" /></button>}
                      {clientProfile && <button type="button" className="icon-action edit-action" aria-label="Modifier mon profil" title="Modifier mon profil" onClick={() => startEdit(record)}><ActionIcon name="edit" /></button>}
                      {ownPendingReservation && <button type="button" className="icon-action edit-action" aria-label="Modifier" title="Modifier" onClick={() => startEdit(record)}><ActionIcon name="edit" /></button>}
                      {ownPendingReservation && <button type="button" className="icon-action danger-action" aria-label="Supprimer" title="Supprimer" onClick={() => deleteRecord(record)}><ActionIcon name="delete" /></button>}
                      {ownCancellableReservation && <button type="button" className="icon-action danger-action" aria-label="Annuler" title="Annuler" onClick={() => cancelReservation(record)}><ActionIcon name="cancel" /></button>}
                      {staff && <button type="button" className="icon-action danger-action" aria-label="Supprimer" title="Supprimer" onClick={() => deleteRecord(record)}><ActionIcon name="delete" /></button>}
                      {active === 'clients' && staff && <button type="button" className="icon-action print-action" aria-label="Imprimer la fiche client" title="Imprimer la fiche client" onClick={() => printClient(record)}><ActionIcon name="print" /></button>}
                      {active === 'paiements' && !staff && !record.envoye_admin && record.statut !== 'cancelled' && <button type="button" className="icon-action edit-action" aria-label="Envoyer le paiement à l’administrateur" title="Envoyer à l’administrateur" onClick={() => sendPayment(record)} disabled={busy}><ActionIcon name="send" /></button>}
                      {active === 'paiements' && !staff && record.reservation_statut === 'pending' && record.statut !== 'cancelled' && <button type="button" className="icon-action danger-action" aria-label="Annuler le paiement" title="Annuler le paiement" onClick={() => cancelPayment(record)} disabled={busy}><ActionIcon name="cancel" /></button>}
                      {active === 'paiements' && staff && <button type="button" className="icon-action print-action" aria-label="Imprimer ou enregistrer le reçu en PDF" title="Imprimer / PDF" onClick={() => printPayment(record)}><ActionIcon name="print" /></button>}
                      {!showActions && '—'}
                    </td>}
                  </tr>
                )
              })}
              {!filtered.length && <tr className="empty-row"><td colSpan={config.columns.length + ((staff || active === 'reservations' || active === 'clients' || active === 'paiements') ? 1 : 0)} className="empty-state">{query ? 'Aucun résultat pour cette recherche.' : 'Aucune donnée pour le moment.'}</td></tr>}
            </tbody></table></div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
