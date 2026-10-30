"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

export type BacktestRequest = components["schemas"]["BacktestRequest-Input"];
export type BacktestOut = components["schemas"]["BacktestOut"];

export const useBacktest = () =>
  useMutation({
    mutationFn: (request: BacktestRequest) => api.send<BacktestOut>("/backtest", "POST", request),
  });
