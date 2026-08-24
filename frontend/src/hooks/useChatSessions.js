import { useEffect, useState } from 'react'

const STORAGE_KEY = 'aima-chat-sessions'
const TITLE_MAX = 40

function createSession() {
  return { id: crypto.randomUUID(), title: 'New chat', messages: [] }
}

function freshState() {
  const session = createSession()
  return { sessions: [session], activeId: session.id, collapsed: false }
}

// A stored blob is only trusted if it has the exact shape we wrote. Anything else
// (older format, hand-edited, truncated) is discarded in favour of a fresh state.
function isValidState(value) {
  if (!value || typeof value !== 'object') return false
  if (!Array.isArray(value.sessions) || value.sessions.length === 0) return false
  const sessionsAreValid = value.sessions.every(
    (session) =>
      session &&
      typeof session.id === 'string' &&
      typeof session.title === 'string' &&
      Array.isArray(session.messages),
  )
  if (!sessionsAreValid) return false
  return value.sessions.some((session) => session.id === value.activeId)
}

function loadState() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return freshState()
    const parsed = JSON.parse(raw)
    if (!isValidState(parsed)) return freshState()
    return { ...parsed, collapsed: Boolean(parsed.collapsed) }
  } catch {
    // Unreadable or unparseable storage is not fatal; start clean.
    return freshState()
  }
}

function titleFrom(text) {
  const trimmed = text.trim()
  if (trimmed.length <= TITLE_MAX) return trimmed
  return trimmed.slice(0, TITLE_MAX) + '…'
}

export default function useChatSessions() {
  const [state, setState] = useState(loadState)

  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch {
      // Quota exceeded or storage disabled: keep working without persistence.
    }
  }, [state])

  const activeSession =
    state.sessions.find((session) => session.id === state.activeId) ?? state.sessions[0]

  function setActiveMessages(updater) {
    setState((prev) => ({
      ...prev,
      sessions: prev.sessions.map((session) => {
        if (session.id !== prev.activeId) return session
        const messages =
          typeof updater === 'function' ? updater(session.messages) : updater
        const firstUser = messages.find((message) => message.role === 'user')
        const title =
          session.title === 'New chat' && firstUser
            ? titleFrom(firstUser.content)
            : session.title
        return { ...session, messages, title }
      }),
    }))
  }

  function newChat() {
    setState((prev) => {
      const current = prev.sessions.find((session) => session.id === prev.activeId)
      // Starting a new chat from an already-empty one would stack blank sessions.
      if (current && current.messages.length === 0) return prev
      const session = createSession()
      return { ...prev, sessions: [session, ...prev.sessions], activeId: session.id }
    })
  }

  function selectChat(id) {
    setState((prev) =>
      prev.sessions.some((session) => session.id === id) ? { ...prev, activeId: id } : prev,
    )
  }

  function toggleCollapsed() {
    setState((prev) => ({ ...prev, collapsed: !prev.collapsed }))
  }

  return {
    sessions: state.sessions,
    activeId: activeSession.id,
    activeMessages: activeSession.messages,
    setActiveMessages,
    newChat,
    selectChat,
    collapsed: state.collapsed,
    toggleCollapsed,
  }
}
