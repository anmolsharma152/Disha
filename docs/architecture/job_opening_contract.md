# JobOpening Contract Specification

> Defines the data contract between scraper outputs, job normalizers, the Career Agent, and downstream consumers.

---

## 1. Schema Reference

File: `schemas.py:150`

```python
class JobOpening(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="forbid")
```

**Key constraint:** `extra="forbid"` means any field not in the schema causes a `ValidationError`. Scrapers cannot pass unrecognized fields.

---

## 2. Field Contract Analysis

### 2.1 Fields Required by Career Agent (must be populated or score degrades)

| Field | Career Agent Use | Fallback | Impact if Missing |
|-------|-----------------|----------|-------------------|
| `title` | Display, skill matching | — | Job is invisible in output |
| `company_name` | Display, grouping | — | Job is invisible in output |
| `location_raw` | Location matching | — | `is_location_match` returns False → job skipped |
| `remote_policy` | Remote fit scoring | `RemotePolicy.UNKNOWN` | Remote fit = 30/100 (vs 100/100 for remote) |
| `experience_level` | Experience fit | `ExperienceLevel.UNKNOWN` | Treated as "mid" level (index 3) |
| `description_raw` | Exclusion filter, LLM enrichment | — | Skipped if missing (empty string) |
| `source_url` | Citations, dedup | — | Job lacks attribution |

### 2.2 Fields That Improve Scoring Quality (optional, but valuable)

| Field | Career Agent Use | Impact if Populated |
|-------|-----------------|---------------------|
| `tech_stack` | Core of skill match % | Without this, match_pct = 0% for all jobs |
| `skills_required` | Skill match % | Adds to the union of job skills |
| `skills_preferred` | Skill match % (lower weight) | Adds to the union of job skills |
| `payout_min` | Compensation fit | `compensation_source` = "posted" → higher confidence |
| `payout_max` | Compensation fit | Used for midpoint → comp fit accuracy |
| `currency` | Comp conversion | Defaults to "USD" in schema; normalizer overrides to "INR" for India jobs |

### 2.3 Fields Used Only for Future Features (safe to leave empty)

| Field | Future Use | Priority |
|-------|-----------|----------|
| `equity_min` / `equity_max` | Total comp estimation | Postpone |
| `bonus_target` | Total comp estimation | Postpone |
| `sign_on_bonus` | Total comp estimation | Postpone |
| `visa_sponsorship` | Visa filter | Not needed for India |
| `h1b_eligible` | Visa filter | Not needed for India |
| `security_clearance` | Visa filter | Not needed |
| `certifications` | Enhanced matching | Postpone |
| `department` / `team` | Organizational context | Postpone |
| `posted_date` | Recency sorting | Postpone |
| `expires_at` | Job expiry | Postpone |
| `application_url` | One-click apply | Use `source_url` if missing |
| `job_hash` | Deduplication | Nice-to-have, can derive |

### 2.4 Fields That Are Derivable or Auto-Generated

| Field | Derivation | Reliability |
|-------|-----------|-------------|
| `job_id` | `uuid4()` auto | Always available |
| `title_normalized` | `_normalize_title()` auto | Good for common patterns |
| `payout_midpoint` | Computed property `(min+max)//2` | Depends on payout fields |
| `total_comp_estimate` | Computed property `base + equity + bonus` | Depends on comp fields |
| `scraped_at` | `datetime.utcnow()` auto | Always available |
| `is_active` | Default `True` | Must be manually set to False |
| `compensation_source` | Default `"estimated"` | Override to `"posted"` when salary is explicit |

---

## 3. Minimum Viable Subset for Phase 2

For a working end-to-end pipeline, a scraper must produce these 8 fields:

```python
JOB_REQUIRED_FIELDS = {
    "title": str,           # From job posting title
    "company_name": str,    # From employer name
    "location_raw": str,    # Raw location string
    "description_raw": str, # Full description text
    "source_url": str,      # Direct URL to posting
    "source_domain": str,   # e.g., "boards.greenhouse.io"
}
```

Plus these 5 fields should be populated when available:

```python
JOB_OPTIONAL_BUT_VALUABLE = {
    "tech_stack": list,       # Extracted technologies
    "skills_required": list,  # Required skills
    "skills_preferred": list, # Preferred skills
    "payout_min": int,        # Minimum salary in currency units
    "payout_max": int,        # Maximum salary in currency units
}
```

And these 3 fields have India-specific defaults that scrapers should set explicitly:

```python
JOB_INDIA_DEFAULTS = {
    "currency": "INR",           # Default is "USD" in schema
    "location_country": "IN",    # Default is "US" in schema
    "scraper_source": "career_page",  # Override per platform
}
```

---

## 4. Scrapability Analysis by Source

### 4.1 Greenhouse API (`boards-api.greenhouse.io`)

| Field | Available | Reliability | Notes |
|-------|-----------|-------------|-------|
| `title` | ✅ `title` | 100% | Direct field |
| `company_name` | ✅ `organization` | 100% | Direct field |
| `location_raw` | ✅ `location.name` | 100% | e.g., "Bangalore, India" |
| `description_raw` | ✅ `content` | 100% | Full HTML description |
| `source_url` | ✅ `absolute_url` | 100% | Direct field |
| `remote_policy` | ⚠️ Inferred | 70% | Check `location.name` for "Remote" |
| `experience_level` | ⚠️ Inferred | 60% | Not in API; infer from title |
| `tech_stack` | ❌ Not structured | — | Must extract from description |
| `skills_required` | ❌ Not structured | — | Must extract from description |
| `payout_min/max` | ❌ Rarely posted | — | Sometimes in description text |
| `department` | ✅ `departments[].name` | 90% | Available |
| `posted_date` | ✅ `updated_at` | 100% | Timestamp available |

**Verdict:** Excellent source. 80% of required fields available directly. Tech stack requires LLM extraction from description. No authentication needed. No anti-bot risk.

### 4.2 Lever API (`api.lever.co/v0/postings`)

| Field | Available | Reliability | Notes |
|-------|-----------|-------------|-------|
| `title` | ✅ `text` | 100% | Direct field |
| `company_name` | ✅ `hostedUrl` → org name | 90% | From company page context |
| `location_raw` | ✅ `categories.location` | 90% | May be "Remote" or city |
| `description_raw` | ✅ `description` | 100% | HTML description |
| `source_url` | ✅ `hostedUrl` | 100% | Direct field |
| `remote_policy` | ✅ `categories.remote` | 90% | "fully", "partially", "none" |
| `experience_level` | ❌ Not structured | — | Infer from title |
| `tech_stack` | ❌ Not structured | — | Must extract from description |
| `skills_required` | ❌ Not structured | — | Must extract from description |
| `payout_min/max` | ❌ Rarely posted | — | Sometimes in `lists` field |
| `department` | ✅ `categories.team` | 80% | Available |
| `posted_date` | ✅ `createdAt` | 100% | Timestamp available |

**Verdict:** Comparable to Greenhouse. Has explicit remote policy field, which Greenhouse lacks. No authentication needed.

### 4.3 Naukri.com (Playwright scraping)

| Field | Available | Reliability | Notes |
|-------|-----------|-------------|-------|
| `title` | ✅ Title element | 90% | Visible on search results |
| `company_name` | ✅ Company element | 90% | Visible on search results |
| `location_raw` | ✅ Location element | 85% | May include multiple cities |
| `description_raw` | ✅ Job detail page | 80% | Requires second request per job |
| `source_url` | ✅ Job URL | 100% | From search results link |
| `remote_policy` | ❌ Rarely explicit | 10% | Most Naukri jobs don't specify |
| `experience_level` | ⚠️ "Years of exp" | 70% | Range string like "2-5 yrs" |
| `tech_stack` | ❌ Not structured | — | Must extract from description |
| `skills_required` | ❌ Not structured | — | Must extract from description |
| `payout_min/max` | ⚠️ LPA range | 60% | Often present as "₹12-20 LPA" or "Not disclosed" |

**Verdict:** Moderate reliability. Best for salary data (highest LPA availability of all sources). Requires Playwright + anti-bot handling. Tech stack extraction requires LLM.

### 4.4 LinkedIn (Playwright scraping)

| Field | Available | Reliability | Notes |
|-------|-----------|-------------|-------|
| `title` | ✅ Title | 90% | Visible |
| `company_name` | ✅ Company | 90% | Visible |
| `location_raw` | ✅ Location | 85% | Visible |
| `description_raw` | ✅ Job detail | 80% | Often truncated, needs "Show more" click |
| `source_url` | ✅ Job URL | 100% | Visible |
| `remote_policy` | ✅ Badge | 70% | Explicit "Remote" / "Hybrid" / "On-site" |
| `experience_level` | ⚠️ "Seniority level" | 70% | In job metadata section |
| `tech_stack` | ❌ Not structured | — | Must extract from description |
| `skills_required` | ✅ Skills section | 70% | "Skills" section on job detail page |
| `payout_min/max` | ⚠️ Salary estimate | 40% | Often hidden or for US-only jobs |

**Verdict:** Best data quality (explicit remote, skills, seniority). Highest scraping difficulty (login required, anti-bot, legal risk). Worst reliability (DOM changes break regularly). Not recommended for Phase 2.

---

## 5. Schema Change Recommendations

### 5.1 Unresolved Question: Schema Defaults

The current schema defaults are US-centric:
- `currency = "USD"` — wrong for India-focused platform
- `location_country = "US"` — wrong for India-focused platform

**Two approaches:**

**Approach A (change defaults):** Change schema defaults to India values. Simple, but any future US scraping must explicitly override defaults. Risk of silent misclassification.

**Approach B (factory functions):** Keep schema defaults. Create `india_job_opening(**overrides) -> JobOpening` factory that sets India defaults. Explicit and correct, but more code.

**Current recommendation:** Approach B. The schema should represent the generic case. India-specific creation is a normalizer responsibility.

### 5.2 Unresolved Question: LPA/CTC Compensation Parsing

The schema uses integer `payout_min`/`payout_max` fields (annual base in currency units). Indian jobs commonly express compensation as:
- `"₹12 LPA"` (12 lakhs per annum) → `1200000`
- `"₹12-20 LPA"` → `payout_min=1200000, payout_max=2000000`
- `"₹1.2 Cr"` (1.2 crores) → `12000000`
- `"₹12-15 LPA + Equity"` → needs parsing

The normalizer must handle these patterns. No schema change required — the integer fields can represent any currency unit.

### 5.3 No Schema Changes Required for Phase 2

The existing `JobOpening` schema can represent all data from Greenhouse, Lever, and Naukri. The only changes needed are:
- Export helper functions for India-specific creation defaults
- Document the 8-field minimum viable contract
- No field additions, removals, or type changes
