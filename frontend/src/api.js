async function request(path, options) {
  const response = await fetch(path, options)

  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (body.detail) detail = body.detail
    } catch {
      // response body was not JSON; keep the generic message
    }
    throw new Error(detail)
  }

  return response.json()
}

export function sendChat(message, history) {
  return request('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })
}

export function fetchConfig() {
  return request('/config')
}
