# Agent registry: Sandiyan: Digital Expansion

> 25 agents · Generated automatically from the data layer

Each agent: a defined mission, tools, outputs, a performance indicator, a human owner and an escalation trigger.

## 1: Leadership and coordination

| ID | Agent | Role | Tools | Outputs | Performance metric | Human owner | Autonomy |
|---|---|---|---|---|---|---|---|
| A01 | Project Manager Agent | Coordination | Linear · Notion · Slack · Gmail | Project status board · Daily report · Risk register | Share of tasks completed on schedule | Digital Project Manager | Autonomous |
| A02 | Operations Manager Agent | Operational coordination | Workshop · Airtable · Internal record | Daily production schedule · Capacity breach alerts · Production report | On-time delivery rate | Workshop Manager | Autonomous |

## 2: Engineering and development

| ID | Agent | Role | Tools | Outputs | Performance metric | Human owner | Autonomy |
|---|---|---|---|---|---|---|---|
| A03 | Platform Engineer Agent | Software development | Git · CI/CD · Cloud · PostgreSQL | Platform releases · Technical performance reports · Security fixes | Mean time to resolve a detected defect (MTTR) | Head of Engineering | Autonomous |
| A04 | User Experience Agent | Design | Figma · Hotjar · A/B Testing | Prototypes · A/B tests · Optimisation recommendations | Cart completion rate | Head of Product | Autonomous |
| A05 | Data Agent | Analytics | Python · dbt · BigQuery · Looker | Data warehouse · Performance dashboards · Data quality reports | Tracking event coverage | Head of Data | Autonomous |
| A06 | Cybersecurity Agent | Security | Vault · Snyk · Cloudflare | Security reports · Permission policies · Incident response | Time to close critical vulnerabilities | Head of Engineering | Autonomous |
| A07 | Integration Agent | Systems integration | Webhooks · Zapier · ERP | Working integrations · Daily sync reports · Failure rerouting | Order sync success rate | Head of Engineering | Autonomous |

## 3: Marketing and content

| ID | Agent | Role | Tools | Outputs | Performance metric | Human owner | Autonomy |
|---|---|---|---|---|---|---|---|
| A08 | Growth Manager Agent | Growth | Meta Ads · Google Ads · GA4 · Looker | Campaign performance reports · Budget allocation plan · Experiment backlog | Customer acquisition cost (CAC) | Marketing Manager | Autonomous |
| A09 | Content Writer Agent | Writing | CMS · ChatGPT API · Notion | Articles · Product guides · Ad copy | Organic sessions driven by content | Marketing Manager | Autonomous, subject to review |
| A10 | Brand Designer Agent | Design | Figma · Photoshop · Canva API | Custom templates · Visual assets · Brand usage guide | Share of assets published without modification | Marketing Manager | Autonomous, subject to review |
| A11 | Conversation Coach Agent | Conversations | WhatsApp API · Training knowledge base · CRM | Instant replies · Lead qualification · FAQ report | First response time and conversation-to-order conversion | Customer Service Manager | Autonomous |
| A12 | Social Media Agent | Publishing | Meta Suite · LinkedIn · Buffer | Scheduled posts · Engagement reports · Content calendar | Engagement rate and follower growth | Marketing Manager | Autonomous |
| A13 | Campaign Analyst Agent | Advertising measurement | GA4 · BigQuery · Looker · Python | Campaign reports · Target segment lists · Attribution recommendations | Attribution model accuracy | Marketing Manager | Autonomous |

## 4: Customer service

| ID | Agent | Role | Tools | Outputs | Performance metric | Human owner | Autonomy |
|---|---|---|---|---|---|---|---|
| A14 | Customer Service Agent | Support | CRM · WhatsApp · Ticketing system | Documented replies · Closed tickets · Satisfaction report | Resolution time and customer satisfaction | Customer Service Manager | Autonomous |
| A15 | After-sales Agent | Relationships | CRM · Review tools · Google Business | Automated follow-ups · Published reviews · Feedback report | Review rate and customer satisfaction | Customer Service Manager | Autonomous |
| A16 | Customer Experience Agent | Improvement | Maze · Hotjar · CRM | Friction maps · Prioritised improvement list · Test results | Visit-to-order conversion rate | Head of Product | Autonomous |

## 5: Operations and manufacturing

| ID | Agent | Role | Tools | Outputs | Performance metric | Human owner | Autonomy |
|---|---|---|---|---|---|---|---|
| A17 | Production Planner Agent | Planning | MRP · Google Sheets · ERP | Production schedule · Material requirements list · Exception report | On-time delivery rate | Workshop Manager | Autonomous |
| A18 | Quality Supervisor Agent | Quality | Inspection templates · Reference images · ERP | Inspection reports · Defect log · Corrective actions | Defect rate and return rate | Workshop Manager | Autonomous |
| A19 | Inventory Agent | Inventory | ERP · Logistics platform · Excel | Purchase orders · Stock health report · Stock-out alerts | Inventory turnover | Storekeeper | Autonomous |
| A20 | Supplier Agent | Procurement | ERP · Supplier register · Email | Purchase orders · Supplier performance report · Documented negotiations | Material cost saving rate | Storekeeper | Autonomous |

## 6: Analytics and decisions

| ID | Agent | Role | Tools | Outputs | Performance metric | Human owner | Autonomy |
|---|---|---|---|---|---|---|---|
| A21 | Market Analyst Agent | Research | Web data collection · Python · Notion | Pricing reports · TAM/SAM/SOM refresh · New opportunities | Accuracy of market refreshes | Marketing Manager | Autonomous |
| A22 | Analytics Agent | Data analysis | Python · BigQuery · Excel | Profitability reports · Updated financial model · Deviation alerts | Accuracy of the cost model | Finance Manager | Autonomous |
| A23 | Risk Review Agent | Governance | Notion · Sheets | Updated risk register · Early warnings · Contingency plan tests | Share of risks with a mitigation action | Digital Project Manager | Autonomous |

## 7: Finance and compliance

| ID | Agent | Role | Tools | Outputs | Performance metric | Human owner | Autonomy |
|---|---|---|---|---|---|---|---|
| A24 | Accounting Agent | Finance | ERP · E-invoicing · Excel | Monthly financial statements · Electronic invoice · Account reconciliation | Days to close the books | Finance Manager | Autonomous, subject to review |
| A25 | Compliance Agent | Compliance | Document management system · Checklist | Compliance reports · Policy updates · Retained records | Share of requirements met | Finance Manager | Autonomous, subject to review |

## AI governance

### Principles

- Every agent has a human owner accountable for its output: there is no agent without an owner.
- The propose-then-review principle is mandatory for any decision touching money or a customer.
- Every agent output is traceable: which data and which instructions produced it.
- Customer personal data is never stored outside approved and authorised systems.
- A quarterly review of every agent's performance against its defined indicator.

### Mandatory human in the loop

- Any refund or discount above 5% is presented to a human before execution.
- Customer service replies that address a complaint or a damage claim are reviewed before sending.
- Content published on social media passes human review before it goes live.
- Any pricing decision or change to the returns policy is signed off by the Finance Manager.
- Closing a customer account or any legal action is never executed automatically.

### Model and data policy

- Models are used on non-sensitive data only; sensitive data is processed inside an approved, access-restricted environment.
- A weekly review of model performance, documenting any drift in output quality.
- No model output may be used without human review in sensitive content.
- The version and settings behind every officially approved output are documented.
- An approved manual fallback exists for every critical process in case the service is unavailable.

### Security and privacy

- Data is encrypted in transit and at rest across every storefront and dashboard path.
- Least-privilege access for every agent, reviewed quarterly.
- Every action an agent performs is fully logged in an immutable audit trail.
- Daily encrypted backups with a monthly restoration test.
- A defined incident disclosure and response policy with clear reporting channels.

### Cost control

- A monthly review of AI tooling subscription cost against the operating benefit it delivers.
- Route each task to the cheapest model tier that meets the need: a small model for repetitive work.
- The cost per order handled by the assistant is measured against the cost of human handling.
- A monthly spend ceiling per agent, with an alert at 80%.
