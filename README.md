# Stocks Flask Application

A Flask web application for managing and tracking stocks with user authentication.

## Running with Docker Compose

This is the recommended way to run the application. The setup uses Docker Compose to run two services:
- **`stock_data_collector`**: A Flask API that serves stock data from the Alpha Vantage API.
- **`scheduler`**: A background service that periodically fetches stock data from the collector and updates the database.

### Prerequisites

- Docker Desktop installed and running.

### Quick Start

1.  **Create a `.env` file**:
    In the root of the project, create a file named `.env`. This file will hold your environment variables. Add the following content to it, replacing `YOUR_API_KEY_HERE` with your actual Alpha Vantage API key.

    ```
    # --- API Configuration ---
    ALPHAVANTAGE_API_KEY=YOUR_API_KEY_HERE

    # --- Server Configuration ---
    # The port the stock_data_collector will run on.
    PORT=5000

    # --- Scheduler Configuration ---
    # The URL the scheduler will use to contact the data collector.
    WEB_SERVICE_URL=http://localhost:5000
    ```

2.  **Build and Run the Services**:
    Open a terminal in the project's root directory and run the following command:
    ```bash
    docker-compose up --build
    ```
    This will build the Docker image for the services and start them. The `stock_data_collector` service will be accessible on your local machine at `http://localhost:5000`.

### Docker Commands

**Start the services in the background:**
```bash
docker-compose up --build -d
```

**View logs from all services:**
```bash
docker-compose logs -f
```

**Stop the services:**
```bash
docker-compose down
```

## Application Structure
```
site/
├── app/
│   ├── stock_data_collector_service.py # The Flask API
│   ├── scheduler.py                    # The database update scheduler
│   ├── db.py                           # Database configuration
│   └── ...
├── .env                    # Environment variables (you need to create this)
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
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