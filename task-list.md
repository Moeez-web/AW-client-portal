# AW Client Report Portal — Task List

## Phase 1: Project Setup & DB

- [ ] **1.1** Initialize project structure with folders:
  ```
  AW_Client_Portal/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py              # Flask entry point
  │   ├── routes/
  │   │   ├── __init__.py
  │   │   ├── clients.py       # Client management routes
  │   │   ├── reports.py       # Report generation routes
  │   │   └── api.py           # JSON API for live calculations
  │   ├── models/
  │   │   ├── __init__.py
  │   │   ├── client.py        # Client & ClientProfile models
  │   │   ├── account.py       # Account model
  │   │   ├── liability.py     # Liability model
  │   │   ├── financial.py     # ClientFinancial model
  │   │   └── report.py        # Report & ReportEntry models
  │   ├── services/
  │   │   ├── __init__.py
  │   │   ├── calculations.py  # All math logic (excess, totals, net worth)
  │   │   └── pdf_generator.py # SACS & TCC PDF generation
  │   ├── enums.py             # AccountType, SubType, Owner, LiabilityType, MaritalStatus
  │   ├── static/
  │   │   ├── css/
  │   │   │   ├── common.css
  │   │   │   ├── landing.css
  │   │   │   ├── client-list.css
  │   │   │   ├── client-form.css
  │   │   │   └── report.css
  │   │   ├── js/
  │   │   │   ├── common.js
  │   │   │   ├── client-form.js
  │   │   │   └── report.js
  │   │   └── images/
  │   └── templates/
  │       ├── base.html         # Base layout with nav
  │       ├── landing/
  │       │   └── index.html
  │       ├── clients/
  │       │   ├── list.html
  │       │   ├── form.html     # Add/Edit client (tabs: profiles, accounts, liabilities, financials)
  │       │   └── detail.html
  │       └── reports/
  │           ├── entry.html    # Quarterly data entry (split: form left, live preview right)
  │           ├── history.html
  │           └── view.html
  ├── db/
  │   └── portal.db
  ├── projectDoc/
  └── requirements.txt
  ```

- [ ] **1.2** Create `requirements.txt` with dependencies:
  - Flask, SQLAlchemy, Jinja2, ReportLab, python-dotenv

- [ ] **1.3** Create `app/enums.py` with all enums:
  - `AccountType`: retirement, non_retirement, trust
  - `SubType`: IRA, Roth_IRA, 401K, Pension, Brokerage, Joint, Property
  - `Owner`: client1, client2, joint
  - `LiabilityType`: Mortgage, Auto_Loan, Student_Loan, Other
  - `MaritalStatus`: single, married

- [ ] **1.4** Create DB models:
  - **clients**: id, case_name, marital_status (enum), created_at
  - **client_profiles**: id, client_id (FK), full_name, dob, age (auto-calc), ssn_last4, monthly_salary_after_tax, role (primary/spouse), is_active, is_deleted
  - **accounts**: id, client_id (FK), owner (enum), account_type (enum), sub_type (enum), account_number_last4, institution_name, is_active, is_deleted
  - **liabilities**: id, client_id (FK), liability_type (enum), interest_rate, balance, is_active, is_deleted
  - **client_financials**: id, client_id (FK), monthly_expense_budget, private_reserve_target, insurance_deductibles
  - **reports**: id, client_id (FK), quarter, year, generated_at, pdf_sacs_path, pdf_tcc_path
  - **report_entries**: id, report_id (FK), account_id (FK), balance, entered_at

- [ ] **1.5** Create DB initialization script with sample seed data

## Phase 2: Backend — Client Management

- [ ] **2.1** Flask app setup — `app/__init__.py` with SQLAlchemy config, Blueprints registration
- [ ] **2.2** Landing page route — `GET /`
- [ ] **2.3** Client list route — `GET /clients`
- [ ] **2.4** Add client — `GET /clients/new`, `POST /clients` (creates client + primary profile + financials)
- [ ] **2.5** Edit client — `GET /clients/<id>`, `PUT /clients/<id>` (profiles, accounts, liabilities, financials in tabs)
- [ ] **2.6** Delete client — `DELETE /clients/<id>` (soft delete, is_deleted=True)
- [ ] **2.7** Add/edit/deactivate spouse profile — `POST /clients/<id>/profiles`, `PUT /clients/<id>/profiles/<pid>`, `PATCH /clients/<id>/profiles/<pid>/deactivate`
- [ ] **2.8** Add/edit/delete accounts — `POST/PUT/DELETE /clients/<id>/accounts/<aid>`
- [ ] **2.9** Add/edit/delete liabilities — `POST/PUT/DELETE /clients/<id>/liabilities/<lid>`

## Phase 3: Backend — Reports & Calculations

- [ ] **3.1** Create `services/calculations.py` with all auto-calculation logic:
  - SACS: Excess = Inflow - Outflow, Private Reserve Target = (6 × expenses) + deductibles
  - TCC: Client 1 Retirement Total, Client 2 Retirement Total, Non-Retirement Total (excl. trust), Grand Total, Liabilities Total (separate, NOT subtracted)
- [ ] **3.2** JSON API endpoint — `POST /api/calculate` (real-time totals from balances)
- [ ] **3.3** Quarterly report entry — `GET /clients/<id>/reports/new`, `POST /clients/<id>/reports`
- [ ] **3.4** Report history — `GET /clients/<id>/reports`
- [ ] **3.5** View saved report — `GET /clients/<id>/reports/<rid>`
- [ ] **3.6** Update quarterly report — `PUT /clients/<id>/reports/<rid>`
- [ ] **3.7** Download SACS PDF — `GET /clients/<id>/reports/<rid>/download/sacs`
- [ ] **3.8** Download TCC PDF — `GET /clients/<id>/reports/<rid>/download/tcc`

## Phase 4: PDF Generation

- [ ] **4.1** Create `services/pdf_generator.py` using ReportLab
- [ ] **4.2** SACS PDF template — green inflow circle, red outflow circle, blue private reserve, arrows, client name, date, fixed layout
- [ ] **4.3** TCC PDF template — retirement bubbles (top, dynamic count), non-retirement (bottom), trust (center), liabilities (separate), gray summary boxes, client info bubbles
- [ ] **4.4** Handle variable number of account bubbles (1-6 per spouse)
- [ ] **4.5** Pixel-perfect layout — no shifting regardless of number sizes
- [ ] **4.6** Company branding (EF blue theme) applied to PDFs

## Phase 5: Frontend — Pages

- [ ] **5.1** Base layout template — nav bar, flash messages, common structure, Tailwind CDN
- [ ] **5.2** Landing page — branded splash, "Enter Portal" button, blue theme
- [ ] **5.3** Client list page — table view, columns: Name, Marital Status, Last Report Date, Action buttons (Edit, Delete, Generate Report, Quarterly Update)
- [ ] **5.4** Client form page — tabbed layout (Profiles, Accounts, Liabilities, Financials)
  - Profiles tab: Client 1 + spouse fields side by side
  - Accounts tab: grouped by type, add/remove, multiple accounts per sub_type
  - Liabilities tab: list with add/remove
  - Financials tab: salary, budget, reserve target, deductibles
- [ ] **5.5** Quarterly report entry page — split layout:
  - Left: data entry form (pre-filled static data, dynamic balance fields, "use last value" button per field)
  - Right: live calculation preview (auto-updates via /api/calculate)
  - Separate tabs for SACS and TCC data
- [ ] **5.6** Report history page — list of quarterly reports with download buttons
- [ ] **5.7** Confirmation modals for delete actions
- [ ] **5.8** Loaders for PDF generation and form submissions

## Phase 6: Frontend — CSS & JS

- [ ] **6.1** `common.css` — EF blue theme variables, typography, spacing, Tailwind overrides
- [ ] **6.2** Page-specific CSS files (landing, client-list, client-form, report)
- [ ] **6.3** `common.js` — form validation helpers, fetch wrapper, loader toggle
- [ ] **6.4** `client-form.js` — dynamic add/remove account rows, tab switching, spouse toggle based on marital status
- [ ] **6.5** `report.js` — real-time calculation updates (calls /api/calculate on input change), "use last value" handler, field highlight for incomplete fields

## Phase 7: Testing & Polish

- [ ] **7.1** Test all CRUD operations for clients, profiles, accounts, liabilities
- [ ] **7.2** Test auto-calculations against PRD rules (excess, totals, liabilities NOT subtracted, trust NOT in non-retirement)
- [ ] **7.3** Test SACS PDF output against PRD template screenshots
- [ ] **7.4** Test TCC PDF output with varying account counts (1-6 bubbles)
- [ ] **7.5** Test married vs single client flows (both reports, spouse add/remove)
- [ ] **7.6** Test quarterly update flow — previous values, "use last value", report history
- [ ] **7.7** UI polish — responsive layout, loader states, form validation, error handling

## Key Rules (from PRD)
- Liabilities displayed separately, NOT subtracted from net worth
- Non-retirement total excludes trust
- Client 1 & Client 2 retirement totals are separate
- Floor = $1,000 minimum balance in each account
- Private Reserve Target = (6 × monthly expenses) + all insurance deductibles
- Excess = Inflow - Outflow
- Grand Total = Client1 Retirement + Client2 Retirement + Non-Retirement + Trust
- is_active + is_deleted pattern on client_profiles, accounts, liabilities
- All reports saved with snapshots (report_entries) for history
