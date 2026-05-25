const items = ['offline by default', 'real execution engine', 'HTTP + stdio agents', 'MIT licensed']

export default function TrustBar() {
  return (
    <section className="trust-strip" aria-label="Ozark principles">
      <div className="container trust-items">
        {items.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </section>
  )
}
