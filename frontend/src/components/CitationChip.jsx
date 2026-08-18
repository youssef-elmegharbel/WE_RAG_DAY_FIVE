import { useState } from 'react'

export default function CitationChip({ citation }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="citation">
      <button
        className="citation-chip"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        {citation.label}
      </button>
      {open && (
        <div className="citation-snippet">
          <div className="citation-title">
            {citation.section} {citation.section_title}
          </div>
          <p>{citation.snippet}{citation.snippet.length >= 400 ? '…' : ''}</p>
        </div>
      )}
    </div>
  )
}
