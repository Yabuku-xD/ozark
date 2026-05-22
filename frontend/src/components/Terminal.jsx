const termHTML = `<span class="ts">14:02:08.114</span>  <span class="prompt">$</span> <span class="cmd">curl</span> <span class="flag">-sX POST</span> <span class="str">http://127.0.0.1:8787/runs/live</span> <span class="dim">\\</span>
<span class="ts">           </span>    <span class="flag">-H</span> <span class="str">'Content-Type: application/json'</span> <span class="dim">\\</span>
<span class="ts">           </span>    <span class="flag">-d</span> <span class="str">'{ </span><span class="key">"endpoint"</span><span class="str">: </span><span class="str">"http://localhost:8080/agent", </span><span class="key">"count"</span><span class="str">: </span><span class="num">50</span><span class="str">, </span><span class="key">"agent_type"</span><span class="str">: </span><span class="str">"customer_support" }'</span>

<span class="ts">14:02:08.119</span>  <span class="dim">→ run.id</span>  <span class="ok">run_3f9c1e</span>   <span class="dim">agent</span> support‑v2   <span class="dim">scenarios</span> <span class="num">50</span>
<span class="ts">14:02:08.142</span>  <span class="ok">▸</span> sc.18420 <span class="dim">happy/refund</span>     turn 1·1   <span class="ok">PASS</span>   126ms
<span class="ts">14:02:08.318</span>  <span class="ok">▸</span> sc.18422 <span class="dim">edge/locked</span>      turn 2·2   <span class="ok">PASS</span>   204ms
<span class="ts">14:02:08.541</span>  <span class="warn">▸</span> sc.18423 <span class="dim">adv/sys‑extract</span>  turn 1·3   <span class="warn">GUARD</span>  <span class="dim">g0dm0d3_system_prompt_injection</span>
<span class="ts">14:02:08.668</span>  <span class="ok">▸</span> sc.18425 <span class="dim">multi/negotiate</span>  turn 4·7   <span class="ok">PASS</span>   312ms
<span class="ts">14:02:08.882</span>  <span class="err">▸</span> sc.18426 <span class="dim">adv/pii</span>          turn 1·2   <span class="err">BLOCK</span>  <span class="dim">no_pii  · args.email leaked</span>
<span class="ts">14:02:09.044</span>  <span class="ok">▸</span> sc.18424 <span class="dim">fault/retry</span>      turn 3·3   <span class="ok">PASS</span>   <span class="dim">recovered 502→200</span>
<span class="ts">14:02:09.221</span>  <span class="ok">▸</span> sc.18428 <span class="dim">happy/reset</span>      turn 2·2   <span class="ok">PASS</span>   178ms
<span class="ts">14:02:09.402</span>  <span class="err">▸</span> sc.18430 <span class="dim">adv/sql</span>          turn 1·1   <span class="err">BLOCK</span>  <span class="dim">destructive_sql · DROP TABLE</span>
<span class="ts">14:02:09.580</span>  <span class="warn">▸</span> sc.18427 <span class="dim">edge/temporal</span>    turn 2·2   <span class="warn">WARN</span>   <span class="dim">ambiguous "next friday"</span>

<span class="ts">14:02:11.911</span>  <span class="dim">···</span> 41 more scenarios <span class="dim">···</span>

<span class="ts">14:02:14.207</span>  <span class="ok">◆ run.complete</span>   passed <span class="ok">42</span> · warned <span class="warn">5</span> · blocked <span class="err">3</span> · score <span class="ok">87.4</span>%`

export default function Terminal() {
  return (
    <section className="s3" data-screen-label="03 Live">
      <div className="s3-frame">
        <div className="s3-inner">
          <div className="s3-grid">
            <div className="s3-left">
              <span className="eyebrow"><span className="pip" />03 · the execution engine</span>
              <h2>Connect your agent.<br /><span className="it">Watch</span> it walk.</h2>
              <p>Point Ozark at any agent over HTTP or stdio. The runner steps it through scenarios one move at a time — every tool call, every guardrail trip, every retry recorded as a trace.</p>
              <div className="s3-flow">
                <div><span className="you">[ your agent ]</span> <span className="arrow">⟶</span> <span className="it">HTTP / stdio</span></div>
                <div><span className="arrow">└─</span> ozark runner <span className="arrow">⟶</span> scenario.step</div>
                <div><span className="arrow">&nbsp;&nbsp;&nbsp;└─</span> policy engine <span className="arrow">⟶</span> guardrail.check</div>
                <div><span className="arrow">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└─</span> coverage.update</div>
                <div><span className="arrow">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└─</span> score.aggregate <span className="arrow">⟶</span> <span className="you">trace.replay</span></div>
              </div>
            </div>

            <div className="s3-terminal">
              <div className="s3-term-bar">
                <span className="dot r" /><span className="dot y" /><span className="dot g" />
                <span className="title">~/agents · ozark runner ▸ live</span>
                <span className="right"><span className="live">stream open · 127.0.0.1:8787</span></span>
              </div>
              <div className="s3-term-body" dangerouslySetInnerHTML={{ __html: termHTML }} />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
