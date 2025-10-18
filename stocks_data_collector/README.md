# Stock Data Collector Service

REST API service that fetches real-time stock data from Alpha Vantage API.

## Features

- Fetches real-time stock quotes from Alpha Vantage
- RESTful API with JSON responses
- Health check endpoint
- Error handling for API limits and failures
- Configurable via environment variables
- Production-ready with Gunicorn

## Structure

```
stocks_data_collector/
├── stock_data_collector_service.py  # Main Flask API
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container configuration
├── .dockerignore                    # Files to exclude
└── README.md                        # This file
```

## Dependencies

- **Config:** Requires `config.py` from parent directory

## API Endpoints

### GET /
Service information and health check
```json
{
  "service": "Flask Stock API",
  "status": "healthy",
  "version": "1.0.0",
  "usage": "/stock/<SYMBOL>",
  "example": "/stock/AAPL"
}
```

### GET /stock/{symbol}
Get real-time stock data for a symbol

**Example:** `GET /stock/AAPL`

**Response:**
```json
{
  "symbol": "AAPL",
  "price": 150.25,
  "change": 2.50,
  "change_percent": 1.69,
  "volume": 50000000,
  "last_trading_day": "2025-10-18",
  "timestamp": "2025-10-18T12:00:00Z"
}
```

**Error Response:**
```json
{
  "error": "API Error: Invalid API call"
}
```

### GET /health
Health check endpoint
```json
{
  "status": "healthy"
}
```

## Configuration

### Environment Variables

Set in `.env` file:
```bash
ALPHAVANTAGE_API_KEY=your_api_key_here
ALPHAVANTAGE_BASE_URL=https://www.alphavantage.co/query
HOST=0.0.0.0
PORT=5000
DEBUG=False
API_TIMEOUT=10
```

### Get Alpha Vantage API Key

1. Go to https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Get your free API key
4. Add it to `.env` file

## Running with Docker

### Build from project root:
```bash
cd d:/share_docker/site
docker build -f stocks_data_collector/Dockerfile -t stock_data_collector .
```

### Run:
```bash
docker run --env-file .env -p 5000:5000 stock_data_collector
```

### Using Docker Compose:

Your `docker-compose.yml` is already configured:
```yaml
stock_data_collector:
  container_name: stock_data_collector
  build: .
  command: ["gunicorn", "--bind", "0.0.0.0:5000", "app.stock_data_collector_service:app"]
  volumes:
    - .:/app
  network_mode: "host"
  env_file:
    - .env
```

Run:
```bash
docker-compose up stock_data_collector
```

## Running Standalone (Without Docker)

```bash
cd stocks_data_collector
pip install -r requirements.txt

# Make sure config.py is accessible
export PYTHONPATH=..

# Set environment variables
export ALPHAVANTAGE_API_KEY=your_key_here

# Run with Flask (development)
python stock_data_collector_service.py

# Or run with Gunicorn (production)
gunicorn --bind 0.0.0.0:5000 stock_data_collector_service:app
```

## Testing the API

### Using curl
```bash
# Health check
curl http://localhost:5000/health

# Service info
curl http://localhost:5000/

# Get Apple stock
curl http://localhost:5000/stock/AAPL

# Get Google stock
curl http://localhost:5000/stock/GOOGL
```

### Using PowerShell
```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:5000/health"

# Get stock data
Invoke-WebRequest -Uri "http://localhost:5000/stock/AAPL" | Select-Object -Expand Content
```

## Error Handling

The service handles:
- **Invalid symbols:** Returns 400 Bad Request
- **API errors:** Returns 404 with error message
- **API rate limits:** Returns error with limit message
- **Network failures:** Returns error with failure reason
- **Timeouts:** 10 second timeout (configurable)

## Alpha Vantage API Limits

Free tier limitations:
- **5 API calls per minute**
- **500 API calls per day**

If you exceed the limit, you'll get:
```json
{
  "error": "API Limit: Thank you for using Alpha Vantage! ..."
}
```

## Logging

The service logs:
- Configuration on startup
- All API requests
- Errors and exceptions

View logs:
```bash
# Docker Compose
docker-compose logs -f stock_data_collector

# Docker
docker logs -f stock_data_collector
```

## Production Deployment

### Docker Build
```bash
# Build
docker build -f stocks_data_collector/Dockerfile -t stock_data_collector:latest .

# Run with proper settings
docker run -d \
  --name stock_data_collector \
  --restart unless-stopped \
  -p 5000:5000 \
  --env-file .env \
  stock_data_collector:latest
```

### Gunicorn Configuration

Default configuration:
- **Workers:** 2 (adjust based on CPU cores)
- **Timeout:** 30 seconds
- **Port:** 5000

To customize, modify the Dockerfile CMD:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "60", "stock_data_collector_service:app"]
```

## Troubleshooting

### Build fails with "cannot find config.py"
- Make sure you're building from project root
- Check that `config.py` exists at project root
- Use: `docker build -f stocks_data_collector/Dockerfile .`

### API returns "API Key required" error
- Check `ALPHAVANTAGE_API_KEY` is set in `.env`
- Verify the API key is valid
- Ensure `.env` file is being loaded

### Service won't start
- Check port 5000 is not already in use
- Verify all environment variables are set
- Check logs for error messages

### "No quote data found" errors
- Verify the stock symbol is valid
- Check Alpha Vantage API status
- Ensure you haven't exceeded rate limits

## Health Monitoring

The Dockerfile includes a health check:
- Interval: 30 seconds
- Timeout: 10 seconds
- Start period: 5 seconds
- Retries: 3

Check container health:
```bash
docker ps
# Look for "healthy" in STATUS column
```

## Security

- Runs as non-root user (`stockapi`)
- API key loaded from environment (not hardcoded)
- Input validation on symbols
- Timeout protection
- Error messages don't expose internals

## Performance Tips

1. **Increase workers** for high traffic:
   ```dockerfile
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", ...]
   ```

2. **Adjust timeout** for slow API responses:
   ```dockerfile
   CMD ["gunicorn", ..., "--timeout", "60", ...]
   ```

3. **Cache responses** (optional):
   - Add Redis for caching
   - Cache responses for 1 minute
   - Reduces API calls

4. **Monitor rate limits**:
   - Track API calls per minute
   - Implement request queuing
   - Add retry logic with backoff

## Integration with Scheduler

The scheduler service calls this API:
```python
# Scheduler makes requests to:
GET http://stock_data_collector:5000/stock/AAPL
```

Make sure both services are on the same Docker network or use `network_mode: "host"`.

