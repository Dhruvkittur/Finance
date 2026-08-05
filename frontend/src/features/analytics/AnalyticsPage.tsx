/**
 * FinPilot AI — Analytics Page
 */

import React from "react";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { BarChart3, Zap, Bot, Clock, TrendingUp } from "lucide-react";
import { analyticsAPI } from "@/lib/api";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-muted-foreground mb-1 font-medium">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }} className="font-semibold">
          {p.name}: {typeof p.value === "number" ? p.value.toLocaleString() : p.value}
        </p>
      ))}
    </div>
  );
};

const SAMPLE_TOKEN_DATA = Array.from({ length: 30 }, (_, i) => ({
  date: `${i + 1}`,
  tokens: Math.floor(Math.random() * 50000 + 5000),
  cost: parseFloat((Math.random() * 3.5 + 0.1).toFixed(3)),
}));

const SAMPLE_AGENT_DATA = [
  { name: "FinanceAnalyst", runs: 245, avg_ms: 1850, tokens: 128000 },
  { name: "RiskAssessment", runs: 189, avg_ms: 2100, tokens: 98000 },
  { name: "Retriever",      runs: 421, avg_ms: 450,  tokens: 45000 },
  { name: "Compliance",     runs: 134, avg_ms: 1600, tokens: 87000 },
  { name: "FraudDetection", runs: 98,  avg_ms: 2400, tokens: 112000 },
  { name: "Supervisor",     runs: 380, avg_ms: 950,  tokens: 65000 },
  { name: "Critic",         runs: 350, avg_ms: 780,  tokens: 52000 },
];

export default function AnalyticsPage() {
  const { data: tokenData } = useQuery({
    queryKey: ["analytics", "tokens", 30],
    queryFn: () => analyticsAPI.getTokenUsage(30).then((r) => r.data),
  });

  const { data: agentData } = useQuery({
    queryKey: ["analytics", "agents"],
    queryFn: () => analyticsAPI.getAgentPerformance().then((r) => r.data),
  });

  const tokenChartData = tokenData?.data?.length > 0 ? tokenData.data : SAMPLE_TOKEN_DATA;
  const agentChartData = agentData?.agents?.length > 0 ? agentData.agents.map((a: any) => ({
    name: a.name.replace("Agent", ""),
    runs: a.total_runs,
    avg_ms: a.avg_duration_ms,
    tokens: a.total_tokens,
  })) : SAMPLE_AGENT_DATA;

  const statCards = [
    { label: "Total Tokens", value: tokenData?.total_tokens ? `${(tokenData.total_tokens / 1000).toFixed(1)}K` : "144.2K", icon: Zap, color: "text-blue-400" },
    { label: "Total Cost",   value: `$${tokenData?.total_cost?.toFixed(3) || "9.421"}`,     icon: TrendingUp, color: "text-emerald-400" },
    { label: "Agent Runs",   value: agentChartData.reduce((s: number, a: any) => s + (a.runs || 0), 0) || "1,817", icon: Bot, color: "text-violet-400" },
    { label: "Avg Response", value: `${(agentChartData.reduce((s: number, a: any) => s + (a.avg_ms || 0), 0) / agentChartData.length).toFixed(0)}ms`, icon: Clock, color: "text-amber-400" },
  ];

  return (
    <div className="p-6 space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-foreground">Usage Analytics</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Detailed performance metrics for your AI agent operations</p>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="glass-card"
          >
            <card.icon size={20} className={`${card.color} mb-3`} />
            <div className="text-2xl font-bold text-foreground">{card.value}</div>
            <div className="text-xs text-muted-foreground mt-1">{card.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Token Usage Over Time */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-card">
        <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
          <Zap size={15} className="text-primary" /> Token Usage — Last 30 Days
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={tokenChartData}>
            <defs>
              <linearGradient id="tokenAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="costAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area type="monotone" dataKey="tokens" name="Tokens" stroke="#3b82f6" fill="url(#tokenAreaGrad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Agent Performance */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="glass-card">
        <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
          <Bot size={15} className="text-violet-400" /> Agent Performance Comparison
        </h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={agentChartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis type="number" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={90} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="runs" name="Total Runs" fill="#3b82f6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
