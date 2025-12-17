import { Navigate, Route, Routes } from 'react-router-dom'
import AppShellLayout from './app/AppShellLayout'
import ProtectedRoute from './app/ProtectedRoute'
import DashboardPage from './pages/DashboardPage'
import DevicesPage from './pages/DevicesPage'
import HistoryPage from './pages/HistoryPage'
import LoginPage from './pages/LoginPage'
import SchedulesPage from './pages/SchedulesPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShellLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="devices" element={<DevicesPage />} />
        <Route path="schedules" element={<SchedulesPage />} />
        <Route path="history" element={<HistoryPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
