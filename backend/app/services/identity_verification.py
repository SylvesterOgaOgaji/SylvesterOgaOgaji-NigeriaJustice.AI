"""
Identity Verification Service for NigeriaJustice.AI

This module provides functionality for verifying identities through 
Nigerian government databases including NIMC, Immigration Service,
INEC, and other authorized databases.
"""

import logging
import asyncio
from typing import Dict, Optional, List, Tuple
import json
import os
import secrets
import base64
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IdentityVerificationService:
    """
    Service for verifying identities through Nigerian government databases.
    
    This service provides secure API integrations with:
    - National Identity Management Commission (NIMC) for NIN verification
    - Nigerian Immigration Service for International Passport verification
    - Independent National Electoral Commission (INEC) for voter ID verification
    - Nigerian Correctional Service for inmate/offender records
    - Interpol for international criminal records
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the identity verification service.
        
        Args:
            config_path: Path to configuration file with API credentials
        """
        self.config_path = config_path
        self.api_credentials = {}
        self.verification_cache = {}  # Simple cache for development
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.api_credentials = json.load(f)
                logger.info(f"Loaded API credentials from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load API credentials: {e}")
        else:
            logger.warning("No API credentials provided. Using mock data for development.")
            
        # Initialize the verification database with mock data for development
        self._initialize_mock_data()
            
    def _initialize_mock_data(self):
        """Initialize mock data for development purposes."""
        # This would be replaced with actual API integrations in production
        self.mock_database = {
            "nin": {
                "12345678901": {
                    "id": "NIN12345678901",
                    "name": "Adewale Johnson",
                    "dob": "1980-05-15",
                    "gender": "Male",
                    "address": "123 Lagos Street, Lagos, Nigeria",
                    "photo": "base64_encoded_photo_data",
                    "fingerprint": "base64_encoded_fingerprint_data",
                    "status": "active"
                },
                "98765432109": {
                    "id": "NIN98765432109",
                    "name": "Chioma Okafor",
                    "dob": "1985-11-23",
                    "gender": "Female",
                    "address": "456 Abuja Road, Abuja, Nigeria",
                    "photo": "base64_encoded_photo_data",
                    "fingerprint": "base64_encoded_fingerprint_data",
                    "status": "active"
                }
            },
            "passport": {
                "A12345678": {
                    "id": "PASS-A12345678",
                    "name": "Mohammed Ibrahim",
                    "dob": "1975-08-30",
                    "gender": "Male",
                    "nationality": "Nigerian",
                    "issue_date": "2020-01-15",
                    "expiry_date": "2030-01-14",
                    "photo": "base64_encoded_photo_data",
                    "status": "active"
                },
                "B87654321": {
                    "id": "PASS-B87654321",
                    "name": "Ngozi Eze",
                    "dob": "1990-03-12",
                    "gender": "Female",
                    "nationality": "Nigerian",
                    "issue_date": "2019-07-20",
                    "expiry_date": "2029-07-19",
                    "photo": "base64_encoded_photo_data",
                    "status": "active"
                }
            },
            "inec": {
                "PVC12345678": {
                    "id": "PVC12345678",
                    "name": "Oluwaseun Adeleke",
                    "dob": "1982-12-05",
                    "gender": "Male",
                    "polling_unit": "LA/01/05/12",
                    "ward": "Ward 5",
                    "lga": "Lagos Island",
                    "state": "Lagos",
                    "registration_date": "2018-05-10",
                    "photo": "base64_encoded_photo_data",
                    "status": "active"
                }
            },
            "correctional": {
                "NCS12345": {
                    "id": "NCS12345",
                    "name": "Redacted Name",
                    "dob": "1988-04-22",
                    "gender": "Male",
                    "facility": "Kirikiri Maximum Security Prison",
                    "offense": "Redacted",
                    "sentence_start": "2021-02-15",
                    "sentence_end": "2026-02-14",
                    "status": "incarcerated"
                }
            },
            "interpol": {
                "IPN-NG-12345": {
                    "id": "IPN-NG-12345",
                    "name": "Redacted International",
                    "nationality": "Nigerian",
                    "status": "watchlist",
                    "notice_type": "Red Notice",
                    "issue_date": "2022-06-10"
                }
            },
            # Court officials for different roles
            "court_officials": {
                "JUD-FCT-001": {
                    "id": "JUD-FCT-001",
                    "name": "Hon. Justice Olufemi Adekoya",
                    "role": "judge",
                    "court": "Federal High Court, Abuja",
                    "nin": "11122233344",
                    "status": "active"
                },
                "PRO-FCT-001": {
                    "id": "PRO-FCT-001",
                    "name": "Barr. Amina Bello",
                    "role": "prosecutor",
                    "affiliation": "Federal Ministry of Justice",
                    "nin": "44455566677",
                    "status": "active"
                },
                "CLK-FCT-001": {
                    "id": "CLK-FCT-001",
                    "name": "Mr. Gabriel Okonkwo",
                    "role": "clerk",
                    "court": "Federal High Court, Abuja",
                    "nin": "77788899900",
                    "status": "active"
                }
            }
        }
        
        logger.info("Initialized mock verification database for development")
    
    async def verify_nin(self, nin: str, fingerprint_data: str = None) -> Tuple[bool, Dict]:
        """
        Verify a National Identification Number (NIN).
        
        Args:
            nin: The NIN to verify
            fingerprint_data: Optional fingerprint data for additional verification
            
        Returns:
            Tuple of (is_verified, person_data)
        """
        # Simulate API request delay
        await asyncio.sleep(0.5)
        
        logger.info(f"Verifying NIN: {nin[:4]}******")
        
        # In production, this would make an API call to NIMC
        # For development, check against mock database
        if nin in self.mock_database.get("nin", {}):
            person_data = self.mock_database["nin"][nin].copy()
            
            # Remove sensitive biometric data from the response
            if "fingerprint" in person_data:
                del person_data["fingerprint"]
                
            # Add verification metadata
            person_data.update({
                "verification_id": f"VERIF-{secrets.token_hex(6)}",
                "verification_timestamp": datetime.now().isoformat(),
                "verification_source": "NIMC"
            })
            
            # Cache the result
            self.verification_cache[nin] = {
                "data": person_data,
                "expires": datetime.now() + timedelta(hours=24)
            }
            
            return True, person_data
        else:
            logger.warning(f"NIN verification failed: {nin[:4]}******")
            return False, {"error": "NIN not found or invalid"}
    
    async def verify_passport(self, passport_number: str) -> Tuple[bool, Dict]:
        """
        Verify an International Passport.
        
        Args:
            passport_number: The passport number to verify
            
        Returns:
            Tuple of (is_verified, person_data)
        """
        # Simulate API request delay
        await asyncio.sleep(0.7)
        
        logger.info(f"Verifying passport: {passport_number[:2]}******")
        
        # In production, this would make an API call to Immigration Service
        # For development, check against mock database
        if passport_number in self.mock_database.get("passport", {}):
            person_data = self.mock_database["passport"][passport_number].copy()
            
            # Add verification metadata
            person_data.update({
                "verification_id": f"VERIF-{secrets.token_hex(6)}",
                "verification_timestamp": datetime.now().isoformat(),
                "verification_source": "Immigration"
            })
            
            # Check if passport is expired
            if "expiry_date" in person_data:
                expiry_date = datetime.fromisoformat(person_data["expiry_date"])
                if expiry_date < datetime.now():
                    logger.warning(f"Passport expired: {passport_number[:2]}******")
                    person_data["status"] = "expired"
                    return False, person_data
            
            # Cache the result
            self.verification_cache[passport_number] = {
                "data": person_data,
                "expires": datetime.now() + timedelta(hours=24)
            }
            
            return True, person_data
        else:
            logger.warning(f"Passport verification failed: {passport_number[:2]}******")
            return False, {"error": "Passport not found or invalid"}
    
    async def check_correctional_records(self, person_id: str, id_type: str) -> Tuple[bool, Dict]:
        """
        Check Nigerian Correctional Service records.
        
        Args:
            person_id: The ID (NIN, passport) of the person
            id_type: Type of ID ("nin", "passport")
            
        Returns:
            Tuple of (record_exists, record_data)
        """
        # Simulate API request delay
        await asyncio.sleep(0.6)
        
        logger.info(f"Checking correctional records for {id_type}: {person_id[:4]}******")
        
        # In production, this would make an API call to Correctional Service
        # For development, return mock data
        # We'll just check if the ID ends with "345" as an example
        if person_id.endswith("345"):
            record = {
                "record_exists": True,
                "record_id": f"NCS{secrets.token_hex(4)}",
                "status": "incarcerated",
                "facility": "Kirikiri Maximum Security Prison",
                "verification_timestamp": datetime.now().isoformat()
            }
            return True, record
        else:
            return False, {"record_exists": False}
    
    async def check_interpol_records(self, person_id: str, id_type: str) -> Tuple[bool, Dict]:
        """
        Check Interpol records.
        
        Args:
            person_id: The ID (NIN, passport) of the person
            id_type: Type of ID ("nin", "passport")
            
        Returns:
            Tuple of (record_exists, record_data)
        """
        # Simulate API request delay
        await asyncio.sleep(0.8)
        
        logger.info(f"Checking Interpol records for {id_type}: {person_id[:4]}******")
        
        # In production, this would make an API call to Interpol
        # For development, return mock data
        # We'll just check if the ID starts with "A" as an example
        if person_id.startswith("A"):
            record = {
                "record_exists": True,
                "notice_type": "Red Notice",
                "issue_date": "2022-06-10",
                "verification_timestamp": datetime.now().isoformat()
            }
            return True, record
        else:
            return False, {"record_exists": False}
    
    async def verify_court_official(self, official_id: str, role: str = None) -> Tuple[bool, Dict]:
        """
        Verify a court official's identity and role.
        
        Args:
            official_id: ID of the court official
            role: Expected role ("judge", "prosecutor", "clerk", etc.)
            
        Returns:
            Tuple of (is_verified, official_data)
        """
        # Simulate API request delay
        await asyncio.sleep(0.4)
        
        logger.info(f"Verifying court official: {official_id}")
        
        # For development, check against mock database
        officials_db = self.mock_database.get("court_officials", {})
        
        if official_id in officials_db:
            official_data = officials_db[official_id].copy()
            
            # If a specific role is expected, verify it
            if role and official_data.get("role") != role:
                logger.warning(f"Role mismatch for {official_id}: expected {role}, got {official_data.get('role')}")
                return False, {"error": f"Official is not authorized as {role}"}
            
            # Add verification metadata
            official_data.update({
                "verification_id": f"VERIF-{secrets.token_hex(6)}",
                "verification_timestamp": datetime.now().isoformat()
            })
            
            return True, official_data
        else:
            logger.warning(f"Court official verification failed: {official_id}")
            return False, {"error": "Court official not found or invalid"}
    
    async def comprehensive_verification(self, 
                                       identity_data: Dict) -> Dict:
        """
        Perform comprehensive identity verification across multiple sources.
        
        Args:
            identity_data: Dict containing identity information (NIN, passport, etc.)
            
        Returns:
            Dict with verification results from all available sources
        """
        results = {
            "verification_id": f"COMP-{secrets.token_hex(8)}",
            "timestamp": datetime.now().isoformat(),
            "verification_complete": False,
            "sources_checked": []
        }
        
        # Check NIN if provided
        if "nin" in identity_data:
            nin = identity_data.get("nin")
            fingerprint = identity_data.get("fingerprint")
            is_verified, nin_data = await self.verify_nin(nin, fingerprint)
            results["nin_verification"] = {
                "verified": is_verified,
                "data": nin_data
            }
            results["sources_checked"].append("NIMC")
            
            # If NIN verification successful, this becomes primary identity
            if is_verified:
                results["primary_verification"] = "nin"
                results["person_name"] = nin_data.get("name")
                results["verification_level"] = "strong"
        
        # Check passport if provided
        if "passport" in identity_data:
            passport = identity_data.get("passport")
            is_verified, passport_data = await self.verify_passport(passport)
            results["passport_verification"] = {
                "verified": is_verified,
                "data": passport_data
            }
            results["sources_checked"].append("Immigration")
            
            # If no NIN verification but passport is verified
            if is_verified and "primary_verification" not in results:
                results["primary_verification"] = "passport"
                results["person_name"] = passport_data.get("name")
                results["verification_level"] = "strong"
        
        # Check correctional records if we have verified identity
        if "primary_verification" in results:
            primary_id = identity_data.get(results["primary_verification"])
            has_record, record_data = await self.check_correctional_records(
                primary_id, results["primary_verification"])
            
            results["correctional_check"] = {
                "record_found": has_record,
                "data": record_data
            }
            results["sources_checked"].append("Correctional")
            
            # Also check Interpol records
            has_record, record_data = await self.check_interpol_records(
                primary_id, results["primary_verification"])
            
            results["interpol_check"] = {
                "record_found": has_record,
                "data": record_data
            }
            results["sources_checked"].append("Interpol")
        
        # Check if the person is a court official
        if "court_official_id" in identity_data:
            official_id = identity_data.get("court_official_id")
            expected_role = identity_data.get("expected_role")
            
            is_verified, official_data = await self.verify_court_official(
                official_id, expected_role)
            
            results["court_official_verification"] = {
                "verified": is_verified,
                "data": official_data
            }
            results["sources_checked"].append("Judiciary")
            
            if is_verified:
                results["is_court_official"] = True
                results["official_role"] = official_data.get("role")
                
                # If we also have primary identity verification, cross-check
                if "primary_verification" in results:
                    primary_name = results.get("person_name", "").lower()
                    official_name = official_data.get("name", "").lower()
                    
                    # Simple name similarity check (would be more sophisticated in production)
                    name_match = primary_name in official_name or official_name in primary_name
                    results["name_cross_check"] = name_match
        
        # Mark verification as complete
        results["verification_complete"] = True
        results["verification_timestamp"] = datetime.now().isoformat()
        
        return results
