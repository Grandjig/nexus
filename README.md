# Nexus Fraud Detection Platform

**Complete Edition v3.1.0** - Enterprise-grade fraud detection for Nigerian banking.

---

## Quick Start

### Windows
```
1. Double-click INSTALL.bat (run once)
2. Double-click START.bat
3. Open http://localhost:8000
```

### Manual
```bash
pip install -r requirements.txt
python nexus/app.py
```

---

## Modules Included

### 1. Transaction Fraud Scoring
- 47 Nigerian-specific fraud features
- Real-time scoring (<100ms)
- Amount, velocity, device, channel analysis
- SIM swap, money mule patterns

### 2. Insider Threat Detection
- Employee action monitoring
- Override abuse detection
- Data harvesting alerts
- Notice period risk tracking
- After-hours activity flagging

### 3. CBN Report Generation
- Monthly e-Fraud Returns (CBN format)
- Suspicious Transaction Reports (STR)
- Currency Transaction Reports (CTR)
- One-click Excel download

### 4. Agent/POS Fraud Detection
- Geo-fencing (CBN 10-meter rule)
- Reversal scam detection  
- Terminal cloning detection
- Unregistered agent flagging
- CAC verification tracking

### 5. Database Persistence
- SQLite (zero configuration)
- Transaction history storage
- Alert management
- Employee audit trail
- Agent profile management

---

## API Endpoints

### Transaction Fraud
```
POST /api/v1/fraud/score        - Score a transaction
POST /api/v1/fraud/score/batch  - Batch scoring
GET  /api/v1/fraud/stats        - Fraud statistics
GET  /api/v1/fraud/rules        - List fraud rules
```

### Insider Threats
```
POST /api/v1/insider/score      - Score employee action
GET  /api/v1/insider/employees  - List employees
GET  /api/v1/insider/alerts     - Insider alerts
GET  /api/v1/insider/stats      - Statistics
```

### Agent Fraud
```
POST /api/v1/agents/score       - Score POS transaction
POST /api/v1/agents/geo-fence   - Check geo-fence
GET  /api/v1/agents             - List agents
GET  /api/v1/agents/alerts      - Agent alerts
```

### CBN Reports
```
GET /api/v1/reports/available       - List reports
GET /api/v1/reports/efraud/download - Download e-Fraud
GET /api/v1/reports/str/download    - Download STR
GET /api/v1/reports/ctr/download    - Download CTR
```

### Alerts & Cases
```
GET  /api/v1/alerts             - List all alerts
GET  /api/v1/alerts/{id}        - Get alert details
POST /api/v1/alerts/{id}/review - Review alert
```

---

## Dashboard

Open http://localhost:8000 for the web dashboard:

- **Transactions Tab**: Real-time fraud monitoring
- **Agent Fraud Tab**: POS/Agent monitoring with geo-fence
- **Insider Threats Tab**: Employee risk monitoring
- **Reports Tab**: CBN report generation

---

## Database

SQLite database is stored in:
```
Nexus-FraudDetection/data/nexus.db
```

To reset:
```bash
rm data/nexus.db
python nexus/app.py
```

---

## Configuration

Environment variables (optional):
```
NEXUS_HOST=0.0.0.0
NEXUS_PORT=8000
NEXUS_DB_PATH=data/nexus.db
```

---

## License

Proprietary - All Rights Reserved

---

**Built for Nigerian Banking** 🇳🇬
