# Pack-A-Mal: Complete Project Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation](#installation)
5. [Deployment](#deployment)
6. [Usage Guide](#usage-guide)
7. [API Documentation](#api-documentation)
8. [Development Guide](#development-guide)
9. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What is Pack-A-Mal?

**Pack-A-Mal** is a comprehensive open-source security analysis platform developed by the OpenSSF (Open Source Security Foundation) that identifies malicious behaviors in packages from popular package repositories. The project provides both static and dynamic analysis capabilities to detect malware, backdoors, typosquatting, and other security threats.

### Key Capabilities

Pack-A-Mal answers critical security questions:
- 🔍 **What files do packages access?**
- 🌐 **What addresses do they connect to?**
- ⚙️ **What commands do they execute?**
- 🔧 **What system calls do they use?**

### Supported Ecosystems

| Ecosystem | Static Analysis | Dynamic Analysis |
|-----------|----------------|------------------|
| **npm** | ✅ | ✅ |
| **PyPI** | ✅ | ✅ |
| **Maven** | ⚠️ | ✅ |
| **RubyGems** | ✅ | ✅ |
| **Crates.io** | ✅ | ✅ |
| **Packagist** | ✅ | ✅ |
| **Wolfi APK** | ❌ | ✅ |

---

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Package Sources"
        A[Package Feeds]
    end
    
    subgraph "Analysis Orchestration"
        B[Scheduler<br/>Job Management]
        C[Worker/Analyzer<br/>Execution Engine]
    end
    
    subgraph "Analysis Engines"
        D1[Static Analysis<br/>Sandbox]
        D2[Dynamic Analysis<br/>Sandbox]
    end
    
    subgraph "Static Analysis Tools"
        E1[OSSGadget<br/>Typosquatting]
        E2[Bandit4mal<br/>Python Malware]
        E3[Py2src<br/>Source Finder]
        E4[Lastpymile<br/>Discrepancy]
    end
    
    subgraph "Dynamic Analysis Tools"
        F1[Network Monitor<br/>Packet Capture]
        F2[File System Monitor<br/>Read/Write/Delete]
        F3[Command Logger<br/>Shell Execution]
        F4[System Call Tracer<br/>strace]
        F5[Yara Scanner<br/>Pattern Matching]
    end
    
    subgraph "Storage & Presentation"
        G[Result Store<br/>S3/Cloud/Local]
        H[Web Dashboard<br/>Django + Nginx]
    end
    
    A --> B
    B --> C
    C --> D1
    C --> D2
    D1 --> E1 & E2 & E3 & E4
    D2 --> F1 & F2 & F3 & F4 & F5
    E1 & E2 & E3 & E4 --> G
    F1 & F2 & F3 & F4 & F5 --> G
    G --> H
```

### Project Structure

```
pack-a-mal_prd/
│
├── cmd/                        # Main applications (Go)
│   ├── analyze/               # Analysis worker
│   ├── scheduler/             # Job scheduler
│   ├── downloader/            # Package downloader
│   └── worker/                # Worker processes
│
├── internal/                   # Internal Go packages
│   ├── analysis/              # Analysis orchestration
│   ├── dynamicanalysis/       # Dynamic analysis logic
│   ├── staticanalysis/        # Static analysis logic
│   ├── sandbox/               # Sandbox management (Podman)
│   ├── pkgmanager/            # Package manager abstractions
│   ├── resultstore/           # Result storage
│   ├── packetcapture/         # Network traffic analysis
│   ├── dnsanalyzer/           # DNS query analysis
│   ├── strace/                # System call tracing
│   └── worker/                # Worker job processing
│
├── sandboxes/                  # Sandbox Docker images
│   ├── dynamicanalysis/       # Dynamic analysis sandbox
│   │   ├── Dockerfile
│   │   └── analyze_*.py       # Analysis scripts per ecosystem
│   └── staticanalysis/        # Static analysis sandbox
│       └── Dockerfile
│
├── web/                        # Web dashboard
│   └── package-analysis-web/  # Django application
│       ├── packamal/          # Django project
│       ├── package_analysis/  # Main app
│       ├── requirements.txt
│       └── manage.py
│
├── prd/                        # Production Docker environment
│   ├── docker-compose.yml     # Full stack deployment
│   ├── backend/               # Django backend
│   ├── frontend/              # Nginx reverse proxy
│   ├── database/              # PostgreSQL init scripts
│   └── Makefile               # Helper commands
│
├── scripts/                    # Automation scripts
│   ├── run_analysis.sh        # Main analysis script
│   ├── analyse-tarballs.sh    # Batch analysis
│   └── deploy.sh              # Deployment script
│
├── configs/                    # Configuration files
│   └── e2e/                   # End-to-end testing config
│
├── infra/                      # Infrastructure as code
├── examples/                   # Example configurations
├── tools/                      # Utility tools
├── test/                       # Test suites
├── Makefile                    # Build automation
└── go.mod                      # Go dependencies
```

---

## Components

### 1. Scheduler ([cmd/scheduler](cmd/scheduler))

**Purpose**: Receives package update notifications and schedules analysis jobs

**Key Features**:
- Listens to package feeds from multiple ecosystems
- Filters package versions using regex patterns
- Publishes analysis tasks to worker queue
- Supports Google Cloud Pub/Sub and Kafka

**Configuration**:
```bash
OSSMALWARE_SUBSCRIPTION_URL=<pub/sub subscription URL>
OSSMALWARE_WORKER_TOPIC=<worker topic URL>
LOGGER_ENV=<dev|prod>
```

**Supported Package Types**:
- npm, PyPI, RubyGems, Packagist, Crates.io

### 2. Analyzer/Worker ([cmd/analyze](cmd/analyze))

**Purpose**: Main analysis orchestrator that executes static and dynamic analysis

**Command-Line Options**:
```bash
./analyze [OPTIONS]

FLAGS:
  -package string          Package name
  -version string          Package version  
  -local string            Local package file path
  -ecosystem string        Package ecosystem (npm, pypi, etc.)
  -mode strings            Analysis modes: static, dynamic (comma-separated)
  -sandbox-image string    Custom sandbox Docker image
  -nopull                  Use local sandbox images
  -analysis-command string Override default analysis script
  -features string         Feature flags to enable/disable
  -list-modes              List available analysis modes
  -list-features           List available feature flags
```

**Example Usage**:
```bash
# Analyze npm package
./analyze -ecosystem npm -package async -mode dynamic,static

# Analyze local Wolfi APK
./analyze -ecosystem wolfi -package myapp -version 1.0.0 \
  -local /path/to/myapp-1.0.0.apk -mode dynamic -nopull
```

### 3. Downloader ([cmd/downloader](cmd/downloader))

**Purpose**: Dedicated service for downloading package archives

**Features**:
- Supports all tracked ecosystems
- Verifies package integrity (checksums)
- Handles caching of downloaded assets
- Prepares packages for analysis

### 4. Worker ([cmd/worker](cmd/worker))

**Purpose**: Background worker service that processes analysis jobs from the queue

**Key Responsibilities**:
- Consumes tasks from Pub/Sub or Kafka
- Instantiates sandboxes (Podman/Docker)
- Orchestrates the analysis lifecycle (Install -> Import -> Analyze)
- Collects and aggregates results
- Uploads reports to storage (S3/GCS/MinIO)

### 5. Sandboxes

#### Static Analysis Sandbox

**Location**: [sandboxes/staticanalysis](sandboxes/staticanalysis)

**Tools Integrated**:

| Tool | Purpose | Ecosystems |
|------|---------|------------|
| **OSSGadget** | Typosquatting detection | PyPI, npm, Maven, RubyGems, Crates.io, Packagist |
| **Bandit4mal** | Python malware patterns | PyPI |
| **Py2src** | Source repository finder | PyPI |
| **Lastpymile** | Source-package discrepancy | PyPI, npm |

**Docker Image**: `pakaremon/static-analysis:latest`

#### Dynamic Analysis Sandbox

**Location**: [sandboxes/dynamicanalysis](sandboxes/dynamicanalysis)

**Monitoring Capabilities**:
- **Network Traffic**: All connections, DNS queries, domains, IPs
- **File System**: Read, write, delete operations
- **Command Execution**: All shell commands
- **System Calls**: strace monitoring
- **Pattern Matching**: Yara rules

**Analysis Phases**:
1. **Install**: Install package using ecosystem's package manager
2. **Import**: Load/import package modules (triggers code execution)
3. **Custom**: Ecosystem-specific additional phases

**Supported Scripts**:
- `analyze_npm.py` - npm packages
- `analyze_pypi.py` - PyPI packages
- `analyze_maven.py` - Maven packages
- `analyze_rubygems.py` - RubyGems packages
- `analyze_crates.py` - Crates.io packages
- `analyze_packagist.py` - Packagist packages
- `analyze_wolfi_apk.py` - Wolfi APK packages

**Docker Image**: `pakaremon/dynamic-analysis:latest`

### 4. Web Dashboard

**Location**: [web/package-analysis-web](web/package-analysis-web)

**Technology Stack**:
- **Framework**: Django 5.1.6
- **Database**: PostgreSQL (production) / SQLite (development)
- **Task Queue**: Redis + Celery
- **Web Server**: Gunicorn + Nginx (production)

**Key Features**:
- Web interface for package submission
- RESTful API for programmatic access
- Real-time queue management
- Analysis results visualization
- API key authentication with rate limiting
- Smart caching (no re-analysis of completed packages)
- Multi-ecosystem support with version lookup

**Database Models**:
- `Package`: Package metadata (name, version, ecosystem)
- `ReportDynamicAnalysis`: Dynamic analysis results (JSON)
- `ReportTyposquatting`: Static analysis results
- `ReportSource`: Source repository information
- `APIKey`: API authentication keys
- `AnalysisTask`: Queue management with timeout tracking

**Queue System**:
- Single container execution (prevents resource conflicts)
- Priority-based task processing
- 30-minute timeout with auto cleanup
- Background worker auto-starts with Django
- Real-time status tracking

---

## Installation

### Prerequisites

#### System Requirements
- **OS**: Linux (Ubuntu 22.04+ recommended) or WSL2 on Windows
- **Go**: 1.23.1 or later
- **Python**: 3.10+ (for web dashboard)
- **Docker**: Latest version
- **Podman**: For sandbox execution (Linux)
- **Make**: Build automation

#### External Tools

1. **OSSGadget v0.1.422**
   ```bash
   wget https://github.com/microsoft/OSSGadget/releases/download/v0.1.422/OSSGadget_linux_0.1.422.tar.gz
   tar -xzf OSSGadget_linux_0.1.422.tar.gz
   # Build Docker image per OSSGadget docs
   ```

2. **Docker Images**
   ```bash
   docker pull pakaremon/ossgadget:latest
   docker pull pakaremon/analysis:latest
   docker pull pakaremon/dynamic-analysis:latest
   docker pull pakaremon/static-analysis:latest
   ```

### Installation Steps

#### 1. Clone Repository
```bash
git clone <repository-url>
cd pack-a-mal_prd
```

#### 2. Build Analysis Components

```bash
# Build all sandbox and analysis images
make build

# Build specific components
make build/sandbox/dynamic_analysis
make build/sandbox/static_analysis
make build/image/analysis
make build/image/scheduler
```

#### 3. Sync Sandbox Images (For Local Testing)

```bash
# Sync to Podman
make sync/sandbox/dynamic_analysis
make sync/sandbox/static_analysis

# OR sync all
make sync
```

#### 4. Install Web Dashboard Dependencies

```bash
cd web/package-analysis-web

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Bandit4mal
cd package_analysis/src/bandit4mal
python setup.py install
cd ../../..
```

---

## Deployment

### Option 1: Docker Deployment (Recommended)

**Full stack deployment with Docker Compose**

#### Quick Start
```bash
cd prd

# Build images
make build

# Start all services
make up

# Run migrations
make migrate

# Create admin user
make createsuperuser

# Access at http://localhost:8080
```

#### Services Included
- PostgreSQL database (port 5433)
- Redis cache (port 6379)
- Django backend with Gunicorn (port 8001)
- 3x Celery workers
- Flower monitoring dashboard (port 5555)
- Nginx reverse proxy (port 8080)

#### Configuration
Copy and customize environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

#### Management Commands
```bash
make logs              # View logs
make restart           # Restart services
make shell-backend     # Backend shell
make shell-db          # Database shell
make test              # Run tests
make down              # Stop services
make clean             # Remove all data
```

### Option 2: Local Analysis (Without Web Dashboard)

**For running individual package analyses**

#### Setup
```bash
# Install Podman (Linux)
sudo apt-get install podman

# Sync sandbox images
make sync
```

#### Run Analysis
```bash
# Using run_analysis.sh script
./scripts/run_analysis.sh -ecosystem npm -package async -mode dynamic

# Additional options
./scripts/run_analysis.sh \
  -ecosystem pypi \
  -package requests \
  -version 2.28.1 \
  -mode dynamic,static \
  -nopull \
  -sandbox-image custom-image

# Wolfi APK analysis
./scripts/run_analysis.sh \
  -ecosystem wolfi \
  -package myapp \
  -local /path/to/myapp.apk \
  -mode dynamic
```

### Option 3: Production Deployment

**High-availability production setup**

#### Components to Deploy

1. **Scheduler** (Job Distribution)
   ```bash
   # Build scheduler image
   make build/image/scheduler
   
   # Run scheduler
   docker run -d \
     -e OSSMALWARE_WORKER_TOPIC=<topic> \
     -e OSSMALWARE_SUBSCRIPTION_URL=<subscription> \
     pakaremon/scheduler:latest
   ```

2. **Analysis Workers** (Package Analysis)
   ```bash
   # Build analysis image
   make build/image/analysis
   
   # Run worker(s)
   docker run -d --privileged \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -e OSSMALWARE_WORKER_SUBSCRIPTION=<subscription> \
     pakaremon/analysis:latest
   ```

3. **Web Dashboard** (User Interface)
   ```bash
   cd web/package-analysis-web
   
   # Setup PostgreSQL database
   createdb packamal_prod
   createuser pakaremon
   
   # Configure settings
   export SECRET_KEY=<secure-random-key>
   export DEBUG=False
   export DATABASE_URL=postgresql://pakaremon:password@localhost/packamal_prod
   
   # Run migrations
   python manage.py migrate
   
   # Collect static files
   python manage.py collectstatic
   
   # Start with Gunicorn
   gunicorn --bind 0.0.0.0:8000 \
     --workers 4 --threads 2 \
     --timeout 300 \
     packamal.wsgi:application
   ```

4. **Nginx** (Reverse Proxy)
   ```nginx
   server {
       listen 80;
       server_name packguard.dev;
       
       location /static/ {
           alias /path/to/staticfiles/;
       }
       
       location /media/ {
           alias /path/to/media/;
       }
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Queue Worker** (Background Tasks)
   ```bash
   # Start queue worker as daemon
   python manage.py start_queue_worker --daemon
   
   # OR with systemd
   sudo systemctl start packamal-queue-worker
   sudo systemctl enable packamal-queue-worker
   ```

#### Production Checklist

- [ ] Generate secure SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use production database (PostgreSQL)
- [ ] Set up SSL/HTTPS
- [ ] Configure firewall
- [ ] Implement rate limiting
- [ ] Set up monitoring (Sentry, ELK, etc.)
- [ ] Configure automated backups
- [ ] Set up CDN for static files
- [ ] Scale workers based on load

---

## Usage Guide

### 1. Web Dashboard Usage

#### Accessing the Dashboard
- **URL**: http://localhost:8080 (Docker) or configured domain
- **Admin Panel**: http://localhost:8080/admin

#### Submit Package for Analysis

**Via Web Interface**:
1. Navigate to Dashboard
2. Select ecosystem (npm, PyPI, etc.)
3. Enter package name and version
4. Click "Submit"
5. View queue position and status
6. Results appear when analysis completes

**Via API**:
```bash
# Get API key first (see API Documentation section)

# Submit analysis
curl -X POST http://localhost:8080/api/v1/analyze/ \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "purl": "pkg:pypi/requests@2.28.1",
    "priority": 0
  }'

# Response:
{
  "success": true,
  "data": {
    "task_id": 123,
    "status": "queued",
    "queue_position": 3,
    "status_url": "http://localhost:8080/api/v1/task/123/",
    "result_url": "http://localhost:8080/media/reports/pypi/requests/2.28.1.json"
  }
}
```

#### Check Analysis Status
```bash
curl -X GET http://localhost:8080/api/v1/task/123/ \
  -H "X-API-Key: YOUR_API_KEY"
```

#### View Results
Once status is "completed", download the JSON report:
```bash
curl -X GET http://localhost:8080/media/reports/pypi/requests/2.28.1.json \
  -H "X-API-Key: YOUR_API_KEY"
```

### 2. Command-Line Analysis

#### Basic Analysis
```bash
cd pack-a-mal_prd

# Dynamic analysis only
./scripts/run_analysis.sh -ecosystem npm -package express -mode dynamic

# Static + Dynamic analysis
./scripts/run_analysis.sh -ecosystem pypi -package django -mode dynamic,static

# Specific version
./scripts/run_analysis.sh -ecosystem npm -package lodash -version 4.17.21 -mode dynamic
```

#### Local Package Analysis
```bash
# Analyze local .whl file
./scripts/run_analysis.sh \
  -ecosystem pypi \
  -package mypackage \
  -local /path/to/mypackage-1.0.0-py3-none-any.whl \
  -mode dynamic

# Analyze local .apk file
./scripts/run_analysis.sh \
  -ecosystem wolfi \
  -package myapp \
  -local /path/to/myapp-1.0.0-r0.apk \
  -mode dynamic
```

#### Custom Sandbox
```bash
./scripts/run_analysis.sh \
  -ecosystem wolfi \
  -package test \
  -local /path/to/package.apk \
  -sandbox-image 'custom-sandbox:latest' \
  -analysis-command 'analyze_custom.py' \
  -mode dynamic \
  -nopull
```

### 3. Batch Analysis
```bash
# Analyze multiple packages
./scripts/analyse-tarballs.sh /path/to/tarballs/

# The script will analyze all packages in the directory
```

### 4. Monitoring and Management

#### Queue Status
```bash
# Check queue via API
curl -X GET http://localhost:8080/api/v1/queue/status/ \
  -H "X-API-Key: YOUR_API_KEY"

# Response shows running and queued tasks
```

#### Flower Dashboard (Celery Monitoring)
- **URL**: http://localhost:5555
- **Features**: Task monitoring, worker status, task history

#### Container/Task Timeouts
```bash
# Check timeout status
curl -X GET http://localhost:8080/api/v1/timeout/status/ \
  -H "X-API-Key: YOUR_API_KEY"

# Manually trigger timeout check
curl -X POST http://localhost:8080/api/v1/timeout/check/ \
  -H "X-API-Key: YOUR_API_KEY"
```

---

## API Documentation

### Authentication

All API endpoints require an API key in the header:
```
X-API-Key: your-api-key-here
```

### Create API Key

**Via Django Shell**:
```bash
docker-compose exec backend python manage.py shell
```

```python
from package_analysis.models import APIKey

# Create API key
api_key = APIKey.objects.create(
    name="My Application",
    rate_limit_per_hour=100
)

print(f"API Key: {api_key.key}")
```

**Via Django Admin**:
1. Navigate to http://localhost:8080/admin
2. Login with superuser credentials
3. Go to "API Keys" → "Add"
4. Enter name and rate limit
5. Save and copy the generated key

### API Endpoints

#### POST /api/v1/analyze/
Submit package for analysis

**Request**:
```json
{
  "purl": "pkg:pypi/requests@2.28.1",
  "priority": 0
}
```

**Response (Queued)**:
```json
{
  "success": true,
  "data": {
    "task_id": 123,
    "status": "queued",
    "queue_position": 3,
    "status_url": "/api/v1/task/123/",
    "result_url": "/media/reports/pypi/requests/2.28.1.json"
  }
}
```

**Response (Cached)**:
```json
{
  "success": true,
  "data": {
    "task_id": 120,
    "status": "completed",
    "result_url": "/media/reports/pypi/requests/2.28.1.json",
    "message": "Analysis already exists (cached result)"
  }
}
```

#### GET /api/v1/task/{task_id}/
Get task status

**Response**:
```json
{
  "success": true,
  "data": {
    "task_id": 123,
    "purl": "pkg:pypi/requests@2.28.1",
    "status": "running",
    "package_name": "requests",
    "package_version": "2.28.1",
    "ecosystem": "pypi",
    "created_at": "2024-01-15T10:30:00Z",
    "started_at": "2024-01-15T10:31:00Z"
  }
}
```

#### GET /api/v1/queue/status/
Get queue status

**Response**:
```json
{
  "success": true,
  "data": {
    "queue_length": 5,
    "running_tasks": [...],
    "queued_tasks": [...]
  }
}
```

#### GET /api/v1/reports/
List analysis reports

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 20, max: 100)
- `status`: Filter by status (pending, queued, running, completed, failed)

**Response**:
```json
{
  "success": true,
  "data": {
    "count": 150,
    "next": "/api/v1/reports/?page=2",
    "previous": null,
    "results": [...]
  }
}
```

### Rate Limiting

- Default: 100 requests/hour per API key
- Configurable per API key
- 429 status code returned when limit exceeded

### Error Responses

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PURL",
    "message": "Invalid package URL format"
  }
}
```

**Common Error Codes**:
- `INVALID_API_KEY`: Invalid or missing API key
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INVALID_PURL`: Malformed package URL
- `PACKAGE_NOT_FOUND`: Package doesn't exist in registry
- `ANALYSIS_FAILED`: Analysis encountered an error

---

## Development Guide

### Setting Up Development Environment

#### 1. Fork and Clone
```bash
git clone <your-fork-url>
cd pack-a-mal_prd
```

#### 2. Development with Docker (Recommended)
```bash
cd prd
make build
make up
make migrate

# Code changes in prd/backend/ auto-reload
```

### Project Structure for Development

```
pack-a-mal_prd/
├── cmd/                  # Entry points (add new commands here)
├── internal/             # Internal packages (add new features)
├── sandboxes/            # Add new sandbox types
├── web/package-analysis-web/
│   ├── package_analysis/ # Django app (add new views, models)
│   └── packamal/         # Django project settings
└── prd/                  # Docker production/development environment
```

### Making Code Changes

#### Backend (Go Components)
```bash
# Make changes in cmd/, internal/, or pkg/

# Rebuild affected component
make build/image/analysis

# Test changes
go test ./...
```

#### Web Dashboard (Django)
```bash
cd prd

# Make changes in backend/package_analysis/ or backend/packamal/

# Changes auto-reload (no rebuild needed)

# Run tests
make test

# Create migrations if models changed
docker-compose exec backend python manage.py makemigrations
make migrate
```

#### Sandboxes
```bash
# Edit sandboxes/dynamicanalysis/Dockerfile or analysis scripts

# Rebuild sandbox
make build/sandbox/dynamic_analysis

# Sync to Podman for local testing
make sync/sandbox/dynamic_analysis

# Test with -nopull flag
./scripts/run_analysis.sh -ecosystem npm -package test -mode dynamic -nopull
```

### Running Tests

#### Go Tests
```bash
# All tests
go test ./...

# Specific package
go test ./internal/analysis

# With coverage
go test -cover ./...
```

#### Django Tests
```bash
cd prd
make test

# OR directly
docker-compose exec backend python manage.py test

# Specific test
docker-compose exec backend python manage.py test package_analysis.tests.TestQueueSystem
```

#### Integration Tests
```bash
# Dynamic analysis test (multiple ecosystems)
make test_dynamic_analysis

# Static analysis test
make test_static_analysis
```

### Code Style

#### Go
- Follow [Google Go Style Guide](https://google.github.io/styleguide/go/index)
- Run `gofmt` before committing
- Add comments to exported functions

#### Python/Django
- Follow PEP 8
- Use type hints where appropriate
- Document all public methods

### Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test thoroughly
3. Commit with descriptive messages
4. Push and create pull request
5. Ensure CI passes

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Troubleshooting

### Common Issues

#### 1. Docker Build Fails

**Issue**: `Error response from daemon: Get https://registry...: denied`

**Solution**:
```bash
# Login to Docker registry
docker login

# OR use different registry
export REGISTRY=myregistry.com
make build
```

#### 2. Sandbox Container Won't Start

**Issue**: Podman not found or permission denied

**Solution**:
```bash
# Install Podman (Linux)
sudo apt-get install podman

# Add user to subuid/subgid
sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 $USER

# Restart
sudo systemctl restart podman
```

#### 3. Database Connection Failed

**Issue**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Check database is running
docker-compose ps database

# Check database logs
docker-compose logs database

# Verify credentials
docker-compose exec backend env | grep POSTGRES
```

#### 4. Static Files Not Loading

**Issue**: 404 errors for CSS/JS files

**Solution**:
```bash
# Recollect static files
docker-compose exec backend python manage.py collectstatic --noinput

# Restart nginx
docker-compose restart frontend

# Check nginx logs
docker-compose logs frontend
```

#### 5. Queue Not Processing Tasks

**Issue**: Tasks stuck in "queued" status

**Solution**:
```bash
# Check worker logs
docker-compose logs celery_worker_1

# Verify Redis is running
docker-compose exec redis redis-cli ping

# Restart workers
docker-compose restart celery_worker_1 celery_worker_2 celery_worker_3
```

#### 6. Analysis Timeout

**Issue**: Task marked as failed after 30 minutes

**Solution**:
- Default timeout is 30 minutes
- For large packages, this may not be enough
- Increase timeout in `AnalysisTask` model or via API
- Check container logs for actual errors before timeout

#### 7. Yara Rules Not Loading

**Issue**: `yara-python` import error

**Solution**:
```bash
# Reinstall yara-python in virtual environment
pip uninstall yara-python
pip install --no-cache-dir yara-python

# OR rebuild Docker image
docker-compose build backend
```

### Getting Help

- **Issues**: Open issue on GitHub
- **Documentation**: Check docs/ directory
- **Community**: OpenSSF Slack #package-analysis channel
- **Logs**: Always check logs first (`docker-compose logs` or `journalctl`)

---

## Case Studies

### Solana Web3.js Supply Chain Attack

**Detection**: Pack-A-Mal successfully detected malicious versions 1.95.6 and 1.95.7

**Findings**:
- Injected code to steal private keys
- Dropper malware hosted on GitHub
- Attempts to exfiltrate `/etc/passwd` and SSH keys
- Network connections to attacker-controlled domains

**Impact**: 350,000+ weekly downloads affected

**Video**: [Case Study Analysis](https://youtu.be/uZQzMZ8dSdI)

---

## Resources

### Documentation
- [Installation Guide](INSTALLATION.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Queue System README](web/package-analysis-web/QUEUE_SYSTEM_README.md)
- [Sandbox Documentation](sandboxes/README.md)

### External Tools
- [OSSGadget](https://github.com/microsoft/OSSGadget)
- [Bandit4mal](https://github.com/lyvd/bandit4mal)
- [Py2src](https://github.com/simonepirocca/py2src)
- [Lastpymile](https://github.com/assuremoss/lastpymile)
- [Package Feeds](https://github.com/ossf/package-feeds)

### Video Demonstrations
- [Pack-A-Mal Features](https://youtu.be/I9vxdmKnqL4)
- [Solana Case Study](https://youtu.be/uZQzMZ8dSdI)

---

## License

Apache License 2.0 (typical for OpenSSF projects)

---

## Conclusion

Pack-A-Mal provides a comprehensive, production-ready platform for detecting malicious packages across multiple ecosystems. With both static and dynamic analysis capabilities, RESTful API, web dashboard, and Docker deployment options, it's a valuable tool for securing open-source software supply chains.

**Key Strengths**:
- ✅ Multi-ecosystem support (7+ package managers)
- ✅ Both static and dynamic analysis
- ✅ Production-ready with proven track record
- ✅ Scalable architecture with queue management
- ✅ Well-documented and actively maintained
- ✅ Docker-first deployment

**Get Started**:
1. Clone repository
2. Run `cd prd && make up`  
3. Access http://localhost:8080
4. Start analyzing packages!

For questions or contributions, see [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue on GitHub.
