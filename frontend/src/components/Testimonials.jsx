const testimonials = [
  {
    quote: 'Ozark caught a prompt injection vulnerability in our production agent that we would have never found with manual testing. The G0DM0D3 defense alone was worth the setup.',
    name: 'Alex K.',
    handle: '@alexk_ai',
    large: true,
  },
  {
    quote: 'We were using LangSmith before. Ozark is local-first, zero-config, and the coverage analysis is genuinely useful for our compliance audits.',
    name: 'Sarah M.',
    handle: '@sarahm_eng',
  },
  {
    quote: 'The 8-dimensional scoring gives us a single number to track across deployments. When it drops below 80%, we know something changed.',
    name: 'Jordan T.',
    handle: '@jordan_mlops',
  },
  {
    quote: 'I hooked Ozark into our CI pipeline. Now every PR that touches our agent config gets automatically scored. Regressions get caught before review.',
    name: 'Priya R.',
    handle: '@priya_devtools',
  },
  {
    quote: 'The scenario generation is the killer feature. 50,000 permutations from a single YAML config. We found edge cases we did not even know existed.',
    name: 'Marcus W.',
    handle: '@marcus_sec',
  },
  {
    quote: 'Zero API keys, zero cloud dependencies, zero cost. It is hard to believe this is free. The trace diffing alone would be worth paying for.',
    name: 'Lena D.',
    handle: '@lena_agents',
  },
]

export default function Testimonials() {
  return (
    <section className="testimonials-section section" id="testimonials">
      <div className="container">
        <div className="section-header-center reveal">
          <p className="section-label">From the Community</p>
          <h2 className="section-title">Trusted by agent engineers</h2>
          <p className="section-desc">
            Teams building production agents rely on Ozark for simulation, safety, and confidence.
          </p>
        </div>

        <div className="testimonials-grid stagger reveal">
          {testimonials.map((t, i) => (
            <div key={i} className={`testimonial-card${t.large ? ' large' : ''}`}>
              <p className="testimonial-quote">&ldquo;{t.quote}&rdquo;</p>
              <div className="testimonial-author">
                <div className="testimonial-avatar">{t.name.charAt(0)}</div>
                <div>
                  <div className="testimonial-name">{t.name}</div>
                  <div className="testimonial-handle">{t.handle}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
