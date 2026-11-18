# syntax=docker/dockerfile:1

# ============================================================
# Stage 1 — Dependencies
# ============================================================
FROM node:24-alpine AS deps

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

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
# Stage 3 — Production dependencies
# ============================================================
FROM node:24-alpine AS production

WORKDIR /app

ENV NODE_ENV=production

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN pnpm install --prod --frozen-lockfile

# Remove package-manager components not required at runtime
RUN rm -rf \
    /usr/local/lib/node_modules/npm \
    /usr/local/bin/npm \
    /usr/local/bin/npx \
    /root/.cache/node/corepack

# Remove build-time packages confirmed unnecessary in production runtime.
RUN rm -rf \
    /app/node_modules/.pnpm/picomatch@4.0.7 \
    /app/node_modules/.pnpm/tinyglobby@0.2.17 \
    /app/node_modules/.pnpm/fdir@6.5.0_picomatch@4.0.7 \
    /app/node_modules/.pnpm/@tanstack+start-plugin-core@1.171.49_*

# Update Alpine packages with available security fixes
RUN apk update && apk upgrade --no-cache zlib


COPY --from=build /app/dist ./dist

EXPOSE 3000

USER node

CMD ["node", "node_modules/srvx/bin/srvx.mjs", "serve", "--prod", "--static", "../client", "--entry", "dist/server/server.js"]
