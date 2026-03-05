"""Seed demo data into the database."""

import asyncio
from database import db, init_database


# Demo employees
DEMO_EMPLOYEES = [
    {
        "employee_id": "EMP001",
        "name": "Adebayo Okonkwo",
        "branch_code": "LG001",
        "department": "Operations",
        "role": "teller",
        "usual_branches": ["LG001"],
        "accounts_accessed_today": 25,
        "accounts_accessed_without_txn": 3,
        "overrides_today": 1,
        "overrides_30d": 8,
        "peer_avg_overrides_30d": 6.0,
        "risk_score": 15.0,
        "risk_level": "low"
    },
    {
        "employee_id": "EMP002",
        "name": "Chioma Eze",
        "branch_code": "LG001",
        "department": "Operations",
        "role": "supervisor",
        "usual_branches": ["LG001", "LG002"],
        "accounts_accessed_today": 45,
        "accounts_accessed_without_txn": 15,
        "overrides_today": 8,
        "overrides_30d": 35,
        "peer_avg_overrides_30d": 12.0,
        "after_hours_logins_7d": 3,
        "risk_score": 62.0,
        "risk_level": "high"
    },
    {
        "employee_id": "EMP003",
        "name": "Ibrahim Yusuf",
        "branch_code": "AB001",
        "department": "Customer Service",
        "role": "customer_service",
        "usual_branches": ["AB001"],
        "accounts_accessed_today": 60,
        "accounts_accessed_without_txn": 45,
        "risk_score": 55.0,
        "risk_level": "medium"
    },
    {
        "employee_id": "EMP004",
        "name": "Ngozi Okafor",
        "branch_code": "LG003",
        "department": "Operations",
        "role": "teller",
        "usual_branches": ["LG003"],
        "is_on_notice": True,
        "notice_end_date": "2024-02-15",
        "accounts_accessed_today": 30,
        "overrides_today": 5,
        "overrides_30d": 25,
        "peer_avg_overrides_30d": 6.0,
        "linked_to_flagged_accounts": 2,
        "risk_score": 78.0,
        "risk_level": "high"
    },
    {
        "employee_id": "EMP005",
        "name": "Emeka Udoh",
        "branch_code": "PH001",
        "department": "IT",
        "role": "it_admin",
        "usual_branches": ["PH001", "PH002", "PH003"],
        "after_hours_logins_7d": 8,
        "risk_score": 45.0,
        "risk_level": "medium"
    },
]

# Demo agents
DEMO_AGENTS = [
    {
        "agent_id": "AGT001",
        "agent_code": "MNP-LG-001",
        "business_name": "Adex POS Services",
        "terminal_id": "TRM001",
        "is_registered": True,
        "cac_verified": True,
        "kyc_level": "standard",
        "registered_latitude": 6.5244,
        "registered_longitude": 3.3792,
        "registered_state": "Lagos",
        "registered_lga": "Lagos Island",
        "geo_fence_enabled": True,
        "total_transactions_30d": 1250,
        "total_volume_30d": 45000000,
        "avg_transaction_amount": 36000,
        "reversal_count_30d": 15,
        "reversal_rate": 0.012,
        "risk_score": 18.0,
        "risk_level": "low"
    },
    {
        "agent_id": "AGT002",
        "agent_code": "MNP-LG-002",
        "business_name": "QuickCash POS",
        "terminal_id": "TRM002",
        "is_registered": True,
        "cac_verified": True,
        "kyc_level": "standard",
        "registered_latitude": 6.4541,
        "registered_longitude": 3.3947,
        "registered_state": "Lagos",
        "registered_lga": "Surulere",
        "geo_fence_enabled": True,
        "total_transactions_30d": 890,
        "total_volume_30d": 28000000,
        "avg_transaction_amount": 31460,
        "reversal_count_30d": 145,
        "reversal_rate": 0.163,
        "risk_score": 72.0,
        "risk_level": "high",
        "is_flagged": True,
        "flagged_reason": "High reversal rate (16.3%)"
    },
    {
        "agent_id": "AGT003",
        "agent_code": "MNP-AB-001",
        "business_name": "Unity POS Center",
        "terminal_id": "TRM003",
        "is_registered": True,
        "cac_verified": False,
        "kyc_level": "basic",
        "registered_latitude": 9.0765,
        "registered_longitude": 7.3986,
        "registered_state": "Abuja",
        "registered_lga": "Garki",
        "geo_fence_enabled": True,
        "total_transactions_30d": 456,
        "total_volume_30d": 12500000,
        "avg_transaction_amount": 27412,
        "reversal_count_30d": 8,
        "reversal_rate": 0.018,
        "risk_score": 45.0,
        "risk_level": "medium"
    },
    {
        "agent_id": "AGT004",
        "agent_code": "MNP-PH-001",
        "business_name": "Harbor POS",
        "terminal_id": "TRM004",
        "is_registered": False,
        "cac_verified": False,
        "kyc_level": "none",
        "registered_latitude": 4.8156,
        "registered_longitude": 7.0498,
        "registered_state": "Rivers",
        "registered_lga": "Port Harcourt",
        "geo_fence_enabled": False,
        "total_transactions_30d": 234,
        "total_volume_30d": 8500000,
        "avg_transaction_amount": 36324,
        "risk_score": 85.0,
        "risk_level": "critical",
        "is_flagged": True,
        "flagged_reason": "Unregistered agent"
    },
    {
        "agent_id": "AGT005",
        "agent_code": "MNP-KN-001",
        "business_name": "Sahel Mobile Money",
        "terminal_id": "TRM005",
        "is_registered": True,
        "cac_verified": True,
        "kyc_level": "enhanced",
        "registered_latitude": 12.0022,
        "registered_longitude": 8.5920,
        "registered_state": "Kano",
        "registered_lga": "Kano Municipal",
        "geo_fence_enabled": True,
        "total_transactions_30d": 678,
        "total_volume_30d": 19800000,
        "avg_transaction_amount": 29204,
        "reversal_count_30d": 5,
        "reversal_rate": 0.007,
        "risk_score": 12.0,
        "risk_level": "low"
    },
]

# Demo transactions
DEMO_TRANSACTIONS = [
    {
        "transaction_ref": "TXN20240115001",
        "channel": "mobile",
        "amount": 25000,
        "fraud_score": 12.5,
        "risk_level": "low",
        "recommendation": "APPROVE",
        "is_flagged": False,
        "should_block": False,
        "risk_factors": [],
        "triggered_rules": []
    },
    {
        "transaction_ref": "TXN20240115002",
        "channel": "ussd",
        "amount": 150000,
        "fraud_score": 35.0,
        "risk_level": "low",
        "recommendation": "APPROVE",
        "is_flagged": False,
        "should_block": False,
        "risk_factors": ["USSD channel"],
        "triggered_rules": ["CHANNEL_USSD"]
    },
    {
        "transaction_ref": "TXN20240115003",
        "channel": "mobile",
        "amount": 2500000,
        "is_new_device": True,
        "fraud_score": 72.5,
        "risk_level": "high",
        "recommendation": "REVIEW",
        "is_flagged": True,
        "should_block": False,
        "risk_factors": ["Amount over N1M", "New device", "New device + Large amount"],
        "triggered_rules": ["AMOUNT_1M", "NEW_DEVICE", "NEW_DEVICE_HIGH_AMT"]
    },
    {
        "transaction_ref": "TXN20240115004",
        "channel": "mobile",
        "amount": 8500000,
        "is_new_device": True,
        "txn_count_1h": 12,
        "fraud_score": 94.5,
        "risk_level": "critical",
        "recommendation": "BLOCK",
        "is_flagged": True,
        "should_block": True,
        "risk_factors": ["Amount over N5M", "New device", "Very high velocity: 12 txns/hour"],
        "triggered_rules": ["AMOUNT_5M", "NEW_DEVICE", "VELOCITY_CRITICAL"]
    },
    {
        "transaction_ref": "TXN20240115005",
        "channel": "ussd",
        "amount": 5200000,
        "is_new_device": True,
        "fraud_score": 89.0,
        "risk_level": "critical",
        "recommendation": "BLOCK",
        "is_flagged": True,
        "should_block": True,
        "risk_factors": ["Amount over N5M", "USSD channel", "New device"],
        "triggered_rules": ["AMOUNT_5M", "CHANNEL_USSD", "NEW_DEVICE"]
    },
]

# Demo alerts
DEMO_ALERTS = [
    {
        "transaction_ref": "TXN20240115004",
        "alert_type": "SIM Swap Attack",
        "severity": "critical",
        "status": "pending",
        "title": "Critical: NGN 8.5M transfer blocked",
        "description": "SIM swapped 2hrs ago, new device, high velocity",
        "fraud_score": 94.5,
        "amount": 8500000,
        "channel": "mobile",
        "risk_factors": ["SIM swapped 2hrs ago", "New device", "12 txns/hour"]
    },
    {
        "transaction_ref": "TXN20240115005",
        "alert_type": "Account Takeover",
        "severity": "critical",
        "status": "pending",
        "title": "Critical: NGN 5.2M USSD transfer",
        "description": "Password reset 6hrs ago, new device, USSD channel",
        "fraud_score": 89.0,
        "amount": 5200000,
        "channel": "ussd",
        "risk_factors": ["Password reset", "New device", "USSD high amount"]
    },
    {
        "transaction_ref": "TXN20240115003",
        "alert_type": "Velocity Breach",
        "severity": "high",
        "status": "reviewing",
        "title": "High: New device large transaction",
        "description": "NGN 2.5M from new device",
        "fraud_score": 72.5,
        "amount": 2500000,
        "channel": "mobile",
        "risk_factors": ["New device", "Large amount"]
    },
]

# Demo insider alerts
DEMO_INSIDER_ALERTS = [
    {
        "employee_id": "EMP004",
        "employee_name": "Ngozi Okafor",
        "action_type": "account_reactivation",
        "threat_type": "notice_period_risk",
        "severity": "critical",
        "status": "pending",
        "risk_score": 88.0,
        "description": "Employee on notice period reactivated dormant account",
        "branch_code": "LG003",
        "risk_factors": ["On notice period", "Dormant account reactivation"]
    },
    {
        "employee_id": "EMP002",
        "employee_name": "Chioma Eze",
        "action_type": "override",
        "threat_type": "override_abuse",
        "severity": "high",
        "status": "pending",
        "risk_score": 75.0,
        "description": "8 overrides today (peer avg: 2)",
        "branch_code": "LG001",
        "risk_factors": ["High override count", "Override rate 2.9x above peers"]
    },
    {
        "employee_id": "EMP003",
        "employee_name": "Ibrahim Yusuf",
        "action_type": "account_view",
        "threat_type": "data_harvesting",
        "severity": "medium",
        "status": "reviewing",
        "risk_score": 55.0,
        "description": "45 account views without transactions today",
        "branch_code": "AB001",
        "risk_factors": ["Data harvesting pattern"]
    },
]


async def seed_all():
    """Seed all demo data."""
    await init_database()
    
    print("\n" + "="*60)
    print("  SEEDING DEMO DATA")
    print("="*60)
    
    # Seed employees
    print("\n[1/5] Seeding employees...")
    for emp in DEMO_EMPLOYEES:
        await db.save_employee(emp)
    print(f"  ✓ {len(DEMO_EMPLOYEES)} employees")
    
    # Seed agents
    print("\n[2/5] Seeding agents...")
    for agent in DEMO_AGENTS:
        await db.save_agent(agent)
    print(f"  ✓ {len(DEMO_AGENTS)} agents")
    
    # Seed transactions
    print("\n[3/5] Seeding transactions...")
    for txn in DEMO_TRANSACTIONS:
        await db.save_transaction(txn)
    print(f"  ✓ {len(DEMO_TRANSACTIONS)} transactions")
    
    # Seed alerts
    print("\n[4/5] Seeding fraud alerts...")
    for alert in DEMO_ALERTS:
        await db.save_alert(alert)
    print(f"  ✓ {len(DEMO_ALERTS)} alerts")
    
    # Seed insider alerts
    print("\n[5/5] Seeding insider alerts...")
    for alert in DEMO_INSIDER_ALERTS:
        await db.save_insider_alert(alert)
    print(f"  ✓ {len(DEMO_INSIDER_ALERTS)} insider alerts")
    
    print("\n" + "="*60)
    print("  ✅ DEMO DATA SEEDED SUCCESSFULLY")
    print("="*60)
    print("\nStart the server with: python app.py")
    print("\n")


if __name__ == "__main__":
    asyncio.run(seed_all())
