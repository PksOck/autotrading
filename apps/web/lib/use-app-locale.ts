"use client";

import { useLocale } from "next-intl";
import type { AppLocale } from "./format";

export const useAppLocale = () => useLocale() as AppLocale;
