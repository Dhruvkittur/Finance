/**
 * FinPilot AI — Documents Redux Slice
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface Document {
  id: string;
  filename: string;
  original_filename: string;
  doc_type: string;
  category?: string;
  title?: string;
  file_size_mb: number;
  status: string;
  chunks_count: number;
  embeddings_generated: boolean;
  page_count?: number;
  summary?: string;
  tags: string[];
  created_at: string;
}

interface ProcessingJob {
  document_id: string;
  filename: string;
  progress: number;
  status: string;
  error?: string;
}

interface DocumentsState {
  documents: Document[];
  selectedDocumentIds: string[];
  processingJobs: ProcessingJob[];
  isUploading: boolean;
  uploadProgress: number;
  isLoading: boolean;
  total: number;
  page: number;
}

const initialState: DocumentsState = {
  documents: [],
  selectedDocumentIds: [],
  processingJobs: [],
  isUploading: false,
  uploadProgress: 0,
  isLoading: false,
  total: 0,
  page: 1,
};

const documentsSlice = createSlice({
  name: "documents",
  initialState,
  reducers: {
    setDocuments(state, action: PayloadAction<{ documents: Document[]; total: number }>) {
      state.documents = action.payload.documents;
      state.total = action.payload.total;
    },
    addDocument(state, action: PayloadAction<Document>) {
      state.documents.unshift(action.payload);
    },
    updateDocumentStatus(state, action: PayloadAction<{ id: string; status: string; chunks_count?: number }>) {
      const doc = state.documents.find((d) => d.id === action.payload.id);
      if (doc) {
        doc.status = action.payload.status;
        if (action.payload.chunks_count !== undefined) {
          doc.chunks_count = action.payload.chunks_count;
        }
      }
    },
    removeDocument(state, action: PayloadAction<string>) {
      state.documents = state.documents.filter((d) => d.id !== action.payload);
      state.selectedDocumentIds = state.selectedDocumentIds.filter((id) => id !== action.payload);
    },
    toggleDocumentSelection(state, action: PayloadAction<string>) {
      const idx = state.selectedDocumentIds.indexOf(action.payload);
      if (idx === -1) {
        state.selectedDocumentIds.push(action.payload);
      } else {
        state.selectedDocumentIds.splice(idx, 1);
      }
    },
    clearSelection(state) {
      state.selectedDocumentIds = [];
    },
    addProcessingJob(state, action: PayloadAction<ProcessingJob>) {
      const existing = state.processingJobs.findIndex((j) => j.document_id === action.payload.document_id);
      if (existing !== -1) {
        state.processingJobs[existing] = action.payload;
      } else {
        state.processingJobs.push(action.payload);
      }
    },
    updateProcessingJob(state, action: PayloadAction<Partial<ProcessingJob> & { document_id: string }>) {
      const job = state.processingJobs.find((j) => j.document_id === action.payload.document_id);
      if (job) {
        Object.assign(job, action.payload);
      }
    },
    removeProcessingJob(state, action: PayloadAction<string>) {
      state.processingJobs = state.processingJobs.filter((j) => j.document_id !== action.payload);
    },
    setUploading(state, action: PayloadAction<boolean>) {
      state.isUploading = action.payload;
      if (!action.payload) state.uploadProgress = 0;
    },
    setUploadProgress(state, action: PayloadAction<number>) {
      state.uploadProgress = action.payload;
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload;
    },
  },
});

export const {
  setDocuments,
  addDocument,
  updateDocumentStatus,
  removeDocument,
  toggleDocumentSelection,
  clearSelection,
  addProcessingJob,
  updateProcessingJob,
  removeProcessingJob,
  setUploading,
  setUploadProgress,
  setLoading,
} = documentsSlice.actions;

export default documentsSlice.reducer;
