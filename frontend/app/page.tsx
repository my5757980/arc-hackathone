"use client";
import React, { useEffect, useState, useCallback } from "react";
import { Zap, Activity, DollarSign, Bot, Play, ExternalLink, CheckCircle, Clock } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Transaction {
  id: string;
  from_agent: string;
  to_agent: string;
  amount_usdc: number;
  tx_hash: string;
  circle_tx_id?: string;
  task_type: string;
  task_result?: string;
  status: string;
  timestamp: string;
  real_onchain?: boolean;
}
interface Wallet {
  agent_name: string;
  wallet_address: string;
  circle_wallet_id: string;
  balance_usdc: number;
  balance_source: string;
}

const AGENT_COLORS: Record<string, string> = {
  DataAnalyst: "#00e5ff",
  ContentWriter: "#a855f7",
  CodeReviewer: "#eab308",
  Translator: "#22c55e",
};

const ac = (a: string) => AGENT_COLORS[a] ?? "#9ca3af";

export default function Dashboard() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoProgress, setDemoProgress] = useState(0);
  const [connected, setConnected] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [txRes, walletRes] = await Promise.all([
        fetch(API + "/api/transactions?limit=100"),
        fetch(API + "/api/wallets"),
      ]);
      const txData = await txRes.json();
      const walletData = await walletRes.json();
      setTransactions(txData.transactions || []);
      setWallets(walletData.wallets || []);
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    const es = new EventSource(API + "/api/events");
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "heartbeat" || data.type === "connected") return;
        setTransactions((prev) => [data, ...prev].slice(0, 200));
        setDemoProgress((prev) => Math.min(prev + 1, 55));
      } catch (_) {}
    };
    return () => es.close();
  }, []);

  const runDemo = useCallback(async () => {
    setDemoRunning(true);
    setDemoProgress(0);
    await fetch(API + "/api/demo/run", { method: "POST" });
    setTimeout(() => { setDemoRunning(false); fetchData(); }, 120000);
  }, [fetchData]);

  const clearAll = useCallback(async () => {
    await fetch(API + "/api/transactions/clear", { method: "DELETE" });
    setTransactions([]);
    setDemoProgress(0);
  }, []);

  const shortHash = (h: string) => (h ? h.slice(0, 8) + "..." + h.slice(-6) : "pending");
  const totalUSDC = transactions.reduce((s, t) => s + (t.amount_usdc || 0), 0);
  const realCount = transactions.filter((t) => t.real_onchain || (t.status !== "simulated")).length;

  const dark = "#0a0a0f";
  const card = { background: "#0f0f1a", border: "1px solid #1e1e3f", borderRadius: "8px" };

  return (
    <div style={{ minHeight: "100vh", background: dark, fontFamily: "monospace", color: "#e2e8f0" }}>
      {/* Header */}
      <header style={{ borderBottom: "1px solid #1e1e3f", padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Zap size={20} color="#00e5ff" />
          <div>
            <h1 style={{ color: "#00e5ff", margin: 0, fontSize: "18px", fontWeight: "bold", textShadow: "0 0 10px #00e5ff" }}>
              AgentFlow
            </h1>
            <p style={{ color: "#6b7280", margin: 0, fontSize: "11px" }}>
              Autonomous AI Agent Economy on Arc — Circle Nanopayments + USDC
            </p>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "12px" }}>
          <div style={{ color: "#9ca3af", display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: connected ? "#22c55e" : "#ef4444", display: "inline-block" }} />
            Arc Testnet {connected ? "Live" : "Connecting..."}
          </div>
          <div style={{ color: "#6b7280", fontSize: "11px" }}>
            Track: Agent-to-Agent Payment Loop
          </div>
        </div>
      </header>

      <main style={{ maxWidth: "1280px", margin: "0 auto", padding: "24px 16px" }}>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px", marginBottom: "24px" }}>
          {[
            { label: "Total Transactions", value: String(transactions.length), color: "#00e5ff", sub: `${realCount} onchain` },
            { label: "USDC Settled", value: "$" + totalUSDC.toFixed(4), color: "#22c55e", sub: "via Arc" },
            { label: "Active Agents", value: "4", color: "#a855f7", sub: "Gemini 2.5 Flash" },
            { label: "Avg Cost/Task", value: "$0.004", color: "#eab308", sub: "vs $1 gas" },
          ].map((s) => (
            <div key={s.label} style={{ ...card, padding: "16px" }}>
              <p style={{ color: "#6b7280", fontSize: "11px", margin: "0 0 6px" }}>{s.label}</p>
              <p style={{ color: s.color, fontSize: "24px", fontWeight: "bold", margin: "0 0 4px" }}>{s.value}</p>
              <p style={{ color: "#4b5563", fontSize: "10px", margin: 0 }}>{s.sub}</p>
            </div>
          ))}
        </div>

        {/* Agent Cards + Demo Button */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: "16px", marginBottom: "24px" }}>
          {[
            { n: "DataAnalyst",   p: "$0.003", d: "Data insights" },
            { n: "ContentWriter", p: "$0.005", d: "Content gen" },
            { n: "CodeReviewer",  p: "$0.008", d: "Code review" },
            { n: "Translator",    p: "$0.002", d: "Translation" },
          ].map((a) => {
            const w = wallets.find((x) => x.agent_name === a.n);
            const cnt = transactions.filter((t) => t.to_agent === a.n).length;
            const c = ac(a.n);
            return (
              <div key={a.n} style={{ background: "#0f0f1a", border: `1px solid ${c}33`, borderRadius: "8px", padding: "16px" }}>
                <h3 style={{ color: c, fontSize: "13px", fontWeight: "bold", margin: "0 0 4px" }}>{a.n}</h3>
                <p style={{ color: "#6b7280", fontSize: "10px", margin: "0 0 12px" }}>{a.d}</p>
                <div style={{ fontSize: "11px" }}>
                  {[["Price", a.p, "#22c55e"], ["Tasks Done", String(cnt), "white"],
                    ["Balance", w ? `$${w.balance_usdc.toFixed(2)}` : "--", "#00e5ff"],
                    ["Source", w?.balance_source ?? "--", "#6b7280"]].map(([k, v, vc]) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                      <span style={{ color: "#6b7280" }}>{k}</span>
                      <span style={{ color: vc, fontWeight: k === "Price" ? "bold" : "normal" }}>{v}</span>
                    </div>
                  ))}
                  {w && (
                    <div style={{ marginTop: "8px", fontSize: "9px", color: "#374151", wordBreak: "break-all" }}>
                      {w.wallet_address.slice(0, 10)}...
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Demo Control */}
          <div style={{ ...card, padding: "16px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "10px" }}>
            <button
              onClick={runDemo}
              disabled={demoRunning}
              style={{
                width: "100%", background: demoRunning ? "#374151" : "linear-gradient(135deg,#00e5ff,#a855f7)",
                color: demoRunning ? "#9ca3af" : "#0a0a0f", fontWeight: "bold", padding: "10px",
                borderRadius: "8px", border: "none", cursor: demoRunning ? "not-allowed" : "pointer", fontSize: "12px",
              }}
            >
              {demoRunning ? "Running..." : "▶ Run Demo (55 txns)"}
            </button>
            {demoRunning && (
              <div style={{ width: "100%" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "#9ca3af", marginBottom: "4px" }}>
                  <span>Progress</span><span>{demoProgress}/55</span>
                </div>
                <div style={{ background: "#1a1a2e", borderRadius: "4px", height: "4px" }}>
                  <div style={{ width: `${(demoProgress / 55) * 100}%`, background: "linear-gradient(90deg,#00e5ff,#a855f7)", height: "4px", borderRadius: "4px", transition: "width 0.3s" }} />
                </div>
              </div>
            )}
            <button
              onClick={clearAll}
              disabled={demoRunning}
              style={{
                width: "100%", background: "transparent", color: "#6b7280",
                fontWeight: "bold", padding: "6px", borderRadius: "8px",
                border: "1px solid #374151", cursor: demoRunning ? "not-allowed" : "pointer", fontSize: "11px",
              }}
            >
              🗑 Clear All Data
            </button>
            <p style={{ fontSize: "10px", color: "#6b7280", margin: 0, textAlign: "center" }}>
              55 Circle DCW transfers<br />Orchestrator → Agents
            </p>
          </div>
        </div>

        {/* Margin Analysis */}
        <div style={{ ...card, padding: "20px", marginBottom: "24px" }}>
          <h2 style={{ color: "#00e5ff", fontSize: "13px", fontWeight: "bold", margin: "0 0 4px" }}>
            Why Gas-Based Chains Kill Sub-Cent Pricing — Arc Nanopayments Solves This
          </h2>
          <p style={{ color: "#4b5563", fontSize: "10px", margin: "0 0 16px" }}>
            Economic proof — required by hackathon criteria
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "16px", fontSize: "11px" }}>
            {[
              {
                title: "Gas-Based (ETH/Polygon)",
                bg: "#1a0a0a", border: "#7f1d1d", c: "#f87171",
                rows: [["Tx cost", "~$1.00", "#f87171"], ["Revenue/tx", "$0.003 USDC", "#9ca3af"], ["1000 tx net", "-$997 LOSS", "#f87171"], ["Viable?", "NO", "#f87171"]],
              },
              {
                title: "Arc Nanopayments",
                bg: "#0a1a0a", border: "#14532d", c: "#4ade80",
                rows: [["Overhead/tx", "~$0.000001", "#4ade80"], ["Revenue/tx", "$0.003 USDC", "#9ca3af"], ["1000 tx net", "+$2.999 PROFIT", "#4ade80"], ["Viable?", "YES", "#4ade80"]],
              },
              {
                title: "Arc Advantage",
                bg: "#0a0f1a", border: "#00e5ff33", c: "#00e5ff",
                rows: [["Finality", "<1 second", "#00e5ff"], ["Gas token", "USDC (stable)", "#00e5ff"], ["Fee savings", "99.9999%", "#00e5ff"], ["Settlement", "Arc EVM L1", "#00e5ff"]],
              },
            ].map((box) => (
              <div key={box.title} style={{ background: box.bg, border: `1px solid ${box.border}`, borderRadius: "8px", padding: "12px" }}>
                <h3 style={{ color: box.c, fontWeight: "bold", margin: "0 0 10px", fontSize: "12px" }}>{box.title}</h3>
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

        {/* Live Transaction Feed */}
        <div style={{ ...card, overflow: "hidden" }}>
          <div style={{ borderBottom: "1px solid #1e1e3f", padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ color: "white", fontSize: "13px", fontWeight: "bold", margin: 0 }}>
              Live Transaction Feed — Arc Testnet
            </h2>
            <span style={{ color: "#6b7280", fontSize: "11px" }}>
              {transactions.length} transactions • {realCount} Circle DCW
            </span>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: "11px", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #1e1e3f", color: "#6b7280" }}>
                  {["From", "To Agent", "Task", "Amount", "Tx Hash", "Status", "Time"].map((h, i) => (
                    <th key={h} style={{ textAlign: i === 3 ? "right" : "left", padding: "8px 12px", fontWeight: "normal" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 100).map((tx, i) => (
                  <tr key={tx.id || i} style={{ borderBottom: "1px solid #1e1e3f22" }}>
                    <td style={{ padding: "7px 12px", color: "#9ca3af" }}>{tx.from_agent}</td>
                    <td style={{ padding: "7px 12px", color: ac(tx.to_agent), fontWeight: "bold" }}>{tx.to_agent}</td>
                    <td style={{ padding: "7px 12px", color: "#6b7280" }}>{tx.task_type}</td>
                    <td style={{ padding: "7px 12px", textAlign: "right", color: "#22c55e", fontFamily: "monospace" }}>
                      ${tx.amount_usdc?.toFixed(4)}
                    </td>
                    <td style={{ padding: "7px 12px", fontFamily: "monospace" }}>
                      <a
                        href={`https://testnet.arcscan.app/tx/${tx.tx_hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "#00e5ff", textDecoration: "none" }}
                        title={tx.tx_hash}
                      >
                        {shortHash(tx.tx_hash)}
                      </a>
                    </td>
                    <td style={{ padding: "7px 12px" }}>
                      <span style={{
                        fontSize: "9px", padding: "2px 6px", borderRadius: "4px",
                        background: tx.status === "CONFIRMED" || tx.status === "confirmed" ? "#14532d" : tx.status === "simulated" ? "#1a1a0a" : "#1a1a2e",
                        color: tx.status === "CONFIRMED" || tx.status === "confirmed" ? "#4ade80" : tx.status === "simulated" ? "#eab308" : "#60a5fa",
                      }}>
                        {tx.status === "simulated" ? "simulated" : tx.status?.toUpperCase() || "PENDING"}
                      </span>
                    </td>
                    <td style={{ padding: "7px 12px", color: "#4b5563" }}>
                      {tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : ""}
                    </td>
                  </tr>
                ))}
                {transactions.length === 0 && (
                  <tr>
                    <td colSpan={7} style={{ padding: "48px", textAlign: "center", color: "#4b5563" }}>
                      Click ▶ Run Demo to fire 55 autonomous Circle DCW transfers on Arc testnet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <footer style={{ textAlign: "center", fontSize: "10px", color: "#374151", padding: "20px" }}>
          AgentFlow — Agentic Economy on Arc 2026 &nbsp;|&nbsp;
          Circle Nanopayments + Arc EVM L1 + Gemini 2.5 Flash &nbsp;|&nbsp;
          Track: Agent-to-Agent Payment Loop
        </footer>
      </main>
    </div>
  );
}
