"""
Warrant Transfer Service for NigeriaJustice.AI

This module provides functionality for creating, managing, and transferring
court warrants to Nigerian Correctional Services and other prosecuting agencies
in a secure and traceable manner.
"""

import logging
import os
import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import hashlib
import base64
import hmac
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

class WarrantTransferService:
    """
    Service for creating, managing, and transferring court warrants.
    
    This service enables secure generation and transfer of warrants to
    Nigerian Correctional Services and other prosecuting agencies with
    proper authentication, verification, and tracking.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the warrant transfer service.
        
        Args:
            storage_path: Path to store warrant data
        """
        self.storage_path = storage_path or os.path.join("data", "warrants")
        self.warrant_types = self._get_warrant_types()
        self.agencies = self._get_agencies()
        
        # Create warrant storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        logger.info("Warrant Transfer Service initialized")
    
    def _get_warrant_types(self) -> Dict[str, Dict]:
        """Get available warrant types with metadata"""
        # In production, this would be loaded from a database or configuration
        return {
            "arrest": {
                "id": "arrest",
                "name": "Warrant of Arrest",
                "description": "Authorizes the arrest of a person",
                "required_fields": ["subject_name", "subject_address", "offence", "issuing_court"],
                "validity_days": 90
            },
            "search": {
                "id": "search",
                "name": "Search Warrant",
                "description": "Authorizes the search of premises",
                "required_fields": ["premises_address", "items_to_search_for", "issuing_court"],
                "validity_days": 30
            },
            "remand": {
                "id": "remand",
                "name": "Remand Warrant",
                "description": "Orders the detention of a person in custody",
                "required_fields": ["subject_name", "detention_facility", "case_number", "issuing_court", "remand_period"],
                "validity_days": 14
            },
            "execution": {
                "id": "execution",
                "name": "Warrant of Execution",
                "description": "Orders the execution of a court judgment",
                "required_fields": ["subject_name", "case_number", "judgment_details", "issuing_court"],
                "validity_days": 365
            },
            "commitment": {
                "id": "commitment",
                "name": "Warrant of Commitment",
                "description": "Commits a convicted person to prison",
                "required_fields": ["subject_name", "correctional_facility", "sentence_details", "case_number", "issuing_court"],
                "validity_days": 365
            }
        }
    
    def _get_agencies(self) -> Dict[str, Dict]:
        """Get available agencies for warrant transfer"""
        # In production, this would be loaded from a database or configuration
        return {
            "ncs": {
                "id": "ncs",
                "name": "Nigerian Correctional Service",
                "description": "Federal agency responsible for prison administration",
                "api_endpoint": "https://api.corrections.gov.ng/warrants",
                "warrant_types": ["remand", "commitment", "execution"],
                "requires_encryption": True
            },
            "npf": {
                "id": "npf",
                "name": "Nigeria Police Force",
                "description": "Federal law enforcement agency",
                "api_endpoint": "https://api.npf.gov.ng/warrants",
                "warrant_types": ["arrest", "search"],
                "requires_encryption": True
            },
            "efcc": {
                "id": "efcc",
                "name": "Economic and Financial Crimes Commission",
                "description": "Agency investigating financial crimes",
                "api_endpoint": "https://api.efcc.gov.ng/warrants",
                "warrant_types": ["arrest", "search"],
                "requires_encryption": True
            },
            "icpc": {
                "id": "icpc",
                "name": "Independent Corrupt Practices Commission",
                "description": "Anti-corruption agency",
                "api_endpoint": "https://api.icpc.gov.ng/warrants",
                "warrant_types": ["arrest", "search"],
                "requires_encryption": True
            }
        }
    
    async def create_warrant(self, warrant_data: Dict, judge_info: Dict) -> Dict:
        """
        Create a new warrant.
        
        Args:
            warrant_data: Data for the warrant
            judge_info: Information about the issuing judge
            
        Returns:
            Created warrant with ID and metadata
        """
        logger.info(f"Creating new warrant of type: {warrant_data.get('warrant_type', 'unknown')}")
        
        # Validate warrant type
        warrant_type = warrant_data.get("warrant_type")
        if not warrant_type or warrant_type not in self.warrant_types:
            logger.error(f"Invalid warrant type: {warrant_type}")
            raise ValueError(f"Invalid warrant type: {warrant_type}")
        
        # Validate required fields
        required_fields = self.warrant_types[warrant_type].get("required_fields", [])
        for field in required_fields:
            if field not in warrant_data or not warrant_data[field]:
                logger.error(f"Missing required field for {warrant_type} warrant: {field}")
                raise ValueError(f"Missing required field for {warrant_type} warrant: {field}")
        
        # Generate warrant ID
        warrant_id = str(uuid.uuid4())
        
        # Calculate expiration date
        validity_days = self.warrant_types[warrant_type].get("validity_days", 30)
        issue_date = datetime.now()
        expiry_date = issue_date + timedelta(days=validity_days)
        
        # Create warrant document
        warrant = {
            "id": warrant_id,
            "type": warrant_type,
            "type_name": self.warrant_types[warrant_type].get("name"),
            "status": "issued",
            "issue_date": issue_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "issuing_judge": {
                "id": judge_info.get("id"),
                "name": judge_info.get("name"),
                "court": judge_info.get("court")
            },
            "data": warrant_data,
            "transfers": [],
            "verification_code": self._generate_verification_code(),
            "digital_signature": self._generate_digital_signature(warrant_data, judge_info)
        }
        
        # Save warrant to storage
        await self._save_warrant(warrant)
        
        logger.info(f"Created warrant with ID: {warrant_id}")
        return warrant
    
    def _generate_verification_code(self) -> str:
        """Generate a human-readable verification code for warrants"""
        # Generate a 6-character alphanumeric code
        code_bytes = os.urandom(3)  # 3 bytes = 6 hex characters
        code = base64.b32encode(code_bytes).decode('utf-8')[:6]
        return code
    
    def _generate_digital_signature(self, warrant_data: Dict, judge_info: Dict) -> str:
        """Generate a digital signature for the warrant"""
        # In a production system, this would use proper digital signatures
        # For now, we'll create a simple HMAC-based signature
        
        # Create a string representation of the warrant data
        data_string = json.dumps(warrant_data, sort_keys=True)
        judge_string = f"{judge_info.get('id')}:{judge_info.get('name')}:{judge_info.get('court')}"
        
        # Create HMAC signature using a secret key
        key = settings.SECRET_KEY.encode('utf-8')
        message = f"{data_string}:{judge_string}".encode('utf-8')
        signature = hmac.new(key, message, hashlib.sha256).hexdigest()
        
        return signature
    
    async def _save_warrant(self, warrant: Dict) -> None:
        """Save warrant to storage"""
        warrant_id = warrant.get("id")
        filename = os.path.join(self.storage_path, f"{warrant_id}.json")
        
        # Save as JSON file
        with open(filename, 'w') as f:
            json.dump(warrant, f, indent=2)
    
    async def get_warrant(self, warrant_id: str) -> Optional[Dict]:
        """
        Get a warrant by ID.
        
        Args:
            warrant_id: ID of the warrant
            
        Returns:
            Warrant data if found, None otherwise
        """
        logger.info(f"Retrieving warrant with ID: {warrant_id}")
        
        # Validate input
        if not warrant_id or not re.match(r'^[0-9a-f-]{36}, warrant_id):
            logger.error(f"Invalid warrant ID format: {warrant_id}")
            raise ValueError("Invalid warrant ID format")
        
        # Check if warrant exists
        filename = os.path.join(self.storage_path, f"{warrant_id}.json")
        if not os.path.exists(filename):
            logger.warning(f"Warrant not found: {warrant_id}")
            return None
        
        # Load warrant from file
        try:
            with open(filename, 'r') as f:
                warrant = json.load(f)
            
            logger.info(f"Successfully retrieved warrant: {warrant_id}")
            return warrant
        except Exception as e:
            logger.error(f"Error loading warrant {warrant_id}: {str(e)}")
            raise
    
    async def verify_warrant(self, warrant_id: str, verification_code: str) -> Tuple[bool, str]:
        """
        Verify a warrant's authenticity.
        
        Args:
            warrant_id: ID of the warrant
            verification_code: Verification code for the warrant
            
        Returns:
            Tuple of (is_valid, message)
        """
        logger.info(f"Verifying warrant: {warrant_id}")
        
        # Get the warrant
        warrant = await self.get_warrant(warrant_id)
        if not warrant:
            return False, "Warrant not found"
        
        # Check verification code
        if warrant.get("verification_code") != verification_code:
            logger.warning(f"Invalid verification code for warrant {warrant_id}")
            return False, "Invalid verification code"
        
        # Check if warrant is expired
        try:
            expiry_date = datetime.fromisoformat(warrant.get("expiry_date", ""))
            if expiry_date < datetime.now():
                logger.warning(f"Warrant {warrant_id} is expired")
                return False, "Warrant is expired"
        except (ValueError, TypeError):
            logger.error(f"Invalid expiry date format for warrant {warrant_id}")
            return False, "Invalid expiry date format"
        
        # Check if warrant is revoked
        if warrant.get("status") == "revoked":
            logger.warning(f"Warrant {warrant_id} is revoked")
            return False, "Warrant is revoked"
        
        logger.info(f"Warrant {warrant_id} is valid")
        return True, "Warrant is valid"
    
    async def transfer_warrant(self, warrant_id: str, agency_id: str, transfer_notes: str = None) -> Dict:
        """
        Transfer a warrant to a specified agency.
        
        Args:
            warrant_id: ID of the warrant
            agency_id: ID of the receiving agency
            transfer_notes: Optional notes about the transfer
            
        Returns:
            Updated warrant with transfer information
        """
        logger.info(f"Transferring warrant {warrant_id} to agency {agency_id}")
        
        # Validate agency
        if agency_id not in self.agencies:
            logger.error(f"Invalid agency ID: {agency_id}")
            raise ValueError(f"Invalid agency ID: {agency_id}")
        
        # Get the warrant
        warrant = await self.get_warrant(warrant_id)
        if not warrant:
            logger.error(f"Warrant not found: {warrant_id}")
            raise ValueError(f"Warrant not found: {warrant_id}")
        
        # Check if warrant type is supported by agency
        warrant_type = warrant.get("type")
        if warrant_type not in self.agencies[agency_id].get("warrant_types", []):
            logger.error(f"Agency {agency_id} does not support warrant type {warrant_type}")
            raise ValueError(f"Agency {agency_id} does not support warrant type {warrant_type}")
        
        # Create transfer record
        transfer = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "agency_id": agency_id,
            "agency_name": self.agencies[agency_id].get("name"),
            "status": "pending",
            "notes": transfer_notes
        }
        
        # Add transfer to warrant
        warrant["transfers"].append(transfer)
        
        # Update warrant status
        warrant["status"] = "transferred"
        
        # Save updated warrant
        await self._save_warrant(warrant)
        
        # In a production system, this would actually call the agency's API
        # For now, we'll simulate a successful transfer
        transfer_result = await self._simulate_agency_transfer(warrant, agency_id)
        
        # Update transfer status based on result
        warrant["transfers"][-1]["status"] = transfer_result.get("status", "failed")
        warrant["transfers"][-1]["response"] = transfer_result.get("message", "")
        
        # Save updated warrant again
        await self._save_warrant(warrant)
        
        logger.info(f"Completed transfer of warrant {warrant_id} to agency {agency_id}")
        return warrant
    
    async def _simulate_agency_transfer(self, warrant: Dict, agency_id: str) -> Dict:
        """Simulate transferring a warrant to an agency (for development)"""
        # In a production system, this would make an API call to the agency
        # For now, we'll return a successful result
        
        # Add a small delay to simulate network communication
        await asyncio.sleep(1)
        
        return {
            "status": "delivered",
            "message": f"Warrant successfully delivered to {self.agencies[agency_id].get('name')}",
            "timestamp": datetime.now().isoformat(),
            "reference_number": f"AGY-{agency_id.upper()}-{str(uuid.uuid4())[:8]}"
        }
    
    async def revoke_warrant(self, warrant_id: str, judge_info: Dict, reason: str) -> Dict:
        """
        Revoke a warrant.
        
        Args:
            warrant_id: ID of the warrant
            judge_info: Information about the revoking judge
            reason: Reason for revocation
            
        Returns:
            Updated warrant
        """
        logger.info(f"Revoking warrant: {warrant_id}")
        
        # Get the warrant
        warrant = await self.get_warrant(warrant_id)
        if not warrant:
            logger.error(f"Warrant not found: {warrant_id}")
            raise ValueError(f"Warrant not found: {warrant_id}")
        
        # Create revocation record
        revocation = {
            "timestamp": datetime.now().isoformat(),
            "judge_id": judge_info.get("id"),
            "judge_name": judge_info.get("name"),
            "judge_court": judge_info.get("court"),
            "reason": reason
        }
        
        # Update warrant
        warrant["status"] = "revoked"
        warrant["revocation"] = revocation
        
        # Save updated warrant
        await self._save_warrant(warrant)
        
        # If the warrant has been transferred, notify the agencies
        if warrant.get("transfers"):
            for transfer in warrant.get("transfers", []):
                agency_id = transfer.get("agency_id")
                if agency_id and transfer.get("status") == "delivered":
                    await self._notify_agency_of_revocation(warrant, agency_id)
        
        logger.info(f"Successfully revoked warrant: {warrant_id}")
        return warrant
    
    async def _notify_agency_of_revocation(self, warrant: Dict, agency_id: str) -> None:
        """Notify an agency that a warrant has been revoked"""
        # In a production system, this would make an API call to the agency
        # For now, we'll just log the notification
        logger.info(f"Notifying agency {agency_id} of revocation of warrant {warrant.get('id')}")
    
    async def get_agency_list(self) -> List[Dict]:
        """
        Get a list of available agencies for warrant transfer.
        
        Returns:
            List of agencies with metadata
        """
        # Convert dictionary to list and return
        return [
            {
                "id": agency_id,
                "name": agency.get("name"),
                "description": agency.get("description"),
                "warrant_types": agency.get("warrant_types", [])
            }
            for agency_id, agency in self.agencies.items()
        ]
    
    async def get_warrant_types(self) -> List[Dict]:
        """
        Get a list of available warrant types.
        
        Returns:
            List of warrant types with metadata
        """
        # Convert dictionary to list and return
        return [
            {
                "id": type_id,
                "name": warrant_type.get("name"),
                "description": warrant_type.get("description"),
                "required_fields": warrant_type.get("required_fields", []),
                "validity_days": warrant_type.get("validity_days")
            }
            for type_id, warrant_type in self.warrant_types.items()
        ]
    
    async def search_warrants(self, search_params: Dict) -> List[Dict]:
        """
        Search for warrants based on parameters.
        
        Args:
            search_params: Search parameters
            
        Returns:
            List of matching warrants
        """
        logger.info(f"Searching warrants with params: {search_params}")
        
        # Get all warrant files
        warrant_files = [f for f in os.listdir(self.storage_path) if f.endswith('.json')]
        
        # Load all warrants
        warrants = []
        for filename in warrant_files:
            try:
                with open(os.path.join(self.storage_path, filename), 'r') as f:
                    warrant = json.load(f)
                warrants.append(warrant)
            except Exception as e:
                logger.error(f"Error loading warrant file {filename}: {str(e)}")
        
        # Filter warrants based on search parameters
        filtered_warrants = warrants
        
        # Filter by status
        if "status" in search_params:
            filtered_warrants = [w for w in filtered_warrants if w.get("status") == search_params["status"]]
        
        # Filter by type
        if "type" in search_params:
            filtered_warrants = [w for w in filtered_warrants if w.get("type") == search_params["type"]]
        
        # Filter by issuing judge
        if "judge_id" in search_params:
            filtered_warrants = [w for w in filtered_warrants if w.get("issuing_judge", {}).get("id") == search_params["judge_id"]]
        
        # Filter by subject name (case insensitive partial match)
        if "subject_name" in search_params:
            subject_name = search_params["subject_name"].lower()
            filtered_warrants = [
                w for w in filtered_warrants 
                if subject_name in w.get("data", {}).get("subject_name", "").lower()
            ]
        
        # Filter by case number
        if "case_number" in search_params:
            filtered_warrants = [
                w for w in filtered_warrants 
                if search_params["case_number"] == w.get("data", {}).get("case_number")
            ]
        
        # Filter by date range (issue date)
        if "date_from" in search_params:
            try:
                date_from = datetime.fromisoformat(search_params["date_from"])
                filtered_warrants = [
                    w for w in filtered_warrants 
                    if datetime.fromisoformat(w.get("issue_date", "")) >= date_from
                ]
            except ValueError:
                logger.warning(f"Invalid date_from format: {search_params['date_from']}")
        
        if "date_to" in search_params:
            try:
                date_to = datetime.fromisoformat(search_params["date_to"])
                filtered_warrants = [
                    w for w in filtered_warrants 
                    if datetime.fromisoformat(w.get("issue_date", "")) <= date_to
                ]
            except ValueError:
                logger.warning(f"Invalid date_to format: {search_params['date_to']}")
        
        # Sort results (default: newest first)
        sort_by = search_params.get("sort_by", "issue_date")
        sort_order = search_params.get("sort_order", "desc")
        
        if sort_by == "issue_date":
            filtered_warrants.sort(
                key=lambda w: w.get("issue_date", ""), 
                reverse=(sort_order == "desc")
            )
        elif sort_by == "expiry_date":
            filtered_warrants.sort(
                key=lambda w: w.get("expiry_date", ""), 
                reverse=(sort_order == "desc")
            )
        
        logger.info(f"Found {len(filtered_warrants)} matching warrants")
        return filtered_warrants
