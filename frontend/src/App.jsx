import { useEffect, useRef, useState } from "react";

const API = import.meta.env.VITE_API_URL || "";
const demoScript = [
  { speaker: "Alex · AI assistant", text: "Hello! This is Alex, an AI assistant calling on behalf of BrightWave Contact Center. Is now an okay time for a quick question?" },
  { speaker: "Prospect · Demo", text: "Sure, I have a minute. What is this about?" },
  { speaker: "Alex · AI assistant", text: "We help businesses with customer support, lead generation, and appointment setting. How are you currently handling customer enquiries?" },
  { speaker: "Prospect · Demo", text: "Our small team handles calls and messages. We struggle to cover evenings and weekends." },
  { speaker: "Alex · AI assistant", text: "That makes sense. Extended coverage can be difficult to staff internally. Are missed enquiries or response delays your biggest concern?" },
  { speaker: "Prospect · Demo", text: "Mostly missed enquiries after business hours." },
  { speaker: "Alex · AI assistant", text: "A dedicated support team or agreed after-hours coverage may be worth exploring. I don't want to guess at pricing or availability, but I can arrange a conversation with our sales team. Would that be useful?" },
  { speaker: "Prospect · Demo", text: "Yes, please have someone contact me." },
  { speaker: "Alex · AI assistant", text: "Absolutely. This is a demo, so no appointment has been booked. In a live deployment, I would confirm your preferred contact details and schedule with our team. Thanks for your time!" }
];

export default function App() {
  const [tab, setTab] = useState("demo");
  const [running, setRunning] = useState(false);
  const [finished, setFinished] = useState(false);
  const [line, setLine] = useState(0);
  const [transcript, setTranscript] = useState([]);
  const [leads, setLeads] = useState([]);
  const [apiState, setApiState] = useState(API ? "checking" : "offline");
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [voiceMessage, setVoiceMessage] = useState("");
  const speechSupported = typeof window !== "undefined" && "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
  const [leadName, setLeadName] = useState("Jordan Lee");
  const [company, setCompany] = useState("Northstar Retail");
  const [industry, setIndustry] = useState("Retail");
  const timer = useRef(null);
  const runId = useRef(0);
  const speechFailed = useRef(false);

  useEffect(() => {
    if (API) {
      fetch(`${API}/leads`)
        .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
        .then((data) => { setLeads(data); setApiState("connected"); })
        .catch(() => setApiState("offline"));
    }
    return () => {
      runId.current += 1;
      clearTimeout(timer.current);
      if (speechSupported) window.speechSynthesis.cancel();
    };
  }, []);

  function startDemo() {
    // Start speaking synchronously with the click so browsers allow playback.
    runId.current += 1;
    const currentRun = runId.current;
    clearTimeout(timer.current);
    if (speechSupported) window.speechSynthesis.cancel();
    speechFailed.current = false;
    setVoiceMessage("");
    setTranscript([]);
    setLine(0);
    setFinished(false);
    setRunning(true);
    playLine(0, currentRun);
  }

  function playLine(index, currentRun) {
    if (runId.current !== currentRun) return;
    if (index >= demoScript.length) {
      setRunning(false);
      setFinished(true);
      return;
    }

    const item = demoScript[index];
    setLine(index);
    setTranscript((items) => [...items, item]);

    const advance = () => {
      if (runId.current !== currentRun) return;
      clearTimeout(timer.current);
      timer.current = setTimeout(() => playLine(index + 1, currentRun), 450);
    };

    if (!voiceEnabled || !speechSupported || speechFailed.current) {
      timer.current = setTimeout(advance, Math.max(2300, item.text.length * 45));
      return;
    }

    try {
      const synth = window.speechSynthesis;
      const utterance = new SpeechSynthesisUtterance(item.text);
      const englishVoices = synth.getVoices().filter((voice) => voice.lang.toLowerCase().startsWith("en"));
      const isAlex = item.speaker.startsWith("Alex");
      // Use distinct browser voices where available; otherwise adjust pitch.
      utterance.voice = englishVoices[isAlex ? 0 : Math.min(1, englishVoices.length - 1)] || null;
      utterance.lang = utterance.voice?.lang || "en-US";
      utterance.rate = isAlex ? 0.96 : 1.02;
      utterance.pitch = isAlex ? 0.92 : 1.12;
      utterance.volume = 1;
      utterance.onend = advance;
      utterance.onerror = (event) => {
        if (runId.current !== currentRun) return;
        speechFailed.current = true;
        setVoiceMessage(`Audio was blocked or unavailable (${event.error || "unknown error"}). The transcript demo will continue. Check browser sound settings and try again.`);
        advance();
      };
      // Safety fallback for browsers that never deliver a speech completion event.
      timer.current = setTimeout(advance, Math.max(14000, item.text.length * 170));
      synth.speak(utterance);
    } catch (error) {
      speechFailed.current = true;
      setVoiceMessage("Your browser could not start audio. The transcript demo will continue.");
      timer.current = setTimeout(advance, Math.max(2300, item.text.length * 45));
    }
  }

  function stopDemo() {
    runId.current += 1;
    clearTimeout(timer.current);
    if (speechSupported) window.speechSynthesis.cancel();
    setRunning(false);
    setFinished(false);
  }

  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">A</div><div><b>Alex AI</b><small>SALES ASSISTANT</small></div></div>
      <button className={tab === "demo" ? "nav active" : "nav"} onClick={() => setTab("demo")}>◉ <span>Live demo</span></button>
      <button className={tab === "leads" ? "nav active" : "nav"} onClick={() => setTab("leads")}>▤ <span>Lead overview</span></button>
      <div className="sidebar-bottom"><span className={apiState === "connected" ? "dot green" : "dot"}></span> API {apiState === "connected" ? "connected" : apiState === "checking" ? "checking" : "not connected"}<small>Interactive presentation mode</small></div>
    </aside>
    <section className="main-area">
      <header className="topbar"><div><div className="eyebrow">AI-POWERED BUSINESS DEVELOPMENT</div><h1>{tab === "demo" ? "Outbound sales demo" : "Lead overview"}</h1></div><span className="demo-pill">DEMO MODE · NO PHONE CALL</span></header>
      {tab === "demo" ? <div className="content-grid">
        <section className="left-column">
          <div className="panel setup-panel">
            <div className="section-heading"><div><span className="step">01</span><h2>Prospect profile</h2></div><span className="muted">Sample data</span></div>
            <div className="fields">
              <label>Contact name<input value={leadName} onChange={(e) => setLeadName(e.target.value)} /></label>
              <label>Company<input value={company} onChange={(e) => setCompany(e.target.value)} /></label>
              <label>Industry<select value={industry} onChange={(e) => setIndustry(e.target.value)}><option>Retail</option><option>Healthcare</option><option>Technology</option><option>Financial services</option><option>Travel & hospitality</option><option>Other</option></select></label>
            </div>
            <div className="profile-note">Alex will use this sample profile in the conversation preview. No real person is contacted.</div>
          </div>
          <div className="panel call-panel">
            <div className="section-heading"><div><span className="step">02</span><h2>AI sales conversation</h2></div><span className={running ? "status live" : "status"}>{running ? "● SIMULATING" : finished ? "✓ COMPLETED" : "READY"}</span></div>
            <div className="voice-stage">
              <div className={running ? "orb pulse" : "orb"}><span>✦</span></div>
              <h3>{running ? "Alex is speaking…" : finished ? "Demo completed" : "Meet Alex"}</h3>
              <p>{running ? "Playing a sample sales conversation with browser-generated speech" : "An AI sales assistant for your contact center"}</p>
              <div className="wave">{Array.from({length:  thirty()}, (_, i) => <i key={i} style={{height: `${10 + ((i * 17) % 27)}px`}} />)}</div>
              <div className="controls">{!running ? <button className="primary" onClick={startDemo}>▶ {finished ? "Replay demo" : "Start demo conversation"}</button> : <button className="stop" onClick={stopDemo}>■ Stop demo</button>}</div>
              <label className="voice-toggle"><input type="checkbox" checked={voiceEnabled && speechSupported} disabled={running || !speechSupported} onChange={(e) => setVoiceEnabled(e.target.checked)} /> 🔊 Speak conversation aloud</label>
              {!speechSupported && <p className="voice-notice">This browser does not support speech playback. Use Chrome, Edge, or Safari for the voice demo.</p>}
              {voiceMessage && <p className="voice-notice" role="status">{voiceMessage}</p>}
            </div>
            <div className="transcript-head"><b>Conversation transcript</b><span>{transcript.length} / {demoScript.length} lines</span></div>
            <div className="transcript">
              {transcript.length === 0 && <div className="empty-transcript">The conversation will appear here when you start the demo.</div>}
              {transcript.map((item, i) => <div className={item.speaker.startsWith("Alex") ? "message ai" : "message prospect"} key={i}><small>{item.speaker}</small><p>{item.text}</p></div>)}
              <div id="transcript-end" />
            </div>
            {finished && <div className="result"><b>✓ Interest qualified · Human follow-up requested</b><span>Demo result only — no CRM record or meeting was created.</span></div>}
          </div>
        </section>
        <aside className="right-column">
          <div className="panel value-panel"><span className="step">03</span><h2>What Alex can sell</h2><p>Introduce your contact center services and discover where prospects need help.</p>
            {["Inbound customer support","Outbound sales campaigns","Lead generation","Appointment setting","Technical support","Customer retention","Dedicated agents","24/7 coverage (if available)"].map((x) => <div className="service" key={x}><span>✓</span>{x}</div>)}
            <small className="disclaimer">Only enable services your company actually provides.</small>
          </div>
          <div className="panel outcome-panel"><span className="step">04</span><h2>Demo call outcome</h2><div className="metric"><strong>{finished ? "1" : "—"}</strong><span>Qualified prospects</span></div><div className="metric"><strong>{finished ? "Yes" : "—"}</strong><span>Human follow-up requested</span></div><div className="metric"><strong>0:21</strong><span>Sample conversation length</span></div></div>
          <div className="human-note"><b>Human-in-the-loop</b><p>Alex qualifies interest and offers a handoff. Your sales team confirms pricing, capacity, and appointments.</p></div>
        </aside>
      </div> : <div className="panel leads-panel"><div className="section-heading"><h2>Saved leads</h2><span className="muted">{leads.length} from API</span></div>{apiState !== "connected" ? <p className="muted">Backend API is not connected. You can still run the interactive demo.</p> : leads.length === 0 ? <p className="muted">No leads have been added yet. Use the API documentation to create a lead.</p> : <div className="table-wrap"><table><thead><tr><th>Company</th><th>Contact</th><th>Country</th><th>Consent</th><th>Status</th></tr></thead><tbody>{leads.map((l) => <tr key={l.id}><td>{l.company_name}</td><td>{l.contact_name || "—"}</td><td>{l.country || "—"}</td><td>{l.consent_status}</td><td>{l.status}</td></tr>)}</tbody></table></div>}</div>}
      <footer>Alex AI · Interactive demo environment · Sample conversation, not a real call</footer>
    </section>
  </main>;
}

function thirty() { return 30; }
