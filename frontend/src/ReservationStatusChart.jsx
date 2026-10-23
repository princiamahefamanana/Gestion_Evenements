import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import './App.css'

const reservationStatuses = [
  { status: 'pending', label: 'En attente', color: '#d99016' },
  { status: 'confirmed', label: 'Confirmées', color: '#15966a' },
  { status: 'cancelled', label: 'Annulées', color: '#d94f65' },
  { status: 'completed', label: 'Terminées', color: '#477bd1' },
]

export default function ReservationStatusChart({ reservations }) {
  const chartData = reservationStatuses.map(({ status, label, color }) => ({
    status,
    label,
    color,
    total: reservations.filter((reservation) => reservation.statut === status).length,
  }))

  return (
    <section className="panel reservation-chart-card" aria-label="Graphique des réservations par statut">
      <div className="panel-heading">
        <div><p className="eyebrow">SUIVI DES RÉSERVATIONS</p><h2>État des réservations</h2></div>
      </div>
      <div className="reservation-chart">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 12, left: -20, bottom: 4 }}>
            <CartesianGrid stroke="#e8edf1" vertical={false} />
            <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
            <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
            <Tooltip cursor={{ fill: '#f4f8f8' }} formatter={(value) => [value, 'Réservations']} />
            <Bar dataKey="total" name="Réservations" radius={[6, 6, 0, 0]} maxBarSize={64}>
              {chartData.map((entry) => (
                <Cell key={entry.status} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="reservation-chart-legend" aria-label="Légende du graphique">
        {chartData.map((entry) => (
          <li key={entry.status}>
            <span style={{ backgroundColor: entry.color }} aria-hidden="true" />
            {entry.label}
          </li>
        ))}
      </ul>
    </section>
  )
}
