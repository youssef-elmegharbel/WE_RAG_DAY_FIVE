import { useEffect, useRef, useState } from 'react'
import ChatInput from './components/ChatInput'
import ChatMessage from './components/ChatMessage'
import { fetchConfig, sendChat } from './api'
import 'katex/dist/katex.min.css'
import './styles.css'

export default function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    fetchConfig().then(setConfig).catch(() => setConfig(null))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(text) {
    const history = messages
      .filter((m) => !m.error)
      .map(({ role, content }) => ({ role, content }))

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const result = await sendChat(text, history)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.answer,
          citations: result.citations,
        },
      ])
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: error.message, error: true },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>AIMA Textbook Assistant</h1>
        {config && (
          <span className="badge">
            {config.provider} · {config.model}
          </span>
        )}
      </header>

      <main className="messages">
        {messages.length === 0 && (
          <div className="empty">
            <p>Ask a question about <em>Artificial Intelligence: A Modern Approach</em>.</p>
            <p className="hint">Try: “What is the difference between BFS and DFS?”</p>
          </div>
        )}
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        {loading && <div className="message message-assistant">Searching the textbook…</div>}
        <div ref={bottomRef} />
      </main>

      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  )
}
