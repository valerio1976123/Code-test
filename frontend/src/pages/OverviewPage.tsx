import { useEffect, useState } from 'react'
import { marketApi } from '../api/client'
import type { Overview } from '../api/types'

export function OverviewPage() {
  const [data, setData] = useState<Overview | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    setErr(null)
    const d = await marketApi.overview()
    setData(d)
  }

  useEffect(() => {
    load().catch((e) => setErr(String(e)))
  }, [])

  async function refreshAll() {
    setBusy(true)
    setErr(null)
    try {
      await marketApi.refreshData()
      await marketApi.retrain()
      await load()
    } catch (e) {
      setErr(String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="row" style={{ marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>Overview</div>
          <div className="muted">Mock data + RandomForest predictions (dev mode).</div>
        </div>
        <div className="row">
          <button className="btn secondary" onClick={() => load().catch((e) => setErr(String(e)))} disabled={busy}>
            Reload
          </button>
          <button className="btn" onClick={() => void refreshAll()} disabled={busy}>
            Refresh data + Predict
          </button>
        </div>
      </div>

      {err ? <div className="error">{err}</div> : null}

      <div className="grid">
        <div className="card">
          <div className="cardTitle">Watchlist items</div>
          <div className="cardValue">{data?.watchlist_items ?? '—'}</div>
        </div>
        <div className="card">
          <div className="cardTitle">Bullish predictions</div>
          <div className="cardValue">{data?.bullish_predictions ?? '—'}</div>
        </div>
        <div className="card">
          <div className="cardTitle">Bearish predictions</div>
          <div className="cardValue">{data?.bearish_predictions ?? '—'}</div>
        </div>
        <div className="card">
          <div className="cardTitle">Unread alerts</div>
          <div className="cardValue">{data?.unread_alerts ?? '—'}</div>
        </div>
      </div>
    </div>
  )
}

