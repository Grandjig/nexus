"""Database module for Nexus - SQLite persistence layer.

Provides:
- Async SQLite database operations
- Automatic schema creation
- CRUD operations for all entities
"""

import aiosqlite
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
import asyncio


# Database path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "nexus.db")


# =============================================================================
# SCHEMA DEFINITION
# =============================================================================

SCHEMA = """
-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    bank_id TEXT DEFAULT 'demo',
    transaction_ref TEXT UNIQUE NOT NULL,
    channel TEXT NOT NULL,
    transaction_type TEXT,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'NGN',
    source_account TEXT,
    dest_account TEXT,
    dest_account_name TEXT,
    location_state TEXT,
    device_id TEXT,
    is_new_device INTEGER DEFAULT 0,
    txn_count_1h INTEGER DEFAULT 0,
    txn_count_24h INTEGER DEFAULT 0,
    fraud_score REAL,
    risk_level TEXT,
    recommendation TEXT,
    is_flagged INTEGER DEFAULT 0,
    should_block INTEGER DEFAULT 0,
    risk_factors TEXT,  -- JSON array
    triggered_rules TEXT,  -- JSON array
    status TEXT DEFAULT 'pending',
    transaction_time TEXT,
    scored_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_txn_ref ON transactions(transaction_ref);
CREATE INDEX IF NOT EXISTS idx_txn_time ON transactions(transaction_time);
CREATE INDEX IF NOT EXISTS idx_txn_flagged ON transactions(is_flagged);
CREATE INDEX IF NOT EXISTS idx_txn_score ON transactions(fraud_score);

-- Fraud alerts table
CREATE TABLE IF NOT EXISTS fraud_alerts (
    id TEXT PRIMARY KEY,
    bank_id TEXT DEFAULT 'demo',
    transaction_id TEXT,
    transaction_ref TEXT,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    title TEXT,
    description TEXT,
    fraud_score REAL,
    risk_factors TEXT,  -- JSON array
    triggered_rules TEXT,  -- JSON array
    amount REAL,
    channel TEXT,
    account TEXT,
    assigned_to TEXT,
    reviewed_by TEXT,
    review_decision TEXT,
    review_notes TEXT,
    reviewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_alert_status ON fraud_alerts(status);
CREATE INDEX IF NOT EXISTS idx_alert_severity ON fraud_alerts(severity);

-- Insider alerts table
CREATE TABLE IF NOT EXISTS insider_alerts (
    id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    employee_name TEXT,
    action_type TEXT NOT NULL,
    threat_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    risk_score REAL,
    description TEXT,
    branch_code TEXT,
    risk_factors TEXT,  -- JSON array
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    employee_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    branch_code TEXT,
    department TEXT,
    role TEXT,
    usual_branches TEXT,  -- JSON array
    accounts_accessed_today INTEGER DEFAULT 0,
    accounts_accessed_without_txn INTEGER DEFAULT 0,
    overrides_today INTEGER DEFAULT 0,
    overrides_30d INTEGER DEFAULT 0,
    peer_avg_overrides_30d REAL DEFAULT 5.0,
    after_hours_logins_7d INTEGER DEFAULT 0,
    is_on_notice INTEGER DEFAULT 0,
    notice_end_date TEXT,
    linked_to_flagged_accounts INTEGER DEFAULT 0,
    transactions_with_same_accounts INTEGER DEFAULT 0,
    risk_score REAL DEFAULT 0,
    risk_level TEXT DEFAULT 'low',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);

-- Agents/POS terminals table
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    agent_id TEXT UNIQUE NOT NULL,
    agent_code TEXT,
    business_name TEXT NOT NULL,
    terminal_id TEXT UNIQUE NOT NULL,
    is_registered INTEGER DEFAULT 1,
    cac_verified INTEGER DEFAULT 0,
    kyc_level TEXT DEFAULT 'basic',
    is_single_principal INTEGER DEFAULT 1,
    registered_latitude REAL,
    registered_longitude REAL,
    registered_state TEXT,
    registered_lga TEXT,
    geo_fence_enabled INTEGER DEFAULT 1,
    geo_fence_radius_meters INTEGER DEFAULT 10,
    total_transactions_30d INTEGER DEFAULT 0,
    total_volume_30d REAL DEFAULT 0,
    avg_transaction_amount REAL DEFAULT 0,
    reversal_count_30d INTEGER DEFAULT 0,
    reversal_rate REAL DEFAULT 0,
    risk_score REAL DEFAULT 0,
    risk_level TEXT DEFAULT 'low',
    is_flagged INTEGER DEFAULT 0,
    flagged_reason TEXT,
    last_transaction_time TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_terminal ON agents(terminal_id);
CREATE INDEX IF NOT EXISTS idx_agent_risk ON agents(risk_score);

-- Agent transactions table
CREATE TABLE IF NOT EXISTS agent_transactions (
    id TEXT PRIMARY KEY,
    terminal_id TEXT NOT NULL,
    agent_code TEXT,
    amount REAL NOT NULL,
    transaction_type TEXT,
    latitude REAL,
    longitude REAL,
    device_id TEXT,
    device_account_count INTEGER DEFAULT 1,
    fraud_score REAL,
    risk_level TEXT,
    fraud_types TEXT,  -- JSON array
    risk_factors TEXT,  -- JSON array
    recommendation TEXT,
    should_block INTEGER DEFAULT 0,
    geo_check TEXT,  -- JSON
    transaction_time TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    customer_id TEXT UNIQUE NOT NULL,
    bvn TEXT,
    first_name TEXT,
    last_name TEXT,
    phone_primary TEXT,
    email TEXT,
    state TEXT,
    lga TEXT,
    kyc_level TEXT DEFAULT 'basic',
    risk_score REAL DEFAULT 50,
    is_pep INTEGER DEFAULT 0,
    is_sanctioned INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    customer_id TEXT,
    account_number TEXT UNIQUE NOT NULL,
    account_name TEXT,
    account_type TEXT DEFAULT 'savings',
    current_balance REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Stats table (for tracking metrics)
CREATE TABLE IF NOT EXISTS daily_stats (
    id TEXT PRIMARY KEY,
    stat_date TEXT NOT NULL,
    total_transactions INTEGER DEFAULT 0,
    total_volume REAL DEFAULT 0,
    flagged_transactions INTEGER DEFAULT 0,
    blocked_transactions INTEGER DEFAULT 0,
    money_saved REAL DEFAULT 0,
    insider_alerts INTEGER DEFAULT 0,
    agent_alerts INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stat_date)
);
"""


# =============================================================================
# DATABASE CLASS
# =============================================================================

class Database:
    """Async SQLite database manager."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        """Connect to database and ensure schema exists."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        
        # Enable foreign keys
        await self._connection.execute("PRAGMA foreign_keys = ON")
        
        # Create schema
        await self._connection.executescript(SCHEMA)
        await self._connection.commit()
        
        print(f"[DB] Connected to {self.db_path}")
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._connection:
            raise RuntimeError("Database not connected")
        return self._connection
    
    # =========================================================================
    # TRANSACTIONS
    # =========================================================================
    
    async def save_transaction(self, txn: Dict[str, Any]) -> str:
        """Save a scored transaction."""
        txn_id = txn.get("id") or str(uuid4())
        
        await self.conn.execute("""
            INSERT OR REPLACE INTO transactions (
                id, transaction_ref, channel, transaction_type, amount,
                source_account, dest_account, location_state, device_id,
                is_new_device, txn_count_1h, txn_count_24h,
                fraud_score, risk_level, recommendation, is_flagged, should_block,
                risk_factors, triggered_rules, status, transaction_time, scored_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn_id,
            txn.get("transaction_ref"),
            txn.get("channel"),
            txn.get("transaction_type", "debit"),
            txn.get("amount"),
            txn.get("source_account"),
            txn.get("dest_account"),
            txn.get("location_state"),
            txn.get("device_id"),
            1 if txn.get("is_new_device") else 0,
            txn.get("txn_count_1h", 0),
            txn.get("txn_count_24h", 0),
            txn.get("fraud_score"),
            txn.get("risk_level"),
            txn.get("recommendation"),
            1 if txn.get("is_flagged") else 0,
            1 if txn.get("should_block") else 0,
            json.dumps(txn.get("risk_factors", [])),
            json.dumps(txn.get("triggered_rules", [])),
            txn.get("status", "completed"),
            txn.get("transaction_time") or datetime.utcnow().isoformat(),
            txn.get("scored_at") or datetime.utcnow().isoformat(),
        ))
        await self.conn.commit()
        return txn_id
    
    async def get_transactions(
        self,
        limit: int = 100,
        offset: int = 0,
        flagged_only: bool = False,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get transactions with optional filtering."""
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        if flagged_only:
            query += " AND is_flagged = 1"
        if min_score is not None:
            query += " AND fraud_score >= ?"
            params.append(min_score)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    async def get_transaction_by_ref(self, ref: str) -> Optional[Dict[str, Any]]:
        """Get transaction by reference."""
        async with self.conn.execute(
            "SELECT * FROM transactions WHERE transaction_ref = ?", (ref,)
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    async def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics."""
        stats = {}
        
        # Total count
        async with self.conn.execute("SELECT COUNT(*) FROM transactions") as cursor:
            stats["total_transactions"] = (await cursor.fetchone())[0]
        
        # Flagged count
        async with self.conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE is_flagged = 1"
        ) as cursor:
            stats["flagged_transactions"] = (await cursor.fetchone())[0]
        
        # Blocked count
        async with self.conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE should_block = 1"
        ) as cursor:
            stats["blocked_transactions"] = (await cursor.fetchone())[0]
        
        # Total volume
        async with self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions"
        ) as cursor:
            stats["total_volume"] = (await cursor.fetchone())[0]
        
        # Money saved (blocked transactions amount)
        async with self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE should_block = 1"
        ) as cursor:
            stats["money_saved"] = (await cursor.fetchone())[0]
        
        # Average score
        async with self.conn.execute(
            "SELECT COALESCE(AVG(fraud_score), 0) FROM transactions"
        ) as cursor:
            stats["avg_fraud_score"] = round((await cursor.fetchone())[0], 2)
        
        # By risk level
        async with self.conn.execute("""
            SELECT risk_level, COUNT(*) as count 
            FROM transactions 
            WHERE risk_level IS NOT NULL
            GROUP BY risk_level
        """) as cursor:
            stats["by_risk_level"] = {
                row["risk_level"]: row["count"] 
                for row in await cursor.fetchall()
            }
        
        # By channel
        async with self.conn.execute("""
            SELECT channel, COUNT(*) as count, SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END) as flagged
            FROM transactions
            WHERE channel IS NOT NULL
            GROUP BY channel
        """) as cursor:
            stats["by_channel"] = {
                row["channel"]: {"total": row["count"], "flagged": row["flagged"]}
                for row in await cursor.fetchall()
            }
        
        return stats
    
    # =========================================================================
    # FRAUD ALERTS
    # =========================================================================
    
    async def save_alert(self, alert: Dict[str, Any]) -> str:
        """Save a fraud alert."""
        alert_id = alert.get("id") or str(uuid4())
        
        await self.conn.execute("""
            INSERT OR REPLACE INTO fraud_alerts (
                id, transaction_id, transaction_ref, alert_type, severity, status,
                title, description, fraud_score, risk_factors, triggered_rules,
                amount, channel, account, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_id,
            alert.get("transaction_id"),
            alert.get("transaction_ref"),
            alert.get("alert_type", "fraud_detection"),
            alert.get("severity", "medium"),
            alert.get("status", "pending"),
            alert.get("title"),
            alert.get("description"),
            alert.get("fraud_score"),
            json.dumps(alert.get("risk_factors", [])),
            json.dumps(alert.get("triggered_rules", [])),
            alert.get("amount"),
            alert.get("channel"),
            alert.get("account"),
            datetime.utcnow().isoformat(),
        ))
        await self.conn.commit()
        return alert_id
    
    async def get_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get fraud alerts."""
        query = "SELECT * FROM fraud_alerts WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    async def update_alert(self, alert_id: str, updates: Dict[str, Any]) -> bool:
        """Update an alert."""
        allowed_fields = ["status", "assigned_to", "reviewed_by", "review_decision", "review_notes"]
        set_clauses = []
        params = []
        
        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"{field} = ?")
                params.append(updates[field])
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        if updates.get("status") == "resolved":
            set_clauses.append("reviewed_at = ?")
            params.append(datetime.utcnow().isoformat())
        
        params.append(alert_id)
        
        await self.conn.execute(
            f"UPDATE fraud_alerts SET {', '.join(set_clauses)} WHERE id = ?",
            params
        )
        await self.conn.commit()
        return True
    
    async def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        stats = {}
        
        async with self.conn.execute("SELECT COUNT(*) FROM fraud_alerts") as cursor:
            stats["total"] = (await cursor.fetchone())[0]
        
        async with self.conn.execute(
            "SELECT COUNT(*) FROM fraud_alerts WHERE status = 'pending'"
        ) as cursor:
            stats["pending"] = (await cursor.fetchone())[0]
        
        async with self.conn.execute("""
            SELECT severity, COUNT(*) as count 
            FROM fraud_alerts 
            GROUP BY severity
        """) as cursor:
            stats["by_severity"] = {
                row["severity"]: row["count"] 
                for row in await cursor.fetchall()
            }
        
        return stats
    
    # =========================================================================
    # INSIDER ALERTS
    # =========================================================================
    
    async def save_insider_alert(self, alert: Dict[str, Any]) -> str:
        """Save an insider threat alert."""
        alert_id = alert.get("id") or str(uuid4())
        
        await self.conn.execute("""
            INSERT OR REPLACE INTO insider_alerts (
                id, employee_id, employee_name, action_type, threat_type,
                severity, status, risk_score, description, branch_code, risk_factors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_id,
            alert.get("employee_id"),
            alert.get("employee_name"),
            alert.get("action_type"),
            alert.get("threat_type"),
            alert.get("severity", "medium"),
            alert.get("status", "pending"),
            alert.get("risk_score"),
            alert.get("description"),
            alert.get("branch_code"),
            json.dumps(alert.get("risk_factors", [])),
        ))
        await self.conn.commit()
        return alert_id
    
    async def get_insider_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get insider alerts."""
        async with self.conn.execute(
            "SELECT * FROM insider_alerts ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    # =========================================================================
    # EMPLOYEES
    # =========================================================================
    
    async def save_employee(self, emp: Dict[str, Any]) -> str:
        """Save or update an employee."""
        emp_id = emp.get("id") or str(uuid4())
        
        await self.conn.execute("""
            INSERT OR REPLACE INTO employees (
                id, employee_id, name, branch_code, department, role,
                usual_branches, accounts_accessed_today, accounts_accessed_without_txn,
                overrides_today, overrides_30d, peer_avg_overrides_30d,
                after_hours_logins_7d, is_on_notice, notice_end_date,
                linked_to_flagged_accounts, transactions_with_same_accounts,
                risk_score, risk_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            emp_id,
            emp.get("employee_id"),
            emp.get("name"),
            emp.get("branch_code"),
            emp.get("department"),
            emp.get("role"),
            json.dumps(emp.get("usual_branches", [])),
            emp.get("accounts_accessed_today", 0),
            emp.get("accounts_accessed_without_txn", 0),
            emp.get("overrides_today", 0),
            emp.get("overrides_30d", 0),
            emp.get("peer_avg_overrides_30d", 5.0),
            emp.get("after_hours_logins_7d", 0),
            1 if emp.get("is_on_notice") else 0,
            emp.get("notice_end_date"),
            emp.get("linked_to_flagged_accounts", 0),
            emp.get("transactions_with_same_accounts", 0),
            emp.get("risk_score", 0),
            emp.get("risk_level", "low"),
        ))
        await self.conn.commit()
        return emp_id
    
    async def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by ID."""
        async with self.conn.execute(
            "SELECT * FROM employees WHERE employee_id = ?", (employee_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    async def get_employees(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all employees."""
        async with self.conn.execute(
            "SELECT * FROM employees ORDER BY risk_score DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    # =========================================================================
    # AGENTS (POS Terminals)
    # =========================================================================
    
    async def save_agent(self, agent: Dict[str, Any]) -> str:
        """Save or update an agent."""
        agent_id = agent.get("id") or str(uuid4())
        
        await self.conn.execute("""
            INSERT OR REPLACE INTO agents (
                id, agent_id, agent_code, business_name, terminal_id,
                is_registered, cac_verified, kyc_level, is_single_principal,
                registered_latitude, registered_longitude, registered_state, registered_lga,
                geo_fence_enabled, geo_fence_radius_meters,
                total_transactions_30d, total_volume_30d, avg_transaction_amount,
                reversal_count_30d, reversal_rate,
                risk_score, risk_level, is_flagged, flagged_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            agent.get("agent_id"),
            agent.get("agent_code"),
            agent.get("business_name"),
            agent.get("terminal_id"),
            1 if agent.get("is_registered", True) else 0,
            1 if agent.get("cac_verified") else 0,
            agent.get("kyc_level", "basic"),
            1 if agent.get("is_single_principal", True) else 0,
            agent.get("registered_latitude"),
            agent.get("registered_longitude"),
            agent.get("registered_state"),
            agent.get("registered_lga"),
            1 if agent.get("geo_fence_enabled", True) else 0,
            agent.get("geo_fence_radius_meters", 10),
            agent.get("total_transactions_30d", 0),
            agent.get("total_volume_30d", 0),
            agent.get("avg_transaction_amount", 0),
            agent.get("reversal_count_30d", 0),
            agent.get("reversal_rate", 0),
            agent.get("risk_score", 0),
            agent.get("risk_level", "low"),
            1 if agent.get("is_flagged") else 0,
            agent.get("flagged_reason"),
        ))
        await self.conn.commit()
        return agent_id
    
    async def get_agent(self, terminal_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by terminal ID."""
        async with self.conn.execute(
            "SELECT * FROM agents WHERE terminal_id = ?", (terminal_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    async def get_agents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all agents."""
        async with self.conn.execute(
            "SELECT * FROM agents ORDER BY risk_score DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    async def save_agent_transaction(self, txn: Dict[str, Any]) -> str:
        """Save an agent transaction."""
        txn_id = str(uuid4())
        
        await self.conn.execute("""
            INSERT INTO agent_transactions (
                id, terminal_id, agent_code, amount, transaction_type,
                latitude, longitude, device_id, device_account_count,
                fraud_score, risk_level, fraud_types, risk_factors,
                recommendation, should_block, geo_check, transaction_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn_id,
            txn.get("terminal_id"),
            txn.get("agent_code"),
            txn.get("amount"),
            txn.get("transaction_type"),
            txn.get("latitude"),
            txn.get("longitude"),
            txn.get("device_id"),
            txn.get("device_account_count", 1),
            txn.get("fraud_score"),
            txn.get("risk_level"),
            json.dumps(txn.get("fraud_types", [])),
            json.dumps(txn.get("risk_factors", [])),
            txn.get("recommendation"),
            1 if txn.get("should_block") else 0,
            json.dumps(txn.get("geo_check")),
            datetime.utcnow().isoformat(),
        ))
        await self.conn.commit()
        return txn_id
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _row_to_dict(self, row: aiosqlite.Row) -> Dict[str, Any]:
        """Convert a database row to dictionary."""
        if row is None:
            return None
        
        d = dict(row)
        
        # Parse JSON fields
        json_fields = [
            "risk_factors", "triggered_rules", "usual_branches",
            "fraud_types", "geo_check"
        ]
        for field in json_fields:
            if field in d and d[field]:
                try:
                    d[field] = json.loads(d[field])
                except:
                    pass
        
        # Convert boolean fields
        bool_fields = [
            "is_flagged", "should_block", "is_new_device", "is_registered",
            "cac_verified", "is_single_principal", "geo_fence_enabled",
            "is_on_notice", "is_pep", "is_sanctioned"
        ]
        for field in bool_fields:
            if field in d:
                d[field] = bool(d[field])
        
        return d


# =============================================================================
# GLOBAL DATABASE INSTANCE
# =============================================================================

db = Database()


async def init_database():
    """Initialize the database (call at startup)."""
    await db.connect()


async def close_database():
    """Close the database (call at shutdown)."""
    await db.disconnect()
