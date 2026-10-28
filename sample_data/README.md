# Sample Data Directory

This directory holds **sample and synthetic data** used for testing, demonstrations,
and development of the AICTE Application Validation Platform (SIH 26261).

## Purpose

All data in this directory is **synthetic / fabricated** and does not represent
any real institution, individual, or AICTE application. It is used solely for:

- Automated test suites (`tests/`)
- Demo and presentation purposes
- Development and debugging

## Types of Test Documents

The following types of sample documents are referenced or generated programmatically:

| Document Type | Description |
|---|---|
| **Affidavit** | Sworn statements from institution management |
| **NOC (No Objection Certificate)** | State government clearance letters |
| **Fire Safety Certificate** | Fire department compliance certificates |
| **Faculty List** | Teaching staff details with qualifications |
| **Financial Statement** | Balance sheet and income/expenditure reports |
| **Land Documents** | Ownership / lease deed records |
| **Building Plan** | Approved architectural plans |
| **Trust / Society Registration** | Registration certificates of governing body |
| **EOA (Extension of Approval)** | AICTE approval extension documents |

## Data Generation

Most test data is generated programmatically in:

- **`tests/conftest.py`** — Pytest fixtures that create in-memory test data
- **`database/seed_data.py`** — Database seeding script with synthetic institutions,
  applications, and documents
- **`tests/test_*.py`** — Individual test files with inline test data

## Important Notes

> ⚠️ **Do NOT place real PII or sensitive documents in this directory.**
>
> All data must remain synthetic. If you need to test with real documents,
> use a separate, gitignored directory and never commit them.

## File Formats

Sample data may include:
- `.json` — Structured data (checklists, field mappings)
- `.png` / `.jpg` — Synthetic test images (generated via OpenCV)
- `.pdf` — Synthetic PDF documents (generated via PyMuPDF)
- `.txt` — Raw text samples for OCR/NLP testing
