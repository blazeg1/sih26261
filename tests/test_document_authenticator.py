"""
Unit tests for 4-Level Document Authentication Engine (modules/document_authenticator.py).
Tests Level 1 Metadata, Level 2 ELA forensics, Level 3 Signatures/QR, and Level 4 Simulated Connectors.
"""

import os
import pytest
import fitz
from PIL import Image
from modules.document_authenticator import (
    DocumentAuthenticator,
    DigiLockerAcademicConnector,
    StateFireServicesConnector,
    StateLandRegistryGISConnector,
    NBAAccreditationConnector
)


@pytest.fixture
def auth_engine():
    return DocumentAuthenticator()


@pytest.fixture
def sample_pdf_with_metadata(tmp_path):
    pdf_path = str(tmp_path / "photoshop_doc.pdf")
    doc = fitz.open()
    page = doc.new_page(width=500, height=500)
    page.insert_text((50, 50), "Certificate Text Sample")
    doc.set_metadata({
        "producer": "Adobe Photoshop 2024",
        "creator": "Adobe Photoshop",
        "creationDate": "D:20240101120000Z",
        "modDate": "D:20260320140000Z"
    })
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_level1_metadata_screening(auth_engine, sample_pdf_with_metadata):
    res = auth_engine.screen_level1_metadata(sample_pdf_with_metadata)
    assert res["level"] == "Level 1: Metadata Screening"
    assert res["status"] == "Possible anomaly - needs human verification"

    indicators = [f["indicator"] for f in res["findings"]]
    assert "Graphic Editing Software Used" in indicators
    assert "Post-Issuance PDF Alteration" in indicators


def test_level2_visual_forensics(auth_engine, tmp_path):
    # Create simple image
    img_path = str(tmp_path / "test_img.jpg")
    img = Image.new("RGB", (300, 300), color=(255, 255, 255))
    img.save(img_path)

    res = auth_engine.screen_level2_visual_forensics(img_path)
    assert res["level"] == "Level 2: Visual Forensics"
    assert "findings" in res
    assert len(res["findings"]) > 0


def test_level4_simulated_connectors(auth_engine):
    # DigiLocker
    digi = auth_engine.connectors["digilocker"]
    res_digi = digi.verify_document("PHD-102914")
    assert res_digi["status"] == "Verified"
    assert res_digi["is_simulated"] is True
    assert "SIMULATED" in res_digi["simulation_notice"]

    # State Fire (Expired case)
    fire = auth_engine.connectors["fire"]
    res_fire = fire.verify_document("NOC-2024-84920")
    assert res_fire["status"] == "Deficiency"
    assert res_fire["is_simulated"] is True

    # State Fire (Valid case)
    res_fire_ok = fire.verify_document("NOC-2025-99999")
    assert res_fire_ok["status"] == "Verified"


def test_full_authentication_pipeline(auth_engine, sample_pdf_with_metadata):
    full_res = auth_engine.run_full_authentication(
        sample_pdf_with_metadata,
        authority_type="fire",
        query_id="NOC-2024-84920"
    )
    assert "overall_status" in full_res
    assert full_res["overall_status"] in ("Deficiency", "Possible anomaly - needs human verification")
    assert "level1_metadata" in full_res["levels"]
    assert "level4_issuer_registry" in full_res["levels"]
    assert "advisory_disclaimer" in full_res
