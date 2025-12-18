import { useEffect, useState } from 'react'
import { marketApi } from '../api/client'
import type { Alert } from '../api/types'

export function AlertsPage() {
  const [items, setItems] = useState<Alert[]>([])
  const [err, setErr] = useState<string | null>(null)

  async function load() {
    setErr(null)
    setItems(await marketApi.alerts())
  }

  useEffect(() => {
    load().catch((e) => setErr(String(e)))
  }, [])

  async function toggleRead(a: Alert) {
    try {
      const updated = await marketApi.markAlertRead(a.id, !a.is_read)
      setItems((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))
    } catch (e) {
      setErr(String(e))
    }
  }

  return (
    <div>
      <div className="row">
        <div>
          <div style={{ fontSize: 20, fontWeight: 800 }}>Alerts</div>
          <div className="muted">Triggered rules show up here.</div>
        </div>
        <button className="btn secondary" onClick={() => load().catch((e) => setErr(String(e)))}>
          Reload
        </button>
      </div>

      {err ? <div className="error">{err}</div> : null}

      <table className="table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Target</th>
            <th>Severity</th>
            <th>Message</th>
            <th>Read</th>
          </tr>
        </thead>
        <tbody>
          {items.map((a) => (
            <tr key={a.id} style={{ opacity: a.is_read ? 0.65 : 1 }}>
              <td className="muted">{new Date(a.triggered_at).toLocaleString()}</td>
              <td>
                <span className="muted">{a.target_type}</span> {a.target_identifier}
              </td>
              <td className="muted">{a.severity}</td>
              <td>{a.message}</td>
              <td>
                <button className="btn secondary" onClick={() => void toggleRead(a)}>
                  {a.is_read ? 'Mark unread' : 'Mark read'}
                </button>
              </td>
            </tr>
          ))}
          {items.length === 0 ? (
            <tr>
              <td colSpan={5} className="muted">
                No alerts yet. (You can add rules via API, or wait for the scheduler to evaluate.)
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  )
}

