const items = [
  'OpenAI', 'Anthropic', 'Llama', 'Mistral', 'Gemini',
  'LangChain', 'Vercel AI SDK', 'Custom HTTP',
]

export default function TrustBar() {
  return (
    <div className="trust-bar">
      <p className="trust-bar-label">Compatible with leading AI frameworks</p>
      <div className="trust-track">
        {[...items, ...items].map((name, i) => (
          <span key={i} className="trust-item">
            <span className="dot" aria-hidden="true" />
            {name}
          </span>
        ))}
      </div>
    </div>
  )
}
