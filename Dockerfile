# Build Next.js application
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build Next.js application
RUN npm run build

# Install Python dependencies for API services
RUN apk add --no-cache python3 py3-pip bash curl && \
    pip install --no-cache-dir --break-system-packages -r requirements.txt || true

# HF Spaces routes traffic to PORT env (default 7860)
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV HOSTNAME=0.0.0.0

EXPOSE 7860

# Start backend (port 8000) + frontend (port 7860) together.
# The frontend proxies /api/* to the backend via next.config.js rewrites.
CMD ["sh", "-c", "python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 & npx next start -p 7860 -H 0.0.0.0"]
