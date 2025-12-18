import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { marketApi } from '../api/client'
import type { WatchlistItemSummary } from '../api/types'

function predPill(direction?: string) {
  if (!direction) return <span className="pill flat">—</span>
  if (direction === 'UP') return <span className="pill up">UP</span>
  if (direction === 'DOWN') return <span className="pill down">DOWN</span>
  return <span className="pill flat">FLAT</span>
}

export function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItemSummary[]>([])
  const [err, setErr] = useState<string | null>(null)

  async function load() {
    setErr(null)
    setItems(await marketApi.watchlistSummary())
  }

  useEffect(() => {
    load().catch((e) => setErr(String(e)))
  }, [])

  return (
    <div>
      <div className="row">
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>Watchlist</div>
          <div className="muted">Click a row for details.</div>
        </div>
        <button className="btn secondary" onClick={() => load().catch((e) => setErr(String(e)))}>
          Reload
        </button>
      </div>

      {err ? <div className="error">{err}</div> : null}

      <table className="table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Symbol</th>
            <th>Name</th>
            <th>Country</th>
            <th>Last</th>
            <th>Daily %</th>
            <th>Prediction</th>
            <th>Conf.</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={`${it.target_type}:${it.symbol}`}>
              <td className="muted">{it.target_type}</td>
              <td>
                <Link to={`/instrument/${it.target_type}/${encodeURIComponent(it.symbol)}`}>{it.symbol}</Link>
              </td>
              <td>{it.name}</td>
              <td className="muted">{it.country}</td>
              <td>{typeof it.last_price === 'number' ? it.last_price.toFixed(2) : '—'}</td>
              <td className="muted">
                {typeof it.daily_change_pct === 'number' ? `${it.daily_change_pct.toFixed(2)}%` : '—'}
              </td>
              <td>{predPill(it.latest_prediction?.predicted_direction)}</td>
              <td className="muted">
                {typeof it.latest_prediction?.confidence_score === 'number'
                  ? it.latest_prediction.confidence_score.toFixed(2)
                  : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

