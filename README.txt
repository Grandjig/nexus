================================================================================
                    NEXUS - Fraud Detection Platform
              Built for Nigerian Banks & Fintechs
================================================================================

Thank you for evaluating Nexus!

--------------------------------------------------------------------------------
QUICK START (2 steps)
--------------------------------------------------------------------------------

STEP 1: INSTALL (one time only)
   - Double-click: INSTALL.bat
   - Wait for it to complete (~2 minutes)
   - You'll see "Installation complete!" when done

STEP 2: RUN
   - Double-click: START.bat
   - Browser opens automatically
   - Dashboard: http://localhost:8000
   - API Docs:  http://localhost:8000/docs

To stop: Press Ctrl+C in the terminal window, or just close it.

--------------------------------------------------------------------------------
WHAT IS NEXUS?
--------------------------------------------------------------------------------

Nexus is a real-time fraud detection platform built specifically for 
Nigerian banking patterns. It scores every transaction from 0-100:

   0-39:  LOW RISK    -> Approve automatically
   40-59: MEDIUM RISK -> Flag for review  
   60-79: HIGH RISK   -> Block, urgent review
   80-100: CRITICAL   -> Auto-block, investigate

--------------------------------------------------------------------------------
KEY FEATURES
--------------------------------------------------------------------------------

[X] 47 Nigerian-specific fraud features
[X] SIM swap detection
[X] POS/Agent fraud detection  
[X] Money mule pattern detection
[X] BVN intelligence
[X] <100ms response time
[X] CBN e-Fraud report generation
[X] Beautiful operations dashboard
[X] REST API for integration

--------------------------------------------------------------------------------
TRY THE API
--------------------------------------------------------------------------------

Score a transaction (PowerShell):

   $body = '{"amount": 5000000, "channel": "mobile", "is_new_device": true}'
   Invoke-RestMethod -Uri "http://localhost:8000/api/v1/fraud/score" -Method Post -Body $body -ContentType "application/json"

Or use the interactive dashboard at http://localhost:8000

--------------------------------------------------------------------------------
SYSTEM REQUIREMENTS  
--------------------------------------------------------------------------------

- Windows 10/11
- Python 3.10+ (installer will check)
- 4GB RAM minimum
- Internet connection (for first install only)

--------------------------------------------------------------------------------
SUPPORT
--------------------------------------------------------------------------------

For questions about Nexus or to discuss integration:

   Email: [your-email@domain.com]
   Phone: [your-phone]

--------------------------------------------------------------------------------
                         (c) 2024 Nexus Technologies
================================================================================
