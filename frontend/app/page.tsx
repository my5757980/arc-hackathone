"use client";
import { useEffect, useState, useCallback } from "react";
import { Zap, Activity, DollarSign, Bot, Play, ExternalLink } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Transaction {
  id: string; from_agent: string; to_agent: string; amount_usdc: number;
  tx_hash: string; task_type: string; status: string; timestamp: string;
}
interface Wallet { agent_name: string; wallet_address: string; balance_usdc: number; }

export default function Dashboard() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoProgress, setDemoProgress] = useState(0);

  useEffect(() => {
    fetch(API + "/api/transactions?limit=100").then(r => r.json()).then(d => setTransactions(d.transactions || []));
    fetch(API + "/api/wallets").then(r => r.json()).then(d => setWallets(d.wallets || []));
  }, []);

  useEffect(() => {
    const es = new EventSource(API + "/api/events");
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "heartbeat" || data.type === "connected") return;
        setTransactions(prev => [data, ...prev].slice(0, 200));
        setDemoProgress(prev => Math.min(prev + 1, 55));
      } catch (err) { /* ignore parse errors */ }
    };
    return () => es.close();
  }, []);

  const runDemo = useCallback(async () => {
    setDemoRunning(true);
    setDemoProgress(0);
    await fetch(API + "/api/demo/run", { method: "POST" });
    setTimeout(() => setDemoRunning(false), 35000);
  }, []);

  const shortHash = (h: string) => h ? h.slice(0, 6) + "..." + h.slice(-4) : "pending";
  const totalUSDC = transactions.reduce((s, t) => s + (t.amount_usdc || 0), 0);
  const ac = (a: string) => a === "DataAnalyst" ? "#00e5ff" : a === "ContentWriter" ? "#a855f7" : a === "CodeReviewer" ? "#eab308" : "#22c55e";

  const dark = "#0a0a0f";
  const card = { background: "#0f0f1a", border: "1px solid #1e1e3f", borderRadius: "8px" };

  return (
    <div style={{ minHeight: "100vh", background: dark, fontFamily: "monospace", color: "#e2e8f0" }}>
      <header style={{ borderBottom: "1px solid #1e1e3f", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Zap size={20} color="#00e5ff" />
          <div>
            <h1 style={{ color: "#00e5ff", margin: 0, fontSize: "18px", fontWeight: "bold", textShadow: "0 0 10px #00e5ff" }}>AgentFlow</h1>
            <p style={{ color: "#6b7280", margin: 0, fontSize: "11px" }}>Autonomous AI Agent Economy on Arc</p>
          </div>
        </div>
        <div style={{ color: "#9ca3af", fontSize: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#22c55e", display: "inline-block" }} />
          Arc Testnet Live
        </div>
      </header>

      <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "24px 16px" }}>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px", marginBottom: "24px" }}>
          {[
            { label: "Transactions", value: String(transactions.length), color: "#00e5ff" },
            { label: "USDC Settled", value: "$" + totalUSDC.toFixed(4), color: "#22c55e" },
            { label: "Active Agents", value: "4", color: "#a855f7" },
            { label: "Avg Cost/Task", value: "$0.004", color: "#eab308" },
          ].map(s => (
            <div key={s.label} style={{ ...card, padding: "16px" }}>
              <p style={{ color: "#6b7280", fontSize: "11px", margin: "0 0 8px" }}>{s.label}</p>
              <p style={{ color: s.color, fontSize: "24px", fontWeight: "bold", margin: 0 }}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Agent Cards + Demo */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: "16px", marginBottom: "24px" }}>
          {[
            { n: "DataAnalyst", p: "$0.003", d: "Data insights" },
            { n: "ContentWriter", p: "$0.005", d: "Content gen" },
            { n: "CodeReviewer", p: "$0.008", d: "Code review" },
            { n: "Translator", p: "$0.002", d: "Translation" },
          ].map(a => {
            const w = wallets.find(x => x.agent_name === a.n);
            const cnt = transactions.filter(t => t.to_agent === a.n).length;
            const c = ac(a.n);
            return (
              <div key={a.n} style={{ background: "#0f0f1a", border: "1px solid " + c + "33", borderRadius: "8px", padding: "16px" }}>
                <h3 style={{ color: c, fontSize: "13px", fontWeight: "bold", margin: "0 0 4px" }}>{a.n}</h3>
                <p style={{ color: "#6b7280", fontSize: "11px", margin: "0 0 12px" }}>{a.d}</p>
                <div style={{ fontSize: "11px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ color: "#6b7280" }}>Price</span><span style={{ color: "#22c55e", fontWeight: "bold" }}>{a.p}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ color: "#6b7280" }}>Tasks</span><span style={{ color: "white" }}>{cnt}</span>
                  </div>
                  {w && (
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#6b7280" }}>Balance</span>
                      <span style={{ color: "#00e5ff" }}>${w.balance_usdc.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          <div style={{ ...card, padding: "16px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "12px" }}>
            <button
              onClick={runDemo}
              disabled={demoRunning}
              style={{ width: "100%", background: demoRunning ? "#374151" : "#00e5ff", color: "#0a0a0f", fontWeight: "bold", padding: "8px", borderRadius: "8px", border: "none", cursor: demoRunning ? "not-allowed" : "pointer", fontSize: "12px" }}
            >
              {demoRunning ? "Running..." : "Run Demo (55 txns)"}
            </button>
            {demoRunning && (
              <div style={{ width: "100%" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "#9ca3af", marginBottom: "4px" }}>
                  <span>Progress</span><span>{demoProgress}/55</span>
                </div>
                <div style={{ background: "#1a1a2e", borderRadius: "4px", height: "4px" }}>
                  <div style={{ width: (demoProgress / 55 * 100) + "%", background: "#00e5ff", height: "4px", borderRadius: "4px", transition: "width 0.3s" }} />
                </div>
              </div>
            )}
            <p style={{ fontSize: "10px", color: "#6b7280", margin: 0, textAlign: "center" }}>55 autonomous Arc transactions</p>
          </div>
        </div>

        {/* Margin Analysis */}
        <div style={{ ...card, padding: "20px", marginBottom: "24px" }}>
          <h2 style={{ color: "#00e5ff", fontSize: "13px", fontWeight: "bold", margin: "0 0 16px" }}>
            Why Gas-Based Chains Make Sub-Cent Pricing Impossible
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "16px", fontSize: "11px" }}>
            {[
              { title: "Gas-Based (ETH)", bg: "#1a0a0a", border: "#7f1d1d", c: "#f87171", rows: [["Tx cost", "~$1.00", "#f87171"], ["Revenue/tx", "$0.003", "#9ca3af"], ["1000 tx net", "-$997 LOSS", "#f87171"]] },
              { title: "Arc Nanopayments", bg: "#0a1a0a", border: "#14532d", c: "#4ade80", rows: [["Overhead/tx", "~$0.000001", "#4ade80"], ["Revenue/tx", "$0.003", "#9ca3af"], ["1000 tx net", "+$2.999 PROFIT", "#4ade80"]] },
              { title: "Arc Advantage", bg: "#0a0f1a", border: "#00e5ff33", c: "#00e5ff", rows: [["Finality", "<1 second", "#00e5ff"], ["Gas token", "USDC (stable)", "#00e5ff"], ["Fee savings", "99.9999%", "#00e5ff"]] },
            ].map(box => (
              <div key={box.title} style={{ background: box.bg, border: "1px solid " + box.border, borderRadius: "8px", padding: "12px" }}>
                <h3 style={{ color: box.c, fontWeight: "bold", margin: "0 0 8px" }}>{box.title}</h3>
                {box.rows.map(([k, v, vc]) => (
                  <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                    <span style={{ color: "#9ca3af" }}>{k}</span>
                    <span style={{ color: vc, fontWeight: "bold" }}>{v}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Transaction Feed */}
        <div style={{ ...card, overflow: "hidden" }}>
          <div style={{ borderBottom: "1px solid #1e1e3f", padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ color: "white", fontSize: "13px", fontWeight: "bold", margin: 0 }}>Live Transaction Feed</h2>
            <span style={{ color: "#6b7280", fontSize: "11px" }}>{transactions.length} transactions</span>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: "11px", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #1e1e3f", color: "#6b7280" }}>
                  {["From", "To Agent", "Task", "Amount", "Tx Hash", "Time"].map((h, i) => (
                    <th key={h} style={{ textAlign: i === 3 ? "right" : "left", padding: "8px 16px", fontWeight: "normal" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 100).map((tx, i) => (
                  <tr key={tx.id || i} style={{ borderBottom: "1px solid #1e1e3f22" }}>
                    <td style={{ padding: "8px 16px", color: "#9ca3af" }}>{tx.from_agent}</td>
                    <td style={{ padding: "8px 16px", color: ac(tx.to_agent), fontWeight: "bold" }}>{tx.to_agent}</td>
                    <td style={{ padding: "8px 16px", color: "#6b7280" }}>{tx.task_type}</td>
                    <td style={{ padding: "8px 16px", textAlign: "right", color: "#22c55e", fontFamily: "monospace" }}>${tx.amount_usdc?.toFixed(4)}</td>
                    <td style={{ padding: "8px 16px", fontFamily: "monospace" }}>
                      <a href={"https://explorer.arc.circle.com/tx/" + tx.tx_hash} target="_blank" rel="noopener noreferrer" style={{ color: "#00e5ff", textDecoration: "none" }}>
                        {shortHash(tx.tx_hash)}
                      </a>
                    </td>
                    <td style={{ padding: "8px 16px", color: "#4b5563" }}>
                      {tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : ""}
                    </td>
                  </tr>
                ))}
                {transactions.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ padding: "32px", textAlign: "center", color: "#4b5563" }}>
                      Click Run Demo to start 55 autonomous Arc transactions
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <footer style={{ textAlign: "center", fontSize: "11px", color: "#374151", padding: "16px" }}>
          AgentFlow - Agentic Economy on Arc 2026 - Circle Nanopayments + Arc EVM L1 + Gemini Flash
        </footer>
      </main>
    </div>
  );
}
