export default function Sidebar({
  sessions,
  activeId,
  onSelect,
  onNewChat,
  collapsed,
  disabled,
}) {
  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`} aria-hidden={collapsed}>
      <div className="sidebar-inner">
        <button className="new-chat" onClick={onNewChat} disabled={disabled}>
          + New chat
        </button>
        <nav className="session-list">
          {sessions.map((session) => (
            <button
              key={session.id}
              className={`session-item ${session.id === activeId ? 'session-item-active' : ''}`}
              onClick={() => onSelect(session.id)}
              disabled={disabled}
              title={session.title}
              aria-current={session.id === activeId}
            >
              {session.title}
            </button>
          ))}
        </nav>
      </div>
    </aside>
  )
}
