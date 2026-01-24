import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsService } from "@/services/settings";
import type { Settings } from "@/types";

export function useSettings() {
  const queryClient = useQueryClient();

  const {
    data: settings,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["settings"],
    queryFn: settingsService.getSettings,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });

  const updateMutation = useMutation({
    mutationFn: settingsService.updateSettings,
    onMutate: async (newSettings) => {
      await queryClient.cancelQueries({ queryKey: ["settings"] });

      const previousSettings = queryClient.getQueryData<Settings>(["settings"]);

      queryClient.setQueryData<Settings>(["settings"], (old) => ({
        ...old,
        ...newSettings,
      }));

      return { previousSettings };
    },
    onError: (err, _, context) => {
      if (context?.previousSettings) {
        queryClient.setQueryData(["settings"], context.previousSettings);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });

  return {
    settings,
    isLoading,
    error,
    refetch,

    updateSettings: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,
  };
}
