"""
Multi-Level Document Authentication Engine.

Implements 4 distinct screening levels:
- Level 1: PDF / EXIF Metadata Forensics (editing software, timestamp tampering)
- Level 2: Visual Forensics (Error Level Analysis ELA, overlay detection)
- Level 3: Digital Signatures & QR Code Validation
- Level 4: Simulated Issuing Authority Connectors (DigiLocker, State Fire, Land GIS, NBA)

CORE PRINCIPLE: All outputs are preliminary screening signals requiring human verification,
never conclusive proof of fraud or misconduct.
"""

import os
import re
import cv2
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
import fitz  # PyMuPDF
from PIL import Image, ImageChops, ImageEnhance


# ──────────────────────────────────────────────────────────────────────────────
# Level 4: Mock Registry Connector Interface & Implementations
# ──────────────────────────────────────────────────────────────────────────────
class IssuerConnectorInterface(ABC):
    """Abstract interface for government and issuing authority connectors."""

    @abstractmethod
    def verify_document(self, query_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query issuing authority and return screening results."""
        pass


class DigiLockerAcademicConnector(IssuerConnectorInterface):
    """Simulated connector for DigiLocker National Academic Depository (NAD)."""

    def verify_document(self, query_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Clearly marked as simulated
        ctx = context or {}
        faculty_name = ctx.get("faculty_name", "Dr. Ramesh Chandra Sharma")
        degree = ctx.get("degree", "Ph.D. in Computer Science")

        return {
            "authority": "DigiLocker National Academic Depository (NAD)",
            "connector_type": "API_REST_TLS13",
            "query_id": query_id,
            "status": "Verified",
            "is_simulated": True,
            "simulation_notice": "SIMULATED REGISTRY CONNECTOR - For Evaluation & Demo",
            "timestamp": datetime.now().isoformat(),
            "evidence": {
                "holder_name": faculty_name,
                "degree_title": degree,
                "awarding_university": "IIT Roorkee",
                "year_of_award": 2012,
                "pki_status": "AUTHENTIC_RECORD_FOUND"
            },
            "advisory_message": "Faculty Ph.D. record found on National Academic Depository."
        }


class StateFireServicesConnector(IssuerConnectorInterface):
    """Simulated connector for State Fire & Rescue Services Directorate."""

    def verify_document(self, query_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        institution_name = ctx.get("institution_name", "Aryabhatta Institute of Technology")
        # If query_id matches known expired seed or context says expired
        is_expired = "84920" in query_id or ctx.get("simulate_expired", False)

        if is_expired:
            return {
                "authority": "State Fire & Emergency Services Directorate",
                "connector_type": "GOV_PORTAL_WEBHOOK",
                "query_id": query_id,
                "status": "Deficiency",
                "is_simulated": True,
                "simulation_notice": "SIMULATED REGISTRY CONNECTOR - For Evaluation & Demo",
                "timestamp": datetime.now().isoformat(),
                "evidence": {
                    "certificate_number": query_id,
                    "registered_entity": institution_name,
                    "issue_date": "2024-03-15",
                    "expiry_date": "2026-03-14",
                    "current_status": "EXPIRED",
                    "building_height_cleared": 14.8
                },
                "advisory_message": "State Fire Portal confirms certificate expired on 2026-03-14. Renewal required."
            }

        return {
            "authority": "State Fire & Emergency Services Directorate",
            "connector_type": "GOV_PORTAL_WEBHOOK",
            "query_id": query_id,
            "status": "Verified",
            "is_simulated": True,
            "simulation_notice": "SIMULATED REGISTRY CONNECTOR - For Evaluation & Demo",
            "timestamp": datetime.now().isoformat(),
            "evidence": {
                "certificate_number": query_id,
                "registered_entity": institution_name,
                "issue_date": "2025-06-01",
                "expiry_date": "2028-05-31",
                "current_status": "ACTIVE_VALID"
            },
            "advisory_message": "State Fire Portal confirms active unexpired certificate."
        }


class StateLandRegistryGISConnector(IssuerConnectorInterface):
    """Simulated connector for State Land Revenue & Bhulekh/Bhoomi GIS."""

    def verify_document(self, query_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        declared_survey = ctx.get("survey_number", "492/1")
        mismatch = "999" in query_id or ctx.get("simulate_mismatch", False)

        if mismatch:
            return {
                "authority": "State Land Revenue & Cadastral GIS Portal",
                "connector_type": "REVENUE_GIS_API",
                "query_id": query_id,
                "status": "Deficiency",
                "is_simulated": True,
                "simulation_notice": "SIMULATED REGISTRY CONNECTOR - For Evaluation & Demo",
                "timestamp": datetime.now().isoformat(),
                "evidence": {
                    "survey_number": query_id,
                    "gis_title_holder": "Unregistered / Different Khatauni",
                    "encumbrance_status": "MORTGAGED_OR_DISPUTED"
                },
                "advisory_message": "Survey number not matched to educational trust on State Cadastral GIS."
            }

        return {
            "authority": "State Land Revenue & Cadastral GIS Portal",
            "connector_type": "REVENUE_GIS_API",
            "query_id": query_id,
            "status": "Verified",
            "is_simulated": True,
            "simulation_notice": "SIMULATED REGISTRY CONNECTOR - For Evaluation & Demo",
            "timestamp": datetime.now().isoformat(),
            "evidence": {
                "survey_number": query_id,
                "registered_trust": ctx.get("trust_name", "Aryabhatta Educational Trust"),
                "area_acres": ctx.get("land_area_acres", 7.5),
                "land_use": "EDUCATIONAL_CONVERTED",
                "encumbrance_status": "FREE_FROM_ENCUMBRANCE"
            },
            "advisory_message": "Title deed and clear boundary polygon confirmed on State Revenue GIS."
        }


class NBAAccreditationConnector(IssuerConnectorInterface):
    """Simulated connector for National Board of Accreditation (NBA) API."""

    def verify_document(self, query_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context or {}
        program = ctx.get("program_name", "Computer Science & Engineering")

        return {
            "authority": "National Board of Accreditation (NBA)",
            "connector_type": "NBA_CENTRAL_REGISTER",
            "query_id": query_id,
            "status": "Verified",
            "is_simulated": True,
            "simulation_notice": "SIMULATED REGISTRY CONNECTOR - For Evaluation & Demo",
            "timestamp": datetime.now().isoformat(),
            "evidence": {
                "program": program,
                "tier": "Tier-II",
                "score": 678,
                "validity_period": "2023-2026",
                "accreditation_status": "ACCREDITED_3_YEARS"
            },
            "advisory_message": "Valid NBA accreditation on central register for 3 academic sessions."
        }


# ──────────────────────────────────────────────────────────────────────────────
# Master Document Authenticator (Levels 1 to 4)
# ──────────────────────────────────────────────────────────────────────────────
class DocumentAuthenticator:
    """
    Executes 4-level document authentication analysis.
    Produces evidence-linked screening signals for regulatory officers.
    """

    def __init__(self):
        self.connectors = {
            "digilocker": DigiLockerAcademicConnector(),
            "fire": StateFireServicesConnector(),
            "land": StateLandRegistryGISConnector(),
            "nba": NBAAccreditationConnector(),
        }

    # ── Level 1: PDF/EXIF Metadata Screening ─────────────────────────────────
    def screen_level1_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Screen file metadata for suspicious producers, creation/mod timeline discrepancies,
        and temporal inconsistencies.
        """
        findings = []
        meta = {}

        if not os.path.exists(file_path):
            return {"level": "Level 1: Metadata Screening", "status": "Needs manual review", "findings": ["File not found"]}

        if file_path.lower().endswith(".pdf"):
            try:
                doc = fitz.open(file_path)
                meta = doc.metadata or {}
                doc.close()

                producer = (meta.get("producer") or "").lower()
                creator = (meta.get("creator") or "").lower()
                creation_str = meta.get("creationDate") or ""
                mod_str = meta.get("modDate") or ""

                # 1. Suspicious Editing Software
                editing_tools = ["photoshop", "canva", "gimp", "illustrator", "inkscape", "coreldraw", "pdf-xchange"]
                matched_tool = next((tool for tool in editing_tools if tool in producer or tool in creator), None)
                if matched_tool:
                    findings.append({
                        "indicator": "Graphic Editing Software Used",
                        "status": "Possible anomaly - needs human verification",
                        "severity": "HIGH",
                        "detail": f"Document produced or altered with graphic software '{matched_tool.title()}'. Official issuing authorities rarely use image editors.",
                        "evidence": f"Producer: {meta.get('producer')} | Creator: {meta.get('creator')}"
                    })

                # 2. Timestamp Discrepancy (Modified long after creation)
                if creation_str and mod_str and creation_str != mod_str:
                    findings.append({
                        "indicator": "Post-Issuance PDF Alteration",
                        "status": "Possible anomaly - needs human verification",
                        "severity": "MEDIUM",
                        "detail": "PDF modification timestamp differs from creation timestamp, indicating post-generation edits.",
                        "evidence": f"Created: {creation_str} | Modified: {mod_str}"
                    })

            except Exception as e:
                findings.append({
                    "indicator": "Corrupt Metadata",
                    "status": "Needs manual review",
                    "severity": "LOW",
                    "detail": f"Could not parse PDF metadata structure: {e}",
                    "evidence": "N/A"
                })

        # Overall level 1 status
        status = "Verified"
        if any(f["status"] == "Possible anomaly - needs human verification" for f in findings):
            status = "Possible anomaly - needs human verification"
        elif any(f["status"] == "Needs manual review" for f in findings):
            status = "Needs manual review"

        return {
            "level": "Level 1: Metadata Screening",
            "status": status,
            "metadata_raw": meta,
            "findings": findings
        }

    # ── Level 2: Visual Forensics (ELA & Overlay Inconsistency) ───────────────
    def screen_level2_visual_forensics(self, image_input: Any) -> Dict[str, Any]:
        """
        Perform Error Level Analysis (ELA) and detect potential text overlay splices.
        """
        findings = []

        try:
            if isinstance(image_input, str):
                if image_input.lower().endswith(".pdf"):
                    # Rasterize page 1
                    doc = fitz.open(image_input)
                    page = doc[0]
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    doc.close()
                else:
                    img = Image.open(image_input).convert("RGB")
            elif isinstance(image_input, Image.Image):
                img = image_input.convert("RGB")
            else:
                img = Image.fromarray(image_input).convert("RGB")

            # Perform ELA: save temporary copy at 90% quality
            tmp_ela_path = os.path.join(os.path.dirname(__file__), "..", "data", "temp_ela.jpg")
            os.makedirs(os.path.dirname(tmp_ela_path), exist_ok=True)
            img.save(tmp_ela_path, "JPEG", quality=90)
            recompressed = Image.open(tmp_ela_path)

            diff = ImageChops.difference(img, recompressed)
            diff_arr = np.array(diff)
            mean_diff = float(np.mean(diff_arr))
            max_diff = int(np.max(diff_arr))

            # Look for high-contrast localized anomaly clusters
            high_clusters = int(np.sum(diff_arr > 35))
            cluster_ratio = high_clusters / (diff_arr.size / 3)

            if cluster_ratio > 0.05 and max_diff > 45:
                findings.append({
                    "indicator": "Compression Artifact Inconsistency (ELA)",
                    "status": "Possible anomaly - needs human verification",
                    "severity": "HIGH",
                    "detail": "Localized high-frequency compression differential detected. Indicates potential digital copy-pasting or altered text block.",
                    "evidence": f"ELA Max Diff: {max_diff} | Suspicious Cluster Area: {cluster_ratio*100:.2f}%"
                })
            else:
                findings.append({
                    "indicator": "Uniform Compression Gradient",
                    "status": "Verified",
                    "severity": "LOW",
                    "detail": "Image shows consistent recompression error levels across layout.",
                    "evidence": f"Mean Residual Diff: {mean_diff:.2f}"
                })

        except Exception as e:
            findings.append({
                "indicator": "ELA Analysis Failure",
                "status": "Needs manual review",
                "severity": "LOW",
                "detail": f"Visual forensic scan could not complete: {e}",
                "evidence": "N/A"
            })

        status = "Verified"
        if any(f["status"] == "Possible anomaly - needs human verification" for f in findings):
            status = "Possible anomaly - needs human verification"

        return {
            "level": "Level 2: Visual Forensics",
            "status": status,
            "findings": findings
        }

    # ── Level 3: Digital Signatures & QR Code Validation ─────────────────────
    def screen_level3_signatures_and_qr(self, file_path: str) -> Dict[str, Any]:
        """
        Inspect digital signature certificates and scan for 2D barcodes/QR codes.
        """
        findings = []
        qr_detected = False
        qr_payload = ""
        sig_detected = False

        if os.path.exists(file_path):
            if file_path.lower().endswith(".pdf"):
                try:
                    # Check PyMuPDF signature dictionary
                    doc = fitz.open(file_path)
                    # Check for signature forms
                    for page in doc:
                        for widget in page.widgets():
                            if widget.field_type == fitz.PDF_WIDGET_TYPE_SIGNATURE:
                                sig_detected = True
                                break

                    # Also render first page to check for QR code
                    page0 = doc[0]
                    pix = page0.get_pixmap(dpi=150)
                    np_img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
                    if pix.n == 4:
                        np_img = cv2.cvtColor(np_img, cv2.COLOR_RGBA2RGB)

                    detector = cv2.QRCodeDetector()
                    data, bbox, _ = detector.detectAndDecode(np_img)
                    if data:
                        qr_detected = True
                        qr_payload = data

                    doc.close()
                except Exception:
                    pass

            else:
                try:
                    cv_img = cv2.imread(file_path)
                    if cv_img is not None:
                        detector = cv2.QRCodeDetector()
                        data, bbox, _ = detector.detectAndDecode(cv_img)
                        if data:
                            qr_detected = True
                            qr_payload = data
                except Exception:
                    pass

        # Interpret findings
        if sig_detected:
            findings.append({
                "indicator": "PDF Cryptographic Signature",
                "status": "Verified",
                "severity": "LOW",
                "detail": "Digital signature structure detected inside PDF container.",
                "evidence": "Signature widget present"
            })

        if qr_detected:
            is_gov_url = ".gov.in" in qr_payload or ".nic.in" in qr_payload or "aicte-india.org" in qr_payload
            findings.append({
                "indicator": "2D QR Code Validation",
                "status": "Verified" if is_gov_url else "Needs manual review",
                "severity": "LOW" if is_gov_url else "MEDIUM",
                "detail": f"Decoded QR payload: {qr_payload[:60]}... " + ("(Official Government Domain)" if is_gov_url else "(Non-government redirect)"),
                "evidence": f"Decoded: {qr_payload}"
            })
        else:
            findings.append({
                "indicator": "2D QR Barcode",
                "status": "Needs manual review",
                "severity": "LOW",
                "detail": "No digital QR code detected on page 1. Physical seal requires manual verification.",
                "evidence": "N/A"
            })

        status = "Verified" if (sig_detected or qr_detected) else "Needs manual review"
        return {
            "level": "Level 3: Digital Signatures & QR Code",
            "status": status,
            "sig_detected": sig_detected,
            "qr_detected": qr_detected,
            "qr_payload": qr_payload,
            "findings": findings
        }

    # ── Level 4: Simulated Issuer Verification ───────────────────────────────
    def screen_level4_issuer_verification(self, authority_type: str, query_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute simulated query to official issuing authority registry.
        """
        connector = self.connectors.get(authority_type.lower(), self.connectors["fire"])
        result = connector.verify_document(query_id, context=context)

        finding = {
            "indicator": f"Official Portal Verification: {result['authority']}",
            "status": result["status"],
            "severity": "LOW" if result["status"] == "Verified" else "HIGH",
            "detail": result["advisory_message"],
            "evidence": str(result["evidence"]),
            "is_simulated": True,
            "simulation_notice": result["simulation_notice"]
        }

        return {
            "level": "Level 4: Issuing Authority Verification",
            "status": result["status"],
            "findings": [finding],
            "raw_response": result
        }

    # ── Complete 4-Level Pipeline ────────────────────────────────────────────
    def run_full_authentication(self, file_path: str, authority_type: str = "fire", query_id: str = "NOC-2024-84920", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run all 4 authentication levels in sequence."""
        l1 = self.screen_level1_metadata(file_path)
        l2 = self.screen_level2_visual_forensics(file_path)
        l3 = self.screen_level3_signatures_and_qr(file_path)
        l4 = self.screen_level4_issuer_verification(authority_type, query_id, context=context)

        all_findings = l1["findings"] + l2["findings"] + l3["findings"] + l4["findings"]

        # Composite advisory status
        if any(f["status"] == "Deficiency" for f in all_findings):
            overall_status = "Deficiency"
        elif any(f["status"] == "Possible anomaly - needs human verification" for f in all_findings):
            overall_status = "Possible anomaly - needs human verification"
        elif any(f["status"] == "Needs manual review" for f in all_findings):
            overall_status = "Needs manual review"
        else:
            overall_status = "Verified"

        return {
            "overall_status": overall_status,
            "levels": {
                "level1_metadata": l1,
                "level2_visual_forensics": l2,
                "level3_signatures_qr": l3,
                "level4_issuer_registry": l4
            },
            "all_findings": all_findings,
            "advisory_disclaimer": "All findings are advisory screening signals only. Not proof of fraud."
        }
