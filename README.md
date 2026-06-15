---
title: DevForge
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
hf_oauth: true
hf_oauth_scopes:
  - inference-api
  - read-repos
---

# DevForge

AI-powered code generation with multi-model Hugging Face parallel execution and GitHub PR sync.

## Features

- **Multi-Model Code Generation**: Run multiple Hugging Face models in parallel on the same project
- **Hugging Face Hub Integration**: Discover and use thousands of code models
- **GitHub Sync**: Generate PRs directly from AI-modified code
- **Side-by-Side Diff**: Compare original vs modified code with unified or split view
- **Open Alternative**: HF-only alternative to Trae / OpenAI Codex

## Running Locally

```bash
# Backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
npm install
npm run dev
```

## Environment Variables

- `HF_TOKEN` — Hugging Face API token for model inference
- `ANTHROPIC_API_KEY` — Optional Anthropic provider
- `GROQ_API_KEY` — Optional Groq provider
- `GITHUB_TOKEN` — GitHub token for PR creation (user-supplied via UI)
