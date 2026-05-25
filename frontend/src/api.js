/** HTTP-клиент к FastAPI с заголовком initData Telegram. */

const API_BASE = import.meta.env.VITE_API_URL || ''

function headers() {
  const initData = window.Telegram?.WebApp?.initData || ''
  return {
    'Content-Type': 'application/json',
    'X-Telegram-Init-Data': initData,
  }
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers(), ...options.headers },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Ошибка запроса')
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  getMe: () => request('/api/users/me'),
  getPalette: () => request('/api/users/palette'),
  setColor: (color) => request('/api/users/me/color', { method: 'PATCH', body: JSON.stringify({ color }) }),

  listGroups: () => request('/api/groups'),
  createGroup: (data) => request('/api/groups', { method: 'POST', body: JSON.stringify(data) }),
  joinGroup: (code) => request(`/api/groups/join/${code}`, { method: 'POST' }),
  getMembers: (groupId) => request(`/api/groups/${groupId}/members`),
  getInvite: (groupId) => request(`/api/groups/${groupId}/invite`),
  updateGroup: (groupId, data) =>
    request(`/api/groups/${groupId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  removeMember: (groupId, memberId) =>
    request(`/api/groups/${groupId}/members/${memberId}`, { method: 'DELETE' }),

  getCalendar: (groupId, year, month, onlyMe = false) =>
    request(`/api/groups/${groupId}/calendar?year=${year}&month=${month}&only_me=${onlyMe}`),
  getDay: (groupId, day) => request(`/api/groups/${groupId}/days/${day}`),
  setAvailability: (groupId, days, status) =>
    request(`/api/groups/${groupId}/availability`, {
      method: 'PUT',
      body: JSON.stringify({ days, status }),
    }),

  listProposals: (groupId) => request(`/api/groups/${groupId}/proposals`),
  createProposal: (groupId, data) =>
    request(`/api/groups/${groupId}/proposals`, { method: 'POST', body: JSON.stringify(data) }),
  voteProposal: (proposalId, status) =>
    request(`/api/proposals/${proposalId}/vote`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
}
