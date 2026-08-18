import CitationChip from './CitationChip'

export default function ChatMessage({ message }) {
  const { role, content, citations = [], error } = message

  return (
    <div className={`message message-${role} ${error ? 'message-error' : ''}`}>
      <div className="message-body">{content}</div>
      {citations.length > 0 && (
        <div className="citations">
          {citations.map((citation) => (
            <CitationChip key={citation.label} citation={citation} />
          ))}
        </div>
      )}
    </div>
  )
}
