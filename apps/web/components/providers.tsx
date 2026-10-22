"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "motion/react";
import { Tooltip } from "radix-ui";
import { useState, type ReactNode } from "react";
import { Toaster } from "sonner";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { staleTime: 15_000, retry: 1 } } }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {/* "user": honour prefers-reduced-motion everywhere (DESIGN.md §8.2). */}
      <MotionConfig reducedMotion="user">
        <Tooltip.Provider delayDuration={300}>
          {children}
          <Toaster
            position="bottom-right"
            toastOptions={{
              style: {
                background: "var(--surface)",
                color: "var(--text)",
                border: "1px solid var(--border)",
                fontFamily: "var(--font-sans)",
              },
            }}
          />
        </Tooltip.Provider>
      </MotionConfig>
    </QueryClientProvider>
  );
}
