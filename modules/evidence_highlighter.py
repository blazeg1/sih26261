"""
Evidence-Linked Highlighter and Risk Scoring Module.

Renders document pages with highlighted bounding boxes corresponding to extracted
regulatory evidence, and computes an explainable composite risk score.

CORE PRINCIPLE: Advisory screening only. Never approves or rejects.
"""

import os
from typing import Dict, List, Optional, Any, Tuple
import fitz  # PyMuPDF
from PIL import Image, ImageDraw


def highlight_evidence_on_page(doc_path: str, page_number: int = 1, bbox: Optional[Dict[str, float]] = None, search_text: Optional[str] = None) -> Optional[Image.Image]:
    """
    Render a PDF page to image and overlay a prominent colored highlight box on the evidence coordinates.
    """
    if not os.path.exists(doc_path):
        # Generate mock page for demonstration if file doesn't exist on disk
        img = Image.new("RGB", (650, 850), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 630, 830], outline=(203, 213, 225), width=2)
        draw.text((40, 50), "OFFICIAL REGULATORY SUBMISSION — AICTE EVIDENCE", fill=(11, 31, 75))
        draw.text((40, 100), f"Document: {os.path.basename(doc_path)}", fill=(71, 85, 105))
        draw.text((40, 140), f"Highlighted Finding: {search_text or 'Evidence finding'}", fill=(239, 68, 68))
        draw.rectangle([35, 130, 480, 170], outline=(239, 68, 68), width=3)
        return img

    try:
        doc = fitz.open(doc_path)
        page_idx = max(0, min(page_number - 1, len(doc) - 1))
        page = doc[page_idx]

        # Locate coordinates if search_text given and no bbox
        if not bbox and search_text:
            rects = page.search_for(search_text)
            if rects:
                r = rects[0]
                bbox = {"x0": r.x0, "y0": r.y0, "x1": r.x1, "y1": r.y1}

        # If bbox is given, draw rectangle on page
        if bbox:
            rect = fitz.Rect(bbox["x0"] - 4, bbox["y0"] - 4, bbox["x1"] + 4, bbox["y1"] + 4)
            # Add highlight annotation
            annot = page.add_rect_annot(rect)
            annot.set_colors(stroke=(1.0, 0.2, 0.2), fill=(1.0, 0.9, 0.3))
            annot.set_opacity(0.4)
            annot.update()

        # Render page to pixmap
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img

    except Exception:
        # Graceful fallback image
        img = Image.new("RGB", (650, 850), color=(248, 250, 252))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"Page {page_number}: {os.path.basename(doc_path)}", fill=(11, 31, 75))
        if search_text:
            draw.text((50, 120), f"Evidence Target: {search_text}", fill=(239, 68, 68))
            draw.rectangle([45, 110, 500, 150], outline=(239, 68, 68), width=3)
        return img


def compute_explainable_risk_score(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate an explainable risk score (0 to 100) where 100 is fully compliant/zero risk.
    Each deduction has a clear plain-language rationale and cited regulatory clause.
    """
    score = 100
    deductions = []

    for f in findings:
        status = str(f.get("status", "")).lower()
        severity = str(f.get("severity", "LOW")).upper()
        rule_name = f.get("rule_name") or f.get("indicator") or f.get("check") or f.get("type", "Check")
        clause = f.get("cited_clause", "APH 2024-27")

        pts = 0
        if "deficiency" in status:
            pts = 25 if severity == "CRITICAL" else 18 if severity == "HIGH" else 10
        elif "anomaly" in status:
            pts = 20 if severity == "CRITICAL" else 14 if severity == "HIGH" else 8
        elif "needs" in status:
            pts = 6

        if pts > 0:
            score = max(0, score - pts)
            deductions.append({
                "finding": rule_name,
                "status": f.get("status"),
                "severity": severity,
                "deduction": -pts,
                "reason": f.get("message") or f.get("detail", "Non-compliance with handbook norms"),
                "clause": clause
            })

    # Risk categorization
    if score >= 85:
        category = "LOW_RISK"
        label = "High Regulatory Compliance"
        color = "#10B981"
    elif score >= 60:
        category = "MODERATE_RISK"
        label = "Deficiency Rectification Required"
        color = "#F59E0B"
    else:
        category = "HIGH_RISK"
        label = "High Scrutiny Attention Required"
        color = "#EF4444"

    return {
        "final_score": score,
        "category": category,
        "label": label,
        "color": color,
        "total_deductions_count": len(deductions),
        "deductions": deductions,
        "advisory_notice": (
            "⚠️ ADVISORY NOTICE: The AI system provides decision-support screening signals only. "
            "It never approves or rejects applications. Final statutory authority remains exclusively with competent AICTE officers."
        )
    }
