import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { knowledgeBaseService } from "@/services/knowledgeBase";
import type { KnowledgeFile } from "@/types";

export function useKnowledgeBase() {
  const queryClient = useQueryClient();

  const {
    data: files = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["knowledge-base", "files"],
    queryFn: knowledgeBaseService.getFiles,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const uploadMutation = useMutation({
    mutationFn: knowledgeBaseService.uploadFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-base", "files"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: knowledgeBaseService.deleteFile,
    onMutate: async (fileId) => {
      await queryClient.cancelQueries({ queryKey: ["knowledge-base", "files"] });

      const previousFiles = queryClient.getQueryData<KnowledgeFile[]>([
        "knowledge-base",
        "files",
      ]);

      queryClient.setQueryData<KnowledgeFile[]>(
        ["knowledge-base", "files"],
        (old) => old?.filter((f) => f.id !== fileId) || []
      );

      return { previousFiles };
    },
    onError: (err, _, context) => {
      if (context?.previousFiles) {
        queryClient.setQueryData(
          ["knowledge-base", "files"],
          context.previousFiles
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-base", "files"] });
    },
  });

  return {
    files,
    isLoading,
    error,
    refetch,

    uploadFile: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,

    deleteFile: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,
  };
}
