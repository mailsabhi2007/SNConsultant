import { useCallback, useState } from "react";
import {
  CloudUpload,
  FileText,
  FileType,
  FileCode,
  File,
  Trash2,
  FolderPlus,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useKnowledgeBase } from "@/hooks/useKnowledgeBase";
import { formatFileSize, formatDate } from "@/lib/utils";
import { toast } from "sonner";

const fileTypeIcons: Record<string, React.ElementType> = {
  pdf: FileText,
  txt: FileType,
  md: FileCode,
  docx: File,
  doc: File,
};

const fileTypeColors: Record<string, string> = {
  pdf: "bg-destructive/15 text-destructive",
  txt: "bg-primary/15 text-primary",
  md: "bg-agent-architect/15 text-agent-architect",
  docx: "bg-agent-consultant/15 text-agent-consultant",
  doc: "bg-agent-consultant/15 text-agent-consultant",
};

function getFileExtension(filename: string): string {
  return filename.split(".").pop()?.toLowerCase() ?? "txt";
}

export function KnowledgeBasePage() {
  const {
    files,
    isLoading,
    uploadFile,
    isUploading,
    deleteFile,
    isDeleting,
  } = useKnowledgeBase();

  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadStep, setUploadStep] = useState("");

  const simulateProgress = () => {
    setUploadProgress(0);
    setUploadStep("Extracting text...");
    const steps = [
      { progress: 30, step: "Extracting text..." },
      { progress: 60, step: "Chunking..." },
      { progress: 90, step: "Creating embeddings..." },
      { progress: 100, step: "Complete" },
    ];
    steps.forEach((s, i) => {
      setTimeout(() => {
        setUploadProgress(s.progress);
        setUploadStep(s.step);
        if (s.progress === 100) {
          setTimeout(() => {
            setUploadProgress(null);
            setUploadStep("");
          }, 800);
        }
      }, (i + 1) * 1000);
    });
  };

  const handleFileUpload = useCallback(
    async (file: File) => {
      simulateProgress();
      try {
        await uploadFile(file);
        toast.success(`${file.name} uploaded successfully`);
      } catch {
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
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFileUpload(file);
    },
    [handleFileUpload]
  );

  const handleDelete = async (fileId: string, filename: string) => {
    try {
      deleteFile(fileId);
      toast.success(`${filename} deleted`);
    } catch {
      toast.error("Failed to delete file");
    }
  };

  const totalChunks = files.reduce((sum, f) => sum + (f.chunk_count ?? 0), 0);

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="px-6 py-6 max-w-5xl mx-auto w-full">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <FolderPlus className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold text-foreground">Knowledge Base</h1>
          </div>
          <p className="text-sm text-muted-foreground">
            Upload internal documents to enhance AI responses
          </p>
          <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
            <span>{files.length} {files.length === 1 ? "file" : "files"}</span>
            <span>·</span>
            <span>{totalChunks} chunks</span>
          </div>
        </div>

        {/* Upload zone */}
        <label
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={cn(
            "mb-6 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed transition-all h-48 backdrop-blur-xl",
            isDragging || isUploading
              ? "border-primary bg-primary/10 shadow-[inset_0_0_40px_0_rgba(148,197,233,0.06),0_0_0_1px_rgba(148,197,233,0.2)]"
              : "border-white/[0.08] bg-card/15 hover:border-primary/30 hover:bg-card/25 hover:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)]"
          )}
        >
          <input
            type="file"
            className="sr-only"
            onChange={handleInputChange}
            disabled={isUploading}
            accept=".txt,.pdf,.md,.doc,.docx"
          />
          <CloudUpload
            className={cn(
              "h-10 w-10 mb-3",
              isDragging ? "text-primary animate-float" : "text-muted-foreground animate-float"
            )}
          />
          <p className="text-sm font-medium text-foreground">
            {isUploading ? "Uploading..." : "Drag & drop files here"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">or click to browse</p>
          <div className="mt-3 flex items-center gap-2">
            {["PDF", "TXT", "MD", "DOCX"].map((fmt) => (
              <Badge key={fmt} variant="secondary" className="text-[10px] border-0">
                {fmt}
              </Badge>
            ))}
          </div>
        </label>

        {/* Upload progress */}
        {uploadProgress !== null && (
          <div className="mb-6 rounded-xl glass-glow p-4 animate-border-glow">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-foreground">Uploading...</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">{uploadStep}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-muted-foreground"
                  onClick={() => setUploadProgress(null)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <Progress value={uploadProgress} className="h-2" />
            <p className="mt-1 text-right text-[11px] text-muted-foreground">{uploadProgress}%</p>
          </div>
        )}

        {/* File grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-xl glass p-4 h-28 animate-pulse" />
            ))}
          </div>
        ) : files.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <FolderPlus className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <p className="text-sm font-medium text-muted-foreground">No documents yet</p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Upload your first document to get started
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {files.map((file) => {
              const ext = getFileExtension(file.filename);
              const Icon = fileTypeIcons[ext] ?? File;
              const colorClass = fileTypeColors[ext] ?? "bg-muted text-muted-foreground";
              return (
                <div
                  key={file.id}
                  className="group relative rounded-xl glass p-4 transition-all hover:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1),0_8px_32px_-8px_rgba(0,0,0,0.4)] hover:border-white/[0.15] hover:-translate-y-0.5"
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={cn(
                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                        colorClass
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate" title={file.filename}>
                        {file.filename}
                      </p>
                      <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                        <span>{formatFileSize(file.file_size)}</span>
                        <span>·</span>
                        <span>{file.chunk_count} chunks</span>
                      </div>
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-[11px] text-muted-foreground">
                          {formatDate(file.created_at)}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span className="h-1.5 w-1.5 rounded-full bg-agent-implementation" />
                          <span className="text-[10px] text-agent-implementation">Indexed</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-2 right-2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
                    onClick={() => handleDelete(file.id, file.filename)}
                    disabled={isDeleting}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
