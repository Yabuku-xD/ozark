const rowLabels = [
  'lookup_user', 'fetch_order', 'refund_init', 'ticket_open',
  'ticket_close', 'send_email', 'log_event', 'db_query',
  'db_write', 'webhook_post', 'read_file', 'archive_user',
]

const rowData = [
  '33222132233332332323323322322323333232322332',
  '23332323333323333323323332323332333232333323',
  '32332323333232333323333232333323323323333323',
  '33323330021232333323333332333333222323333333',
  '22322320003323323333232333232323232332333222',
  '33232323333w2332332323323333223232333232333w',
  '22332223332323g332322322232332222332322332w2',
  '33233233322332323330g00232333233222333233323',
  '22322322ww23223232232233223222322222322232w2',
  '11212232233322232323g223332222322332232333g2',
  '12122212222232222w22222222222222222222232223',
  '001000g00g0000g0g00g0010000000000g00g00g0g00',
]

const alphas = { '0': '0.04', '1': '0.18', '2': '0.40', '3': '0.85' }

const ticks = Array.from({ length: 40 }, (_, i) => `t${String(i + 1).padStart(2, '0')}`)

export default function Coverage() {
  return (
    <section className="s6" data-screen-label="06 Coverage">
      <div className="s6-head">
        <div className="left">
          <span className="eyebrow"><span className="pip" />06 · coverage cartography</span>
          <h2>Where you <span className="it">haven't</span> been yet.</h2>
        </div>
        <div className="right">
          Tool × state coverage
          <span className="v lining">94.<span className="em">2</span>%</span>
          <div style={{marginTop:'18px',opacity:0.7}}>31 transition gaps detected</div>
        </div>
      </div>

      <div className="s6-heat-wrap">
        <div className="s6-heat-axis-x">
          <div className="label" />
          <div className="ticks">
            {ticks.map(t => <span key={t}>{t}</span>)}
          </div>
        </div>

        {rowData.map((row, ri) => (
          <div key={ri} className="s6-heat-row">
            <div className="ylabel">{rowLabels[ri]}</div>
            <div className="cells">
              {Array.from({ length: 40 }, (_, ci) => {
                const ch = row[ci] || '0'
                if (ch === 'g') return <span key={ci} className="gap" />
                if (ch === 'w') return <span key={ci} className="warn" />
                return <span key={ci} style={{'--a': alphas[ch] || '0.04'}} />
              })}
            </div>
          </div>
        ))}

        <div className="s6-callout" style={{top:'140px',right:'130px'}}>
          <span className="lbl">gap · t22 → archive_user</span>
          Branch never reached. Two-factor lockout path skipped in all 50,000 generated scenarios. <span style={{color:'var(--rust)'}}>Suggested pack: lockout.yaml</span>
        </div>
      </div>

      <div className="s6-legend">
        <span style={{color:'var(--ink-2)'}}>tool · state · transition</span>
        <span style={{color:'var(--rust-dim)'}}>● covered</span>
        <span style={{color:'var(--amber)'}}>● partial</span>
        <span style={{color:'var(--sig-red)'}}>● gap</span>
        <div className="scale">
          {['0.04','0.15','0.30','0.50','0.75','1'].map(a => (
            <span key={a} style={{'--a': a}} />
          ))}
        </div>
      </div>
    </section>
  )
}
