# Ed-Tech Sales & Marketing Funnel Tracking System

## Organization Context
- **Type**: Ed-tech organization (small team)
- **Location**: India-based
- **Offerings**: International financial certifications + other programs

## Core Problem
Need a centralized sales and marketing funnel tracking system to understand and measure business performance.

---

## Current Sales Funnel Structure

### Stage 1: Top of Funnel (TOFU)
- **Channel**: Performance Marketing
- **Metric Needed**: Total leads generated from marketing campaigns
- **Notes**: Primary lead generation source

### Stage 2: Communication Layer
- **Channels**: Email, WhatsApp
- **Tracking Priority**: NOT required for current phase
- **Purpose**: Lead nurturing between stages

### Stage 3: Middle of Funnel (MOFU)
- **Engagement Activity**: Webinar (or similar events)
- **Metrics Needed**: 
  - Number of leads who register for webinar
  - Number of registered leads who actually attend
- **Critical Conversion**: Registration → Attendance

### Stage 4: Bottom of Funnel (BOFU)
- **Owner**: Sales Team
- **Input**: Attended webinar leads (handed over from marketing)
- **Activities**: Sales calls, follow-ups
- **Metric Needed**: Conversion to customers

---

## Key Funnel Metrics to Track

1. **Marketing Leads Generated** (TOFU)
2. **Webinar Registrations** (MOFU)
3. **Webinar Attendance** (MOFU)
4. **Sales Handover** (Attended leads → Sales team)
5. **Sales Conversions** (BOFU)

---

## Data Capture Information

### 1. Top of Funnel (Performance Marketing)
**Storage**: Google Sheets (automated capture from campaigns)

**Data Fields**:
- Name
- Email
- Phone number
- City
- Question 1
- utmSource
- utmMedium
- utmCamp
- created date

**Usage**: This sheet serves as the source for email/WhatsApp communication campaigns

---

### 2. Middle of Funnel - Zoom Webinars
**Platform**: Zoom
**Capture Method**: Manual report downloads (2 separate reports)

**Events Tracked**:
1. Webinar Registration
2. Webinar Attendance

**Data Fields** (Combined from both reports):
- Webinar Date
- Webinar ID
- Attended (Y/N flag)
- User Name (Original Name)
- First Name
- Last Name
- Email
- Phone
- Registration Time
- Registration Source
- Attendance Type
- Join Time
- Leave Time
- Time in Session (minutes)
- Country/Region Name
- Webinar name
- Webinar conductor

**Current Processing**: 
- Streamlit UI-based system (live, but not full-fledged)
- Script exists for data cleaning and enrichment
- Handles different formats from Zoom registration vs attendance reports
- Outputs cleaned file with required fields pre-filled

---

### 3. Middle of Funnel - Boot Camps
**Similar to webinars but with key differences**:
- Duration: 2-day events (vs single webinar session)
- Additional field: **Boot camp day** (Day 1, Day 2, or Both)
- Data structure mostly identical to webinar format
- Same cleaning/processing workflow applies

---

### 4. Lead Source Tagging System
**Purpose**: Categorize leads by their engagement source for conversion tracking

**Source Types**:
- Webinar source
- Bootcamp
- Other sources (to be detailed)

**Why This Matters**: 
- Different sources have different conversion ratios
- Each source follows a unique customer journey
- Different engagement matrices and processes per source

---

### 5. Bottom of Funnel (Sales Team)
**Storage**: CRM system
**Access Method**: API calls available
**Status**: No changes needed - can pull data directly via API

**What Happens Here**:
- Attended leads (from webinars/bootcamps) handed over to sales
- Sales team performs calls and follow-ups
- Conversion tracking managed in CRM

---

## System Architecture: Two-Part Design

### 🎯 Critical Design Principle: Two Independent Systems

#### **PART 1: Top → Middle Funnel (Marketing to Engagement)**
**Scope**: Performance marketing → Zoom events → Lead assignment
**Data Sources**:
- Performance marketing campaigns (Google Sheets auto-capture)
- Zoom webinars/bootcamps (manual CSV upload)
- Marketing spend data (Google Sheets import)

**Key Events**:
- Lead generation from campaigns
- Webinar/bootcamp registration
- Webinar/bootcamp attendance
- Lead source tagging

**Output**: Qualified leads ready for sales handover

---

#### **PART 2: Sales Funnel (Post-Assignment)**
**Scope**: Lead assignment → Sales conversion
**Data Sources**:
- CRM API (assigned leads data)
- CRM API (sales/revenue data)

**Key Events**:
- Lead assignment to sales rep
- Sales calls and follow-ups
- Deal progression
- Revenue conversion

**Output**: Sales performance and conversion metrics

---

### Integration Point: Lead Assignment
- **Boundary**: When lead is assigned to sales team member
- **Data Flow**: Part 1 generates qualified leads → Part 2 tracks their conversion
- **Primary Key**: Phone number (consistent across both parts)
- **Attribution**: First-touch model applied in Part 1, carried through to Part 2

---

## Existing Streamlit App Analysis

### Current Functionality
**Purpose**: Clean and enrich Zoom webinar/bootcamp data
**Features**:
1. ✅ Multi-section CSV parsing (Topic, Host, Panelist, Attendee, Registrant)
2. ✅ Data normalization (names, emails, phones, dates)
3. ✅ Phone number standardization (10-digit cleanup, 91 prefix)
4. ✅ Deduplication logic (phone → email → individual records)
5. ✅ Attendance aggregation (join/leave times, session duration)
6. ✅ Metadata enrichment (webinar date, conductor, category)
7. ✅ Bootcamp day detection (Day 1 vs Day 2 from topic/date)
8. ✅ First-touch attribution for duplicates (earliest timestamp)
9. ✅ WebEngage event firing (optional - not needed for our use case)

### Key Logic Patterns (Reusable)

**Phone Normalization**:
```python
def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) >= 10:
        digits = digits[-10:]
    if len(digits) != 10:
        return ""
    return digits
```

**UserID Generation**:
```python
def build_user_id(phone: str) -> str:
    # Returns: "91" + 10-digit phone
    tail = digits[-10:].zfill(10)
    return f"91{tail}"
```

**Deduplication Strategy**:
1. Group by phone (primary)
2. If no phone → group by email (secondary)
3. If neither → treat as individual record
4. Within group: sort by timestamp, take earliest

**Category/Conductor Resolution**:
- Token-based matching (e.g., "acca" in topic → "ACCA" category)
- Webinar ID lookup for conductor override
- Host/Panelist fallback hierarchy
- Approved conductor canonicalization

**Bootcamp Day Detection**:
- Regex pattern: `Day[\s\-_]*([12])`
- Fallback: Date day-of-week (Sat=Day1, Sun=Day2)
- Default: Day 1 if uncertain

### What to Reuse
- ✅ Phone/email normalization functions
- ✅ Deduplication logic (critical!)
- ✅ Date parsing utilities
- ✅ Proper casing functions
- ✅ Category mapping logic
- ⚠️ WebEngage integration (skip - not needed)

### What to Enhance
- Support all source types (not just Zoom webinars/bootcamps)
- Integrate with CRM API calls
- Add spend data processing
- Build unified output layer

---

## Technical Infrastructure & Constraints

### CRM System
- **Type**: Custom in-house CRM (no off-the-shelf integrations available)
- **API Access**: CSV output format, simple authentication
- **Current Usage**: Google Apps Script + IMPORTRANGE functions
- **Rate Limits**: CRM API has no issues; Google Sheets rate limits are the bottleneck
- **Scheduling**: Can be scheduled (currently daily in Sheets before rate limit issues)
- **Trigger**: Potentially needs manual trigger (TBD based on solution architecture)
- **Data Volume**: Full dumps (no incremental/date range filters)

### Google Sheets Limitation
⚠️ **CRITICAL BLOCKER**: Google Apps Script rate limits recently became stringent
- Cannot fetch all required data in single run
- Scripts fail mid-execution daily
- This is the PRIMARY reason for seeking new solution
- **Cannot rely on Google Apps Script for data orchestration**
- **Unknown if rate limits apply to final output writes** (needs research)

### Zoom Integration Constraints
⚠️ **HARD CONSTRAINT**: No Zoom API access possible
- Cannot create Zoom apps
- Scopes not configured due to contractual limitations
- **Manual CSV download is the only option** (non-negotiable)
- Existing Streamlit script handles cleaning of downloaded files

### Current Tools Stack
1. **Google Sheets** - TOFU lead capture (auto) + manual data aggregation
2. **Zoom** - Webinar/event hosting; CSV export only
3. **Streamlit UI** - Data cleaning (partially built, can be extended)
4. **Custom CRM** - Sales pipeline; API accessible (CSV format)
5. **Email/WhatsApp** - Communication layer (not tracked currently)

### Existing Assets (Reusable)
- ✅ Data cleaning script for Zoom reports (Streamlit)
- ✅ Funnel mapping CSV (dynamic, needs to remain editable)
- ✅ CRM API endpoints (CSV output)
- ✅ Complex attribution logic (documented in formulas + Streamlit code)
- ✅ Dashboard formulas (Google Sheets)

---

## Solution Requirements

### Functional Requirements

**1. Data Freshness: D-1 Updates**
- Daily sync required (not real-time)
- Data must be complete up to previous day (D-1)
- Example: On Nov 4, data complete through Nov 3
- **Acceptable sync window**: Late night or early morning daily batch

**2. Manual Intervention Points**
- **Monthly**: Manual mapping for "Miscellaneous" sources (acceptable)
- **Daily**: Zoom CSV upload (unavoidable due to API constraints)
- **Everything else**: Should be automated

**3. Dynamic Configuration**
- Funnel mapping must be editable without code changes
- Add/remove sources easily (e.g., deprecated ACCA_FinProClub, ACCA_Influencer)
- Maintain flexibility for new programs/campaigns
- **CSV-based config preferred** (non-technical user editable)

**4. Output Format**
- **Clean, analysis-ready dataset** (not a dashboard)
- Format agnostic - should work with any BI tool
- User should be able to create dashboards independently
- All raw data + calculated fields available
- **Options**: CSV files (cloud storage), Database (PostgreSQL/MySQL), Single Google Sheet (if rate limits allow)
- **Preference**: Simple, easy to maintain, minimal technical intervention

**5. Two-Part System Architecture**
- **Part 1**: Top → Middle funnel (independent processing)
- **Part 2**: Sales funnel (independent processing)
- Clear separation of concerns
- Shared primary key (phone number) for joining

### Non-Functional Requirements

**Performance**:
- No Google rate limit dependency
- Handle 3+ months of historical data
- Process thousands of leads daily
- CRM API returns full dumps (not incremental)

**Reliability**:
- Daily sync must complete successfully
- Clear error handling and logging
- Ability to re-run failed steps

**Maintainability**:
- Simple enough for small team to manage
- Clear documentation
- No complex infrastructure
- **Open source / free tier preferred**
- Minimal technical skills needed for operation

**Flexibility**:
- Support new source types easily (beyond Zoom webinars/bootcamps)
- Accommodate schema changes in CRM
- Scale to more programs/certifications
- Handle deprecated sources gracefully

---

## Core Problem Statement (Updated)

### The Pain Points
1. **No Single Source of Truth**: Data scattered across multiple sheets and tabs
2. **Google Sheets Rate Limit Blocker**: Cannot fetch all data reliably via Apps Script
3. **Manual Data Pulling**: Daily repetitive work pulling from CRM, Sheets, Zoom
4. **Multi-Tab Complexity**: Data needs cleaning across 5-6 tabs before dashboard use
5. **Time-Intensive**: Most time spent on data wrangling vs. analysis
6. **Error-Prone**: Manual processes increase risk of mistakes
7. **Lack of Confidence**: Hard to trust data accuracy with so many moving parts

### What's Already Automated
✅ Dashboard calculations (formulas in place - but not the end goal)
✅ Google Sheets lead capture from campaigns (TOFU)
✅ Zoom data cleaning (Streamlit script exists)
✅ CRM API access (works reliably)

### What Needs Automation
❌ Daily CRM data pulls (without Google rate limits)
❌ Monthly lead deduplication and attribution
❌ Sales data enrichment process
❌ Spend data import and aggregation
❌ Cross-system data joining (phone-based)
❌ **Unified data output layer** (analysis-ready format)

### What Stays Manual (Acceptable)
✅ Zoom CSV download (contractual constraint)
✅ Monthly miscellaneous source mapping (low frequency)

---

## Data Flow Summary

```
Performance Marketing Campaigns
         ↓
   Google Sheets (TOFU leads)
         ↓
Email/WhatsApp Communications (not tracked)
         ↓
   Zoom Registration (manual download)
         ↓
   Streamlit Cleaning Script
         ↓
   Zoom Attendance (manual download)
         ↓
   Lead Source Tagging Applied
         ↓
   CRM (Sales handover via API)
         ↓
   Conversion Tracking
```

---

## Current Manual Workflow (3-Phase Process)

### PHASE 1: Assigned Leads Processing (Monthly)
**Goal**: Pull and process all leads assigned in current month with proper attribution

#### Step 1.1: Pull Raw Assigned Leads (Tab: `all_leads`)
**Data Source**: CRM Query (last 3 months)
**Columns**: 
- sources
- assignOn (assignment date)
- leadMobile (phone number)
- employee (assigned sales rep)

#### Step 1.2: Filter Current Month Leads (Tab: `M0_Leads`)
**Logic**: Extract current month's leads from all_leads
**Formula**: `=FILTER({all_leads!A:C,all_leads!D:D},all_leads!B:B>int(DATE(2025,MONTH(today()-2),1)))`
**Columns**: Same as all_leads (4 columns)

**Additional Column - Funnel Mapping**:
- Column 5: **Funnel** (broader category mapped from source)
- Formula: `=ARRAYFORMULA(IF(A2:A="", "", IFERROR(VLOOKUP(A2:A, Funnel_Mapping!A:B, 2, FALSE), "Other Sources (Miscellaneous)")))`
- Maps individual sources to funnel categories using lookup table
- Defaults to "Other Sources (Miscellaneous)" if not found

#### Step 1.3: Deduplicate & Attribute (Tab: `M0`)
**Goal**: Create unique lead list with first-touch attribution

**Deduplication Logic**:
- Group by unique phone number (leadMobile)
- For duplicate leads, attribute to **first source** chronologically

**Column Mappings**:

1. **First Source & Date Attribution**:
   - Formula: `=INDEX(SORT(FILTER({M0_Leads!E:E, M0_Leads!B:B}, M0_Leads!C:C = A21),2, TRUE),1)`
   - Filters all records for that phone number
   - Sorts by date (assignOn) ascending
   - Returns first funnel category

2. **Attended Flag**:
   - Formula: `=ARRAYFORMULA(IF(A2:A29029="", "", XLOOKUP(A2:A29029, Zoom_Jun30!B:B, Zoom_Jun30!A:A, , 0)))`
   - Looks up phone number in Zoom attendance data
   - Returns "Yes/No" or 0 if not found
   - Tab format: Phone | Attended

3. **Assigned Employee**:
   - Formula: `=XLOOKUP(A21,M0_Leads!C:C,M0_Leads!D:D,,0)`
   - Maps phone to assigned sales rep

**Output**: Unique leads with attribution + attendance + employee assignment
**Dashboard Metric**: This feeds "Assigned MTD" count

---

### PHASE 2: Sales Data Processing
**Goal**: Pull converted sales data and enrich with source attribution

#### Step 2.1: Pull Sales Data from CRM Query
**Source**: CRM API/Query
**Columns** (44 total):
- _id, status, txn_id, sid, emiId, pId
- paymentGateway, target, targetSuperGroup, courseName
- source, tokenAmount, WithOut_Token_paidAmount, createdOn
- pType, eBookRev, bookRev, paymentType, DP, lastEmiDate
- paidAmount, corePartner, StudentContact, StudentSignupDate
- StudentName, TotalAmount, product, mandateStatus, StudentEmail
- EBook_Net_Amount, Book_Net_Amount, Product_Net_Amount, netAmount
- employeeName, employeeTeam, Total_emi, Paid_Emi_Count
- Unpaid_Emi_Count, Paid_Emi_Amount, Unpaid_Amount, Last_Paid_Date
- netAmountAfterPDD, assignedLeadSources, Funnel

#### Step 2.2: Add Enrichment Columns

**Column 1: Manual Mapping**
- Purpose: Manually correct sources for "Miscellaneous" category leads
- Process: Manual data entry for unclassified leads

**Column 2: FINAL FUNNEL** (Calculated)
- Formula:
```
=MAP(
  AR3, AS3,
  LAMBDA(ar, as,
    IF(
      TRIM(ar)="Other Sources (Miscellaneous)",
      IFNA( VLOOKUP(TRIM(as), Sheet13!J:K, 2, FALSE), ar ),
      IF( LEN(as), as, ar
    )
  )
)
```
- Logic:
  - If Funnel = "Miscellaneous" → lookup Manual Mapping value
  - Else if assignedLeadSources exists → use that
  - Else use original Funnel value

**Column 3: Attended**
- Formula: `=XLOOKUP(W3,Zoom_Jun30!B:B,Zoom_Jun30!A:A,,0)`
- Looks up StudentContact (phone) in Zoom attendance data
- Returns attendance flag

**Output**: Sales data enriched with proper source attribution and attendance status

---

### PHASE 3: Marketing Spend Data Processing
**Goal**: Calculate total spend per funnel/source for ROI analysis

#### Step 3.1: Import Raw Spend Data (Tab: `Perf_import`)
**Source**: Another Google Sheet (via IMPORTRANGE)
**Columns** (44 total):
- date_time, campaign, ad_group, impressions, clicks, cost
- account, video_views, platform, AccountDescriptiveName
- CampaignType, Objective, Category, subCategory
- goalID, goalName, region, Installs, SignUps, Purchases
- Revenue, Web Purchases, Web Revenue, Subscribers
- Super Leads, Skill Leads, Online Purchases, Online Revenue
- Lead Purchases, Lead Revenue, Pass Purchases, Pass Revenue
- Pass Pro Purchases, Pass Pro Revenue, SuperCoaching Purchases
- SuperCoaching Revenue, SkillAcademy Purchases, SkillAcademy Revenue
- Book Purchases, Book Revenue, Total Purchases, Total Revenue
- **Funnel** (source category)

#### Step 3.2: Aggregate Spend by Funnel (Tab: `raw`)
**Columns Needed**:
- Column D: Funnel names (source categories)
- Column I: Total Spend per Funnel

**Calculation**:
- Formula: `=SUMIFS(Perf_import!F:F,Perf_import!AQ:AQ,D2)`
- Sums cost (column F) where Funnel (column AQ) matches current row's funnel

**Output**: Clean spend summary by source for dashboard

---

### Dashboard Auto-Update
- Once all 3 phases complete, dashboard formulas auto-calculate metrics
- Dashboard already has fixed formulas in place
- No manual dashboard updates needed

---

## Core Problem Statement

### The Pain Points
1. **No Single Source of Truth**: Data scattered across multiple sheets and tabs
2. **Manual Data Pulling**: Daily repetitive work pulling from CRM, Sheets, Zoom
3. **Multi-Tab Complexity**: Data needs cleaning across 5-6 tabs before dashboard use
4. **Time-Intensive**: Most time spent on data wrangling vs. analysis
5. **Error-Prone**: Manual processes increase risk of mistakes
6. **Lack of Confidence**: Hard to trust data accuracy with so many moving parts

### What's Already Automated
✅ Dashboard calculations (formulas in place)
✅ Google Sheets lead capture from campaigns
✅ Zoom data cleaning (Streamlit script exists)

### What Needs Automation
❌ Daily data pulls from CRM query
❌ Monthly lead deduplication and attribution
❌ Sales data enrichment process
❌ Spend data import and aggregation
❌ Cross-tab data synchronization
❌ Unified reporting layer

---

*Last Updated: Added comprehensive data capture architecture and current system state*
