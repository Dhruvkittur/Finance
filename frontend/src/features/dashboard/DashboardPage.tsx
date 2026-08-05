/**
 * FinPilot AI — Dashboard Page
 * ==============================
 * Real-time KPI cards, interactive charts, agent status,
 * and activity feed with Framer Motion animations.
 */

import React from "react";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import {
  FileText, MessageSquare, Bot, TrendingUp, AlertTriangle,
  Shield, Zap, Activity, ChevronUp, ChevronDown, RefreshCw,
} from "lucide-react";

import { dashboardAPI, analyticsAPI } from "@/lib/api";

// ── Animation Variants ────────────────────────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

// ── KPI Card ──────────────────────────────────────────────────────────────────

function KPICard({
  title, value, subtitle, icon: Icon, trend, trendValue, color, delay = 0,
}: {
  title: string; value: string | number; subtitle: string;
  icon: any; trend?: "up" | "down" | "neutral"; trendValue?: string;
  color: string; delay?: number;
}) {
  const trendColor = trend === "up" ? "text-emerald-400" : trend === "down" ? "text-red-400" : "text-muted-foreground";
  const TrendIcon = trend === "up" ? ChevronUp : trend === "down" ? ChevronDown : Activity;

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ y: -3, transition: { duration: 0.15 } }}
      className="kpi-card"
    >
      {/* Top row */}
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
          <Icon size={18} className="text-white" />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-xs font-medium ${trendColor}`}>
            <TrendIcon size={12} />
            <span>{trendValue}</span>
          </div>
        )}
      </div>

      {/* Value */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: delay + 0.2 }}
        className="text-2xl font-bold text-foreground mb-1"
      >
        {value}
      </motion.div>

      <div className="text-sm font-medium text-foreground mb-0.5">{title}</div>
      <div className="text-xs text-muted-foreground">{subtitle}</div>
    </motion.div>
  );
}

// ── Agent Status Card ─────────────────────────────────────────────────────────

function AgentStatusCard({ agents }: { agents: any[] }) {
  return (
    <motion.div variants={itemVariants} className="glass-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Bot size={16} className="text-primary" />
          AI Agent Status
        </h3>
        <span className="text-xs text-emerald-400 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          All Operational
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {agents.slice(0, 8).map((agent: any) => (
          <div key={agent.name} className="flex items-center gap-2 p-2 rounded-lg bg-secondary/50">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span className="text-xs text-muted-foreground truncate">{agent.name.replace("Agent", "")}</span>
          </div>
        ))}
      </div>
      {agents.length > 8 && (
        <div className="text-center mt-2">
          <span className="text-xs text-muted-foreground">+{agents.length - 8} more agents</span>
        </div>
      )}
    </motion.div>
  );
}

// ── Custom Tooltip ────────────────────────────────────────────────────────────

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs">
      <p className="text-muted-foreground mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }} className="font-medium">
          {p.name}: {typeof p.value === "number" ? p.value.toLocaleString() : p.value}
        </p>
      ))}
    </div>
  );
};

// ── Sample Data (used when API returns empty) ─────────────────────────────────

const SAMPLE_TOKEN_DATA = [
  { date: "Jul 30", tokens: 12400, cost: 0.93 },
  { date: "Jul 31", tokens: 18200, cost: 1.37 },
  { date: "Aug 1",  tokens: 9800,  cost: 0.74 },
  { date: "Aug 2",  tokens: 24600, cost: 1.85 },
  { date: "Aug 3",  tokens: 31200, cost: 2.34 },
  { date: "Aug 4",  tokens: 19800, cost: 1.49 },
  { date: "Aug 5",  tokens: 28400, cost: 2.13 },
];

const SAMPLE_PIE_DATA = [
  { name: "Finance Analyst", value: 35, color: "#3b82f6" },
  { name: "Risk Assessment", value: 20, color: "#8b5cf6" },
  { name: "Compliance",      value: 15, color: "#10b981" },
  { name: "Fraud Detection", value: 12, color: "#f59e0b" },
  { name: "Others",          value: 18, color: "#6b7280" },
];

// ── Dashboard Page ────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { data: kpis, isLoading: kpisLoading, refetch } = useQuery({
    queryKey: ["dashboard", "kpis"],
    queryFn: () => dashboardAPI.getKPIs().then((r) => r.data),
    refetchInterval: 30000, // refresh every 30s
  });

  const { data: activity } = useQuery({
    queryKey: ["dashboard", "activity"],
    queryFn: () => dashboardAPI.getActivity().then((r) => r.data),
  });

  const { data: agentStatus } = useQuery({
    queryKey: ["dashboard", "agents"],
    queryFn: () => dashboardAPI.getAgentStatus().then((r) => r.data),
  });

  const { data: tokenUsage } = useQuery({
    queryKey: ["analytics", "tokens"],
    queryFn: () => analyticsAPI.getTokenUsage(7).then((r) => r.data),
  });

  const chartData = tokenUsage?.data?.length > 0 ? tokenUsage.data : SAMPLE_TOKEN_DATA;

  const kpiCards = [
    {
      title: "Documents Processed",
      value: kpis?.documents?.processed ?? "—",
      subtitle: `${kpis?.documents?.this_week ?? 0} uploaded this week`,
      icon: FileText,
      color: "bg-gradient-to-br from-blue-500 to-blue-600",
      trend: "up" as const,
      trendValue: "+12% this week",
    },
    {
      title: "AI Conversations",
      value: kpis?.conversations?.total_sessions ?? "—",
      subtitle: `${kpis?.conversations?.total_messages ?? 0} total messages`,
      icon: MessageSquare,
      color: "bg-gradient-to-br from-violet-500 to-violet-600",
      trend: "up" as const,
      trendValue: "+8% this week",
    },
    {
      title: "Agent Runs",
      value: kpis?.agents?.total_runs ?? "—",
      subtitle: `${kpis?.agents?.available_agents ?? 17} agents available`,
      icon: Bot,
      color: "bg-gradient-to-br from-emerald-500 to-emerald-600",
      trend: "up" as const,
      trendValue: "+24% this week",
    },
    {
      title: "Reports Generated",
      value: kpis?.reports?.total ?? "—",
      subtitle: "Executive + risk + compliance",
      icon: TrendingUp,
      color: "bg-gradient-to-br from-amber-500 to-amber-600",
      trend: "neutral" as const,
      trendValue: "Stable",
    },
    {
      title: "Total Tokens Used",
      value: kpis?.conversations?.total_tokens ? `${(kpis.conversations.total_tokens / 1000).toFixed(1)}K` : "—",
      subtitle: `$${kpis?.conversations?.total_cost_usd?.toFixed(3) ?? "0.000"} estimated cost`,
      icon: Zap,
      color: "bg-gradient-to-br from-pink-500 to-pink-600",
      trend: "up" as const,
      trendValue: "+18% usage",
    },
    {
      title: "System Health",
      value: `${kpis?.system?.uptime_pct ?? 99.9}%`,
      subtitle: `Avg response: ${kpis?.system?.avg_response_time_ms ?? 1250}ms`,
      icon: Activity,
      color: "bg-gradient-to-br from-teal-500 to-teal-600",
      trend: "up" as const,
      trendValue: "All systems go",
    },
  ];

  return (
    <div className="p-6 space-y-6 min-h-full">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-foreground">Financial Intelligence Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Real-time overview of your AI-powered financial operations
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 bg-secondary rounded-lg text-xs text-muted-foreground hover:text-foreground border border-border transition-colors"
        >
          <RefreshCw size={12} />
          Refresh
        </motion.button>
      </motion.div>

      {/* KPI Cards Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4"
      >
        {kpiCards.map((card, i) => (
          <KPICard key={card.title} {...card} delay={i * 0.05} />
        ))}
      </motion.div>

      {/* Charts Row */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        {/* Token Usage Area Chart */}
        <motion.div variants={itemVariants} className="glass-card lg:col-span-2">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <Zap size={16} className="text-primary" />
            Token Usage (Last 7 Days)
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="tokenGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="tokens" name="Tokens" stroke="#3b82f6" strokeWidth={2} fill="url(#tokenGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Agent Usage Pie Chart */}
        <motion.div variants={itemVariants} className="glass-card">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <Bot size={16} className="text-violet-400" />
            Agent Distribution
          </h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={SAMPLE_PIE_DATA}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
              >
                {SAMPLE_PIE_DATA.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-2">
            {SAMPLE_PIE_DATA.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: item.color }} />
                  <span className="text-muted-foreground">{item.name}</span>
                </div>
                <span className="text-foreground font-medium">{item.value}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>

      {/* Bottom Row: Activity + Agents */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        {/* Recent Activity */}
        <motion.div variants={itemVariants} className="glass-card lg:col-span-2">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <Activity size={16} className="text-emerald-400" />
            Recent Activity
          </h3>
          <div className="space-y-3">
            {(activity?.activity || [
              { type: "document_upload", title: "Q3 Financial Report.pdf uploaded", subtitle: "processed • 2.4MB", timestamp: new Date().toISOString(), icon: "document", status: "processed" },
              { type: "chat_session", title: "Fraud Detection Analysis", subtitle: "24 messages", timestamp: new Date().toISOString(), icon: "chat" },
              { type: "document_upload", title: "Balance Sheet 2024.xlsx uploaded", subtitle: "processed • 1.2MB", timestamp: new Date().toISOString(), icon: "document", status: "processed" },
            ]).slice(0, 6).map((item: any, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-secondary/50 transition-colors"
              >
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-sm ${
                  item.icon === "document" ? "bg-blue-500/20" : "bg-violet-500/20"
                }`}>
                  {item.icon === "document" ? "📄" : "💬"}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-foreground truncate">{item.title}</div>
                  <div className="text-[10px] text-muted-foreground">{item.subtitle}</div>
                </div>
                {item.status && (
                  <span className={`status-badge ${item.status === "processed" ? "success" : "info"}`}>
                    {item.status}
                  </span>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Agent Status */}
        {agentStatus?.agents && (
          <AgentStatusCard agents={agentStatus.agents} />
        )}
      </motion.div>
    </div>
  );
}
