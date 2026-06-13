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
RUN apk add --no-cache python3 py3-pip && \
    pip install --no-cache-dir -r requirements.txt || true && \
    pip install --no-cache-dir playwright==1.60.0 && \
    python -m playwright install chromium || true

# Expose port for HF Spaces (default: 7860)
EXPOSE 7860 3000 8001 8002 8003

# Set environment
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Start Next.js production server
CMD ["npm", "start"]
