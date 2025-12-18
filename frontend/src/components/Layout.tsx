import { NavLink, Outlet } from 'react-router-dom'
import './layout.css'

export function Layout() {
  return (
    <div className="appShell">
      <header className="topBar">
        <div className="brand">AI Market Monitor</div>
        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'navLink active' : 'navLink')}>
            Overview
          </NavLink>
          <NavLink to="/watchlist" className={({ isActive }) => (isActive ? 'navLink active' : 'navLink')}>
            Watchlist
          </NavLink>
          <NavLink to="/alerts" className={({ isActive }) => (isActive ? 'navLink active' : 'navLink')}>
            Alerts
          </NavLink>
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}

