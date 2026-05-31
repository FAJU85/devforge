---
title: DevForge
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
---

# ⚡ DevForge — AI Coding Agent

> **GitHub:** [github.com/FAJU85/devforge](https://github.com/FAJU85/devforge)
> **Live Space:** [huggingface.co/spaces/vooom/devforge](https://huggingface.co/spaces/vooom/devforge)

Professional web-based AI coding agent with GitHub OAuth, Claude + Groq + HF models, multi-agent pipeline, skills, rules, and custom instructions.

## 🔄 GitHub ↔ HF Space Sync

Every push to `main` on GitHub automatically deploys to the HF Space via GitHub Actions.

## ⚡ Features
- GitHub OAuth (one-click, Device Flow)
- Repo browser — search and load any GitHub repo
- File context — select up to 8 files
- Multi-agent pipeline — Plan → Implement → Review
- Skills: Go · Zod · Tests · Errors · Security · Docs · Perf · SOLID
- Custom Rules and Instructions
- Light/Dark theme
- Providers: Claude · Groq (free) · HF Models

## 🚀 Providers
| Provider | Cost | Get Key |
|---|---|---|
| Claude | ~$0.05–0.30/task | console.anthropic.com |
| **Groq** | **Free tier** | console.groq.com |
| HF Models | Credits required | hf.co/settings/tokens |

## 📁 Structure
```
devforge/
├── main.py                          # FastAPI backend
├── static/index.html                # Full frontend
├── requirements.txt
├── Dockerfile
└── .github/workflows/
    ├── sync-to-hf.yml               # GitHub → HF Space
    └── sync-from-hf.yml             # HF Space → GitHub
```
