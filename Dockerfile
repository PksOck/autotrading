# Production image for the Next.js standalone server.
# Build:  docker build -t northstar-research .
# Run:    docker run --rm -p 3000:3000 -e NEXT_PUBLIC_SITE_URL=https://example.com northstar-research
FROM node:22-alpine AS deps
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS builder
RUN corepack enable
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
# No public/ directory in this repo yet; re-add `COPY --from=builder /app/public ./public` if static assets are introduced.
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
