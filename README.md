# 🏛️ AICTE Approval Validation Platform

> **SIH 26261** — AI-Powered Application Validation, Document Authentication & Regulatory Compliance Verification

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Problem Statement

The All India Council for Technical Education (AICTE) processes thousands of applications for Extension of Approval (EoA) and other approval-related changes. Manual verification of documents is time-consuming, error-prone, and resource-intensive. This platform provides AI-powered decision support for:

- **Document Validation** — OCR-based extraction, classification, and completeness checks
- **Anomaly Detection** — Identify suspicious alterations, duplicates, and inconsistencies
- **Compliance Checking** — Configurable regulatory checklists with category-wise scoring
- **Verification Workflow** — Issuing authority verification through APIs and official sources
- **Dashboard & Audit Trail** — Centralized monitoring with full traceability

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 📄 OCR & Document Processing | Extract text from PDFs and images using Tesseract + PyMuPDF |
| 🤖 Document Classification | Auto-classify documents (Affidavit, NOC, Fire Safety, etc.) |
| 🔍 Cross-Document Validation | Check consistency across all application documents |
| ⚠️ Anomaly Detection | Detect metadata tampering, duplicates, and forgery indicators |
| ✅ Regulatory Compliance | Configurable checklists from AICTE Approval Process Handbook |
| 🔗 Verification Service | Simulate issuing authority verification (NBA, NAAC, etc.) |
| 📊 Interactive Dashboard | Real-time Plotly charts for application monitoring |
| 📝 Audit Trail | Complete traceability with role-based access |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| OCR | Tesseract (pytesseract) |
| PDF Processing | PyMuPDF (fitz) |
| Image Processing | OpenCV |
| Data Matching | Pandas + RapidFuzz |
| Validation | Pydantic v2 |
| Database | SQLite |
| Charts | Plotly |
| Testing | Pytest |

## 📦 Installation

### Prerequisites
- Python 3.9+
- Tesseract OCR ([Install Guide](https://github.com/tesseract-ocr/tesseract))

### Setup

```bash
# Clone the repository
git clone https://github.com/your-team/sih-26261-aicte.git
cd sih-26261-aicte

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app will automatically initialize the database and seed it with demo data on first run.

### Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Reviewer | reviewer1 | review123 |
| Viewer | viewer1 | viewer123 |

## 📁 Project Structure

```
sihdemo/
├── app.py                          # Main Streamlit entry point
├── requirements.txt                # Python dependencies
├── config/
│   ├── settings.py                 # Application configuration
│   └── checklists/                 # Regulatory checklist JSONs
│       ├── eoa_checklist.json
│       └── new_institution_checklist.json
├── database/
│   ├── db.py                       # SQLite database manager
│   └── seed_data.py                # Demo data seeder
├── modules/
│   ├── ocr_engine.py               # Tesseract OCR wrapper
│   ├── pdf_processor.py            # PyMuPDF PDF processing
│   ├── image_preprocessor.py       # OpenCV image enhancement
│   ├── document_classifier.py      # Document type classification
│   ├── data_extractor.py           # Structured field extraction
│   ├── validation_engine.py        # Pydantic validation rules
│   ├── anomaly_detector.py         # Anomaly/forgery detection
│   ├── compliance_checker.py       # Regulatory compliance checks
│   ├── comparison_engine.py        # RapidFuzz field comparison
│   └── verification_service.py     # Issuing authority verification
├── pages/
│   ├── 1_📋_Application_Upload.py
│   ├── 2_🔍_Document_Validation.py
│   ├── 3_⚠️_Anomaly_Detection.py
│   ├── 4_✅_Compliance_Check.py
│   ├── 5_📊_Dashboard.py
│   └── 6_📝_Audit_Trail.py
├── utils/
│   ├── auth.py                     # Role-based authentication
│   └── helpers.py                  # Utility functions
├── tests/                          # Pytest test suite
└── sample_data/                    # Synthetic test data
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 👥 Team

*SIH 2026 — Team Details*

---

<p align="center">
  Built for <strong>Smart India Hackathon 2026</strong> — Problem Statement 26261
</p>
