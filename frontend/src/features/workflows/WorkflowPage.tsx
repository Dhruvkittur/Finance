/**
 * FinPilot AI — Workflow Builder
 * ================================
 * Visual drag-and-drop pipeline builder using React Flow (@xyflow/react).
 */

import React, { useCallback, useState } from "react";
import { motion } from "framer-motion";
import {
  ReactFlow, Background, Controls, MiniMap, addEdge, useNodesState,
  useEdgesState, Connection, Edge, Node, BackgroundVariant,
  Handle, Position, NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Save, Play, Plus, Zap, Bot, GitBranch, Mail, Database, Download,
  AlertTriangle, Loader2,
} from "lucide-react";
import { workflowsAPI } from "@/lib/api";

// ── Custom Node Types ─────────────────────────────────────────────────────────

function WorkflowNode({ data, type }: { data: any; type: string }) {
  const nodeStyles: Record<string, { bg: string; border: string; icon: string; label: string }> = {
    trigger:    { bg: "bg-amber-500/20",  border: "border-amber-500/30",  icon: "⚡", label: "Trigger" },
    agent:      { bg: "bg-blue-500/20",   border: "border-blue-500/30",   icon: "🤖", label: "AI Agent" },
    condition:  { bg: "bg-violet-500/20", border: "border-violet-500/30", icon: "🔀", label: "Condition" },
    approval:   { bg: "bg-green-500/20",  border: "border-green-500/30",  icon: "✅", label: "Approval" },
    email:      { bg: "bg-pink-500/20",   border: "border-pink-500/30",   icon: "📧", label: "Email" },
    database:   { bg: "bg-teal-500/20",   border: "border-teal-500/30",   icon: "🗄️", label: "Database" },
    export:     { bg: "bg-indigo-500/20", border: "border-indigo-500/30", icon: "📤", label: "Export" },
  };

  const style = nodeStyles[type] || nodeStyles.agent;

  return (
    <div className={`min-w-32 rounded-xl border ${style.bg} ${style.border} p-3 shadow-lg backdrop-blur-sm`}>
      <Handle type="target" position={Position.Top} className="!bg-border !border-border" />
      <div className="flex items-center gap-2">
        <span className="text-lg">{style.icon}</span>
        <div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{style.label}</div>
          <div className="text-xs font-semibold text-foreground">{data.label}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-border !border-border" />
    </div>
  );
}

const nodeTypes: NodeTypes = {
  trigger:   (props) => <WorkflowNode {...props} type="trigger" />,
  agent:     (props) => <WorkflowNode {...props} type="agent" />,
  condition: (props) => <WorkflowNode {...props} type="condition" />,
  approval:  (props) => <WorkflowNode {...props} type="approval" />,
  email:     (props) => <WorkflowNode {...props} type="email" />,
  database:  (props) => <WorkflowNode {...props} type="database" />,
  export:    (props) => <WorkflowNode {...props} type="export" />,
};

// ── Default workflow template ─────────────────────────────────────────────────

const DEFAULT_NODES: Node[] = [
  { id: "1", type: "trigger",   position: { x: 300, y: 50 },  data: { label: "Document Upload" } },
  { id: "2", type: "agent",     position: { x: 200, y: 170 }, data: { label: "Document Agent" } },
  { id: "3", type: "agent",     position: { x: 400, y: 170 }, data: { label: "Finance Analyst" } },
  { id: "4", type: "agent",     position: { x: 300, y: 290 }, data: { label: "Risk Assessment" } },
  { id: "5", type: "condition", position: { x: 300, y: 410 }, data: { label: "Risk > 70?" } },
  { id: "6", type: "approval",  position: { x: 150, y: 530 }, data: { label: "Manager Approval" } },
  { id: "7", type: "agent",     position: { x: 450, y: 530 }, data: { label: "Report Generator" } },
  { id: "8", type: "email",     position: { x: 300, y: 650 }, data: { label: "Send Report" } },
];

const DEFAULT_EDGES: Edge[] = [
  { id: "e1-2", source: "1", target: "2", animated: true },
  { id: "e1-3", source: "1", target: "3", animated: true },
  { id: "e2-4", source: "2", target: "4" },
  { id: "e3-4", source: "3", target: "4" },
  { id: "e4-5", source: "4", target: "5" },
  { id: "e5-6", source: "5", target: "6", label: "High Risk", style: { stroke: "#ef4444" } },
  { id: "e5-7", source: "5", target: "7", label: "OK", style: { stroke: "#10b981" } },
  { id: "e6-8", source: "6", target: "8" },
  { id: "e7-8", source: "7", target: "8" },
];

// ── Node Palette ──────────────────────────────────────────────────────────────

const NODE_PALETTE = [
  { type: "trigger", label: "Trigger", icon: "⚡" },
  { type: "agent", label: "AI Agent", icon: "🤖" },
  { type: "condition", label: "Condition", icon: "🔀" },
  { type: "approval", label: "Approval", icon: "✅" },
  { type: "email", label: "Email", icon: "📧" },
  { type: "database", label: "Database", icon: "🗄️" },
  { type: "export", label: "Export", icon: "📤" },
];

// ── Workflow Page ─────────────────────────────────────────────────────────────

export default function WorkflowPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState(DEFAULT_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(DEFAULT_EDGES);
  const [workflowName, setWorkflowName] = useState("Financial Document Pipeline");
  const [isSaving, setIsSaving] = useState(false);
  const queryClient = useQueryClient();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  );

  const addNode = (type: string, label: string) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: { label },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const saveWorkflow = async () => {
    setIsSaving(true);
    try {
      await workflowsAPI.create({
        name: workflowName,
        nodes: nodes.map(({ id, type, position, data }) => ({ id, type, position, data })),
        edges: edges.map(({ id, source, target, label, animated }) => ({ id, source, target, label, animated })),
      });
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex h-full">
      {/* Left Palette */}
      <div className="w-56 flex-shrink-0 border-r border-border bg-card p-4">
        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Add Nodes
        </div>
        <div className="space-y-2">
          {NODE_PALETTE.map((node) => (
            <motion.button
              key={node.type}
              whileHover={{ x: 3 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => addNode(node.type, node.label)}
              className="w-full flex items-center gap-3 p-2.5 rounded-lg bg-secondary hover:bg-secondary/80 border border-border text-sm text-foreground transition-all"
            >
              <span className="text-lg">{node.icon}</span>
              <span>{node.label}</span>
            </motion.button>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-border space-y-2">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            Workflow
          </div>
          <input
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs text-foreground outline-none focus:border-primary"
            placeholder="Workflow name..."
          />
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={saveWorkflow}
            disabled={isSaving}
            className="w-full flex items-center justify-center gap-2 py-2 bg-primary rounded-lg text-primary-foreground text-xs font-medium"
          >
            {isSaving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
            Save Workflow
          </motion.button>
          <button className="w-full flex items-center justify-center gap-2 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-emerald-400 text-xs font-medium hover:bg-emerald-500/30 transition-colors">
            <Play size={12} />
            Run
          </button>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 bg-background">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          className="bg-background"
        >
          <Background variant={BackgroundVariant.Dots} color="rgba(59,130,246,0.15)" gap={24} size={1.5} />
          <Controls className="!bg-card !border-border" />
          <MiniMap
            className="!bg-card !border-border"
            nodeColor="#1e293b"
            maskColor="rgba(0,0,0,0.5)"
          />
        </ReactFlow>
      </div>
    </div>
  );
}
