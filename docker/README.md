# Docker Deployment Guide

## Quick Start

One command to start:

```bash
cd docker
docker-compose up -d
```

Service will be available at: `http://localhost:8001/mcp`

## How It Works

The `Dockerfile` automatically downloads the documentation index during build:

```dockerfile
RUN curl -L -o site/search/search_index.json \
    https://raw.githubusercontent.com/tronprotocol/documentation-en/gh-pages/search/search_index.json
```

So you don't need to manually download anything.

## Common Commands

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Restart
docker-compose restart

# Check status
docker-compose ps

# Enter container
docker-compose exec mcp-server sh
```

## Update Documentation Index

If you want to update to the latest documentation:

```bash
# Rebuild image to fetch latest index
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Port Already in Use

If port 8001 is occupied, modify `docker-compose.yml`:

```yaml
ports:
  - "8002:8001"  # Change 8002 to any free port
```

Then access via `http://localhost:8002/mcp`

### Check If Index Exists

```bash
docker-compose exec mcp-server ls -la site/search/
```

## Production Recommendations

1. **Resource limits**:
   ```yaml
   # Add to docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512M
   ```

2. **Use specific image tag** instead of building every time
