import api from "./api";
import type { KnowledgeFile } from "@/types";

interface ApiFile {
  doc_id: number;
  filename: string;
  file_type?: string | null;
  file_size: number;
  uploaded_at: string;
  chunk_count: number;
}

function transformFile(file: ApiFile): KnowledgeFile {
  return {
    id: String(file.doc_id),
    filename: file.filename,
    file_size: file.file_size,
    chunk_count: file.chunk_count,
    created_at: file.uploaded_at,
    user_id: "",
  };
}

export const knowledgeBaseService = {
  async uploadFile(file: File): Promise<KnowledgeFile> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post<ApiFile>("/api/kb/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    return transformFile(response.data);
  },

  async getFiles(): Promise<KnowledgeFile[]> {
    const response = await api.get<ApiFile[]>("/api/kb/files");
    return response.data.map(transformFile);
  },

  async deleteFile(fileId: string): Promise<void> {
    await api.delete(`/api/kb/files/${fileId}`);
  },
};

// Legacy exports for backward compatibility
export const uploadFile = knowledgeBaseService.uploadFile;
export const listFiles = knowledgeBaseService.getFiles;
export const deleteFile = (docId: number) =>
  knowledgeBaseService.deleteFile(String(docId));
