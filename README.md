# Smart City Traffic Management System
- **Database**: SQLite with SQLAlchemy ORM
- **Caching**: Redis for real-time state
- **Frontend**: Vanilla JS + Modern CSS
- **Deployment**: Docker Compose
- **Package Manager**: UV (ultra-fast Python package installer)

## 📦 Installation

### Using Docker (Recommended)
```bash
docker-compose up --build
```

### Local Development
```bash
# Install dependencies
uv sync

# Run the application  
uv run uvicorn app.main:app --reload
```

Access at: **http://localhost:8000/api/v1/frontend/**

## 🎯 Usage Guide

### Dashboard Navigation

1. **Sidebar**: Click on cities to expand/collapse areas
2. **Select Area**: Click an area name to filter intersections
3. **View All**: Reload page to see all intersections again

### Managing Traffic Lights

1. **View Status**: See real-time countdown timers
2. **Manual Control**: Click "⚙️ Manage" button
3. **Change Status**: Select RED/YELLOW/GREEN
4. **Adjust Duration**: Set timer (5-300 seconds)

### Admin Operations

#### Add City
1. Click "+ Add City" button
2. Enter name and code
3. Save

#### Add Area
1. Click "+ Add Area" button
2. Select parent city
3. Enter area name and code
4. Save

## 🔄 How It Works

### Automatic Light Cycling
- Lights change based on traffic density
- Higher density = longer green time
- WebSocket broadcasts state changes in real-time

### Real-time Countdown
- Client-side countdown for smooth UX
- Server provides end_time via WebSocket
- Auto-refreshes when timer reaches zero

## 📡 API Endpoints

### Cities
- `POST /api/v1/cities/` - Create
- `GET /api/v1/cities/` - List all
- `PUT /api/v1/cities/{id}` - Update
- `DELETE /api/v1/cities/{id}` - Delete

### Areas
- `POST /api/v1/areas/` - Create
- `GET /api/v1/areas/` - List all
- `PUT /api/v1/areas/{id}` - Update
- `DELETE /api/v1/areas/{id}` - Delete

### Traffic Control
- `POST /api/v1/admin/traffic-lights/{id}/manual` - Manual override
- `PUT /api/v1/admin/traffic-lights/{id}/duration` - Update duration

### WebSocket
- `WS /api/v1/ws` - Real-time updates

## 🎨 UI Features

- **Glassmorphism Cards**: Semi-transparent with backdrop blur
- **Gradient Backgrounds**: Purple-blue theme
- **Pulse Animations**: Active lights pulse realistically
- **Collapsible Sidebar**: Save screen space
- **Responsive Design**: Works on all devices

## 📁 Project Structure

```
app/
├── api/v1/endpoints/
│   ├── cities.py          # City CRUD
│   ├── areas.py           # Area CRUD
│   ├── admin.py           # Admin controls
│   ├── websocket.py       # WebSocket handler
│   └── frontend.py        # Dashboard routes
├── core/
│   ├── config.py          # Settings
│   └── traffic_logic.py   # Control logic
├── models/                # SQLAlchemy models
├── schemas/               # Pydantic schemas
├── static/
│   ├── css/styles.css     # Modern styling
│   └── js/app.js          # Frontend logic
└── templates/
    └── dashboard.html     # Main UI
```

## 🔧 Configuration

Edit `.env` file:
```bash
DATABASE_URL=sqlite:///./traffic.db
REDIS_URL=redis://localhost:6379/0
```

## 🐛 Troubleshooting

### Redis Connection Issues
- Ensure Redis is running: `docker-compose up redis`
- Check `REDIS_URL` in `.env`

### WebSocket Not Connecting
- Check browser console for errors
- Verify server is running on correct port

### Timer Not Updating
- Ensure JavaScript is enabled
- Check WebSocket connection status

## 📝 License

MIT License

## 👤 Author

Smart City Traffic Management System - Production Ready
