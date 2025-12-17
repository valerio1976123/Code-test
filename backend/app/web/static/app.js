(() => {
  const ACCESS_KEY = 'crazynet_access_token'
  const REFRESH_KEY = 'crazynet_refresh_token'

  function getAccess() {
    return localStorage.getItem(ACCESS_KEY)
  }
  function getRefresh() {
    return localStorage.getItem(REFRESH_KEY)
  }
  function setTokens(tokens) {
    localStorage.setItem(ACCESS_KEY, tokens.access_token)
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
  }
  function clearTokens() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  }

  async function apiFetch(path, options = {}) {
    const headers = new Headers(options.headers || {})
    const token = getAccess()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }

    const res = await fetch(`/api${path}`, { ...options, headers })
    if (res.status !== 401) return res

    // try refresh
    const refresh = getRefresh()
    if (!refresh) return res

    const rr = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (!rr.ok) {
      clearTokens()
      return res
    }
    const tokens = await rr.json()
    setTokens(tokens)

    const headers2 = new Headers(options.headers || {})
    headers2.set('Authorization', `Bearer ${tokens.access_token}`)
    if (!headers2.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
      headers2.set('Content-Type', 'application/json')
    }
    return fetch(`/api${path}`, { ...options, headers: headers2 })
  }

  function requireAuthOrRedirect() {
    const page = window.CRAZYNET_PAGE
    if (page === 'login') return
    if (!getAccess()) {
      window.location.href = '/login'
    }
  }

  function wireLogout() {
    const btn = document.getElementById('logoutBtn')
    if (!btn) return
    btn.addEventListener('click', () => {
      clearTokens()
      window.location.href = '/login'
    })
  }

  async function initLogin() {
    const form = document.getElementById('loginForm')
    if (!form) return
    const err = document.getElementById('loginError')

    form.addEventListener('submit', async (e) => {
      e.preventDefault()
      err.textContent = ''
      const username = document.getElementById('username').value
      const password = document.getElementById('password').value

      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        err.textContent = data.detail || 'Login failed'
        return
      }
      const tokens = await res.json()
      setTokens(tokens)
      window.location.href = '/dashboard'
    })
  }

  async function initDashboard() {
    const refresh = document.getElementById('refreshDashboard')
    async function load() {
      const res = await apiFetch('/dashboard/summary')
      if (!res.ok) return
      const d = await res.json()
      document.getElementById('devicesTotal').textContent = d.devices.total
      document.getElementById('devicesEnabled').textContent = d.devices.enabled
      document.getElementById('devicesDisabled').textContent = d.devices.disabled
      document.getElementById('execTotal').textContent = d.executions_last_24h.total
      document.getElementById('execSuccess').textContent = d.executions_last_24h.success
      document.getElementById('execFailed').textContent = d.executions_last_24h.failed

      const body = document.getElementById('recentBody')
      body.innerHTML = ''
      for (const e of d.recent_executions) {
        const tr = document.createElement('tr')
        tr.innerHTML = `
          <td class="py-2 pr-4">${e.id}</td>
          <td class="py-2 pr-4">${e.device_id}</td>
          <td class="py-2 pr-4">${e.status}</td>
          <td class="py-2 pr-4">${new Date(e.created_at).toLocaleString()}</td>
        `
        body.appendChild(tr)
      }
    }
    refresh?.addEventListener('click', load)
    await load()
  }

  async function initDevices() {
    const body = document.getElementById('devicesBody')
    const refresh = document.getElementById('refreshDevices')
    const form = document.getElementById('createDeviceForm')
    const msg = document.getElementById('createDeviceMsg')

    async function load() {
      const res = await apiFetch('/devices')
      if (!res.ok) return
      const items = await res.json()
      body.innerHTML = ''
      for (const d of items) {
        const tr = document.createElement('tr')
        tr.innerHTML = `
          <td class="py-2 pr-4">${d.id}</td>
          <td class="py-2 pr-4">${d.name}</td>
          <td class="py-2 pr-4">${d.host}:${d.port}</td>
          <td class="py-2 pr-4">${d.vendor}</td>
          <td class="py-2 pr-4">${d.is_enabled ? 'Yes' : 'No'}</td>
          <td class="py-2 pr-4">
            <button data-act="run" data-id="${d.id}" class="text-sm underline mr-2">Run now</button>
            <button data-act="edit" data-id="${d.id}" class="text-sm underline mr-2">Edit</button>
            <button data-act="del" data-id="${d.id}" class="text-sm text-red-600 underline">Delete</button>
          </td>
        `
        body.appendChild(tr)
      }
    }

    body.addEventListener('click', async (e) => {
      const t = e.target
      if (!(t instanceof HTMLElement)) return
      const act = t.getAttribute('data-act')
      const id = t.getAttribute('data-id')
      if (!act || !id) return

      if (act === 'run') {
        const res = await apiFetch(`/devices/${id}/run-now`, { method: 'POST' })
        const d = await res.json().catch(() => ({}))
        alert(res.ok ? `Queued execution #${d.execution_id}` : (d.detail || 'Run now failed'))
        return
      }

      if (act === 'del') {
        if (!confirm(`Delete device #${id}?`)) return
        const res = await apiFetch(`/devices/${id}`, { method: 'DELETE' })
        if (!res.ok) alert('Delete failed')
        await load()
        return
      }

      if (act === 'edit') {
        // minimal edit: toggle enabled
        const enabled = prompt('Set enabled? (true/false)', 'true')
        if (enabled == null) return
        const res = await apiFetch(`/devices/${id}`, {
          method: 'PUT',
          body: JSON.stringify({ is_enabled: enabled === 'true' }),
        })
        if (!res.ok) alert('Update failed')
        await load()
      }
    })

    refresh?.addEventListener('click', load)

    form?.addEventListener('submit', async (e) => {
      e.preventDefault()
      msg.textContent = ''
      const fd = new FormData(form)
      const payload = {
        name: fd.get('name'),
        host: fd.get('host'),
        port: Number(fd.get('port') || 22),
        vendor: fd.get('vendor') || 'generic',
        username: fd.get('username') || '',
        password: fd.get('password') || null,
        command_profile_json: fd.get('command_profile_json') || null,
        is_enabled: fd.get('is_enabled') === 'on',
      }
      const res = await apiFetch('/devices', { method: 'POST', body: JSON.stringify(payload) })
      const data = await res.json().catch(() => ({}))
      msg.textContent = res.ok ? 'Created' : (data.detail || 'Create failed')
      msg.className = res.ok ? 'ml-2 text-sm text-green-700' : 'ml-2 text-sm text-red-700'
      if (res.ok) form.reset()
      await load()
    })

    await load()
  }

  async function initSchedules() {
    const schedulesBody = document.getElementById('schedulesBody')
    const deviceSelect = document.getElementById('scheduleDevice')
    const refresh = document.getElementById('refreshSchedules')
    const form = document.getElementById('createScheduleForm')
    const msg = document.getElementById('createScheduleMsg')

    async function loadDevicesIntoSelect() {
      const res = await apiFetch('/devices')
      if (!res.ok) return
      const devices = await res.json()
      deviceSelect.innerHTML = ''
      for (const d of devices) {
        const opt = document.createElement('option')
        opt.value = String(d.id)
        opt.textContent = `${d.name} (${d.host})`
        deviceSelect.appendChild(opt)
      }
    }

    async function loadSchedules() {
      const res = await apiFetch('/schedules')
      if (!res.ok) return
      const items = await res.json()
      schedulesBody.innerHTML = ''
      for (const s of items) {
        const tr = document.createElement('tr')
        tr.innerHTML = `
          <td class="py-2 pr-4">${s.id}</td>
          <td class="py-2 pr-4">${s.name}</td>
          <td class="py-2 pr-4">${s.device_id}</td>
          <td class="py-2 pr-4">${s.schedule_type}</td>
          <td class="py-2 pr-4">${s.is_enabled ? 'Yes' : 'No'}</td>
          <td class="py-2 pr-4">${s.next_run_at ? new Date(s.next_run_at).toLocaleString() : '-'}</td>
          <td class="py-2 pr-4">
            <button data-act="toggle" data-id="${s.id}" class="text-sm underline mr-2">Toggle</button>
            <button data-act="del" data-id="${s.id}" class="text-sm text-red-600 underline">Delete</button>
          </td>
        `
        schedulesBody.appendChild(tr)
      }
    }

    schedulesBody.addEventListener('click', async (e) => {
      const t = e.target
      if (!(t instanceof HTMLElement)) return
      const act = t.getAttribute('data-act')
      const id = t.getAttribute('data-id')
      if (!act || !id) return

      if (act === 'del') {
        if (!confirm(`Delete schedule #${id}?`)) return
        const res = await apiFetch(`/schedules/${id}`, { method: 'DELETE' })
        if (!res.ok) alert('Delete failed')
        await loadSchedules()
      }

      if (act === 'toggle') {
        // naive: fetch current list row by reloading then flip; simplest: prompt
        const enabled = prompt('Set enabled? (true/false)', 'true')
        if (enabled == null) return
        const res = await apiFetch(`/schedules/${id}`, { method: 'PUT', body: JSON.stringify({ is_enabled: enabled === 'true' }) })
        if (!res.ok) alert('Update failed')
        await loadSchedules()
      }
    })

    refresh?.addEventListener('click', async () => {
      await loadDevicesIntoSelect()
      await loadSchedules()
    })

    form?.addEventListener('submit', async (e) => {
      e.preventDefault()
      msg.textContent = ''
      const fd = new FormData(form)
      const payload = {
        name: fd.get('name'),
        device_id: Number(fd.get('device_id') || 0),
        schedule_type: fd.get('schedule_type'),
        run_once_at: (fd.get('run_once_at') || '').toString() || null,
        time_of_day: (fd.get('time_of_day') || '').toString() || null,
        weekdays: (fd.get('weekdays') || '').toString() || null,
        every_n_hours: Number(fd.get('every_n_hours') || 0) || null,
        is_enabled: fd.get('is_enabled') === 'on',
      }
      const res = await apiFetch('/schedules', { method: 'POST', body: JSON.stringify(payload) })
      const data = await res.json().catch(() => ({}))
      msg.textContent = res.ok ? 'Created' : (data.detail || 'Create failed')
      msg.className = res.ok ? 'ml-2 text-sm text-green-700' : 'ml-2 text-sm text-red-700'
      await loadSchedules()
    })

    await loadDevicesIntoSelect()
    await loadSchedules()
  }

  async function initHistory() {
    const body = document.getElementById('historyBody')
    const deviceSelect = document.getElementById('historyDevice')
    const statusSelect = document.getElementById('historyStatus')
    const apply = document.getElementById('applyHistory')
    const refresh = document.getElementById('refreshHistory')

    async function loadDevices() {
      const res = await apiFetch('/devices')
      if (!res.ok) return
      const devices = await res.json()
      deviceSelect.innerHTML = ''
      const opt0 = document.createElement('option')
      opt0.value = ''
      opt0.textContent = '(any)'
      deviceSelect.appendChild(opt0)
      for (const d of devices) {
        const opt = document.createElement('option')
        opt.value = String(d.id)
        opt.textContent = d.name
        deviceSelect.appendChild(opt)
      }
    }

    async function loadExecutions() {
      const params = new URLSearchParams()
      if (deviceSelect.value) params.set('device_id', deviceSelect.value)
      if (statusSelect.value) params.set('status', statusSelect.value)
      params.set('limit', '200')

      const res = await apiFetch(`/executions?${params.toString()}`)
      if (!res.ok) return
      const items = await res.json()
      body.innerHTML = ''
      for (const e of items) {
        const tr = document.createElement('tr')
        tr.innerHTML = `
          <td class="py-2 pr-4">${e.id}</td>
          <td class="py-2 pr-4">${e.device_id}</td>
          <td class="py-2 pr-4">${e.status}</td>
          <td class="py-2 pr-4">${new Date(e.created_at).toLocaleString()}</td>
          <td class="py-2 pr-4">${e.error_message || '-'}</td>
          <td class="py-2 pr-4">
            <button data-act="dl" data-id="${e.id}" class="text-sm underline ${e.output_path ? '' : 'opacity-40 pointer-events-none'}">Download</button>
          </td>
        `
        body.appendChild(tr)
      }
    }

    body.addEventListener('click', async (ev) => {
      const t = ev.target
      if (!(t instanceof HTMLElement)) return
      const act = t.getAttribute('data-act')
      const id = t.getAttribute('data-id')
      if (act !== 'dl' || !id) return

      const res = await apiFetch(`/executions/${id}/download`)
      if (!res.ok) {
        alert('Download failed')
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `execution_${id}.txt`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    })

    apply?.addEventListener('click', loadExecutions)
    refresh?.addEventListener('click', async () => {
      await loadDevices()
      await loadExecutions()
    })

    await loadDevices()
    await loadExecutions()
  }

  async function bootstrap() {
    requireAuthOrRedirect()
    wireLogout()

    const page = window.CRAZYNET_PAGE
    if (page === 'login') return initLogin()
    if (page === 'dashboard') return initDashboard()
    if (page === 'devices') return initDevices()
    if (page === 'schedules') return initSchedules()
    if (page === 'history') return initHistory()
  }

  bootstrap()
})()
