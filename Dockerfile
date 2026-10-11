# syntax=docker/dockerfile:1

# ============================================================
# Stage 1 — Dependencies
# ============================================================
FROM node:24-alpine AS deps

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile


# ============================================================
# Stage 2 — Build
# ============================================================
FROM node:24-alpine AS build

WORKDIR /app

RUN corepack enable

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN pnpm build


# ============================================================
# Stage 3 — Production
# ============================================================
FROM node:24-alpine AS production

WORKDIR /app

ENV NODE_ENV=production

COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

EXPOSE 3000

USER node

CMD ["node", "node_modules/srvx/bin/srvx.mjs", "serve", "--prod", "--static", "../client", "--entry", "dist/server/server.js"]