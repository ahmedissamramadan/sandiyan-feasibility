# -*- coding: utf-8 -*-
"""
================================================================================
خطوات دليل التنفيذ (SOP): النسخة الإنجليزية
--------------------------------------------------------------------------------
بنية كل بند: (الخطوة، المخرَج، المسؤول، معيار القبول)
================================================================================
"""

SOP_EN = {
    "س01": ("Document control and revision log", "Digital Project Manager", [
        ("Record document ownership, reference and confidentiality", "Control record", "Executive management", "Every field completed and signed"),
        ("Maintain the revision log and approval templates", "Templates", "Digital Project Manager", "Log populated and versioned"),
        ("Run the review sessions and capture the minutes", "Minutes", "Digital Project Manager", "Minutes filed against each section"),
        ("Issue version 1.0 for approval", "Document", "Chief Executive", "Approved version released"),
    ]),
    "س02": ("Executive summary and investment decision card", "Digital Project Manager", [
        ("Refresh the governing indicators from the live model", "One-page summary", "Analytics Agent", "Figures reconcile with the model"),
        ("Draft the recommendation and the funding request", "Narrative", "Digital Project Manager", "Signed-off wording"),
        ("Convert each condition into a verifiable test", "Condition register", "Executive management", "Every condition has a test"),
        ("Table the decision at board level", "Board pack", "Chief Executive", "Decision minuted"),
    ]),
    "س03": ("Legal and institutional framework", "Finance Manager", [
        ("Verify that every licence is in date and renew on time", "Licence register", "Compliance Agent", "No licence lapses"),
        ("Document the ownership structure and the IP position", "Legal note", "Founding partner", "Registered and filed"),
        ("Review data protection obligations end to end", "Compliance checklist", "Compliance Agent", "Policy published and enforced"),
    ]),
    "س04": ("Project description and scope", "Workshop Manager", [
        ("Update the asset and capacity register monthly", "Asset register", "Workshop Manager", "Figures evidenced"),
        ("Re-confirm material prices and supplier lead times", "Price list", "Storekeeper", "Valid quotations on file"),
        ("Model the achievable output against real orders", "Capacity model", "Production Planner Agent", "Production plan issued"),
    ]),
    "س05": ("The conceptual basis of feasibility", "Digital Project Manager", [
        ("Tag the source of every figure in the study", "Source register", "Analytics Agent", "Every figure traceable"),
        ("Close or justify the gap between estimate and measurement", "Gap log", "Digital Project Manager", "Every gap closed or justified"),
    ]),
    "س06": ("Strategic analysis", "Marketing Manager", [
        ("Refresh the EFE and IFE matrices", "Two matrices", "Risk Review Agent", "Weights justified"),
        ("Revisit SWOT and TOWS each quarter", "Matrix", "Market Analyst Agent", "Strategies updated"),
        ("Re-run the PESTEL and Porter analyses", "Analysis", "Market Analyst Agent", "Actions named"),
    ]),
    "س07": ("Market and demand analysis", "Marketing Manager", [
        ("Update the market sizing and the SOM estimate", "Sizing note", "Market Analyst Agent", "Estimate evidenced"),
        ("Review competitor pricing weekly", "Price log", "Market Analyst Agent", "Log kept current"),
        ("Test purchase intent and measure the conversion", "Test report", "Growth Manager Agent", "Test data captured"),
    ]),
    "س08": ("The AI layer and the agent map", "Digital Project Manager", [
        ("Assign a human owner to every agent", "Ownership register", "Digital Project Manager", "No agent without an owner"),
        ("Publish the boundaries on what may be executed automatically", "Policy", "Risk Review Agent", "Policy approved"),
        ("Review agent performance quarterly", "Performance report", "Project Manager Agent", "Report with corrective actions"),
    ]),
    "س09": ("Marketing and sales strategy", "Marketing Manager", [
        ("Reallocate the advertising budget by channel return", "Allocation plan", "Growth Manager Agent", "Reallocated quarterly"),
        ("Run A/B tests across the buying journey", "Test results", "Customer Experience Agent", "Decisions taken from data"),
        ("Grow the owned contact list", "List report", "Social Media Agent", "Documented monthly growth"),
    ]),
    "س10": ("Operations and manufacturing", "Workshop Manager", [
        ("Schedule production and match orders to capacity", "Schedule", "Production Planner Agent", "On-time delivery ≥ 92%"),
        ("Inspect the product before dispatch", "Inspection record", "Quality Supervisor Agent", "Photographs on file"),
        ("Measure the returns cycle and its cost", "Cost report", "Analytics Agent", "Cost quantified"),
    ]),
    "س11": ("Technology and digital infrastructure", "Head of Engineering", [
        ("Build the store and the order management system", "Release", "Platform Engineer Agent", "Test suite green"),
        ("Test every integration and the stock synchronisation", "Integration test", "Integration Agent", "Sync success ≥ 95%"),
        ("Run the security review and the restore test", "Security review", "Cybersecurity Agent", "No critical finding open"),
    ]),
    "س12": ("Human resources and organisation", "Digital Project Manager", [
        ("Approve the structure and the hiring plan", "Plan", "Executive management", "Approved"),
        ("Train the workshop team on Order Hub", "Training session", "Project Manager Agent", "Practical assessment passed"),
        ("Review the usage and permissions policies", "Policy", "Compliance Agent", "Signed by every user"),
    ]),
    "س13": ("Financial tables", "Finance Manager", [
        ("Review the assumptions and re-base the model", "Model", "Analytics Agent", "Model updated"),
        ("Re-forecast after month three", "Model", "Finance Manager", "Variance documented"),
        ("Issue a one-page sensitivity note to the executive team", "Note", "Analytics Agent", "Note delivered"),
    ]),
    "س14": ("Risks and mitigation plan", "Digital Project Manager", [
        ("Update the risk register and rescore the risks", "Register", "Risk Review Agent", "Every risk has an action"),
        ("Test the contingency plans on a schedule", "Test", "Risk Review Agent", "Result documented"),
    ]),
    "س15": ("Schedule and roadmap", "Digital Project Manager", [
        ("Update the status of every phase weekly", "Board", "Project Manager Agent", "Updated weekly"),
        ("Verify that the decision gates are honoured", "Gate review", "Executive management", "No gate bypassed"),
    ]),
    "س16": ("Performance indicators and measurement framework", "Head of Data", [
        ("Configure and validate the tracking events", "Tracking plan", "Data Agent", "Coverage ≥ 95%"),
        ("Publish the weekly performance dashboard", "Dashboard", "Data Agent", "Published on schedule"),
    ]),
    "س17": ("Findings, recommendations and the investment decision", "Chief Executive", [
        ("Review the recommendation and its conditions", "Document", "Executive management", "Recommendation approved"),
        ("Confirm the next steps, their owners and their dates", "Plan", "Digital Project Manager", "Every step dated"),
    ]),
    "س18": ("Appendices", "Analytics Agent", [
        ("Update the index of sources", "Source list", "Analytics Agent", "Every source verifiable"),
        ("Refresh the glossary of terms", "Glossary", "Analytics Agent", "Updated"),
    ]),
}
