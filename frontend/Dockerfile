# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build production bundle
RUN npm run build

# Runtime stage
FROM node:20-alpine as runtime

WORKDIR /app

# Install serve to run the SPA
RUN npm install -g serve

# Copy built assets from builder
COPY --from=build /app/dist ./dist

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Serve the SPA on port 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
