# Web Application Service

Main Flask web application with user authentication, manager dashboard, and stock portfolio management.

## Features

- **User Authentication:** Login and signup functionality
- **Manager Dashboard:** Admin interface for management
- **Stock Portfolio:** View and manage stocks
- **Session Management:** Flask-Login for secure sessions
- **Database Integration:** PostgreSQL for data persistence

## Structure

```
app/
├── run.py                    # Application entry point
├── models.py                 # User data models
├── utils.py                  # Utility functions
├── blueprints/               # Flask blueprints (modular routes)
│   ├── loginpage/           # Login functionality
│   │   ├── login.py
│   │   └── templates/
│   │       └── login.html
│   ├── signuppage/          # User registration
│   │   ├── signup.py
│   │   └── templates/
│   │       └── signup.html
│   ├── managerpage/         # Manager dashboard
│   │   ├── manager_page.py
│   │   └── templates/
│   │       └── manager.html
│   └── stocks/              # Stock management
│       ├── stocks.py
│       └── templates/
│           └── stocks.html
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── .dockerignore           # Files to exclude
└── README.md               # This file
```

## Dependencies

- **Database:** Requires `db/` module from parent directory
- **Flask:** Web framework
- **Flask-Login:** User session management
- **PostgreSQL:** Database backend

## Routes

- `/` - Login page
- `/signup` - User registration
- `/manager` - Manager dashboard (requires authentication)
- `/stocks` - Stock portfolio management (requires authentication)

## Configuration

### Environment Variables

The application uses Flask-Login for session management. Database connection is configured in `db/db.py`.

**Secret Key:** Currently hardcoded as `'456789'` - should be moved to environment variable for production.

## Running with Docker

### Build from project root:
```bash
cd d:/share_docker/site
docker build -f app/Dockerfile -t web_app .
```

### Run:
```bash
docker run --env-file .env -p 8080:8080 web_app
```

### Using Docker Compose:

Your `docker-compose.yml` is configured:
```yaml
web_app:
  container_name: web_app
  build:
    context: .
    dockerfile: app/Dockerfile
  ports:
    - "8080:8080"
  network_mode: "host"
  env_file:
    - .env
  restart: unless-stopped
```

Run:
```bash
docker-compose up web_app
```

## Running Standalone (Without Docker)

```bash
cd app
pip install -r requirements.txt

# Make sure db/ is accessible
export PYTHONPATH=..

# Run with Flask (development)
python run.py

# Or run with Gunicorn (production)
gunicorn --bind 0.0.0.0:8080 run:app
```

## Database Setup

The application requires a PostgreSQL database with a `users` table:

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    country VARCHAR(100),
    user_type VARCHAR(50)
);
```

Also requires a `stocks` table:
```sql
CREATE TABLE stocks (
    name VARCHAR(10) PRIMARY KEY,
    price DECIMAL(10, 2),
    trading_volume BIGINT
);
```

Database connection is configured in `db/db.py`.

## Authentication Flow

1. **Login:** User enters credentials at `/`
2. **Validation:** Credentials checked against database
3. **Session:** Flask-Login creates secure session
4. **Access:** User can access protected routes
5. **Logout:** Session cleared

## User Types

The application supports different user types:
- Regular users
- Managers (access to `/manager` routes)

User type is stored in the database and checked during authentication.

## Testing the Application

### Using Browser
1. Navigate to: http://localhost:8080
2. Try login or signup
3. Access manager dashboard
4. View stocks portfolio

### Using curl
```bash
# Check if running
curl http://localhost:8080/

# Note: Most routes require authentication via browser
```

## Logging

The application includes logging utilities:
- View logs at `log.txt`
- Version info at `version.txt`
- Logger setup in `utils.py`

View logs:
```bash
# Docker Compose
docker-compose logs -f web_app

# Docker
docker logs -f web_app
```

## Production Deployment

### Security Recommendations

1. **Secret Key:** Move to environment variable
   ```python
   app.secret_key = os.getenv('SECRET_KEY', 'fallback-key')
   ```

2. **Debug Mode:** Ensure `debug=False` in production
   ```python
   app.run(debug=False, host='0.0.0.0', port=8080)
   ```

3. **HTTPS:** Use reverse proxy (nginx) with SSL/TLS

4. **Database:** Use environment variables for credentials

### Gunicorn Configuration

Default configuration:
- **Workers:** 2 (adjust based on CPU cores)
- **Timeout:** 120 seconds
- **Port:** 8080

To customize, modify the Dockerfile CMD:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "60", "run:app"]
```

## Troubleshooting

### Build fails with "cannot find db/"
- Make sure you're building from project root
- Check that `db/` folder exists at project root
- Use: `docker build -f app/Dockerfile .`

### Import errors at runtime
- Verify `PYTHONPATH=/app` is set
- Check that `db/` was copied correctly
- Verify blueprints are accessible

### Database connection issues
- Check connection string in `db/db.py`
- Verify PostgreSQL is running and accessible
- Check credentials are correct
- Ensure database tables exist

### Login not working
- Verify `users` table exists and has data
- Check password hashing is correct
- Ensure session secret key is set
- Check Flask-Login configuration

### Templates not found
- Verify blueprints/*/templates/ folders exist
- Check template paths in route handlers
- Ensure Flask can find template directories

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

## Integration with Other Services

The web app integrates with:

1. **Database (PostgreSQL):**
   - User authentication
   - Stock data storage

2. **Stock Service (optional):**
   - Can fetch stock data from stock_data_collector service
   - Display real-time prices

## Performance Tips

1. **Increase workers** for high traffic:
   ```dockerfile
   CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", ...]
   ```

2. **Enable caching:**
   - Add Flask-Caching for page caching
   - Cache database queries
   - Static file caching

3. **Database connection pooling:**
   - Implement connection pooling in `db/db.py`
   - Reuse connections instead of creating new ones

4. **Static files:**
   - Serve static files via nginx in production
   - Use CDN for assets

## Development

### Hot Reload (Development Mode)

For development with auto-reload:
```bash
# In docker-compose-dev.yml (create if needed)
command: ["flask", "run", "--host=0.0.0.0", "--port=8080", "--reload"]
environment:
  - FLASK_ENV=development
  - FLASK_DEBUG=1
```

### Adding New Routes

1. Create new blueprint in `blueprints/`
2. Create templates folder
3. Register blueprint in `run.py`
4. Add authentication if needed

### Testing

Create test files:
```bash
# Unit tests
python test_*.py

# Or use pytest
pytest app/
```

## Security Notes

- Runs as non-root user (`webapp`)
- Input validation on forms
- CSRF protection via Flask
- Password hashing (ensure bcrypt/werkzeug is used)
- Session management via Flask-Login
- SQL injection protection via parameterized queries

## Port Configuration

- **Default Port:** 8080 (to avoid conflict with stock_data_collector on 5000)
- Can be changed in Dockerfile and docker-compose.yml
- Update health check if port changes

## Migration Notes

If migrating from standalone Flask to containerized:
1. Ensure all file paths are relative
2. Move secrets to environment variables
3. Update database connection strings
4. Test all routes and functionality

## Support

For issues:
1. Check logs: `docker-compose logs web_app`
2. Verify database connectivity
3. Ensure all dependencies are installed
4. Check environment variables are set

## Next Steps

1. ✅ Dockerfile created
2. Move secret key to environment variable
3. Add automated tests
4. Set up CI/CD pipeline
5. Configure production database
6. Add monitoring and alerting

