# Amana goAML Filing Engine — Product Spec (v0.1)

The compliance model the engine implements. This is the internal reference that keeps the code honest
and gives us a single place to update when FIU rules change.

## Why these three reports

UAE DNFBPs (real-estate brokers, precious-metals dealers, corporate-service providers, auditors,
lawyers) must register on goAML and file. The three highest-frequency / highest-fear filings are:

| Report | Full name | Trigger | Threshold | Deadline |
|---|---|---|---|---|
| **STR** | Suspicious Transaction Report | Reasonable grounds to suspect ML/TF | None (suspicion-driven) | Immediately / without delay |
| **REAR** | Real Estate Activity Report | Freehold sale/purchase with cash (or part-cash) | ≥ AED 55,000 | After the qualifying transaction |
| **DPMSR** | Dealers in Precious Metals & Stones Report | Cash/wire transaction with a customer | ≥ AED 55,000 | Within 2 weeks |

STRs are sporadic but carry criminal liability if missed; REAR/DPMSR recur with deal flow and are the
everyday workhorses that justify a monthly subscription. One engine serves all three because they share
the same shape: **structured inputs → validated report → goAML XML**.

## Data model

**Reporting entity (the DNFBP / MLRO)**
`name*, type, licenseNo, rentityId (goAML), mlroName*, mlroEmail, emirate, preparedBy`

**Subject** — `kind = person | entity`
- Person: `fullName*, nationality, idType, idNumber, dob, address`
- Entity: `fullName*, tradeLicense, address, uboName, uboNationality, uboIdNumber`

**Transaction**
`date, amount* (AED), method (cash|wire|cheque|crypto|card|other), direction, counterparty,
propertyRef (REAR), goodsDesc (DPMSR)`

**STR-only:** `indicators[], screening{pep, sanctions}, grounds*` · **All:** `action`
(`*` = required by validation)

## Red-flag indicator taxonomy (STR)

Grouped for the UI; each code maps to an official goAML indicator code in a version-specific lookup.

- **Structuring & cash** — `STR-STRUCT`, `STR-CASHINT`, `STR-RAPID`
- **Source of funds / wealth** — `STR-SOF`, `STR-SOW`, `STR-OVERPAY`
- **Third parties & control** — `STR-3RDPARTY`, `STR-NOMINEE`, `STR-UBO`
- **Screening & exposure** — `STR-PEP`, `STR-SANCTION`, `STR-ADVMEDIA`
- **Behaviour & geography** — `STR-EVASIVE`, `STR-URGENCY`, `STR-HIGHRISK`

## Threshold logic (AED 55,000)

- Applies to **REAR** and **DPMSR** only. STR has no monetary threshold.
- `amount ≥ 55,000` by a cash-like method (cash/wire/cheque/crypto) → **mandatory filing triggered**.
- `amount ≥ 55,000` by another method → flag to **confirm method** (likely mandatory).
- `amount < 55,000` → not mandatory as REAR/DPMSR, but **file an STR if suspicious**.

## Validation rules

- **Errors (block):** missing entity name, missing MLRO, missing subject name; for STR: no indicator
  selected, or no grounds.
- **Warnings (allow, flag):** missing date/amount; entity subject with no UBO recorded; amount below
  threshold for a threshold report; a PEP/sanctions hit recorded on a non-STR (prompt to also file an
  STR and freeze per Targeted Financial Sanctions rules).
- Always surfaces the **filing deadline** for the selected report type.

## goAML XML mapping (and the caveat)

The engine emits a well-formed `<report>` with: `rentity_id`, `submission_code`, `report_code`,
`entity_reference`, `submission_date`, `currency_code_local`, `reporting_person` (MLRO), `location`,
`reason`, `action`, a `transaction` (number, date, `transmode_code`, `amount_local`, and the subject
under `t_to_my_client` as `t_person` or `t_entity` with a UBO `director_id`), and `report_indicators`.

> **Caveat:** element names and code lists (`transmode_code`, indicator codes, report codes) are
> version-specific to the FIU's goAML schema. Before any live upload, reconcile this output against the
> current goAML XSD / Excel import template. v0.1 deliberately produces a **file to review and upload**,
> not a direct submission — so we prove ROI without waiting on FIU integration access.

## CDD & UBO module (`cdd.js`)

**Ultimate Beneficial Owner tracing.** Input is an ownership tree: the subject company's `owners[]`,
where each owner is a `person` (a leaf) or an `entity` (a branch with its own `owners[]`).

- **Algorithm:** depth-first walk carrying a cumulative fraction. For each edge, `effective =
  parentFraction × (percent / 100)`. Person nodes accumulate their effective % (summed across all paths
  they appear on); entity nodes recurse.
- **UBO test:** any natural person whose aggregated effective ownership is **≥ 25%** is a UBO. Each UBO
  carries the chain that produced it (e.g. *60% of Marina Holdings → 60% of Gulf Trading = 36%*).
- **Fallback:** if nobody reaches 25%, the result flags that control-by-other-means, then the **senior
  managing official**, must be recorded (per UAE rules).
- **Outputs:** `ubos[]`, all `persons[]` with effective %, `layers` (depth traced), `totalTraced`.

**CDD risk rating.** Transparent additive score over weighted factors:

| Factor | Weight | | Factor | Weight |
|---|---|---|---|---|
| Sanctions/watchlist match | forces **High** | | Nominee/hidden ownership | 2 |
| PEP | 2 | | Complex/opaque ownership | 1 |
| Adverse media | 2 | | Cash-intensive activity | 1 |
| High-risk jurisdiction | 2 | | Non-resident | 1 |
| Unclear source of funds | 2 | | | |

Bands: **Low** 0–2 · **Medium** 3–5 · **High** 6+ (a sanctions hit always → High). Each band returns the
concrete MLRO actions (EDD, senior approval, SOF evidence, monitoring cadence; freeze + STR on a sanctions hit).

## AI assist module (`ai.js`) — optional, off by default

- **Reversible PII redaction.** Emails, Emirates-ID and long ID numbers are swapped for opaque
  `⟦TOKEN⟧`s before any provider call, then restored locally in the result — the provider never sees real
  identifiers, and the final narrative keeps the real values.
- **Offline tidy.** A deterministic formatter (no network, no key) that always works.
- **Narrative polish.** Prompt strictly forbids inventing/altering facts, preserves section structure and
  tokens; formal regulatory tone.
- **Document extraction.** Vision prompt returns strict JSON (`fullName, idType, idNumber, nationality,
  dob, expiry, address`) from an ID/licence image.
- **Providers.** Anthropic (Messages API, with browser-access header) and OpenAI-compatible (OpenAI /
  Azure / gateways via base URL). Keys live in `localStorage` only. Public APIs may require a proxy from a
  `file://` page (CORS); production routes to an in-region endpoint.

## Roadmap to v1

1. **Live screening** — perform PEP / sanctions / adverse-media screening (today we capture results; next
   we run them) with false-positive triage + audit trail.
2. **Compliance cockpit** — multi-client dashboard, deadline reminders, immutable audit log, one-click inspection pack.
3. **goAML integration** — schema-validated export / API.
4. **In-region AI** — enterprise endpoint (removes CORS caveat, strengthens PDPL posture).
5. **Productionization** — hosting, auth, encrypted storage, SOC 2 / ISO 27001.
