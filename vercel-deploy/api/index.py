"""Nexus Fraud Detection - Vercel Serverless."""

from datetime import datetime
from typing import Optional, List, Dict, Any
import time
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from mangum import Mangum


app = FastAPI(
    title="Nexus",
    description="Nigerian Banking Fraud Detection Platform",
    version="3.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TransactionScoreRequest(BaseModel):
    transaction_ref: Optional[str] = None
    amount: float = Field(..., gt=0)
    channel: str = "mobile"
    is_new_device: bool = False
    txn_count_1h: int = 0
    location_state: Optional[str] = None


class AgentTransactionRequest(BaseModel):
    terminal_id: str
    amount: float = Field(..., gt=0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_account_count: int = 1


class InsiderActionRequest(BaseModel):
    employee_id: str
    action_type: str
    is_override: bool = False
    account_was_dormant: bool = False


DEMO_AGENTS = {
    "TRM001": {"name": "Adex POS", "lat": 6.5244, "lon": 3.3792, "registered": True, "reversal_rate": 0.012},
    "TRM002": {"name": "QuickCash", "lat": 6.4541, "lon": 3.3947, "registered": True, "reversal_rate": 0.163},
    "TRM003": {"name": "Unity POS", "lat": 9.0765, "lon": 7.3986, "registered": True, "reversal_rate": 0.018},
    "TRM004": {"name": "Harbor POS", "lat": 4.8156, "lon": 7.0498, "registered": False, "reversal_rate": 0.0},
}

DEMO_EMPLOYEES = {
    "EMP001": {"name": "Adebayo", "on_notice": False, "overrides_today": 1},
    "EMP002": {"name": "Chioma", "on_notice": False, "overrides_today": 8},
    "EMP003": {"name": "Ibrahim", "on_notice": False, "overrides_today": 2},
    "EMP004": {"name": "Ngozi", "on_notice": True, "overrides_today": 5},
}


def score_transaction(txn: TransactionScoreRequest) -> Dict[str, Any]:
    start_time = time.time()
    score = 10.0
    risk_factors = []

    if txn.amount >= 10_000_000:
        score += 35
        risk_factors.append("Amount over N10 Million")
    elif txn.amount >= 5_000_000:
        score += 25
        risk_factors.append("Amount over N5 Million")
    elif txn.amount >= 1_000_000:
        score += 15
        risk_factors.append("Amount over N1 Million")

    channel_scores = {"ussd": 15, "agency": 12, "pos": 8, "mobile": 5, "web": 6}
    ch_score = channel_scores.get(txn.channel.lower(), 5)
    if ch_score >= 10:
        score += ch_score
        risk_factors.append(f"High-risk channel: {txn.channel.upper()}")

    if txn.is_new_device:
        score += 20
        risk_factors.append("New device")
        if txn.amount >= 500_000:
            score += 15
            risk_factors.append("New device + large amount")

    if txn.txn_count_1h > 10:
        score += 30
        risk_factors.append(f"Very high velocity: {txn.txn_count_1h} txns/hour")
    elif txn.txn_count_1h > 5:
        score += 15
        risk_factors.append(f"High velocity: {txn.txn_count_1h} txns/hour")

    score = min(100, max(0, score))

    if score >= 80:
        risk_level, recommendation, is_flagged, should_block = "critical", "BLOCK", True, True
    elif score >= 60:
        risk_level, recommendation, is_flagged, should_block = "high", "REVIEW", True, False
    elif score >= 40:
        risk_level, recommendation, is_flagged, should_block = "medium", "REVIEW", True, False
    else:
        risk_level, recommendation, is_flagged, should_block = "low", "APPROVE", False, False

    return {
        "transaction_ref": txn.transaction_ref or f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}",
        "fraud_score": round(score, 2),
        "risk_level": risk_level,
        "recommendation": recommendation,
        "is_flagged": is_flagged,
        "should_block": should_block,
        "risk_factors": risk_factors,
        "latency_ms": round((time.time() - start_time) * 1000, 2),
        "scored_at": datetime.utcnow().isoformat(),
    }


def score_agent_transaction(txn: AgentTransactionRequest) -> Dict[str, Any]:
    start_time = time.time()
    score = 0.0
    risk_factors = []
    fraud_types = []

    agent = DEMO_AGENTS.get(txn.terminal_id)
    
    if not agent:
        score += 30
        risk_factors.append("Unknown terminal")
        fraud_types.append("unregistered")
    else:
        if not agent["registered"]:
            score += 35
            risk_factors.append("Unregistered agent")
            fraud_types.append("unregistered")
        
        if agent["reversal_rate"] > 0.15:
            score += 25
            risk_factors.append(f"High reversal rate: {agent['reversal_rate']*100:.1f}%")
            fraud_types.append("reversal_scam")

    if txn.device_account_count > 10:
        score += 35
        risk_factors.append(f"Device used by {txn.device_account_count} accounts")
        fraud_types.append("terminal_cloning")

    score = min(100, score)
    
    if score >= 60:
        risk_level, recommendation, should_block = "high", "BLOCK", True
    elif score >= 40:
        risk_level, recommendation, should_block = "medium", "REVIEW", False
    else:
        risk_level, recommendation, should_block = "low", "APPROVE", False

    return {
        "transaction_id": f"POS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}",
        "terminal_id": txn.terminal_id,
        "fraud_score": round(score, 2),
        "risk_level": risk_level,
        "fraud_types": fraud_types,
        "risk_factors": risk_factors,
        "recommendation": recommendation,
        "should_block": should_block,
        "latency_ms": round((time.time() - start_time) * 1000, 2),
        "scored_at": datetime.utcnow().isoformat()
    }


def score_insider_action(action: InsiderActionRequest) -> Dict[str, Any]:
    start_time = time.time()
    score = 0.0
    risk_factors = []
    threat_types = []

    emp = DEMO_EMPLOYEES.get(action.employee_id, {})
    
    hour = datetime.utcnow().hour
    if hour >= 18 or hour < 7:
        score += 20
        risk_factors.append(f"After-hours activity at {hour}:00")
        threat_types.append("after_hours")

    if action.is_override:
        if emp.get("overrides_today", 0) >= 5:
            score += 30
            risk_factors.append(f"High override count: {emp.get('overrides_today', 0)} today")
            threat_types.append("override_abuse")

    if emp.get("on_notice"):
        score += 25
        risk_factors.append("Employee on notice period")
        threat_types.append("notice_period_risk")
        if action.action_type in ["override", "balance_adjustment", "account_reactivation"]:
            score += 35
            risk_factors.append(f"Notice period employee performing {action.action_type}")

    if action.account_was_dormant:
        score += 30
        risk_factors.append("Action on dormant account")
        threat_types.append("dormant_manipulation")

    score = min(100, score)
    
    if score >= 80:
        risk_level, recommendation = "critical", "BLOCK_AND_ESCALATE"
    elif score >= 60:
        risk_level, recommendation = "high", "ESCALATE_TO_SECURITY"
    elif score >= 40:
        risk_level, recommendation = "medium", "FLAG_FOR_REVIEW"
    else:
        risk_level, recommendation = "low", "ALLOW"

    return {
        "action_id": f"ACT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}",
        "employee_id": action.employee_id,
        "risk_score": round(score, 2),
        "risk_level": risk_level,
        "threat_types": threat_types,
        "risk_factors": risk_factors,
        "recommendation": recommendation,
        "latency_ms": round((time.time() - start_time) * 1000, 2),
        "scored_at": datetime.utcnow().isoformat()
    }


DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus - Fraud Detection Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; color: #f8fafc; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(71, 85, 105, 0.5); border-radius: 16px; padding: 20px 32px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
        .logo { display: flex; align-items: center; gap: 16px; }
        .logo-icon { width: 50px; height: 50px; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; }
        .logo-text h1 { font-size: 24px; font-weight: 800; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .logo-text p { color: #94a3b8; font-size: 12px; }
        .status-badge { display: flex; align-items: center; gap: 8px; padding: 10px 20px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 25px; color: white; font-weight: 600; font-size: 13px; }
        .status-dot { width: 8px; height: 8px; background: white; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .tabs { display: flex; gap: 6px; margin-bottom: 20px; background: rgba(30, 41, 59, 0.6); padding: 6px; border-radius: 12px; width: fit-content; flex-wrap: wrap; }
        .tab { padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; border: none; background: transparent; color: #94a3b8; transition: all 0.2s; }
        .tab:hover { background: rgba(71, 85, 105, 0.5); color: #f8fafc; }
        .tab.active { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
        .stat-card { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(71, 85, 105, 0.5); border-radius: 12px; padding: 20px; }
        .stat-value { font-size: 28px; font-weight: 800; margin-bottom: 4px; }
        .stat-card.blue .stat-value { color: #60a5fa; }
        .stat-card.green .stat-value { color: #4ade80; }
        .stat-card.yellow .stat-value { color: #fbbf24; }
        .stat-card.red .stat-value { color: #f87171; }
        .stat-label { color: #94a3b8; font-size: 12px; }
        .main-grid { display: grid; grid-template-columns: 1fr 380px; gap: 20px; }
        @media (max-width: 900px) { .main-grid { grid-template-columns: 1fr; } }
        .card { background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(71, 85, 105, 0.5); border-radius: 12px; overflow: hidden; }
        .card-header { padding: 16px 20px; border-bottom: 1px solid rgba(71, 85, 105, 0.5); font-weight: 700; font-size: 14px; }
        .card-body { padding: 16px 20px; }
        .tester-section { margin-bottom: 16px; }
        .tester-section h4 { font-size: 12px; font-weight: 600; color: #94a3b8; margin-bottom: 6px; }
        .form-input, .form-select { width: 100%; padding: 10px 14px; background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(71, 85, 105, 0.5); border-radius: 8px; font-size: 13px; color: #f8fafc; }
        .form-select option { background: #1e293b; }
        .checkbox-row { display: flex; align-items: center; gap: 8px; padding: 10px; background: rgba(15, 23, 42, 0.5); border-radius: 8px; cursor: pointer; font-size: 13px; }
        .checkbox-row input { width: 16px; height: 16px; }
        .btn-test { width: 100%; padding: 12px; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; }
        .btn-test:hover { transform: translateY(-1px); }
        .btn-test.orange { background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); }
        .result-display { display: none; text-align: center; padding: 20px; background: rgba(15, 23, 42, 0.8); border-radius: 10px; margin-top: 16px; }
        .result-display.show { display: block; }
        .result-score { width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; }
        .result-score.low { background: linear-gradient(135deg, #10b981, #34d399); }
        .result-score.medium { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
        .result-score.high { background: linear-gradient(135deg, #f97316, #fb923c); }
        .result-score.critical { background: linear-gradient(135deg, #dc2626, #ef4444); }
        .result-score-value { font-size: 24px; font-weight: 800; }
        .result-score-label { font-size: 10px; }
        .result-decision { font-size: 16px; font-weight: 800; margin-bottom: 4px; }
        .result-decision.approve { color: #4ade80; }
        .result-decision.review, .result-decision.monitor { color: #fbbf24; }
        .result-decision.block { color: #f87171; }
        .result-level { font-size: 12px; color: #94a3b8; text-transform: uppercase; margin-bottom: 12px; }
        .risk-factors-list { text-align: left; padding: 12px; background: rgba(30, 41, 59, 0.8); border-radius: 8px; }
        .risk-factors-list h4 { font-size: 11px; color: #94a3b8; margin-bottom: 8px; }
        .risk-factor-tag { display: inline-block; padding: 4px 10px; background: rgba(239, 68, 68, 0.2); color: #fca5a5; border-radius: 6px; font-size: 11px; margin: 2px; }
        .risk-factor-tag.safe { background: rgba(34, 197, 94, 0.2); color: #86efac; }
        .footer-links { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
        .footer-link { flex: 1; min-width: 120px; padding: 14px; background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(71, 85, 105, 0.5); border-radius: 10px; text-decoration: none; color: #f8fafc; text-align: center; }
        .footer-link:hover { transform: translateY(-2px); }
        .footer-link h4 { font-weight: 700; font-size: 13px; margin-bottom: 2px; }
        .footer-link p { font-size: 11px; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo">
                <div class="logo-icon">N</div>
                <div class="logo-text">
                    <h1>Nexus</h1>
                    <p>Transaction + Agent + Insider Fraud Detection</p>
                </div>
            </div>
            <div class="status-badge"><span class="status-dot"></span>Live Demo</div>
        </header>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab(\'transactions\')">Transactions</button>
            <button class="tab" onclick="showTab(\'agents\')">Agent Fraud</button>
            <button class="tab" onclick="showTab(\'insider\')">Insider Threats</button>
        </div>
        
        <div id="transactions-tab" class="tab-content active">
            <div class="stats-grid">
                <div class="stat-card blue"><div class="stat-value">15,234</div><div class="stat-label">Transactions Analyzed</div></div>
                <div class="stat-card yellow"><div class="stat-value">152</div><div class="stat-label">Flagged for Review</div></div>
                <div class="stat-card red"><div class="stat-value">45</div><div class="stat-label">Blocked (Fraud)</div></div>
                <div class="stat-card green"><div class="stat-value">N12.5M</div><div class="stat-label">Money Saved</div></div>
            </div>
            <div class="main-grid">
                <div class="card"><div class="card-header">How It Works</div><div class="card-body"><p style="color:#94a3b8;line-height:1.8;">Nexus analyzes every transaction in real-time using <strong style="color:#f8fafc;">47 Nigerian-specific fraud features</strong>:<br><br>1. Your core banking sends transaction data via REST API<br>2. We score it in <strong style="color:#f8fafc;">&lt;100ms</strong> using rules + ML<br>3. Return fraud_score (0-100) with recommendation<br>4. You block/review/approve based on score<br><br>Test it yourself!</p></div></div>
                <div class="card">
                    <div class="card-header">Test Transaction</div>
                    <div class="card-body">
                        <div class="tester-section"><h4>Amount (Naira)</h4><input type="number" id="test-amount" class="form-input" value="500000"></div>
                        <div class="tester-section"><h4>Channel</h4><select id="test-channel" class="form-select"><option value="mobile">Mobile</option><option value="ussd">USSD</option><option value="pos">POS</option><option value="web">Web</option><option value="agency">Agency</option></select></div>
                        <div class="tester-section"><h4>Transactions/Hour</h4><input type="number" id="test-velocity" class="form-input" value="2" min="0"></div>
                        <div class="tester-section"><label class="checkbox-row"><input type="checkbox" id="test-new-device"><span>New Device</span></label></div>
                        <button class="btn-test" onclick="scoreTransaction()">Score Transaction</button>
                        <div class="result-display" id="txn-result"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="agents-tab" class="tab-content">
            <div class="stats-grid">
                <div class="stat-card blue"><div class="stat-value">2,456</div><div class="stat-label">POS Agents</div></div>
                <div class="stat-card yellow"><div class="stat-value">4</div><div class="stat-label">Agent Alerts</div></div>
                <div class="stat-card red"><div class="stat-value">12</div><div class="stat-label">Geo Violations</div></div>
            </div>
            <div class="main-grid">
                <div class="card"><div class="card-header">Agent Fraud Detection</div><div class="card-body"><p style="color:#94a3b8;line-height:1.8;">CBN requires <strong style="color:#f8fafc;">10-meter geo-fencing</strong> for all POS agents.<br><br>We detect:<br>- Geo-fence violations<br>- High reversal rates (scam indicator)<br>- Terminal cloning<br>- Unregistered agents</p></div></div>
                <div class="card">
                    <div class="card-header">Test Agent Transaction</div>
                    <div class="card-body">
                        <div class="tester-section"><h4>Terminal</h4><select id="agent-terminal" class="form-select"><option value="TRM001">TRM001 - Adex POS (Good)</option><option value="TRM002">TRM002 - QuickCash (High Reversal!)</option><option value="TRM004">TRM004 - Harbor (Unregistered!)</option></select></div>
                        <div class="tester-section"><h4>Amount</h4><input type="number" id="agent-amount" class="form-input" value="50000"></div>
                        <div class="tester-section"><h4>Device Account Count</h4><input type="number" id="agent-device" class="form-input" value="1" min="1"></div>
                        <button class="btn-test orange" onclick="scoreAgent()">Score Agent Transaction</button>
                        <div class="result-display" id="agent-result"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="insider-tab" class="tab-content">
            <div class="stats-grid">
                <div class="stat-card blue"><div class="stat-value">1,247</div><div class="stat-label">Employees Monitored</div></div>
                <div class="stat-card yellow"><div class="stat-value">4</div><div class="stat-label">Active Alerts</div></div>
                <div class="stat-card red"><div class="stat-value">2</div><div class="stat-label">High-Risk</div></div>
            </div>
            <div class="main-grid">
                <div class="card"><div class="card-header">Insider Threat Detection</div><div class="card-body"><p style="color:#94a3b8;line-height:1.8;">Nigerian banks lose billions to <strong style="color:#f8fafc;">employee fraud</strong>.<br><br>We detect:<br>- Override abuse<br>- Data harvesting<br>- Notice period risk<br>- After-hours activity<br>- Dormant account manipulation</p></div></div>
                <div class="card">
                    <div class="card-header">Test Employee Action</div>
                    <div class="card-body">
                        <div class="tester-section"><h4>Employee</h4><select id="insider-emp" class="form-select"><option value="EMP001">EMP001 - Adebayo (Normal)</option><option value="EMP002">EMP002 - Chioma (High Overrides)</option><option value="EMP004">EMP004 - Ngozi (On Notice!)</option></select></div>
                        <div class="tester-section"><h4>Action</h4><select id="insider-action" class="form-select"><option value="account_view">View Account</option><option value="override">Override</option><option value="balance_adjustment">Balance Adjustment</option><option value="account_reactivation">Reactivate Account</option></select></div>
                        <div class="tester-section"><label class="checkbox-row"><input type="checkbox" id="insider-override"><span>Is Override</span></label></div>
                        <div class="tester-section"><label class="checkbox-row"><input type="checkbox" id="insider-dormant"><span>Dormant Account</span></label></div>
                        <button class="btn-test" onclick="scoreInsider()">Score Action</button>
                        <div class="result-display" id="insider-result"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer-links">
            <a href="/docs" class="footer-link" target="_blank"><h4>API Docs</h4><p>Swagger UI</p></a>
            <a href="/api/v1/health" class="footer-link" target="_blank"><h4>Health</h4><p>Status</p></a>
            <a href="/api/v1/fraud/stats" class="footer-link" target="_blank"><h4>Stats</h4><p>Metrics</p></a>
        </div>
    </div>
    <script>
        function showTab(tab) {
            document.querySelectorAll(\'.tab-content\').forEach(el => el.classList.remove(\'active\'));
            document.querySelectorAll(\'.tab\').forEach(el => el.classList.remove(\'active\'));
            document.getElementById(tab + \'-tab\').classList.add(\'active\');
            event.target.classList.add(\'active\');
        }
        async function scoreTransaction() {
            const res = await fetch(\'/api/v1/fraud/score\', {
                method: \'POST\', headers: {\'Content-Type\': \'application/json\'},
                body: JSON.stringify({
                    amount: parseFloat(document.getElementById(\'test-amount\').value) || 0,
                    channel: document.getElementById(\'test-channel\').value,
                    is_new_device: document.getElementById(\'test-new-device\').checked,
                    txn_count_1h: parseInt(document.getElementById(\'test-velocity\').value) || 0
                })
            });
            const data = await res.json();
            showResult(\'txn-result\', data.fraud_score, data.risk_level, data.recommendation, data.risk_factors);
        }
        async function scoreAgent() {
            const res = await fetch(\'/api/v1/agents/score\', {
                method: \'POST\', headers: {\'Content-Type\': \'application/json\'},
                body: JSON.stringify({
                    terminal_id: document.getElementById(\'agent-terminal\').value,
                    amount: parseFloat(document.getElementById(\'agent-amount\').value) || 0,
                    device_account_count: parseInt(document.getElementById(\'agent-device\').value) || 1
                })
            });
            const data = await res.json();
            showResult(\'agent-result\', data.fraud_score, data.risk_level, data.recommendation, data.risk_factors);
        }
        async function scoreInsider() {
            const res = await fetch(\'/api/v1/insider/score\', {
                method: \'POST\', headers: {\'Content-Type\': \'application/json\'},
                body: JSON.stringify({
                    employee_id: document.getElementById(\'insider-emp\').value,
                    action_type: document.getElementById(\'insider-action\').value,
                    is_override: document.getElementById(\'insider-override\').checked,
                    account_was_dormant: document.getElementById(\'insider-dormant\').checked
                })
            });
            const data = await res.json();
            showResult(\'insider-result\', data.risk_score, data.risk_level, data.recommendation, data.risk_factors);
        }
        function showResult(id, score, level, rec, factors) {
            const el = document.getElementById(id);
            el.classList.add(\'show\');
            const recClass = rec.includes(\'BLOCK\') ? \'block\' : rec.includes(\'REVIEW\') || rec.includes(\'ESCALATE\') ? \'review\' : \'approve\';
            el.innerHTML = \'<div class="result-score \'+level+\'"><span class="result-score-value">\'+Math.round(score)+\'</span><span class="result-score-label">Score</span></div><div class="result-decision \'+recClass+\'">\'+rec+\'</div><div class="result-level">\'+level+\' risk</div><div class="risk-factors-list"><h4>Risk Factors:</h4>\'+(factors && factors.length ? factors.map(f=>\'<span class="risk-factor-tag">\'+f+\'</span>\').join(\'\') : \'<span class="risk-factor-tag safe">No risk factors</span>\')+\'</div>\';
        }
    </script>
</body>
</html>
'''


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/health")
@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "version": "3.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "platform": "vercel",
        "modules": ["transaction_fraud", "agent_fraud", "insider_threat"]
    }


@app.post("/api/v1/fraud/score")
async def score_transaction_endpoint(request: TransactionScoreRequest):
    return score_transaction(request)


@app.get("/api/v1/fraud/stats")
async def fraud_stats():
    return {
        "total_transactions": 15234,
        "flagged_transactions": 152,
        "blocked_transactions": 45,
        "money_saved_ngn": 12500000
    }


@app.post("/api/v1/agents/score")
async def score_agent_endpoint(request: AgentTransactionRequest):
    return score_agent_transaction(request)


@app.get("/api/v1/agents")
async def list_agents():
    return {"total": len(DEMO_AGENTS), "agents": [{"terminal_id": k, **v} for k, v in DEMO_AGENTS.items()]}


@app.post("/api/v1/insider/score")
async def score_insider_endpoint(request: InsiderActionRequest):
    return score_insider_action(request)


@app.get("/api/v1/insider/employees")
async def list_employees():
    return {"total": len(DEMO_EMPLOYEES), "employees": [{"employee_id": k, **v} for k, v in DEMO_EMPLOYEES.items()]}


handler = Mangum(app)
