/**
 * FinPilot AI — Documents Page
 * ==============================
 * Drag-and-drop file upload with real-time processing status,
 * document library, and semantic search.
 */

import React, { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { useDispatch, useSelector } from "react-redux";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload, FileText, File, X, Search, Filter, Trash2,
  CheckCircle, Clock, AlertCircle, Loader2, Eye, Download,
  ChevronDown, RefreshCw, Database, Zap,
} from "lucide-react";

import { RootState } from "@/app/store";
import { addDocument, updateDocumentStatus, removeDocument, setUploading, setUploadProgress } from "@/app/slices/documentsSlice";
import { documentsAPI } from "@/lib/api";

// ── Document Status Indicator ─────────────────────────────────────────────────

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "processed":
      return <CheckCircle size={14} className="text-emerald-400" />;
    case "processing":
      return <Loader2 size={14} className="text-blue-400 animate-spin" />;
    case "pending":
      return <Clock size={14} className="text-amber-400" />;
    case "failed":
      return <AlertCircle size={14} className="text-red-400" />;
    default:
      return <Clock size={14} className="text-muted-foreground" />;
  }
}

// ── File Type Icon ────────────────────────────────────────────────────────────

function FileIcon({ docType }: { docType: string }) {
  const icons: Record<string, string> = {
    pdf: "📄", docx: "📝", pptx: "📊", xlsx: "📈",
    csv: "📋", txt: "📃", image: "🖼️",
  };
  return <span className="text-xl">{icons[docType] || "📁"}</span>;
}

// ── Document Card ─────────────────────────────────────────────────────────────

function DocumentCard({ doc, onDelete }: { doc: any; onDelete: (id: string) => void }) {
  const statusColors: Record<string, string> = {
    processed: "success", processing: "info", pending: "warning", failed: "danger",
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ y: -2 }}
      className="glass-card group relative"
    >
      {/* Delete button */}
      <button
        onClick={() => onDelete(doc.id)}
        className="absolute top-3 right-3 w-6 h-6 rounded-md flex items-center justify-center text-muted-foreground hover:text-red-400 hover:bg-red-400/10 opacity-0 group-hover:opacity-100 transition-all"
      >
        <Trash2 size={12} />
      </button>

      <div className="flex items-start gap-3 mb-3">
        <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center flex-shrink-0">
          <FileIcon docType={doc.doc_type} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-foreground truncate" title={doc.original_filename}>
            {doc.title || doc.original_filename}
          </div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {doc.file_size_mb}MB • {doc.doc_type?.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-2 mb-3">
        <StatusIcon status={doc.status} />
        <span className={`status-badge ${statusColors[doc.status] || "info"}`}>
          {doc.status}
        </span>
        {doc.chunks_count > 0 && (
          <span className="text-[10px] text-muted-foreground ml-auto">
            {doc.chunks_count} chunks
          </span>
        )}
      </div>

      {/* Progress bar for processing */}
      {doc.status === "processing" && (
        <div className="progress-bar mb-3">
          <motion.div
            className="progress-fill"
            animate={{ width: ["30%", "70%", "50%"] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </div>
      )}

      {/* Stats */}
      {doc.status === "processed" && (
        <div className="flex gap-3 text-[10px] text-muted-foreground">
          {doc.page_count && <span>{doc.page_count}p</span>}
          {doc.embeddings_generated && (
            <span className="flex items-center gap-0.5">
              <Zap size={9} className="text-primary" />
              Indexed
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
}

// ── Upload Zone ───────────────────────────────────────────────────────────────

function UploadZone({ onUpload }: { onUpload: (files: File[]) => void }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onUpload,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
      "text/csv": [".csv"],
      "text/plain": [".txt"],
      "image/*": [".png", ".jpg", ".jpeg", ".tiff"],
    },
    multiple: true,
  });

  return (
    <motion.div
      {...(getRootProps() as any)}
      whileHover={{ scale: 1.005 }}
      animate={isDragActive ? { scale: 1.02, borderColor: "#3b82f6" } : { scale: 1 }}
      className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
        isDragActive
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary/50 hover:bg-secondary/30"
      }`}
    >
      <input {...getInputProps()} />

      <motion.div
        animate={isDragActive ? { y: -8 } : { y: 0 }}
        className="flex flex-col items-center gap-4"
      >
        <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl ${
          isDragActive ? "bg-primary/20" : "bg-secondary"
        }`}>
          {isDragActive ? "🎯" : <Upload className="text-muted-foreground" size={28} />}
        </div>

        <div>
          <p className="text-base font-semibold text-foreground">
            {isDragActive ? "Drop your files here" : "Upload Financial Documents"}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            Drag & drop or click to browse
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            PDF, DOCX, PPTX, Excel, CSV, TXT, Images • Max 50MB each
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ── Documents Page ────────────────────────────────────────────────────────────

export default function DocumentsPage() {
  const dispatch = useDispatch();
  const queryClient = useQueryClient();
  const { isUploading, uploadProgress } = useSelector((s: RootState) => s.documents);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentsAPI.list().then((r) => r.data),
    refetchInterval: 5000, // Poll for status updates
  });

  const documents = (data?.documents || []).filter((doc: any) => {
    const matchesSearch = !search || doc.original_filename.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || doc.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsAPI.delete(id),
    onSuccess: (_, id) => {
      dispatch(removeDocument(id));
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const handleUpload = async (files: File[]) => {
    dispatch(setUploading(true));

    for (const file of files) {
      try {
        dispatch(setUploadProgress(0));
        const res = await documentsAPI.upload(file, (pct) => {
          dispatch(setUploadProgress(pct));
        });
        dispatch(addDocument(res.data));
        queryClient.invalidateQueries({ queryKey: ["documents"] });
      } catch (err) {
        console.error("Upload failed:", err);
      }
    }

    dispatch(setUploading(false));
    dispatch(setUploadProgress(0));
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-foreground">Document Intelligence</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {data?.total || 0} documents • AI-powered processing and semantic search
          </p>
        </div>

        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => refetch()}
            className="flex items-center gap-2 px-3 py-2 bg-secondary rounded-lg text-xs text-muted-foreground hover:text-foreground border border-border"
          >
            <RefreshCw size={12} />
          </motion.button>
          <div className="flex items-center gap-2 px-3 py-2 glass rounded-lg border border-border text-xs text-muted-foreground">
            <Database size={12} />
            <span>{(data?.documents || []).filter((d: any) => d.embeddings_generated).length} indexed</span>
          </div>
        </div>
      </motion.div>

      {/* Upload Zone */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <UploadZone onUpload={handleUpload} />
      </motion.div>

      {/* Upload Progress */}
      <AnimatePresence>
        {isUploading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="glass rounded-xl p-4"
          >
            <div className="flex items-center gap-3 mb-2">
              <Loader2 size={14} className="text-primary animate-spin" />
              <span className="text-sm text-foreground">Uploading and processing...</span>
              <span className="ml-auto text-sm text-primary font-medium">{uploadProgress}%</span>
            </div>
            <div className="progress-bar">
              <motion.div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search + Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents..."
            className="w-full bg-secondary border border-border rounded-lg pl-9 pr-4 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
          />
        </div>

        {["all", "processed", "processing", "pending", "failed"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              statusFilter === s
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-muted-foreground hover:text-foreground border border-border"
            }`}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Document Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-36 rounded-xl bg-secondary animate-pulse" />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="text-4xl mb-4">📁</div>
          <p className="text-foreground font-medium">No documents found</p>
          <p className="text-muted-foreground text-sm mt-1">
            Upload financial documents to get started
          </p>
        </motion.div>
      ) : (
        <motion.div
          layout
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
        >
          <AnimatePresence>
            {documents.map((doc: any) => (
              <DocumentCard
                key={doc.id}
                doc={doc}
                onDelete={(id) => deleteMutation.mutate(id)}
              />
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  );
}
