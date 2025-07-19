# Stocks Flask Application

A Flask web application for managing and tracking stocks with user authentication.

## Features

- User login and authentication
- Stock management and tracking
- Real-time stock data via yfinance
- PostgreSQL database integration
- Responsive web interface

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Quick Start

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Or use the provided script (Windows):**
   ```bash
   build-and-run.bat
   ```

3. **Access the application:**
   - Open your browser and go to: `http://localhost:5000`

### Docker Commands

**Build the image:**
```bash
docker-compose build
```

**Start the application:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop the application:**
```bash
docker-compose down
```

**Rebuild and restart:**
```bash
docker-compose down
docker-compose up --build
```

## Manual Setup (Without Docker)

### Prerequisites

- Python 3.8+
- PostgreSQL database

### Installation

1. **Install dependencies:**
   ```bash
   cd app
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python run.py
   ```

3. **Access the application:**
   - Open your browser and go to: `http://localhost:5000`

## Login Credentials

- **Email:** `Elad.glx@gmail.com`
- **Password:** `password123`

## Application Structure

```
stocks/
├── app/                    # Flask application
│   ├── blueprints/
│   │   ├── loginpage/      # Login functionality
│   │   ├── signuppage/     # Signup functionality
│   │   ├── managerpage/    # Manager interface
│   │   └── stocks/         # Stock management
│   ├── templates/          # HTML templates
│   ├── run.py              # Application entry point
│   ├── db.py               # Database configuration
│   ├── utils.py            # Utility functions
│   └── requirements.txt    # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore           # Docker ignore file
└── README.md               # This file
```

## Database

The application uses PostgreSQL with the following main tables:
- `users` - User accounts and authentication
- `stocks` - Stock data and information

## Environment Variables

The following environment variables can be configured:
- `FLASK_ENV` - Flask environment (development/production)
- `PYTHONUNBUFFERED` - Python output buffering
- Database connection string (configured in `db.py`)

## Health Check

The Docker container includes a health check that monitors the application status at `http://localhost:5000/`.

## Troubleshooting

### Common Issues

1. **Port already in use:**
   - Change the port in `docker-compose.yml` or stop other services using port 5000

2. **Database connection issues:**
   - Verify the database connection string in `app/db.py`
   - Ensure the database is accessible from the container

3. **Build failures:**
   - Check that all files are present in the `app/` directory
   - Verify the `requirements.txt` file is up to date

### Logs

View application logs:
```bash
docker-compose logs -f stocks-app
```

## Development

For development, you can run the application directly without Docker:
```bash
cd app
python run.py
```

The application will run in debug mode with auto-reload enabled. 