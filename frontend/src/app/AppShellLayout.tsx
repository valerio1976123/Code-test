import { AppShell, Burger, Group, NavLink, ScrollArea, Text } from '@mantine/core'
import { IconDeviceFloppy, IconHistory, IconLayoutDashboard, IconLogout, IconRouter } from '@tabler/icons-react'
import { useState } from 'react'
import { NavLink as RRNavLink, Outlet, useNavigate } from 'react-router-dom'
import { clearTokens } from '../lib/auth'

export default function AppShellLayout() {
  const [opened, setOpened] = useState(false)
  const nav = useNavigate()

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 260, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={() => setOpened((o) => !o)} hiddenFrom="sm" size="sm" />
            <Text fw={700}>Crazynet Device Backup</Text>
          </Group>
          <NavLink
            label="Logout"
            leftSection={<IconLogout size={16} />}
            onClick={() => {
              clearTokens()
              nav('/login')
            }}
          />
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="xs">
        <ScrollArea>
          <NavLink
            component={RRNavLink}
            to="/dashboard"
            label="Dashboard"
            leftSection={<IconLayoutDashboard size={16} />}
            onClick={() => setOpened(false)}
          />
          <NavLink
            component={RRNavLink}
            to="/devices"
            label="Devices"
            leftSection={<IconRouter size={16} />}
            onClick={() => setOpened(false)}
          />
          <NavLink
            component={RRNavLink}
            to="/schedules"
            label="Schedules"
            leftSection={<IconDeviceFloppy size={16} />}
            onClick={() => setOpened(false)}
          />
          <NavLink
            component={RRNavLink}
            to="/history"
            label="History"
            leftSection={<IconHistory size={16} />}
            onClick={() => setOpened(false)}
          />
        </ScrollArea>
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  )
}
