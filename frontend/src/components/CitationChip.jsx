import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'

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
          <button
            className="citation-close"
            onClick={() => setOpen(false)}
            aria-label="Close excerpt"
            title="Close excerpt"
          >
            ×
          </button>
          <div className="citation-title">
            {citation.section} {citation.section_title}
          </div>
          <div className="citation-body">
            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
              {citation.snippet + (citation.snippet.length >= 400 ? '…' : '')}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}
