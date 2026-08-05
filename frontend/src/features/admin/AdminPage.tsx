/**
 * FinPilot AI — Admin Page
 */

import React from "react";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { Shield, Users, Activity, Database, Clock, CheckCircle, XCircle } from "lucide-react";
import { adminAPI } from "@/lib/api";

export default function AdminPage() {
  const { data: systemStats } = useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => adminAPI.getSystemStats().then((r) => r.data),
  });

  const { data: usersData } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: () => adminAPI.listUsers().then((r) => r.data),
  });

  const { data: auditData } = useQuery({
    queryKey: ["admin", "audit"],
    queryFn: () => adminAPI.getAuditLogs().then((r) => r.data),
  });

  const stats = [
    { label: "Total Users",     value: systemStats?.users ?? "—",        icon: Users,    color: "text-blue-400" },
    { label: "Total Documents", value: systemStats?.documents ?? "—",     icon: Database, color: "text-violet-400" },
    { label: "Chat Sessions",   value: systemStats?.chat_sessions ?? "—", icon: Activity, color: "text-emerald-400" },
    { label: "Cost (Total)",    value: `$${systemStats?.total_cost_usd?.toFixed(2) ?? "0.00"}`, icon: Shield, color: "text-amber-400" },
  ];

  return (
    <div className="p-6 space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-3">
          <Shield size={22} className="text-primary" />
          Administration
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5">System management and audit logs</p>
      </motion.div>

      {/* System Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }} className="glass-card">
            <s.icon size={20} className={`${s.color} mb-3`} />
            <div className="text-2xl font-bold text-foreground">{s.value}</div>
            <div className="text-xs text-muted-foreground mt-1">{s.label}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Users Table */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="glass-card">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <Users size={15} className="text-primary" /> Users ({usersData?.total || 0})
          </h3>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {(usersData?.users || []).slice(0, 10).map((user: any) => (
              <div key={user.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-secondary/50 transition-colors">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                  {user.full_name?.[0]?.toUpperCase() || "U"}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-foreground truncate">{user.full_name}</div>
                  <div className="text-[10px] text-muted-foreground">{user.email}</div>
                </div>
                <span className={`status-badge ${user.status === "active" ? "success" : "danger"}`}>
                  {user.role}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Audit Log */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-card">
          <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <Activity size={15} className="text-amber-400" /> Audit Log
          </h3>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {(auditData?.logs || []).slice(0, 15).map((log: any) => (
              <div key={log.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-secondary/50 transition-colors">
                {log.success ? <CheckCircle size={12} className="text-emerald-400 mt-0.5" /> : <XCircle size={12} className="text-red-400 mt-0.5" />}
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-foreground">{log.action}</div>
                  <div className="text-[10px] text-muted-foreground">{log.resource_type} • {log.ip_address}</div>
                </div>
                <div className="text-[10px] text-muted-foreground flex items-center gap-1 flex-shrink-0">
                  <Clock size={9} />
                  {new Date(log.created_at).toLocaleTimeString()}
                </div>
              </div>
            ))}
            {(!auditData?.logs || auditData.logs.length === 0) && (
              <div className="text-center py-8 text-muted-foreground text-sm">No audit logs found</div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
