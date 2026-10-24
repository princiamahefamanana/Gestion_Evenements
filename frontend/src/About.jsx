import './about.css'

const MPD_SVG = `${import.meta.env.BASE_URL}mpd.svg`
const MPD_PNG = `${import.meta.env.BASE_URL}mpd.png`


const informations = [
  ['Nom', 'Princia'],
  ['Matricule', '3405/24'],
  ['Classe', 'IGFIB'],
]

const PK = 'Clé primaire'
const REQ = 'Obligatoire'

const tables = [
  {
    name: 'utilisateurs',
    description: 'Comptes de connexion de l’application, avec leur rôle (administrateur, organisateur ou participant).',
    fields: [
      ['id', 'BigAutoField', PK],
      ['username', 'varchar(150)', 'Obligatoire, unique'],
      ['password', 'varchar(128)', 'Obligatoire, mot de passe haché'],
      ['last_login', 'datetime', 'Facultatif'],
      ['is_superuser', 'bool', REQ],
      ['first_name', 'varchar(150)', REQ],
      ['last_name', 'varchar(150)', REQ],
      ['email', 'varchar(254)', REQ],
      ['is_staff', 'bool', REQ],
      ['is_active', 'bool', REQ],
      ['date_joined', 'datetime', REQ],
      ['role', 'varchar(20)', 'admin, organizer ou participant'],
      ['phone', 'varchar(30)', '10 chiffres (vide autorisé)'],
    ],
  },
  {
    name: 'clients',
    description: 'Regroupe les clients de l’espace événementiel, avec un compte de connexion facultatif.',
    fields: [
      ['id', 'BigAutoField', PK],
      ['nom', 'varchar(200)', REQ],
      ['email', 'varchar(254)', 'Obligatoire, unique'],
      ['telephone', 'varchar(30)', '10 chiffres (vide autorisé)'],
      ['cree_le', 'datetime', 'Date de création automatique'],
      ['user_id', 'bigint', 'Clé étrangère → utilisateurs.id, unique, facultatif'],
    ],
  },
  {
    name: 'espaces',
    description: 'Salles proposées à la réservation, avec leur capacité, leur tarif et leur disponibilité.',
    fields: [
      ['id', 'BigAutoField', PK],
      ['nom', 'varchar(200)', REQ],
      ['adresse', 'varchar(255)', REQ],
      ['capacite', 'integer', 'Obligatoire, au moins 80'],
      ['tarif_horaire', 'decimal(12,2)', 'Obligatoire, au moins 100 000 Ar'],
      ['description', 'text', 'Vide autorisé'],
      ['disponible', 'bool', 'Ouvert aux nouvelles réservations'],
    ],
  },
  {
    name: 'types_evenements',
    description: 'Catégories d’événements : mariage, anniversaire, conférence…',
    fields: [
      ['id', 'BigAutoField', PK],
      ['nom', 'varchar(100)', 'Obligatoire, unique'],
      ['description', 'text', 'Vide autorisé'],
    ],
  },
  {
    name: 'reservations',
    description: 'Réservation d’un espace par un client pour un type d’événement.',
    fields: [
      ['id', 'BigAutoField', PK],
      ['client_id', 'bigint', 'Clé étrangère → clients.id'],
      ['espace_id', 'bigint', 'Clé étrangère → espaces.id'],
      ['type_evenement_id', 'bigint', 'Clé étrangère → types_evenements.id'],
      ['date_debut', 'datetime', REQ],
      ['date_fin', 'datetime', 'Obligatoire, après date_debut'],
      ['nombre_invites', 'integer', 'Obligatoire, au moins 10'],
      ['statut', 'varchar(20)', 'pending, confirmed, cancelled ou completed'],
      ['montant_total', 'decimal(12,2)', 'Montant estimé'],
      ['cree_le', 'datetime', 'Date de création automatique'],
    ],
  },
  {
    name: 'paiements',
    description: 'Règlements effectués pour une réservation.',
    fields: [
      ['id', 'BigAutoField', PK],
      ['reservation_id', 'bigint', 'Clé étrangère → reservations.id'],
      ['montant', 'decimal(12,2)', 'Obligatoire, supérieur à 0'],
      ['mode_paiement', 'varchar(20)', 'cash, transfer ou card'],
      ['statut', 'varchar(20)', 'pending, paid ou cancelled'],
      ['reference', 'varchar(100)', 'Unique si renseignée'],
      ['envoye_admin', 'bool', 'Transmis à l’administration'],
      ['date_paiement', 'datetime', 'Date de création automatique'],
    ],
  },
]

const iconProps = { 'aria-hidden': true, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' }

function About({ standalone = false, onBack }) {
  const Title = standalone ? 'h1' : 'h2'

  const content = (
    <>
      <p className="eyebrow">ESPACE ÉVÉNEMENTIEL</p>
      <Title>À propos</Title>
      <p className="about-lead">Présentation du projet et étude du schéma de base de données relationnelle (SBDR).</p>

      <section className="about-block">
        <h3 className="about-heading">
          <svg {...iconProps}><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" /></svg>
          Informations
        </h3>
        <dl className="about-info">
          {informations.map(([label, value]) => (
            <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
          ))}
        </dl>
      </section>

      <section className="about-block">
        <h3 className="about-heading">
          <svg {...iconProps}><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M9 4v16" /></svg>
          Modèle physique de données (MPD)
        </h3>
        <div className="about-actions">
          <a className="about-button" href={MPD_SVG} target="_blank" rel="noreferrer">Ouvrir en grand</a>
          <a className="about-button secondary" href={MPD_PNG} download="mpd-espace-evenementiel.png">Télécharger (PNG)</a>
        </div>
        <div className="about-mpd-scroll" tabIndex={0} aria-label="Schéma MPD, défilement horizontal possible">
          <img
            src={MPD_SVG}
            alt="Modèle physique de données : tables utilisateurs, clients, espaces, types_evenements, reservations et paiements avec leurs clés et leurs relations."
            loading="lazy"
          />
        </div>
      </section>

      <section className="about-block">
        <h3 className="about-heading">
          <svg {...iconProps}><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" /></svg>
          Tables
        </h3>
        <div className="about-tables">
          {tables.map((table) => (
            <article className="about-table-card" key={table.name}>
              <header>
                <h4><code>{table.name}</code></h4>
                <p>{table.description}</p>
              </header>
              <div className="about-table-scroll">
                <table>
                  <thead>
                    <tr><th>Champ</th><th>Type</th><th>Contraintes / rôle</th></tr>
                  </thead>
                  <tbody>
                    {table.fields.map(([field, type, role]) => (
                      <tr key={field}>
                        <td><code>{field}</code></td>
                        <td>{type}</td>
                        <td>{role}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  )

  if (!standalone) {
    return <section className="about-panel is-embedded">{content}</section>
  }

  return (
    <main className="about-public">
      <div className="about-public-bar">
        <div className="brand-header">
          <div className="brand-mark">E</div>
          <strong>Espace événementiel</strong>
        </div>
        <button type="button" className="text-action" onClick={onBack}>← Retour à la connexion</button>
      </div>
      <section className="about-panel">{content}</section>
    </main>
  )
}

export default About
