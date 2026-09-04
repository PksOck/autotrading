import { z } from "zod";

export const paperOrderSchema = z.object({
  symbol: z.string().trim().min(1),
  side: z.enum(["buy", "sell"]),
  quantity: z.number().finite().positive(),
  limitPrice: z.number().finite().positive().nullable().default(null),
  idempotencyKey: z.string().trim().min(1).default(() => crypto.randomUUID()),
});

export type PaperOrder = z.infer<typeof paperOrderSchema>;

export function parsePaperOrder(input: unknown): PaperOrder {
  return paperOrderSchema.parse(input);
}
