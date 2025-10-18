# Scheduler Service

Background service that periodically updates stock data by fetching from the stock data collector service and storing in the database.

## Features

- Periodic stock data updates (configurable interval)
- Fetches stock symbols from database
- Calls stock data collector service for each symbol
- Updates database with latest price and volume
- Automatic retry on failures
- Comprehensive logging

## Structure

```
schedualer/
├── scheduler.py         # Main scheduler application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── README.md           # This file
```

## Dependencies

- **Database:** Requires `db/db.py` module from parent directory
- **Stock Service:** Calls the stock data collector service API

## Configuration

### Environment Variables

Set in `.env` file:
```bash
WEB_SERVICE_URL=http://localhost:5000  # URL of stock data collector service
```

### Schedule Interval

Default: Every 1 minute (for testing)

To change, edit `scheduler.py` line 127:
```python
# For testing (every 1 minute)
scheduler.add_job(update_all_stocks, 'interval', minutes=1)

# For production (every 12 hours)
scheduler.add_job(update_all_stocks, 'interval', hours=12)
```

## Running with Docker

### Build from project root:
```bash
cd d:/share_docker/site
docker build -f schedualer/Dockerfile -t scheduler .
```

### Run:
```bash
docker run --env-file .env scheduler
```

### Using Docker Compose:

Update your `docker-compose.yml`:
```yaml
scheduler:
  container_name: scheduler
  build:
    context: .
    dockerfile: schedualer/Dockerfile
  env_file:
    - .env
  environment:
    - WEB_SERVICE_URL=http://stock_data_collector:5000
  network_mode: "host"
```

Then run:
```bash
docker-compose up scheduler
```

## Running Standalone (Without Docker)

```bash
cd schedualer
pip install -r requirements.txt
export WEB_SERVICE_URL=http://localhost:5000  # or set in .env
python scheduler.py
```

## How It Works

1. **On Startup:**
   - Runs an initial update immediately
   - Starts the scheduled job

2. **Scheduled Updates:**
   - Fetches all stock symbols from database
   - For each symbol:
     - Calls stock service API: `GET {WEB_SERVICE_URL}/stock/{symbol}`
     - Extracts price and volume from response
     - Updates database record

3. **Error Handling:**
   - Logs errors but continues with other stocks
   - Database transactions with rollback on failure
   - API timeouts and retry logic

## Database Schema

Expected `stocks` table:
```sql
CREATE TABLE stocks (
    name VARCHAR(10) PRIMARY KEY,
    price DECIMAL(10, 2),
    trading_volume BIGINT
);
```

## Logging

All operations are logged with timestamps:
- INFO: Successful operations
- WARNING: Skipped updates or missing data
- ERROR: Failed operations or connection issues

View logs:
```bash
# Docker Compose
docker-compose logs -f scheduler

# Docker
docker logs -f scheduler
```

## Troubleshooting

### Scheduler not updating
- Check WEB_SERVICE_URL is correct
- Verify stock service is running
- Check database connection in `db/db.py`
- Ensure stocks table has data

### Import errors
- Dockerfile must build from project root
- db/ directory must be accessible
- Check PYTHONPATH is set correctly

### Database connection issues
- Verify connection string in `db/db.py`
- Check database credentials
- Ensure PostgreSQL is accessible

## Production Recommendations

1. **Change schedule interval:**
   - Edit line 127 in `scheduler.py`
   - Change from `minutes=1` to `hours=12`

2. **Monitoring:**
   - Set up log aggregation
   - Monitor for ERROR messages
   - Alert on repeated failures

3. **Resource limits:**
   - Add memory/CPU limits in docker-compose
   - Monitor container resource usage

4. **Restart policy:**
   - Use `restart: unless-stopped` in docker-compose
   - Ensures service restarts on failure

