import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AlertsPage } from './pages/AlertsPage'
import { InstrumentPage } from './pages/InstrumentPage'
import { OverviewPage } from './pages/OverviewPage'
import { WatchlistPage } from './pages/WatchlistPage'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/watchlist" element={<WatchlistPage />} />
        <Route path="/instrument/:type/:symbol" element={<InstrumentPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
      </Route>
    </Routes>
  )
}

export default App
