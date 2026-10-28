"""
Data Extraction Module.

Extracts structured fields from OCR text based on document type,
using regex patterns for dates, IDs, names, amounts, and other fields.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime


class DataExtractor:
    """Extracts structured data fields from document OCR text."""

    def __init__(self) -> None:
        """Initialize the data extractor with common regex patterns."""
        self._date_patterns = [
            # DD/MM/YYYY or DD-MM-YYYY
            r"\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})\b",
            # YYYY-MM-DD (ISO)
            r"\b(\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b",
            # Month DD, YYYY (e.g., January 15, 2024)
            r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b",
            # DD Month YYYY (e.g., 15 January 2024)
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
            # Abbreviated months
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})\b",
        ]

        self._aicte_id_patterns = [
            r"\b(\d{1,2}-\d{7,10})\b",
            r"(?:AICTE|aicte)\s*(?:ID|Id|id|No\.?|Number)?\s*:?\s*(\w{1,5}-?\d{5,12})",
            r"(?:F\.?\s*No\.?|File\s*No\.?)\s*:?\s*([\w\-/]+\d{4,})",
            r"(?:Application\s*(?:ID|No\.?))\s*:?\s*(\w+-\d{4,})",
        ]

        self._email_pattern = r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
        self._phone_pattern = r"\b(?:\+91[\-\s]?)?(?:0)?[6-9]\d{9}\b"
        self._pincode_pattern = r"\b[1-9]\d{5}\b"
        self._amount_pattern = r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)\s*(?:lakh|lac|crore|cr)?"

    def extract_fields(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        Extract relevant fields from document text based on document type.

        Args:
            text: OCR-extracted text from the document.
            doc_type: Type of the document (e.g., AFFIDAVIT, NOC, etc.).

        Returns:
            Dictionary containing extracted field values.
        """
        common_fields = {
            "dates": self._extract_dates(text),
            "aicte_id": self._extract_aicte_id(text),
            "institution_name": self._extract_institution_name(text),
            "emails": self._extract_email_addresses(text),
            "phone_numbers": self._extract_phone_numbers(text),
            "pincode": self._extract_pincode(text),
            "amounts": self._extract_amounts(text),
            "names": self._extract_names(text),
            "reference_numbers": self._extract_reference_numbers(text),
        }

        # Add type-specific fields
        type_extractors = {
            "FACULTY_LIST": lambda: {"faculty_data": self._extract_faculty_data(text)},
            "EOA_CERTIFICATE": lambda: {
                "programme_data": self._extract_programme_data(text),
                "academic_year": self._extract_academic_year(text),
            },
            "FINANCIAL_STATEMENT": lambda: {
                "financial_figures": self._extract_amounts(text),
            },
            "LAND_DOCUMENT": lambda: {
                "area_details": self._extract_area_details(text),
            },
            "ACCREDITATION_CERT": lambda: {
                "accreditation_details": self._extract_accreditation_details(text),
            },
        }

        extractor = type_extractors.get(doc_type)
        if extractor:
            common_fields.update(extractor())

        return common_fields

    def _extract_dates(self, text: str) -> List[str]:
        """
        Find all dates in the text using multiple format patterns.

        Args:
            text: Input text to search.

        Returns:
            List of date strings found in the text.
        """
        dates = []
        for pattern in self._date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)

        # Deduplicate while preserving order
        seen = set()
        unique_dates = []
        for d in dates:
            d_norm = d.strip()
            if d_norm not in seen:
                seen.add(d_norm)
                unique_dates.append(d_norm)

        return unique_dates

    def _extract_aicte_id(self, text: str) -> Optional[str]:
        """
        Extract AICTE ID or file number from text.

        Args:
            text: Input text to search.

        Returns:
            AICTE ID string if found, else None.
        """
        for pattern in self._aicte_id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_institution_name(self, text: str) -> Optional[str]:
        """
        Extract institution name from text by looking for common patterns.

        Args:
            text: Input text to search.

        Returns:
            Institution name if found, else None.
        """
        patterns = [
            r"(?:Name of (?:the )?(?:Institution|College|Institute|University))\s*:?\s*(.+?)(?:\n|$)",
            r"(?:Institution|College|Institute)\s*Name\s*:?\s*(.+?)(?:\n|$)",
            r"(?:This is to certify that)\s+(.+?)(?:\s+is|\s+has|\s*,)",
            r"(?:M/s\.?|Shri|Sri)\s+(.+?(?:College|Institute|University|School).+?)(?:\n|,|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up common artifacts
                name = re.sub(r"\s+", " ", name).strip(" ,.:;")
                if len(name) > 5:  # Filter out very short matches
                    return name
        return None

    def _extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """
        Find monetary amounts in the text.

        Args:
            text: Input text to search.

        Returns:
            List of dicts with 'amount', 'currency', and 'context' keys.
        """
        amounts = []
        full_pattern = r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)\s*(lakh|lac|crore|cr|thousand)?"

        for match in re.finditer(full_pattern, text, re.IGNORECASE):
            raw_amount = match.group(1).replace(",", "")
            multiplier_word = match.group(2)

            try:
                amount = float(raw_amount)
            except ValueError:
                continue

            multiplier = 1
            if multiplier_word:
                word = multiplier_word.lower()
                if word in ("lakh", "lac"):
                    multiplier = 100000
                elif word in ("crore", "cr"):
                    multiplier = 10000000
                elif word == "thousand":
                    multiplier = 1000

            # Get surrounding context
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].strip()

            amounts.append({
                "amount": amount * multiplier,
                "raw": match.group(0),
                "multiplier": multiplier_word or "",
                "currency": "INR",
                "context": context,
            })

        return amounts

    def _extract_names(self, text: str) -> List[str]:
        """
        Extract person names from text near common label keywords.

        Args:
            text: Input text to search.

        Returns:
            List of extracted name strings.
        """
        name_patterns = [
            r"(?:Name|Signed by|Authorized by|Principal|Director|Chairman|Secretary|Deponent)\s*:?\s*([A-Z][a-zA-Z\s\.]{3,40})",
            r"(?:Shri|Smt|Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+([A-Z][a-zA-Z\s\.]{3,40})",
        ]

        names = []
        seen = set()
        for pattern in name_patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1).strip()
                name = re.sub(r"\s+", " ", name).strip(" ,.:;")
                if name and name not in seen and len(name) > 3:
                    seen.add(name)
                    names.append(name)

        return names

    def _extract_phone_numbers(self, text: str) -> List[str]:
        """
        Extract Indian phone numbers from text.

        Args:
            text: Input text to search.

        Returns:
            List of phone number strings.
        """
        matches = re.findall(self._phone_pattern, text)
        return list(set(matches))

    def _extract_email_addresses(self, text: str) -> List[str]:
        """
        Extract email addresses from text.

        Args:
            text: Input text to search.

        Returns:
            List of email address strings.
        """
        matches = re.findall(self._email_pattern, text)
        return list(set(matches))

    def _extract_pincode(self, text: str) -> Optional[str]:
        """
        Extract an Indian postal pincode from text.

        Args:
            text: Input text to search.

        Returns:
            First pincode found, or None.
        """
        # Look specifically near address context
        context_pattern = r"(?:Pin\s*(?:Code)?|Postal\s*Code|ZIP)\s*:?\s*(\d{6})"
        match = re.search(context_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

        # Fallback: find any 6-digit number that looks like a pincode
        matches = re.findall(self._pincode_pattern, text)
        for m in matches:
            # Indian pincodes start with 1-9
            if m[0] != "0":
                return m
        return None

    def _extract_faculty_data(self, text: str) -> List[Dict[str, str]]:
        """
        Extract faculty information from a faculty list document.

        Args:
            text: OCR text from a faculty list.

        Returns:
            List of dicts with name, designation, qualification, department keys.
        """
        faculty = []

        # Try to find tabular data patterns
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue

            # Look for lines containing faculty info indicators
            if any(kw in line.lower() for kw in ["professor", "lecturer", "hod", "dr.", "prof."]):
                # Try to split into components
                parts = re.split(r"\s{2,}|\t+|\|", line)
                parts = [p.strip() for p in parts if p.strip()]

                if len(parts) >= 2:
                    entry = {"name": parts[0]}
                    if len(parts) >= 2:
                        entry["designation"] = parts[1]
                    if len(parts) >= 3:
                        entry["qualification"] = parts[2]
                    if len(parts) >= 4:
                        entry["department"] = parts[3]
                    faculty.append(entry)

        return faculty

    def _extract_programme_data(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract programme/course information from EOA or approval documents.

        Args:
            text: OCR text from an approval document.

        Returns:
            List of dicts with programme_name, level, intake keys.
        """
        programmes = []

        # Common engineering programme names
        prog_patterns = [
            r"(B\.?\s*(?:Tech|E)|M\.?\s*(?:Tech|E)|MBA|MCA|B\.?\s*Arch|B\.?\s*Pharm)",
            r"(Computer\s*Science|Mechanical|Civil|Electrical|Electronics|Information\s*Technology)",
        ]

        # Try to find intake numbers near programme names
        intake_pattern = r"(\d{2,3})\s*(?:seats|intake|students)"

        for pattern in prog_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                prog_name = match.group(1).strip()

                # Look for intake number nearby
                nearby_text = text[match.start():min(match.end() + 100, len(text))]
                intake_match = re.search(intake_pattern, nearby_text, re.IGNORECASE)

                programmes.append({
                    "programme_name": prog_name,
                    "level": "UG" if any(x in prog_name.upper() for x in ["B.", "B.TECH", "BE", "BARCH"]) else "PG",
                    "intake": int(intake_match.group(1)) if intake_match else None,
                })

        return programmes

    def _extract_reference_numbers(self, text: str) -> List[str]:
        """
        Extract reference numbers, file numbers, and registration numbers.

        Args:
            text: Input text to search.

        Returns:
            List of reference number strings.
        """
        patterns = [
            r"(?:Ref\.?\s*(?:No\.?)?|Reference\s*(?:No\.?)?)\s*:?\s*([\w\-/]+)",
            r"(?:Regd\.?\s*No\.?|Registration\s*No\.?)\s*:?\s*([\w\-/]+)",
            r"(?:Certificate\s*No\.?)\s*:?\s*([\w\-/]+)",
            r"(?:File\s*No\.?|F\.?\s*No\.?)\s*:?\s*([\w\-/]+)",
        ]

        refs = []
        seen = set()
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                ref = match.group(1).strip()
                if ref and ref not in seen and len(ref) > 2:
                    seen.add(ref)
                    refs.append(ref)

        return refs

    def _extract_academic_year(self, text: str) -> Optional[str]:
        """
        Extract academic year (e.g., '2024-25' or '2024-2025') from text.

        Args:
            text: Input text to search.

        Returns:
            Academic year string if found, else None.
        """
        patterns = [
            r"(?:Academic\s*Year|A\.?\s*Y\.?|Session)\s*:?\s*(\d{4}\s*[-–]\s*\d{2,4})",
            r"\b(20\d{2}\s*[-–]\s*\d{2,4})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_area_details(self, text: str) -> Dict[str, Any]:
        """
        Extract land and built-up area details from land/building documents.

        Args:
            text: Input text to search.

        Returns:
            Dictionary with land_area, built_up_area, and their units.
        """
        result = {}

        area_patterns = [
            (r"(?:land\s*area|total\s*(?:land\s*)?area)\s*:?\s*([\d,.]+)\s*(acres?|hectares?|sq\.?\s*(?:ft|feet|m|meters?|yards?))", "land_area"),
            (r"(?:built[\s-]*up\s*area|carpet\s*area|constructed\s*area)\s*:?\s*([\d,.]+)\s*(sq\.?\s*(?:ft|feet|m|meters?))", "built_up_area"),
            (r"(?:plinth\s*area)\s*:?\s*([\d,.]+)\s*(sq\.?\s*(?:ft|feet|m|meters?))", "plinth_area"),
        ]

        for pattern, key in area_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result[key] = {
                    "value": float(match.group(1).replace(",", "")),
                    "unit": match.group(2).strip(),
                }

        return result

    def _extract_accreditation_details(self, text: str) -> Dict[str, Any]:
        """
        Extract accreditation-specific details.

        Args:
            text: Input text to search.

        Returns:
            Dictionary with accreditation body, grade, validity, etc.
        """
        result = {}

        # Accreditation body
        if re.search(r"\bNBA\b", text):
            result["body"] = "NBA"
        elif re.search(r"\bNAAC\b", text):
            result["body"] = "NAAC"

        # Grade
        grade_match = re.search(r"(?:Grade|Rating)\s*:?\s*([A-Z][+\-]?(?:\+\+)?)", text, re.IGNORECASE)
        if grade_match:
            result["grade"] = grade_match.group(1)

        # CGPA
        cgpa_match = re.search(r"(?:CGPA|Score)\s*:?\s*([\d.]+)", text, re.IGNORECASE)
        if cgpa_match:
            result["cgpa"] = float(cgpa_match.group(1))

        # Validity
        validity_match = re.search(r"(?:Valid\s*(?:up\s*to|till|until))\s*:?\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
        if validity_match:
            result["valid_until"] = validity_match.group(1).strip()

        return result
