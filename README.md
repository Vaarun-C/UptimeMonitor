# 🔍 Uptime Monitor

A comprehensive web application for monitoring website uptime and performance with real-time notifications and detailed analytics.

## ✨ Features

### Core Monitoring
- **Real-time URL monitoring** - Check website availability every 5 minutes
- **Multi-user support** - Individual accounts with personal dashboards
- **Category organization** - Group your monitored URLs by category (Production, Staging, etc.)
- **Immediate checks** - Trigger on-demand status checks for any URL

### Analytics & Reporting
- **Uptime percentage** - 24-hour rolling uptime calculations
- **Response time tracking** - Monitor performance trends over time
- **Detailed logs** - View complete check history with timestamps
- **Interactive charts** - Visual response time trends using Plotly

### Notifications
- **Email summaries** - Automated uptime reports sent to users
- **Status alerts** - Get notified when sites go down or recover
- **HTML-formatted emails** - Beautiful, detailed email reports

### Web Interface
- **Modern Streamlit dashboard** - Clean, responsive user interface
- **Real-time updates** - Live status monitoring with auto-refresh
- **User authentication** - Secure login system with password hashing
- **RESTful API** - Full API access for automation and integrations

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Gmail account (for email notifications)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd uptime-monitor
   ```

2. **Install dependencies**
   ```bash
   pip install fastapi uvicorn streamlit aiohttp pandas plotly python-dotenv
   ```

3. **Configure email notifications (optional)**
   Create a `.env` file in the project root:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_USER=your-email@gmail.com
   APP_PASSWORD=your-16-char-app-password
   ```

   **For Gmail users:**
   - Enable 2-Factor Authentication
   - Generate an App Password (not your regular password)
   - Use the 16-character App Password in the `.env` file

### Running the Application

1. **Start the API server**
   ```bash
   python main.py
   ```

2. **Start the web interface** (in a new terminal)
   ```bash
   streamlit run frontend.py
   ```

3. **Access the application**
   - Web Dashboard: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📊 Usage

### Getting Started
1. **Create an account** - Register with username, password, and email
2. **Add URLs to monitor** - Enter websites you want to track
3. **Organize with categories** - Group URLs by environment or purpose
4. **Monitor in real-time** - View uptime percentages and response times

### Dashboard Features
- **URL Management** - Add, remove, and categorize monitored URLs
- **Status Overview** - Color-coded uptime indicators (🟢 >99%, 🟡 95-99%, 🔴 <95%)
- **Detailed Analytics** - Click "Details" to view response time charts and logs
- **Manual Checks** - Force immediate checks for any URL or all URLs
- **Email Reports** - Send comprehensive uptime summaries to your email

### API Endpoints

#### Authentication
- `POST /register` - Create new user account
- `GET /me` - Get current user information

#### URL Management
- `POST /track` - Add URL to monitoring
- `GET /my-urls` - List all monitored URLs
- `DELETE /urls/{url}` - Remove URL from monitoring
- `PUT /urls/{url}/category` - Update URL category

#### Monitoring & Status
- `GET /status/{url}` - Get uptime statistics for URL
- `GET /logs/{url}` - Get detailed check logs
- `POST /check/{url}` - Trigger immediate URL check
- `POST /check-all` - Check all user's URLs immediately

#### Notifications
- `POST /send-report` - Send uptime summary email

## 🏗️ Architecture

### Components
- **FastAPI Backend** (`api_backend.py`) - RESTful API with authentication
- **Streamlit Frontend** (`frontend.py`) - Interactive web dashboard
- **Database Manager** (`database_manager.py`) - SQLite database operations
- **Monitoring Service** (`monitoring_service.py`) - Async URL checking engine
- **Notification Service** (`notification_service.py`) - Email reporting system

### Database Schema
- **users** - User accounts with hashed passwords
- **urls** - Monitored URLs with categories and ownership
- **checks** - Historical check results with timestamps and metrics

### Technology Stack
- **Backend**: FastAPI, SQLite, aiohttp
- **Frontend**: Streamlit, Plotly, Pandas
- **Monitoring**: Asyncio, concurrent URL checking
- **Authentication**: HTTP Basic Auth with PBKDF2 password hashing
- **Notifications**: SMTP email with HTML formatting

## 🛠️ Configuration

### Environment Variables
```env
# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@gmail.com
APP_PASSWORD=your-app-password

# Database (optional - defaults to uptime_monitor.db)
DATABASE_PATH=uptime_monitor.db
```

### Monitoring Settings
- **Check Interval**: 5 minutes (configurable in `monitoring_service.py`)
- **Timeout**: 30 seconds per URL
- **Uptime Calculation**: Rolling 24-hour window
- **Concurrent Checks**: Up to 100 simultaneous connections

## 📈 Monitoring Details

### Status Definitions
- **Success**: HTTP status code < 400
- **Error**: HTTP status code ≥ 400, timeout, or connection error
- **Uptime Percentage**: (Successful checks / Total checks) × 100

### Performance Metrics
- **Response Time**: End-to-end request duration in milliseconds
- **Status Codes**: HTTP response codes for debugging
- **Check History**: Complete log of all monitoring attempts

## 🔒 Security

### Authentication
- HTTP Basic Authentication for API access
- PBKDF2 password hashing with random salts
- User isolation - users can only access their own URLs

### Database Security
- SQLite with WAL mode for concurrent access
- Foreign key constraints for data integrity
- SQL injection protection with parameterized queries

### Performance Optimization
- **Database Indexing**: Indexes on user_id, url_id, and timestamp
- **Connection Pooling**: aiohttp connector limits and reuse
- **Concurrent Checks**: Async processing of multiple URLs
- **WAL Mode**: SQLite Write-Ahead Logging for better concurrency
**Happy Monitoring!** 🔍✨
