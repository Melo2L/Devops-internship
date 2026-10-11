"""Technology detection for JavaScript and TypeScript projects."""

from collections.abc import Mapping

PACKAGE_TECHNOLOGIES: dict[str, str] = {
    "react": "React",
    "next": "Next.js",
    "vite": "Vite",
    "typescript": "TypeScript",
    "tailwindcss": "Tailwind CSS",
    "@tanstack/react-router": "TanStack Router",
    "@tanstack/react-start": "TanStack Start",
    "@angular/core": "Angular",
    "vue": "Vue.js",
    "svelte": "Svelte",
    "astro": "Astro",
    "nuxt": "Nuxt",
    "express": "Express",
    "@nestjs/core": "NestJS",
    "fastify": "Fastify",
    "koa": "Koa",
    "hono": "Hono",
    "gatsby": "Gatsby",
    "remix": "Remix",
    "@remix-run/react": "Remix",
    "react-router": "React Router",
    "electron": "Electron",
    "expo": "Expo",
    "react-native": "React Native",
    "prettier": "Prettier",
    "eslint": "ESLint",
    "vitest": "Vitest",
    "jest": "Jest",
    "playwright": "Playwright",
    "@playwright/test": "Playwright",
    "cypress": "Cypress",
    "webpack": "Webpack",
    "rollup": "Rollup",
    "esbuild": "esbuild",
    "turbo": "Turborepo",
    "nx": "Nx",
    "prisma": "Prisma",
    "drizzle-orm": "Drizzle ORM",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
    "mongoose": "Mongoose",
    "zod": "Zod",
    "openapi-types": "OpenAPI",
    "graphql": "GraphQL",
    "@opentelemetry/api": "OpenTelemetry",
}


def detect_javascript_technologies(
    package_json: Mapping[str, object],
) -> set[str]:
    """Identify known technologies from package manifest dependencies."""

    dependencies: set[str] = set()

    for section in ("dependencies", "devDependencies", "peerDependencies"):
        section_data = package_json.get(section, {})

        if isinstance(section_data, Mapping):
            dependencies.update(name for name in section_data if isinstance(name, str))

    return {
        technology
        for package, technology in PACKAGE_TECHNOLOGIES.items()
        if package in dependencies
    }
