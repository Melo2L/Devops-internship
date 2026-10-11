##### Project Engineering Guidelines

##### Architecture

- UI pages should read application data through `src/services`.
- Domain types belong in `src/types`.
- Demo/mock data belongs in `src/data`.
- Demo session state belongs in `src/hooks`.
- Keep UI components independent from data-source implementation.
- The current mock services are intentionally designed to be replaced by a FastAPI API later.

##### Security

- Never commit real credentials, API keys, tokens, or secrets.
- Treat uploaded projects as untrusted input.
- Do not execute uploaded project code directly.
- Keep security findings and scan results clearly separated from UI presentation.

##### Git

- Use feature branches for changes.
- Keep commits small and descriptive.
- Keep `main` in a releasable state.
