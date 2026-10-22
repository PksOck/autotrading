"use client";

import { motion } from "motion/react";
import type { ReactNode } from "react";
import { duration, ease } from "@/lib/motion";

/** MO-07: page content fades and rises 8 px on navigation; header and menu stay still. */
export default function Template({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: duration.slow, ease: ease.standard }}
    >
      {children}
    </motion.div>
  );
}
