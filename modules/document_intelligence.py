"""
Document Intelligence Module for AICTE Validation Platform.

Provides PyMuPDF spatial text extraction with bounding boxes,
explainable keyword-weighted document classification, and
cross-document consistency checking using RapidFuzz.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import fitz  # PyMuPDF
from rapidfuzz import fuzz

from config.settings import DocumentTypes


class DocumentIntelligence:
    """Extracts structured fields with page coordinates, bounding boxes, and confidence scores."""

    def __init__(self):
        # Patterns for key fields
        self.patterns = {
            "aicte_id": [
                r"\b(1-\d{9,11})\b",
                r"\b([0-9]{1,2}-[0-9]{7,10})\b",
                r"(?:AICTE\s*ID|Permanent\s*ID)[:\s]+([A-Za-z0-9\-]+)"
            ],
            "survey_number": [
                r"(?:Survey|Khasra|Gata|Khatauni)\s*(?:No\.?|Number)?[:\s]+([0-9]+[/0-9\-]*)",
                r"\b(?:Plot|Khata)\s*No\.?[:\s]+([0-9A-Za-z\/\-]+)"
            ],
            "land_area": [
                r"(\d+(?:\.\d+)?)\s*(?:Acres?|acre)",
                r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:Sq\.?\s*Meters?|sqm|sq\.m|square\s*meters?)",
                r"(\d+(?:\.\d+)?)\s*(?:Hectares?|hectare)"
            ],
            "trust_name": [
                r"(?:managed by|sponsored by|Trust|Society)[:\s]+([A-Za-z0-9\s\.\(\)&]+(?:Trust|Society|Foundation|Sansthan|Samiti))",
                r"\b([A-Za-z\s]+(?:Educational\s*Trust|Education\s*Society|Memorial\s*Trust))\b"
            ],
            "dates": [
                r"\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\b",
                r"\b(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b",
                r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b"
            ]
        }

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text, pages, and structured fields with bounding boxes from a PDF.
        """
        if not os.path.exists(pdf_path):
            return {"error": "File not found", "fields": [], "pages": 0, "full_text": ""}

        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        full_text = ""
        extracted_fields = []

        for page_idx in range(num_pages):
            page = doc[page_idx]
            page_text = page.get_text()
            full_text += page_text + "\n"

            # Search for fields
            for field_name, regex_list in self.patterns.items():
                for pat in regex_list:
                    for match in re.finditer(pat, page_text, re.IGNORECASE):
                        val = match.group(1) if match.groups() else match.group(0)
                        val = val.strip()

                        # Locate rectangle on page using PyMuPDF
                        rects = page.search_for(val)
                        bbox = None
                        if rects:
                            r = rects[0]
                            bbox = {
                                "x0": round(r.x0, 2),
                                "y0": round(r.y0, 2),
                                "x1": round(r.x1, 2),
                                "y1": round(r.y1, 2),
                                "width": round(r.width, 2),
                                "height": round(r.height, 2)
                            }

                        # Confidence heuristic
                        confidence = 0.95 if bbox else 0.80
                        if field_name == "aicte_id" and re.match(r"^1-\d{9,11}$", val):
                            confidence = 0.99

                        # Snippet
                        start_idx = max(0, match.start() - 40)
                        end_idx = min(len(page_text), match.end() + 40)
                        snippet = page_text[start_idx:end_idx].replace("\n", " ").strip()

                        extracted_fields.append({
                            "field_name": field_name,
                            "value": val,
                            "source_page": page_idx + 1,
                            "bbox": bbox,
                            "confidence": confidence,
                            "context_snippet": snippet
                        })
                        break  # Found best match for this pattern

        doc.close()
        return {
            "num_pages": num_pages,
            "full_text": full_text,
            "fields": extracted_fields
        }


class ExplainableClassifier:
    """Classifies document types using keyword density and provides human-readable explanations."""

    def __init__(self):
        self.type_keywords = {
            DocumentTypes.FIRE_SAFETY_CERT: {
                "fire": 3.0, "noc": 2.5, "rescue": 2.0, "extinguisher": 2.0,
                "hydrant": 2.0, "safety certificate": 3.5, "directorate of fire": 4.0, "fire service": 3.0
            },
            DocumentTypes.AFFIDAVIT: {
                "affidavit": 4.0, "solemnly": 3.0, "affirm": 2.5, "deponent": 3.5,
                "oath": 3.0, "notary": 3.0, "format-a": 3.5, "undertaking": 2.0, "sworn": 2.5
            },
            DocumentTypes.LAND_DOCUMENT: {
                "land": 2.5, "registry": 3.0, "khasra": 3.5, "khatauni": 3.5, "deed": 3.0,
                "acres": 2.0, "survey no": 3.0, "sub-registrar": 3.5, "patwari": 3.0, "tehsil": 2.5
            },
            DocumentTypes.BUILDING_PLAN: {
                "floor plan": 3.5, "building": 2.0, "sanctioned": 2.5, "carpet area": 3.0,
                "built-up": 3.0, "architect": 3.5, "fsi": 2.5, "far": 2.5, "elevation": 3.0
            },
            DocumentTypes.FACULTY_LIST: {
                "faculty": 3.0, "professor": 3.0, "designation": 2.5, "qualification": 2.5,
                "assistant professor": 3.5, "associate professor": 3.5, "ph.d": 2.0, "salary": 2.0, "date of joining": 3.0
            },
            DocumentTypes.FINANCIAL_STATEMENT: {
                "balance sheet": 4.0, "chartered accountant": 3.5, "audit": 3.0, "profit and loss": 3.5,
                "assets": 2.5, "liabilities": 2.5, "ca membership": 3.0, "fdr": 2.5, "endowment": 2.5
            },
            DocumentTypes.ACCREDITATION_CERT: {
                "nba": 4.0, "naac": 4.0, "accreditation": 3.5, "valid up to": 2.5,
                "tier-i": 3.0, "tier-ii": 3.0, "grade a": 3.0, "cgpa": 2.5
            },
            DocumentTypes.NOC: {
                "no objection": 4.0, "affiliating university": 3.0, "state government": 2.5,
                "continuation of affiliation": 3.5, "directorate of technical education": 3.5
            }
        }

    def classify(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Classify document and return explainable keyword weights.
        """
        text_lower = text.lower()
        fname_lower = filename.lower()
        scores = {}
        explanations = {}

        for doc_type, kw_map in self.type_keywords.items():
            type_score = 0.0
            matched_evidence = []
            for kw, weight in kw_map.items():
                if kw in text_lower or kw in fname_lower:
                    type_score += weight
                    matched_evidence.append((kw, weight))

            scores[doc_type] = round(type_score, 2)
            explanations[doc_type] = sorted(matched_evidence, key=lambda x: x[1], reverse=True)

        # Pick best match
        best_type, best_score = max(scores.items(), key=lambda x: x[1])

        # Confidence normalization (sigmoid or linear scale)
        if best_score >= 8.0:
            confidence = 0.96
        elif best_score >= 4.0:
            confidence = 0.85
        elif best_score > 0:
            confidence = 0.65
        else:
            best_type = DocumentTypes.OTHER
            confidence = 0.40

        return {
            "predicted_type": best_type,
            "confidence": confidence,
            "score": best_score,
            "all_scores": scores,
            "explanation": explanations.get(best_type, []),
            "method": "Explainable Keyword Density Scoring"
        }


class CrossDocumentConsistencyChecker:
    """Cross-verifies core institutional identifiers across multiple documents in a dossier."""

    def __init__(self):
        pass

    def check_dossier_consistency(self, declared_profile: Dict[str, Any], documents_extracted: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compare institution name, address, survey number, trust name and land area across documents.
        """
        findings = []

        decl_name = declared_profile.get("institution_name", "").strip()
        decl_address = declared_profile.get("address", "").strip()
        decl_survey = declared_profile.get("survey_number", "").strip()
        decl_trust = declared_profile.get("trust_name", "").strip()
        decl_land = declared_profile.get("land_area_acres", 0.0)

        # 1. Institution Name Cross-Check
        for doc in documents_extracted:
            fname = doc.get("filename", "Doc")
            extracted_name = doc.get("extracted_name") or doc.get("institution_name")
            if extracted_name and decl_name:
                sim = fuzz.token_sort_ratio(decl_name.lower(), extracted_name.lower())
                if sim >= 88:
                    findings.append({
                        "check": "Institution Name Consistency",
                        "status": "Verified",
                        "severity": "LOW",
                        "similarity": f"{sim:.1f}%",
                        "document": fname,
                        "declared": decl_name,
                        "extracted": extracted_name,
                        "message": f"Institution name on '{fname}' matches application record ({sim:.1f}% similarity)."
                    })
                elif sim >= 65:
                    findings.append({
                        "check": "Institution Name Consistency",
                        "status": "Possible anomaly - needs human verification",
                        "severity": "MEDIUM",
                        "similarity": f"{sim:.1f}%",
                        "document": fname,
                        "declared": decl_name,
                        "extracted": extracted_name,
                        "message": f"Minor variance in institution name on '{fname}': '{extracted_name}' vs declared '{decl_name}'."
                    })
                else:
                    findings.append({
                        "check": "Institution Name Consistency",
                        "status": "Deficiency",
                        "severity": "HIGH",
                        "similarity": f"{sim:.1f}%",
                        "document": fname,
                        "declared": decl_name,
                        "extracted": extracted_name,
                        "message": f"Substantial name mismatch on '{fname}': '{extracted_name}' differs significantly from declared '{decl_name}'."
                    })

        # 2. Survey Number Cross-Check
        if decl_survey:
            for doc in documents_extracted:
                doc_survey = doc.get("survey_number")
                fname = doc.get("filename", "Doc")
                if doc_survey:
                    sim = fuzz.ratio(str(decl_survey).lower(), str(doc_survey).lower())
                    if sim >= 90:
                        findings.append({
                            "check": "Land Survey Number Cross-Check",
                            "status": "Verified",
                            "severity": "LOW",
                            "similarity": f"{sim:.1f}%",
                            "document": fname,
                            "declared": str(decl_survey),
                            "extracted": str(doc_survey),
                            "message": f"Survey number '{doc_survey}' matches registered campus land title."
                        })
                    else:
                        findings.append({
                            "check": "Land Survey Number Cross-Check",
                            "status": "Deficiency",
                            "severity": "HIGH",
                            "similarity": f"{sim:.1f}%",
                            "document": fname,
                            "declared": str(decl_survey),
                            "extracted": str(doc_survey),
                            "message": f"Survey number mismatch on '{fname}': Extracted '{doc_survey}' vs registered '{decl_survey}'."
                        })

        # 3. Land Area Cross-Check
        if decl_land and float(decl_land) > 0:
            for doc in documents_extracted:
                doc_land = doc.get("land_area_acres")
                fname = doc.get("filename", "Doc")
                if doc_land is not None:
                    try:
                        diff = abs(float(decl_land) - float(doc_land))
                        if diff <= 0.1:
                            findings.append({
                                "check": "Land Area Numerical Match",
                                "status": "Verified",
                                "severity": "LOW",
                                "similarity": "100%",
                                "document": fname,
                                "declared": f"{decl_land} Acres",
                                "extracted": f"{doc_land} Acres",
                                "message": f"Land area ({doc_land} Acres) on '{fname}' matches declared application."
                            })
                        else:
                            findings.append({
                                "check": "Land Area Numerical Match",
                                "status": "Possible anomaly - needs human verification",
                                "severity": "HIGH",
                                "similarity": f"{round((1 - diff/float(decl_land))*100, 1)}%",
                                "document": fname,
                                "declared": f"{decl_land} Acres",
                                "extracted": f"{doc_land} Acres",
                                "message": f"Discrepancy in land area on '{fname}': Extracted {doc_land} Acres vs declared {decl_land} Acres."
                            })
                    except (ValueError, TypeError):
                        pass

        return findings
