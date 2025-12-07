# The Greatest API - Backend Deployment on Render

This is a FastAPI backend application for The Greatest API. This README provides instructions for deploying the backend on Render.

## Prerequisites

- Python 3.8 or higher
- A Render account
- Git repository (for deployment)

## Local Development

To run the backend locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## Deployment on Render

### Step 1: Prepare Your Repository

1. Ensure all files are committed to your Git repository.
2. Make sure `requirements.txt` includes all necessary dependencies, including `gunicorn`.

### Step 2: Create a New Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" and select "Web Service"
3. Connect your Git repository
4. Configure the service:
   - **Name**: Choose a name for your service (e.g., `the-greatest-backend`)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: Leave blank (Render will use the Procfile)

### Step 3: Configure Environment Variables

In your Render service settings, add the following environment variables:

- `DATABASE_URL`: Your database URL (e.g., PostgreSQL URL for production)
- `SECRET_KEY`: A secret key for JWT tokens
- Any other environment variables your app requires

### Step 4: Database Setup

For production, use a PostgreSQL database:

1. Create a PostgreSQL database on Render or another provider
2. Set the `DATABASE_URL` environment variable to point to your database
3. The app will automatically create tables on startup

### Step 5: Deploy

1. Click "Create Web Service"
2. Render will build and deploy your application
3. Once deployed, your API will be available at the provided URL

## Configuration Details

### Gunicorn Configuration

The `Procfile` contains:
```
web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

This starts Gunicorn with:
- 4 worker processes
- Uvicorn workers (for ASGI support)
- The main FastAPI app

### Environment Variables

The app uses `python-decouple` for environment variable management. Key variables:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key

### CORS Configuration

The app is configured to allow CORS from `http://localhost:3000` for development. Update this in `main.py` for production.

## API Endpoints

- `GET /`: Welcome message
- `POST /auth/register`: User registration
- `POST /auth/login`: User login
- `/chat/*`: Chat functionality
- `/files/*`: File management
- `/projects/*`: Project management
- `/users/*`: User management

## Troubleshooting

- **Build Failures**: Check that all dependencies are listed in `requirements.txt`
- **Runtime Errors**: Check environment variables and database connection
- **CORS Issues**: Update CORS origins in `main.py` for your frontend domain

## Additional Notes

- The app creates a default user on startup: username "THE GREATEST", password "0769636386"
- File uploads are stored in the `uploads/` directory
- SQLite is used for local development; use PostgreSQL for production
