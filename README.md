# Smart City Traffic Management System

A production-ready backend and dashboard for managing smart city traffic lights, built with FastAPI, SQLite, Redis, and Docker.

## Features

-   **Dashboard**: Real-time visualization of traffic intersections and light status.
-   **Adaptive Control**: Traffic lights automatically cycle based on simulated traffic density.
-   **Simulation**: Manually adjust traffic density to test the adaptive logic.
-   **REST API**: Fully documented API for external integration.
-   **Containerized**: Easy deployment with Docker.

## Tech Stack

-   **Backend**: FastAPI (Python 3.12)
-   **Database**: SQLite (SQLAlchemy ORM)
-   **Caching**: Redis
-   **Frontend**: Jinja2 Templates + HTMX
-   **Dependency Management**: `uv`

## Getting Started

### Prerequisites

-   Docker & Docker Compose

### Running the Project

1.  Clone the repository.
2.  Start the services:
    ```bash
    docker-compose up --build
    ```
3.  Access the application:
    -   **Dashboard**: [http://localhost:8000/api/v1/frontend/](http://localhost:8000/api/v1/frontend/)
    -   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Usage

1.  Open the Dashboard.
2.  You will see a sample intersection "Main St & 1st Ave".
3.  Use the "Low", "Med", "High" buttons to simulate traffic density for a specific direction.
4.  The system will automatically adjust the lights (logic runs in background/on-demand).
5.  Click "Refresh Status" to see the latest state (or implement auto-refresh).

## API Endpoints

-   `GET /api/v1/frontend/`: Dashboard view.
-   `POST /api/v1/frontend/simulate/{id}/density`: Update traffic density.
-   `GET /api/v1/traffic-lights/`: List all lights.
