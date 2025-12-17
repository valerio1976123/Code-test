import { Button, Center, Paper, PasswordInput, Stack, Text, TextInput } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../lib/api'

export default function LoginPage() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin')
  const [loading, setLoading] = useState(false)
  const nav = useNavigate()

  return (
    <Center h="100vh" p="md">
      <Paper withBorder p="lg" w={380} radius="md">
        <Stack>
          <Text fw={700} size="lg">
            Login
          </Text>
          <TextInput label="Username" value={username} onChange={(e) => setUsername(e.currentTarget.value)} />
          <PasswordInput label="Password" value={password} onChange={(e) => setPassword(e.currentTarget.value)} />
          <Button
            loading={loading}
            onClick={async () => {
              setLoading(true)
              try {
                await login(username, password)
                nav('/dashboard')
              } catch (e: any) {
                notifications.show({ color: 'red', message: e?.response?.data?.detail || 'Login failed' })
              } finally {
                setLoading(false)
              }
            }}
          >
            Entra
          </Button>
          <Text size="xs" c="dimmed">
            Default seed: admin/admin
          </Text>
        </Stack>
      </Paper>
    </Center>
  )
}
