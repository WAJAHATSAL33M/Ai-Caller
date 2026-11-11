import { useEffect, useState } from "react";
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [leads, setLeads] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    fetch(`${API}/leads`)
      .then((r) => { if (!r.ok) throw new Error("API unavailable"); return r.json(); })
      .then(setLeads)
      .catch(() => setError("Could not load leads. Check that the API is running."));
  }, []);
  return <main className="shell">
    <header><div className="eyebrow">SALES OPERATIONS</div><h1>AI Sales Caller</h1>
      <p>Lead overview · English-language outbound sales assistant</p></header>
    <section className="panel">
      <div className="panel-head"><h2>Leads</h2><span>{leads.length} shown</span></div>
      {error && <p className="error">{error}</p>}
      {!error && leads.length === 0 && <p className="muted">No leads yet. Add one through the API docs at <a href={`${API}/docs`}>{API}/docs</a>.</p>}
      {leads.length > 0 && <div className="table-wrap"><table>
        <thead><tr><th>Company</th><th>Contact</th><th>Country</th><th>Consent</th><th>Status</th></tr></thead>
        <tbody>{leads.map((lead) => <tr key={lead.id}><td>{lead.company_name}</td>
          <td>{lead.contact_name || "—"}</td><td>{lead.country || "—"}</td>
          <td>{lead.consent_status}</td><td>{lead.status}</td></tr>)}</tbody>
      </table></div>}
    </section>
    <footer>Starter dashboard · Calls require documented authorization before dialing.</footer>
  </main>;
}
