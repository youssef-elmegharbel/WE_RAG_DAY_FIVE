import { useEffect, useRef, useState } from 'react'
import ChatInput from './components/ChatInput'
import ChatMessage from './components/ChatMessage'
import Sidebar from './components/Sidebar'
import useChatSessions from './hooks/useChatSessions'
import { fetchConfig, sendChat } from './api'
import 'katex/dist/katex.min.css'
import './styles.css'

export default function App() {
  const {
    sessions,
    activeId,
    activeMessages,
    setActiveMessages,
    newChat,
    selectChat,
    collapsed,
    toggleCollapsed,
  } = useChatSessions()
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    fetchConfig().then(setConfig).catch(() => setConfig(null))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeMessages, activeId])

  async function handleSend(text) {
    const history = activeMessages
      .filter((m) => !m.error)
      .map(({ role, content }) => ({ role, content }))

    setActiveMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const result = await sendChat(text, history)
      setActiveMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.answer,
          citations: result.citations,
        },
      ])
    } catch (error) {
      setActiveMessages((prev) => [
        ...prev,
        { role: 'assistant', content: error.message, error: true },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={selectChat}
        onNewChat={newChat}
        collapsed={collapsed}
        disabled={loading}
      />

      <div className="app">
        <header className="header">
          <div className="header-left">
            <button
              className="sidebar-toggle"
              onClick={toggleCollapsed}
              aria-label={collapsed ? 'Show chat history' : 'Hide chat history'}
              aria-expanded={!collapsed}
            >
              ☰
            </button>
            <h1>AIMA Textbook Assistant</h1>
          </div>
          {config && (
            <span className="badge">
              {config.provider} · {config.model}
            </span>
          )}
        </header>

        <main className="messages">
          {activeMessages.length === 0 && (
            <div className="empty">
              <p>Ask a question about <em>Artificial Intelligence: A Modern Approach</em>.</p>
              <p className="hint">Try: “What is the difference between BFS and DFS?”</p>
            </div>
          )}
          {activeMessages.map((message, index) => (
            <ChatMessage key={`${activeId}-${index}`} message={message} />
          ))}
          {loading && <div className="message message-assistant">Searching the textbook…</div>}
          <div ref={bottomRef} />
        </main>

        <ChatInput onSend={handleSend} disabled={loading} />
      </div>
    </div>
  )
}
