import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { marketApi } from '../api/client'
import type { Prediction, PriceBar } from '../api/types'

function fmtDate(s: string) {
  const d = new Date(s)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export function InstrumentPage() {
  const params = useParams()
  const targetType = (params.type as 'stock' | 'index') ?? 'stock'
  const symbol = (params.symbol ?? '').toUpperCase()

  const [prices, setPrices] = useState<PriceBar[]>([])
  const [preds, setPreds] = useState<Prediction[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    setErr(null)
    if (!symbol) return
    Promise.all([marketApi.prices(symbol, targetType, 365), marketApi.predictions(symbol, targetType, 120)])
      .then(([p, pr]) => {
        setPrices(p)
        setPreds(pr)
      })
      .catch((e) => setErr(String(e)))
  }, [symbol, targetType])

  const priceSeries = useMemo(() => {
    return prices.map((b) => ({
      t: fmtDate(b.timestamp),
      close: b.close,
    }))
  }, [prices])

  const predSeries = useMemo(() => {
    const m: Record<string, number> = { UP: 1, FLAT: 0, DOWN: -1 }
    return [...preds]
      .reverse()
      .map((p) => ({
        t: fmtDate(p.timestamp_generated),
        dir: m[p.predicted_direction] ?? 0,
        conf: p.confidence_score,
      }))
  }, [preds])

  return (
    <div>
      <div className="row" style={{ marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>
            {symbol} <span className="muted">({targetType})</span>
          </div>
          <div className="muted">
            <Link to="/watchlist">← Back to watchlist</Link>
          </div>
        </div>
      </div>

      {err ? <div className="error">{err}</div> : null}

      <div className="card" style={{ marginBottom: 12 }}>
        <div className="cardTitle">Price (close)</div>
        <div style={{ height: 240, marginTop: 8 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={priceSeries}>
              <XAxis dataKey="t" hide />
              <YAxis domain={['auto', 'auto']} />
              <Tooltip />
              <Line type="monotone" dataKey="close" stroke="#6c7cff" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <div className="cardTitle">Prediction direction timeline (DOWN=-1, FLAT=0, UP=1)</div>
        <div style={{ height: 220, marginTop: 8 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={predSeries}>
              <XAxis dataKey="t" hide />
              <YAxis domain={[-1, 1]} ticks={[-1, 0, 1]} />
              <Tooltip />
              <Line type="stepAfter" dataKey="dir" stroke="#7df0bf" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="muted" style={{ marginTop: 10 }}>
          Latest: {preds[0] ? `${preds[0].predicted_direction} (${preds[0].confidence_score.toFixed(2)})` : '—'}
        </div>
      </div>
    </div>
  )
}

