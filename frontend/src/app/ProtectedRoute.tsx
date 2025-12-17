import { Center, Loader } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { api } from '../lib/api'
import { clearTokens, getAccessToken } from '../lib/auth'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [ok, setOk] = useState<boolean | null>(null)
  const loc = useLocation()

  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setOk(false)
      return
    }

    api
      .get('/auth/me')
      .then(() => setOk(true))
      .catch(() => {
        clearTokens()
        notifications.show({ color: 'red', message: 'Sessione scaduta. Effettua di nuovo il login.' })
        setOk(false)
      })
  }, [])

  if (ok === null) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    )
  }

  if (!ok) {
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  }

  return <>{children}</>
}
