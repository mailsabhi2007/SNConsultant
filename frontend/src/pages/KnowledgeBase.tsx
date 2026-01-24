import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, Trash2, Loader2, FolderOpen, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/common/EmptyState";
import { useKnowledgeBase } from "@/hooks/useKnowledgeBase";
import { formatFileSize, formatDate } from "@/lib/utils";
import { toast } from "sonner";

export function KnowledgeBasePage() {
  const {
    files,
    isLoading,
    uploadFile,
    isUploading,
    deleteFile,
    isDeleting,
  } = useKnowledgeBase();

  const [dragActive, setDragActive] = useState(false);

  const handleFileUpload = useCallback(
    async (file: File) => {
      try {
        await uploadFile(file);
        toast.success(`${file.name} uploaded successfully`);
      } catch (error) {
        toast.error("Failed to upload file");
      }
    },
    [uploadFile]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
      e.target.value = "";
    }
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);

      const file = e.dataTransfer.files?.[0];
      if (file) {
        handleFileUpload(file);
      }
    },
    [handleFileUpload]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  const handleDelete = async (fileId: string, filename: string) => {
    try {
      deleteFile(fileId);
      toast.success(`${filename} deleted`);
    } catch (error) {
      toast.error("Failed to delete file");
    }
  };

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Knowledge Base</h1>
        <p className="mt-1 text-muted-foreground">
          Upload documents to enhance the AI's responses with your knowledge.
        </p>
      </div>

      {/* Upload area */}
      <Card className="mb-8">
        <CardContent className="pt-6">
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
              dragActive
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-muted-foreground/50"
            }`}
          >
            <input
              type="file"
              id="file-upload"
              className="absolute inset-0 cursor-pointer opacity-0"
              onChange={handleInputChange}
              disabled={isUploading}
              accept=".txt,.pdf,.md,.doc,.docx"
            />

            {isUploading ? (
              <Loader2 className="h-10 w-10 animate-spin text-primary" />
            ) : (
              <Upload className="h-10 w-10 text-muted-foreground" />
            )}

            <p className="mt-4 text-center text-sm font-medium">
              {isUploading ? "Uploading..." : "Drop a file here or click to upload"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Supports TXT, PDF, MD, DOC, DOCX files
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Files list */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Uploaded Files</CardTitle>
          <CardDescription>
            {files.length} {files.length === 1 ? "file" : "files"} in your knowledge base
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : files.length === 0 ? (
            <EmptyState
              icon={FolderOpen}
              title="No files uploaded"
              description="Upload documents to build your knowledge base"
              className="py-8"
            />
          ) : (
            <div className="space-y-2">
              <AnimatePresence initial={false}>
                {files.map((file) => (
                  <motion.div
                    key={file.id}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.15 }}
                    className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                        <FileText className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="font-medium">{file.filename}</p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{formatFileSize(file.file_size)}</span>
                          <span>•</span>
                          <span>{file.chunk_count} chunks</span>
                          <span>•</span>
                          <span>{formatDate(file.created_at)}</span>
                        </div>
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(file.id, file.filename)}
                      disabled={isDeleting}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
