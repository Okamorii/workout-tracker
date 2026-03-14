-- Workout Tracker Database Setup
-- Drop existing objects
DROP VIEW IF EXISTS recovery_trends CASCADE;
DROP VIEW IF EXISTS running_prs CASCADE;
DROP VIEW IF EXISTS auto_detected_prs CASCADE;
DROP VIEW IF EXISTS user_dashboard_summary CASCADE;
DROP VIEW IF EXISTS weekly_strength_volume CASCADE;
DROP VIEW IF EXISTS weekly_running_mileage CASCADE;
DROP VIEW IF EXISTS running_logs_with_trimp CASCADE;
DROP VIEW IF EXISTS strength_logs_with_1rm CASCADE;
DROP FUNCTION IF EXISTS calculate_workout_streak CASCADE;
DROP FUNCTION IF EXISTS check_strength_volume_spike CASCADE;
DROP FUNCTION IF EXISTS check_running_volume_spike CASCADE;
DROP FUNCTION IF EXISTS calculate_volume CASCADE;
DROP FUNCTION IF EXISTS get_best_1rm CASCADE;
DROP FUNCTION IF EXISTS calculate_1rm CASCADE;
DROP FUNCTION IF EXISTS calculate_trimp CASCADE;
DROP FUNCTION IF EXISTS get_exercise_substitutes CASCADE;
DROP FUNCTION IF EXISTS add_substitution CASCADE;
DROP TABLE IF EXISTS body_measurements CASCADE;
DROP TABLE IF EXISTS planned_workouts CASCADE;
DROP TABLE IF EXISTS template_exercises CASCADE;
DROP TABLE IF EXISTS workout_templates CASCADE;
DROP TABLE IF EXISTS exercise_substitutions CASCADE;
DROP TABLE IF EXISTS recovery_logs CASCADE;
DROP TABLE IF EXISTS personal_records CASCADE;
DROP TABLE IF EXISTS running_logs CASCADE;
DROP TABLE IF EXISTS strength_logs CASCADE;
DROP TABLE IF EXISTS workout_sessions CASCADE;
DROP TABLE IF EXISTS exercises CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =============================================================================
-- TABLES
-- =============================================================================

-- Users table for authentication
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Exercise library
CREATE TABLE exercises (
    exercise_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    muscle_group VARCHAR(50),
    exercise_type VARCHAR(20) CHECK (exercise_type IN ('strength', 'cardio')),
    video_reference_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workout sessions
CREATE TABLE workout_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    session_type VARCHAR(20) CHECK (session_type IN ('upper_body', 'running', 'other')),
    duration_minutes INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strength training logs
CREATE TABLE strength_logs (
    log_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES workout_sessions(session_id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(exercise_id),
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight_kg DECIMAL(6,2),
    rpe INTEGER CHECK (rpe BETWEEN 1 AND 10),
    rest_seconds INTEGER,
    tempo VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Running logs
CREATE TABLE running_logs (
    log_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES workout_sessions(session_id) ON DELETE CASCADE,
    run_type VARCHAR(20) CHECK (run_type IN ('easy', 'tempo', 'interval', 'long', 'other')),
    distance_km DECIMAL(6,2),
    duration_minutes INTEGER,
    avg_pace_per_km DECIMAL(5,2),
    elevation_gain_meters INTEGER,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    perceived_effort VARCHAR(20),
    weather_conditions VARCHAR(50),
    route_notes TEXT,
    interval_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Personal records
CREATE TABLE personal_records (
    record_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(exercise_id),
    record_type VARCHAR(20) CHECK (record_type IN ('1RM', 'rep_max', 'volume', 'distance', 'pace')),
    value DECIMAL(10,2),
    date_achieved DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recovery tracking
CREATE TABLE recovery_logs (
    recovery_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 10),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    muscle_soreness INTEGER CHECK (muscle_soreness BETWEEN 1 AND 10),
    motivation_score INTEGER CHECK (motivation_score BETWEEN 1 AND 10),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exercise substitutions (bidirectional)
CREATE TABLE exercise_substitutions (
    substitution_id SERIAL PRIMARY KEY,
    exercise_id INTEGER NOT NULL REFERENCES exercises(exercise_id) ON DELETE CASCADE,
    substitute_id INTEGER NOT NULL REFERENCES exercises(exercise_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exercise_id, substitute_id),
    CHECK (exercise_id <> substitute_id)
);

-- Workout templates
CREATE TABLE workout_templates (
    template_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    workout_type VARCHAR(50) DEFAULT 'upper_body',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Template exercises (exercises within a template)
CREATE TABLE template_exercises (
    template_exercise_id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES workout_templates(template_id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(exercise_id),
    order_index INTEGER DEFAULT 0,
    target_sets INTEGER DEFAULT 3,
    target_reps INTEGER DEFAULT 10,
    notes VARCHAR(200)
);

-- Add extra columns to strength_logs
ALTER TABLE strength_logs ADD COLUMN IF NOT EXISTS warmup_sets INTEGER DEFAULT 0;
ALTER TABLE strength_logs ADD COLUMN IF NOT EXISTS template_exercise_id INTEGER REFERENCES template_exercises(template_exercise_id) ON DELETE SET NULL;
ALTER TABLE strength_logs ADD COLUMN IF NOT EXISTS set_number INTEGER DEFAULT NULL;

-- Planned workouts (weekly planning)
CREATE TABLE planned_workouts (
    plan_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    planned_date DATE NOT NULL,
    workout_type VARCHAR(20) NOT NULL,
    description VARCHAR(255),
    target_duration INTEGER,
    target_distance DECIMAL(6,2),
    template_id INTEGER REFERENCES workout_templates(template_id),
    completed BOOLEAN DEFAULT FALSE,
    completed_session_id INTEGER REFERENCES workout_sessions(session_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Body measurements tracking
CREATE TABLE body_measurements (
    measurement_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    measurement_date DATE NOT NULL DEFAULT CURRENT_DATE,
    weight_kg DECIMAL(5,2),
    body_fat_pct DECIMAL(4,1),
    chest_cm DECIMAL(5,1),
    waist_cm DECIMAL(5,1),
    hips_cm DECIMAL(5,1),
    left_arm_cm DECIMAL(4,1),
    right_arm_cm DECIMAL(4,1),
    left_thigh_cm DECIMAL(5,1),
    right_thigh_cm DECIMAL(5,1),
    left_calf_cm DECIMAL(4,1),
    right_calf_cm DECIMAL(4,1),
    neck_cm DECIMAL(4,1),
    shoulders_cm DECIMAL(5,1),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_workout_sessions_date ON workout_sessions(session_date);
CREATE INDEX idx_workout_sessions_user ON workout_sessions(user_id);
CREATE INDEX idx_strength_logs_session ON strength_logs(session_id);
CREATE INDEX idx_running_logs_session ON running_logs(session_id);
CREATE INDEX idx_exercises_type ON exercises(exercise_type);
CREATE INDEX idx_recovery_logs_date ON recovery_logs(log_date);
CREATE INDEX idx_recovery_logs_user ON recovery_logs(user_id);
CREATE INDEX idx_personal_records_user ON personal_records(user_id);
CREATE INDEX idx_substitutions_exercise ON exercise_substitutions(exercise_id);
CREATE INDEX idx_substitutions_substitute ON exercise_substitutions(substitute_id);
CREATE INDEX idx_templates_user ON workout_templates(user_id);
CREATE INDEX idx_template_exercises_template ON template_exercises(template_id);
CREATE INDEX idx_planned_workouts_user ON planned_workouts(user_id);
CREATE INDEX idx_planned_workouts_date ON planned_workouts(planned_date);
CREATE INDEX idx_body_measurements_user ON body_measurements(user_id);
CREATE INDEX idx_body_measurements_date ON body_measurements(measurement_date);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- 1RM Estimation using Epley Formula: weight × (1 + reps/30)
CREATE OR REPLACE FUNCTION calculate_1rm(weight DECIMAL, reps INTEGER)
RETURNS DECIMAL AS $$
BEGIN
    IF reps = 1 THEN
        RETURN weight;
    ELSIF reps <= 0 OR weight <= 0 THEN
        RETURN 0;
    ELSE
        RETURN ROUND(weight * (1 + reps::DECIMAL / 30), 2);
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Get best estimated 1RM for an exercise
CREATE OR REPLACE FUNCTION get_best_1rm(p_exercise_id INTEGER, p_user_id INTEGER DEFAULT NULL)
RETURNS TABLE(exercise_name VARCHAR, best_1rm DECIMAL, achieved_date DATE) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.name,
        MAX(calculate_1rm(sl.weight_kg, sl.reps)),
        ws.session_date
    FROM strength_logs sl
    JOIN workout_sessions ws ON sl.session_id = ws.session_id
    JOIN exercises e ON sl.exercise_id = e.exercise_id
    WHERE sl.exercise_id = p_exercise_id
      AND (p_user_id IS NULL OR ws.user_id = p_user_id)
    GROUP BY e.name, ws.session_date
    ORDER BY MAX(calculate_1rm(sl.weight_kg, sl.reps)) DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- TRIMP (Training Impulse) Score Calculation
-- Formula: Duration (min) × HR_ratio × 0.64 × e^(1.92 × HR_ratio)
CREATE OR REPLACE FUNCTION calculate_trimp(
    duration_min INTEGER,
    avg_hr INTEGER,
    max_hr INTEGER,
    resting_hr INTEGER DEFAULT 60,
    gender CHAR DEFAULT 'M'
)
RETURNS DECIMAL AS $$
DECLARE
    hr_ratio DECIMAL;
    gender_factor DECIMAL;
BEGIN
    IF duration_min IS NULL OR avg_hr IS NULL OR max_hr IS NULL THEN
        RETURN NULL;
    END IF;

    IF max_hr <= resting_hr THEN
        RETURN 0;
    END IF;

    hr_ratio := (avg_hr - resting_hr)::DECIMAL / (max_hr - resting_hr);

    IF hr_ratio < 0 THEN hr_ratio := 0; END IF;
    IF hr_ratio > 1 THEN hr_ratio := 1; END IF;

    IF gender = 'F' THEN
        gender_factor := 1.67;
    ELSE
        gender_factor := 1.92;
    END IF;

    RETURN ROUND(duration_min * hr_ratio * 0.64 * EXP(gender_factor * hr_ratio), 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Volume calculation for strength training
CREATE OR REPLACE FUNCTION calculate_volume(sets INTEGER, reps INTEGER, weight DECIMAL)
RETURNS DECIMAL AS $$
BEGIN
    RETURN COALESCE(sets, 0) * COALESCE(reps, 0) * COALESCE(weight, 0);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Check running volume spike (>10% increase)
CREATE OR REPLACE FUNCTION check_running_volume_spike(p_user_id INTEGER)
RETURNS TABLE(
    current_week DATE,
    current_distance DECIMAL,
    previous_distance DECIMAL,
    increase_percent DECIMAL,
    is_spike BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH weekly_data AS (
        SELECT
            DATE_TRUNC('week', ws.session_date)::DATE AS week_start,
            SUM(rl.distance_km) AS total_distance_km,
            LAG(SUM(rl.distance_km)) OVER (ORDER BY DATE_TRUNC('week', ws.session_date)) AS prev_distance
        FROM running_logs rl
        JOIN workout_sessions ws ON rl.session_id = ws.session_id
        WHERE ws.user_id = p_user_id OR p_user_id IS NULL
        GROUP BY DATE_TRUNC('week', ws.session_date)
    )
    SELECT
        wd.week_start,
        wd.total_distance_km,
        wd.prev_distance,
        CASE
            WHEN wd.prev_distance > 0 THEN
                ROUND(((wd.total_distance_km - wd.prev_distance) / wd.prev_distance * 100), 2)
            ELSE 0
        END,
        CASE
            WHEN wd.prev_distance > 0 AND
                 ((wd.total_distance_km - wd.prev_distance) / wd.prev_distance * 100) > 10
            THEN TRUE
            ELSE FALSE
        END
    FROM weekly_data wd
    WHERE wd.prev_distance IS NOT NULL
    ORDER BY wd.week_start DESC;
END;
$$ LANGUAGE plpgsql;

-- Check strength volume spike (>20% increase)
CREATE OR REPLACE FUNCTION check_strength_volume_spike(p_user_id INTEGER)
RETURNS TABLE(
    current_week DATE,
    muscle_group VARCHAR,
    current_volume DECIMAL,
    previous_volume DECIMAL,
    increase_percent DECIMAL,
    is_spike BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH weekly_data AS (
        SELECT
            DATE_TRUNC('week', ws.session_date)::DATE AS week_start,
            e.muscle_group AS mg,
            SUM(calculate_volume(sl.sets, sl.reps, sl.weight_kg)) AS total_volume,
            LAG(SUM(calculate_volume(sl.sets, sl.reps, sl.weight_kg))) OVER (
                PARTITION BY e.muscle_group ORDER BY DATE_TRUNC('week', ws.session_date)
            ) AS prev_volume
        FROM strength_logs sl
        JOIN workout_sessions ws ON sl.session_id = ws.session_id
        JOIN exercises e ON sl.exercise_id = e.exercise_id
        WHERE ws.user_id = p_user_id OR p_user_id IS NULL
        GROUP BY DATE_TRUNC('week', ws.session_date), e.muscle_group
    )
    SELECT
        wd.week_start,
        wd.mg,
        wd.total_volume,
        wd.prev_volume,
        CASE
            WHEN wd.prev_volume > 0 THEN
                ROUND(((wd.total_volume - wd.prev_volume) / wd.prev_volume * 100), 2)
            ELSE 0
        END,
        CASE
            WHEN wd.prev_volume > 0 AND
                 ((wd.total_volume - wd.prev_volume) / wd.prev_volume * 100) > 20
            THEN TRUE
            ELSE FALSE
        END
    FROM weekly_data wd
    WHERE wd.prev_volume IS NOT NULL
    ORDER BY wd.week_start DESC, wd.mg;
END;
$$ LANGUAGE plpgsql;

-- Calculate workout streak
CREATE OR REPLACE FUNCTION calculate_workout_streak(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    streak INTEGER := 0;
    check_date DATE := CURRENT_DATE;
    has_workout BOOLEAN;
BEGIN
    LOOP
        SELECT EXISTS(
            SELECT 1 FROM workout_sessions
            WHERE user_id = p_user_id
            AND session_date = check_date
        ) INTO has_workout;

        IF has_workout THEN
            streak := streak + 1;
            check_date := check_date - INTERVAL '1 day';
        ELSE
            check_date := check_date - INTERVAL '1 day';
            SELECT EXISTS(
                SELECT 1 FROM workout_sessions
                WHERE user_id = p_user_id
                AND session_date = check_date
            ) INTO has_workout;

            IF NOT has_workout THEN
                EXIT;
            END IF;
        END IF;

        IF streak > 365 THEN EXIT; END IF;
    END LOOP;

    RETURN streak;
END;
$$ LANGUAGE plpgsql;

-- Get substitutes with last performance
CREATE OR REPLACE FUNCTION get_exercise_substitutes(p_exercise_id INTEGER, p_user_id INTEGER)
RETURNS TABLE(
    substitute_exercise_id INTEGER,
    exercise_name VARCHAR,
    muscle_group VARCHAR,
    last_sets INTEGER,
    last_reps INTEGER,
    last_weight_kg DECIMAL,
    last_performed DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (e.exercise_id)
        e.exercise_id,
        e.name,
        e.muscle_group,
        sl.sets,
        sl.reps,
        sl.weight_kg,
        ws.session_date
    FROM exercise_substitutions es
    JOIN exercises e ON e.exercise_id = es.substitute_id
    LEFT JOIN strength_logs sl ON sl.exercise_id = e.exercise_id
    LEFT JOIN workout_sessions ws ON ws.session_id = sl.session_id AND ws.user_id = p_user_id
    WHERE es.exercise_id = p_exercise_id
    ORDER BY e.exercise_id, ws.session_date DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- Helper to add bidirectional substitution
CREATE OR REPLACE FUNCTION add_substitution(ex1 INTEGER, ex2 INTEGER)
RETURNS VOID AS $$
BEGIN
    INSERT INTO exercise_substitutions (exercise_id, substitute_id)
    VALUES (ex1, ex2), (ex2, ex1)
    ON CONFLICT DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Strength logs with estimated 1RM
CREATE OR REPLACE VIEW strength_logs_with_1rm AS
SELECT
    sl.log_id,
    sl.session_id,
    sl.exercise_id,
    e.name AS exercise_name,
    sl.sets,
    sl.reps,
    sl.weight_kg,
    sl.rpe,
    calculate_1rm(sl.weight_kg, sl.reps) AS estimated_1rm,
    sl.created_at
FROM strength_logs sl
JOIN exercises e ON sl.exercise_id = e.exercise_id;

-- Running logs with TRIMP scores
CREATE OR REPLACE VIEW running_logs_with_trimp AS
SELECT
    rl.log_id,
    rl.session_id,
    rl.run_type,
    rl.distance_km,
    rl.duration_minutes,
    rl.avg_pace_per_km,
    rl.avg_heart_rate,
    rl.max_heart_rate,
    calculate_trimp(rl.duration_minutes, rl.avg_heart_rate, rl.max_heart_rate) AS trimp_score,
    rl.perceived_effort,
    rl.created_at
FROM running_logs rl;

-- Weekly running mileage
CREATE OR REPLACE VIEW weekly_running_mileage AS
SELECT
    ws.user_id,
    DATE_TRUNC('week', ws.session_date)::DATE AS week_start,
    SUM(rl.distance_km) AS total_distance_km,
    COUNT(rl.log_id) AS run_count,
    SUM(rl.duration_minutes) AS total_duration_min,
    AVG(calculate_trimp(rl.duration_minutes, rl.avg_heart_rate, rl.max_heart_rate)) AS avg_trimp
FROM running_logs rl
JOIN workout_sessions ws ON rl.session_id = ws.session_id
GROUP BY ws.user_id, DATE_TRUNC('week', ws.session_date);

-- Weekly strength volume
CREATE OR REPLACE VIEW weekly_strength_volume AS
SELECT
    ws.user_id,
    DATE_TRUNC('week', ws.session_date)::DATE AS week_start,
    e.muscle_group,
    SUM(calculate_volume(sl.sets, sl.reps, sl.weight_kg)) AS total_volume,
    COUNT(DISTINCT ws.session_id) AS session_count
FROM strength_logs sl
JOIN workout_sessions ws ON sl.session_id = ws.session_id
JOIN exercises e ON sl.exercise_id = e.exercise_id
GROUP BY ws.user_id, DATE_TRUNC('week', ws.session_date), e.muscle_group;

-- User dashboard summary
CREATE OR REPLACE VIEW user_dashboard_summary AS
SELECT
    u.user_id,
    u.username,
    (SELECT COUNT(*) FROM workout_sessions ws WHERE ws.user_id = u.user_id) AS total_workouts,
    (SELECT COUNT(*) FROM workout_sessions ws WHERE ws.user_id = u.user_id AND ws.session_type = 'upper_body') AS strength_sessions,
    (SELECT COUNT(*) FROM workout_sessions ws WHERE ws.user_id = u.user_id AND ws.session_type = 'running') AS running_sessions,
    (SELECT COUNT(*) FROM workout_sessions ws
     WHERE ws.user_id = u.user_id
     AND ws.session_date >= DATE_TRUNC('week', CURRENT_DATE)) AS workouts_this_week,
    (SELECT COALESCE(SUM(rl.distance_km), 0)
     FROM running_logs rl
     JOIN workout_sessions ws ON rl.session_id = ws.session_id
     WHERE ws.user_id = u.user_id) AS total_distance_km,
    (SELECT COALESCE(SUM(calculate_volume(sl.sets, sl.reps, sl.weight_kg)), 0)
     FROM strength_logs sl
     JOIN workout_sessions ws ON sl.session_id = ws.session_id
     WHERE ws.user_id = u.user_id) AS total_volume_lifted
FROM users u;

-- Auto-detected PRs for strength
CREATE OR REPLACE VIEW auto_detected_prs AS
SELECT DISTINCT ON (ws.user_id, sl.exercise_id)
    ws.user_id,
    e.name AS exercise_name,
    sl.weight_kg AS best_weight,
    sl.reps AS reps_at_best,
    calculate_1rm(sl.weight_kg, sl.reps) AS estimated_1rm,
    ws.session_date AS achieved_date
FROM strength_logs sl
JOIN workout_sessions ws ON sl.session_id = ws.session_id
JOIN exercises e ON sl.exercise_id = e.exercise_id
WHERE e.exercise_type = 'strength'
ORDER BY ws.user_id, sl.exercise_id, calculate_1rm(sl.weight_kg, sl.reps) DESC;

-- Running PRs
CREATE OR REPLACE VIEW running_prs AS
SELECT
    ws.user_id,
    'Fastest 5K' AS record_type,
    MIN(rl.duration_minutes) AS value,
    MIN(ws.session_date) AS achieved_date
FROM running_logs rl
JOIN workout_sessions ws ON rl.session_id = ws.session_id
WHERE rl.distance_km BETWEEN 4.9 AND 5.1
GROUP BY ws.user_id
UNION ALL
SELECT
    ws.user_id,
    'Fastest 10K' AS record_type,
    MIN(rl.duration_minutes) AS value,
    MIN(ws.session_date) AS achieved_date
FROM running_logs rl
JOIN workout_sessions ws ON rl.session_id = ws.session_id
WHERE rl.distance_km BETWEEN 9.9 AND 10.1
GROUP BY ws.user_id
UNION ALL
SELECT
    ws.user_id,
    'Longest Run' AS record_type,
    MAX(rl.distance_km) AS value,
    MAX(ws.session_date) AS achieved_date
FROM running_logs rl
JOIN workout_sessions ws ON rl.session_id = ws.session_id
GROUP BY ws.user_id
UNION ALL
SELECT
    ws.user_id,
    'Best Pace' AS record_type,
    MIN(rl.avg_pace_per_km) AS value,
    MIN(ws.session_date) AS achieved_date
FROM running_logs rl
JOIN workout_sessions ws ON rl.session_id = ws.session_id
WHERE rl.avg_pace_per_km > 0
GROUP BY ws.user_id;

-- Recovery trends
CREATE OR REPLACE VIEW recovery_trends AS
SELECT
    user_id,
    DATE_TRUNC('week', log_date)::DATE AS week_start,
    ROUND(AVG(sleep_quality), 1) AS avg_sleep,
    ROUND(AVG(energy_level), 1) AS avg_energy,
    ROUND(AVG(muscle_soreness), 1) AS avg_soreness,
    ROUND(AVG(motivation_score), 1) AS avg_motivation,
    COUNT(*) AS logs_count
FROM recovery_logs
GROUP BY user_id, DATE_TRUNC('week', log_date);

-- =============================================================================
-- SAMPLE DATA
-- =============================================================================

-- Insert sample exercises
INSERT INTO exercises (name, description, muscle_group, exercise_type) VALUES
('Bench Press', 'Standard barbell bench press', 'Chest', 'strength'),
('Incline Dumbbell Press', 'Incline bench dumbbell press', 'Chest', 'strength'),
('Cable Flyes', 'Cable crossover flyes', 'Chest', 'strength'),
('Squat', 'Barbell back squat', 'Legs', 'strength'),
('Deadlift', 'Conventional barbell deadlift', 'Back', 'strength'),
('Barbell Row', 'Bent over barbell row', 'Back', 'strength'),
('Pull-ups', 'Bodyweight pull-ups', 'Back', 'strength'),
('Lat Pulldown', 'Cable lat pulldown', 'Back', 'strength'),
('Overhead Press', 'Standing barbell overhead press', 'Shoulders', 'strength'),
('Lateral Raises', 'Dumbbell lateral raises', 'Shoulders', 'strength'),
('Face Pulls', 'Cable face pulls', 'Shoulders', 'strength'),
('Barbell Curl', 'Standing barbell curl', 'Biceps', 'strength'),
('Hammer Curls', 'Dumbbell hammer curls', 'Biceps', 'strength'),
('Tricep Pushdown', 'Cable tricep pushdown', 'Triceps', 'strength'),
('Skull Crushers', 'Lying tricep extension', 'Triceps', 'strength'),
('Easy Run', 'Comfortable pace run', 'Cardio', 'cardio'),
('Tempo Run', 'Sustained harder effort', 'Cardio', 'cardio'),
('Interval Run', 'High intensity intervals', 'Cardio', 'cardio'),
('Long Run', 'Endurance building run', 'Cardio', 'cardio');
