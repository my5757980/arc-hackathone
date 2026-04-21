import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentFlow — Autonomous AI Agent Economy",
  description: "Sub-cent USDC micropayments between AI agents via Circle Nanopayments on Arc",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-arc-dark">{children}</body>
    </html>
  );
}
