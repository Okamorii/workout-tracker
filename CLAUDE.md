# CLAUDE.md

This file provides guidance to Claude Code when working with the GymProject workout tracking application.

## Project Overview

A fully-functional Flask workout tracking PWA for personal fitness monitoring:
- **Upper body strength training** (2x/week, Jeff Nippard's program)
- **Running sessions** (4x/week, Campus.coach methodology)

**Status: 100% Complete** - All core features implemented and deployed via Docker.

## Environment

| Component | Details |
|-----------|---------|
| Host | 192.168.0.117 (Debian 13 LXC on Proxmox) |
| Python | 3.13 |
| Database | PostgreSQL 16 |
| Deployment | Docker Compose |
| App URL | http://192.168.0.117:5000 |

## Docker Deployment (Production)

The app runs in Docker containers. **Always use Docker commands for the live app.**

```bash
# Start/stop containers
cd /root/gym
docker compose up -d
docker compose down

# View logs
docker compose logs -f

# Access Docker database (IMPORTANT: this is the live database)
docker exec workout_db psql -U workout -d workout_tracker

# Access Flask shell
docker exec -it workout_app flask shell

# Rebuild after code changes
docker compose build && docker compose up -d
```

### Container Architecture

```
workout_network
├── workout_app (Flask/Gunicorn on port 5000)
│   └── Connects to workout_db:5432
└── workout_db (PostgreSQL 16 on port 5433 external)
```

### Important: Two PostgreSQL Instances

1. **Docker PostgreSQL** (`workout_db` container, port 5433) - **LIVE APP USES THIS**
2. **Host PostgreSQL** (local, port 5432) - For development/testing only

When modifying user data or debugging the live app, always use:
```bash
docker exec workout_db psql -U workout -d workout_tracker -c "YOUR SQL HERE"
```

## Database Schema

**Tables:**
- `users` - Authentication (username, email, bcrypt password_hash)
- `exercises` - Exercise library (name, muscle_group, exercise_type, movement_type)
- `exercise_substitutions` - Bidirectional exercise alternatives
- `workout_sessions` - Session records (date, type, duration, notes)
- `strength_logs` - Sets, reps, weight, RPE, rest_time, warmup_sets per exercise
- `running_logs` - Distance, duration, avg_hr, run_type, interval_details
- `personal_records` - PRs for lifts (1RM) and running
- `recovery_logs` - Sleep, energy, soreness, motivation (1-10)
- `body_measurements` - Weight, body fat, circumferences
- `workout_templates` - Reusable workout structures
- `template_exercises` - Exercises within templates (with warmup_sets)
- `planned_workouts` - Weekly planning

**Key Columns:**
- `exercises.movement_type` - 'compound' or 'isolation' (used for smart warm-up calculation)
- `strength_logs.warmup_sets` - Number of warm-up sets performed before working sets
- `strength_logs.set_number` - Individual set number (1, 2, 3...) for per-set logging
- `template_exercises.warmup_sets` - Suggested warm-up sets for template
- `template_exercises.target_sets` - Target number of working sets
- `template_exercises.target_reps` - Target reps per set

**Key Functions (PostgreSQL):**
- `calculate_1rm(weight, reps)` - Epley formula
- `calculate_trimp(duration, avg_hr, max_hr)` - Training impulse
- `check_running_volume_spike(user_id)` - >10% mileage alert
- `check_strength_volume_spike(user_id)` - >20% volume alert

## Application Structure

```
/root/gym/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py             # Config classes
│   ├── models/
│   │   ├── user.py           # User model (flask-bcrypt auth)
│   │   ├── exercise.py       # Exercise with MUSCLE_GROUPS, movement_type
│   │   ├── workout.py        # WorkoutSession, StrengthLog, RunningLog
│   │   ├── records.py        # PersonalRecord
│   │   ├── recovery.py       # RecoveryLog
│   │   ├── body_measurements.py
│   │   ├── template.py       # WorkoutTemplate with smart warmup calculation
│   │   └── planning.py       # PlannedWorkout
│   ├── blueprints/
│   │   ├── auth/             # Login, register, profile
│   │   ├── dashboard/        # Main overview
│   │   ├── workouts/         # Strength training
│   │   ├── running/          # Cardio sessions
│   │   ├── recovery/         # Recovery logging
│   │   ├── exercises/        # Exercise library
│   │   ├── analytics/        # Charts, comparisons
│   │   ├── planning/         # Weekly calendar
│   │   ├── templates/        # Workout templates
│   │   ├── body/             # Body measurements
│   │   ├── export/           # CSV exports
│   │   └── api/              # REST API with JWT
│   ├── templates/            # Jinja2 templates
│   └── static/
│       ├── css/style.css     # Mobile-first CSS
│       ├── js/app.js         # Validation, timers, charts
│       ├── manifest.json     # PWA manifest
│       └── sw.js             # Service worker
├── tests/                    # Pytest test suite
├── docker-compose.yml
├── Dockerfile
├── Makefile                  # Convenience commands
├── setup_database.sql        # Full schema
└── run.py                    # Entry point
```

## Key Features

### Implemented
- User auth with flask-login + flask-bcrypt
- Strength workout logging with auto PR detection
- **Individual working set logging** - each set has its own reps input (Set 1: 10, Set 2: 8)
- **Smart warm-up suggestions** based on exercise order and type
- Running sessions with interval builder
- Recovery tracking (sleep/energy/soreness/motivation)
- Body measurements tracking
- Exercise library with 57 exercises (compound/isolation classified)
- Exercise substitutes by apparatus (cable/dumbbell/barbell/machine)
- Workout templates (with target_sets/target_reps pre-filling the form)
- Weekly planning calendar
- Analytics with Chart.js (heatmaps, comparisons, trends)
- Volume spike alerts
- Readiness score calculation
- PWA (installable, offline-capable)
- CSV data export
- REST API with JWT

### Working Sets UI
When logging exercises, each working set has its own row:
- Select number of working sets (1-4) from dropdown
- Each set shows "Set 1", "Set 2", etc. with individual reps input
- Template exercises pre-fill with `target_sets` and `target_reps`
- Logged sets display as "2 sets: 10/8 reps @ 60kg"

### Smart Warm-up Logic
When using a workout template, warm-up sets are auto-suggested:
- **First compound for a muscle group**: 3 warm-up sets
- **First isolation for a muscle group**: 2 warm-up sets
- **Muscle already warmed from previous exercise**: 1 warm-up set

### Key Formulas
- **1RM (Epley)**: `weight * (1 + reps/30)`
- **Volume**: `sets * reps * weight`
- **TRIMP**: Training impulse from HR data
- **Readiness**: `avg(sleep, energy, 10-soreness, motivation)`

## Users

| Username | Email | Password |
|----------|-------|----------|
| `Maxime` | maxime.florent@proton.me | `maxime` |
| `Leyla` | leyla@gym.local | `leyla` |

To reset password:
```bash
# Generate new hash
python3 -c "from flask_bcrypt import Bcrypt; from flask import Flask; b=Bcrypt(Flask(__name__)); print(b.generate_password_hash('NEW_PASSWORD').decode())"

# Update in Docker DB
docker exec workout_db psql -U workout -d workout_tracker -c "UPDATE users SET password_hash = 'HASH_HERE' WHERE username = 'USERNAME';"
```

To create new user:
```bash
# Generate hash then insert
docker exec workout_db psql -U workout -d workout_tracker -c "
INSERT INTO users (username, email, password_hash)
VALUES ('NewUser', 'email@example.com', 'HASH_HERE');
"
```

## Exercise Database

57 strength exercises organized by muscle group and classified as compound/isolation:

| Muscle | Compound | Isolation |
|--------|----------|-----------|
| Back | Barbell Row, Pull-ups, Lat Pulldown, Cable Row, Machine Row, DB Rows | - |
| Chest | Bench Press, DB Press, Incline Press, Machine Press | Flyes, Peck Deck |
| Shoulders | Overhead Press, DB Shoulder Press, Machine Press | Lateral Raises, Face Pull, Rear Delt |
| Biceps | - | All curls (Barbell, EZ, Cable, DB, Hammer, Machine) |
| Triceps | - | Pushdowns, Skull Crushers, Extensions |
| Legs | Squat, Leg Press, Lunges | Leg Extension, Leg Curl |
| Hamstrings | Deadlift, Romanian DL | Leg Curl |

## Common Tasks

### Run Tests
```bash
cd /root/gym
pytest
pytest --cov=app --cov-report=html
```

### View Logs
```bash
docker compose logs -f workout_app
```

### Database Backup
```bash
make backup
# or
docker exec workout_db pg_dump -U workout workout_tracker > backup.sql
```

### Add New Exercise
```bash
docker exec workout_db psql -U workout -d workout_tracker -c "
INSERT INTO exercises (name, muscle_group, exercise_type, movement_type)
VALUES ('Exercise Name', 'Chest', 'strength', 'compound');
"
```

### Copy Template to Another User
```bash
# Get user IDs and template ID first, then:
docker exec workout_db psql -U workout -d workout_tracker -c "
INSERT INTO workout_templates (user_id, name, description, workout_type)
SELECT NEW_USER_ID, name, description, workout_type
FROM workout_templates WHERE template_id = SOURCE_TEMPLATE_ID;
"
# Then copy template_exercises with the new template_id
```

## File Locations

| Purpose | Path |
|---------|------|
| Main app | `/root/gym/app/__init__.py` |
| Models | `/root/gym/app/models/` |
| Routes | `/root/gym/app/blueprints/*/` |
| CSS | `/root/gym/app/static/css/style.css` |
| JS | `/root/gym/app/static/js/app.js` |
| Base template | `/root/gym/app/templates/base.html` |
| DB schema | `/root/gym/setup_database.sql` |
| Docker config | `/root/gym/docker-compose.yml` |

## Future Enhancements (Not Yet Built)

- Goal setting with progress tracking
- Photo progress uploads
- Dark/light theme toggle
- Password reset via email
- Weekly summary email
