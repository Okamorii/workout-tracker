# Workout Tracker

A full-featured workout tracking application for monitoring strength training and running sessions. Built with Flask, PostgreSQL, and Chart.js.

**This project was vibecoded with [Claude Code](https://claude.ai/code).**

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![PWA](https://img.shields.io/badge/PWA-Installable-purple)

## Features

### Workout Logging
- **Strength Training** - Log sets, reps, weight, RPE, and rest times
- **Smart Warm-up Suggestions** - Auto-calculated warm-up sets based on exercise type and order
- **Running Sessions** - Track distance, duration, pace, heart rate, and run type (easy/tempo/interval/long)
- **Interval Builder** - Structured interval configuration with warm up, intervals, recovery, and cool down
- **Recovery Tracking** - Daily sleep, energy, soreness, and motivation scores (1-10)
- **Body Measurements** - Weight, body fat %, and circumference measurements

### Analytics & Progress
- **PR Detection** - Automatic personal record detection with celebration modal
- **Activity Heatmap** - GitHub-style calendar showing workout consistency
- **Week Comparison** - This week vs last week side-by-side stats
- **PR History Graph** - Visualize lift progression over time
- **Heart Rate Zones** - Running zone distribution analysis
- **Volume Tracking** - Weekly volume trends by muscle group
- **Readiness Score** - Daily training readiness based on recovery metrics

### Planning & Templates
- **Workout Templates** - Save and reuse workout structures with smart warm-up suggestions
- **Weekly Planning** - Calendar view with workout scheduling
- **Exercise Library** - 57 exercises classified as compound/isolation, organized by apparatus (cable/dumbbell/barbell/machine)
- **Exercise Substitutes** - Alternative exercises for when equipment is busy

### Technical Features
- **Mobile-First PWA** - Installable on phones, works offline
- **REST API** - JWT-authenticated API for external integrations
- **Data Export** - CSV export for all workout data
- **Docker Deployment** - One-command deployment with docker compose

## Screenshots

The app features a dark theme optimized for gym use:

- Dashboard with quick stats and readiness score
- Exercise logging with rest timer and PR alerts
- Analytics with interactive charts
- Activity heatmap showing workout streaks

## Quick Start

### Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/workout-tracker.git
cd workout-tracker

# Copy environment file
cp .env.example .env

# Start containers
docker compose up -d

# App available at http://localhost:5000
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE workout_tracker;"
sudo -u postgres psql -d workout_tracker -f setup_database.sql

# Configure environment
export DATABASE_URL="postgresql://user:pass@localhost/workout_tracker"
export SECRET_KEY="your-secret-key"

# Run the app
python run.py
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask 3.0, SQLAlchemy, Flask-Login |
| Database | PostgreSQL 16 |
| Frontend | Jinja2, Chart.js, Vanilla JS |
| Styling | Custom CSS (mobile-first, dark theme) |
| Auth | Session-based (web), JWT (API) |
| Deployment | Docker, Gunicorn |

## Project Structure

```
/app
  /blueprints
    /auth        - Login, register, profile
    /dashboard   - Main dashboard
    /workouts    - Strength training
    /running     - Running sessions
    /recovery    - Recovery logging
    /body        - Body measurements
    /exercises   - Exercise library
    /analytics   - Charts and progress
    /planning    - Weekly planning
    /templates   - Workout templates
    /export      - CSV data export
    /api         - REST API (JWT)
  /models        - SQLAlchemy models
  /templates     - Jinja2 templates
  /static        - CSS, JS, PWA assets
```

## API Endpoints

The REST API uses JWT authentication:

```bash
# Login and get token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token for requests
curl http://localhost:5000/api/workouts \
  -H "Authorization: Bearer <token>"
```

Key endpoints:
- `POST /api/auth/login` - Get JWT token
- `GET /api/workouts` - List workouts
- `POST /api/workouts` - Create workout
- `GET /api/stats/summary` - Stats overview
- `GET /api/stats/prs` - Personal records

## Docker Commands

```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f

# Stop containers
docker compose down

# Backup database
docker compose exec db pg_dump -U workout workout_tracker > backup.sql

# Restore database
docker compose exec -T db psql -U workout workout_tracker < backup.sql
```

Or use the Makefile:

```bash
make up        # Start containers
make down      # Stop containers
make logs      # View logs
make shell     # Shell into web container
make db-shell  # Connect to database
make backup    # Backup database
make test      # Run tests
```

## Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Required |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `FLASK_ENV` | Environment (development/production) | production |

## Training Programs

This app is designed around:

- **Strength**: Jeff Nippard's Upper Body program (2x/week)
- **Running**: Campus.coach methodology (4x/week)

But it's flexible enough for any training program.

## Key Formulas

- **Estimated 1RM (Epley)**: `weight × (1 + reps/30)`
- **Volume**: `sets × reps × weight`
- **TRIMP**: Training impulse based on duration and heart rate
- **Readiness**: Average of (sleep, energy, 10-soreness, motivation)

## Contributing

This project was vibecoded - built entirely through conversation with Claude Code. Feel free to fork and continue the vibe!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this for your own training!

---

Built with Claude Code | Vibecoded with love
