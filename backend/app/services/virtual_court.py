"""
Virtual Court Service for NigeriaJustice.AI

This module provides functionality for managing virtual court sessions,
allowing remote participation in court proceedings with secure identity
verification.
"""

import logging
import os
import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import random
import string
import asyncio

from app.core.config import settings
from app.services.identity_verification import IdentityVerificationService

logger = logging.getLogger(__name__)

class VirtualCourtService:
    """
    Service for managing virtual court sessions.
    
    This service enables the creation, management, and execution of
    virtual court sessions with secure identity verification.
    """
    
    def __init__(self, storage_path: str = None, identity_service: Optional[IdentityVerificationService] = None):
        """
        Initialize the virtual court service.
        
        Args:
            storage_path: Path to store session data
            identity_service: Identity verification service instance
        """
        self.storage_path = storage_path or os.path.join("data", "virtual_sessions")
        self.identity_service = identity_service or IdentityVerificationService()
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        logger.info("Virtual Court Service initialized")
    
    async def create_session(self, session_data: Dict, judge_info: Dict) -> Dict:
        """
        Create a new virtual court session.
        
        Args:
            session_data: Data for the session
            judge_info: Information about the presiding judge
            
        Returns:
            Created session with ID and access codes
        """
        logger.info(f"Creating new virtual court session for case {session_data.get('case_number', 'unknown')}")
        
        # Validate required fields
        required_fields = ["case_number", "case_title", "scheduled_date", "scheduled_time"]
        for field in required_fields:
            if field not in session_data or not session_data[field]:
                logger.error(f"Missing required field for virtual session: {field}")
                raise ValueError(f"Missing required field for virtual session: {field}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Generate access codes for different roles
        access_codes = self._generate_access_codes()
        
        # Create session document
        session = {
            "id": session_id,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "case": {
                "number": session_data.get("case_number"),
                "title": session_data.get("case_title"),
                "type": session_data.get("case_type")
            },
            "schedule": {
                "date": session_data.get("scheduled_date"),
                "time": session_data.get("scheduled_time"),
                "duration_minutes": session_data.get("duration_minutes", 60)
            },
            "presiding_judge": {
                "id": judge_info.get("id"),
                "name": judge_info.get("name"),
                "court": judge_info.get("court")
            },
            "participants": session_data.get("participants", []),
            "access_codes": access_codes,
            "recording": {
                "enabled": session_data.get("recording_enabled", True),
                "auto_transcription": session_data.get("auto_transcription", True)
            },
            "documents": session_data.get("documents", []),
            "events": [],
            "metadata": {
                "court_room": session_data.get("court_room"),
                "jurisdiction": session_data.get("jurisdiction"),
                "public_access": session_data.get("public_access", False)
            }
        }
        
        # Save session to storage
        await self._save_session(session)
        
        logger.info(f"Created virtual court session with ID: {session_id}")
        return session
    
    def _generate_access_codes(self) -> Dict[str, str]:
        """Generate secure access codes for virtual court roles"""
        
        # Generate random 8-character alphanumeric codes
        def generate_code():
            chars = string.ascii_uppercase + string.digits
            return ''.join(random.choice(chars) for _ in range(8))
        
        # Create codes for different roles
        return {
            "judge": generate_code(),
            "prosecutor": generate_code(),
            "defense": generate_code(),
            "witness": generate_code(),
            "clerk": generate_code(),
            "public": generate_code() if settings.COURT_CONFIG.get("allow_public_access", False) else None
        }
    
    async def _save_session(self, session: Dict) -> None:
        """Save session to storage"""
        session_id = session.get("id")
        filename = os.path.join(self.storage_path, f"{session_id}.json")
        
        # Save as JSON file
        with open(filename, 'w') as f:
            json.dump(session, f, indent=2)
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get a virtual court session by ID.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session data if found, None otherwise
        """
        logger.info(f"Retrieving virtual court session with ID: {session_id}")
        
        # Check if session exists
        filename = os.path.join(self.storage_path, f"{session_id}.json")
        if not os.path.exists(filename):
            logger.warning(f"Session not found: {session_id}")
            return None
        
        # Load session from file
        try:
            with open(filename, 'r') as f:
                session = json.load(f)
            
            logger.info(f"Successfully retrieved session: {session_id}")
            return session
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, update_data: Dict) -> Dict:
        """
        Update a virtual court session.
        
        Args:
            session_id: ID of the session
            update_data: Data to update
            
        Returns:
            Updated session
        """
        logger.info(f"Updating virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Update session fields
        if "status" in update_data:
            session["status"] = update_data["status"]
        
        if "schedule" in update_data:
            for key, value in update_data["schedule"].items():
                session["schedule"][key] = value
        
        if "participants" in update_data:
            session["participants"] = update_data["participants"]
        
        if "documents" in update_data:
            session["documents"] = update_data["documents"]
        
        if "metadata" in update_data:
            for key, value in update_data["metadata"].items():
                session["metadata"][key] = value
        
        # Add update event
        session["events"].append({
            "type": "update",
            "timestamp": datetime.now().isoformat(),
            "details": "Session updated"
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully updated session: {session_id}")
        return session
    
    async def start_session(self, session_id: str, judge_info: Dict) -> Dict:
        """
        Start a virtual court session.
        
        Args:
            session_id: ID of the session
            judge_info: Information about the presiding judge
            
        Returns:
            Updated session
        """
        logger.info(f"Starting virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if judge is authorized
        if judge_info.get("id") != session["presiding_judge"].get("id"):
            logger.error(f"Unauthorized judge attempt to start session: {session_id}")
            raise ValueError("Only the presiding judge can start this session")
        
        # Check if session is in the right state
        if session["status"] not in ["scheduled", "postponed"]:
            logger.error(f"Cannot start session in current state: {session['status']}")
            raise ValueError(f"Cannot start session in current state: {session['status']}")
        
        # Update session state
        session["status"] = "in_progress"
        session["events"].append({
            "type": "start",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": judge_info.get("name"),
            "details": "Session started"
        })
        
        # For recording sessions, initialize recording data
        if session["recording"]["enabled"]:
            session["recording"]["started_at"] = datetime.now().isoformat()
            session["recording"]["segments"] = []
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully started session: {session_id}")
        return session
    
    async def end_session(self, session_id: str, judge_info: Dict, outcome: Optional[str] = None) -> Dict:
        """
        End a virtual court session.
        
        Args:
            session_id: ID of the session
            judge_info: Information about the presiding judge
            outcome: Optional outcome of the session
            
        Returns:
            Updated session
        """
        logger.info(f"Ending virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if judge is authorized
        if judge_info.get("id") != session["presiding_judge"].get("id"):
            logger.error(f"Unauthorized judge attempt to end session: {session_id}")
            raise ValueError("Only the presiding judge can end this session")
        
        # Check if session is in progress
        if session["status"] != "in_progress":
            logger.error(f"Cannot end session in current state: {session['status']}")
            raise ValueError(f"Cannot end session in current state: {session['status']}")
        
        # Update session state
        session["status"] = "completed"
        session["events"].append({
            "type": "end",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": judge_info.get("name"),
            "details": outcome or "Session ended"
        })
        
        # For recording sessions, finalize recording data
        if session["recording"]["enabled"] and "started_at" in session["recording"]:
            session["recording"]["ended_at"] = datetime.now().isoformat()
            
            # Calculate duration
            try:
                start_time = datetime.fromisoformat(session["recording"]["started_at"])
                end_time = datetime.fromisoformat(session["recording"]["ended_at"])
                duration_seconds = (end_time - start_time).total_seconds()
                session["recording"]["duration_seconds"] = duration_seconds
            except (ValueError, TypeError):
                logger.warning(f"Could not calculate recording duration for session {session_id}")
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully ended session: {session_id}")
        return session
    
    async def join_session(self, session_id: str, participant_data: Dict) -> Dict:
        """
        Join a virtual court session.
        
        Args:
            session_id: ID of the session
            participant_data: Data about the participant
            
        Returns:
            Session access information
        """
        logger.info(f"Participant joining virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if session is joinable
        if session["status"] not in ["scheduled", "in_progress"]:
            logger.error(f"Cannot join session in current state: {session['status']}")
            raise ValueError(f"Cannot join session in current state: {session['status']}")
        
        # Verify access code
        role = participant_data.get("role", "").lower()
        provided_code = participant_data.get("access_code")
        
        if role not in session["access_codes"] or not provided_code:
            logger.error(f"Invalid role or missing access code: {role}")
            raise ValueError("Invalid role or missing access code")
        
        if provided_code != session["access_codes"][role]:
            logger.error(f"Invalid access code for role {role}")
            raise ValueError("Invalid access code")
        
        # Check identity verification if required
        if role in ["judge", "prosecutor", "defense"] and settings.COURT_CONFIG.get("require_identity_verification", True):
            # Verify identity
            identity_verified = await self._verify_participant_identity(participant_data)
            if not identity_verified:
                logger.error(f"Identity verification failed for participant in role: {role}")
                raise ValueError("Identity verification failed")
        
        # Generate join token (would be a JWT in production)
        join_token = str(uuid.uuid4())
        
        # Add participant to session
        participant_entry = {
            "id": participant_data.get("id", str(uuid.uuid4())),
            "name": participant_data.get("name"),
            "role": role,
            "joined_at": datetime.now().isoformat()
        }
        
        # Update participants list if not already present
        participant_exists = False
        for i, p in enumerate(session["participants"]):
            if p.get("id") == participant_entry["id"]:
                session["participants"][i] = {**p, **participant_entry}
                participant_exists = True
                break
        
        if not participant_exists:
            session["participants"].append(participant_entry)
        
        # Add join event
        session["events"].append({
            "type": "join",
            "timestamp": datetime.now().isoformat(),
            "participant": {
                "id": participant_entry["id"],
                "name": participant_entry["name"],
                "role": participant_entry["role"]
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Participant {participant_entry['name']} joined session {session_id} as {role}")
        
        # Return access information
        return {
            "session_id": session_id,
            "case_title": session["case"]["title"],
            "access_token": join_token,
            "participant_id": participant_entry["id"],
            "role": role,
            "status": session["status"],
            "session_details": {
                "presiding_judge": session["presiding_judge"]["name"],
                "scheduled_time": f"{session['schedule']['date']} {session['schedule']['time']}",
                "participants_count": len(session["participants"])
            }
        }
    
    async def _verify_participant_identity(self, participant_data: Dict) -> bool:
        """Verify the identity of a participant"""
        # In production, this would use the identity verification service
        # For now, check if the required identity info is provided
        
        if not participant_data.get("identity"):
            logger.warning("No identity data provided for verification")
            return False
        
        identity_data = participant_data["identity"]
        
        # Check for NIN or passport
        if "nin" in identity_data:
            # Verify NIN using identity service
            is_verified, _ = await self.identity_service.verify_nin(identity_data["nin"])
            return is_verified
        elif "passport" in identity_data:
            # Verify passport using identity service
            is_verified, _ = await self.identity_service.verify_passport(identity_data["passport"])
            return is_verified
        elif "court_official_id" in identity_data:
            # Verify court official using identity service
            is_verified, _ = await self.identity_service.verify_court_official(
                identity_data["court_official_id"], 
                identity_data.get("expected_role")
            )
            return is_verified
        else:
            logger.warning("No recognized identity credential provided")
            return False
    
    async def leave_session(self, session_id: str, participant_id: str) -> Dict:
        """
        Leave a virtual court session.
        
        Args:
            session_id: ID of the session
            participant_id: ID of the participant
            
        Returns:
            Updated session
        """
        logger.info(f"Participant leaving virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Find participant
        participant = None
        for p in session["participants"]:
            if p.get("id") == participant_id:
                participant = p
                break
        
        if not participant:
            logger.error(f"Participant not found in session: {participant_id}")
            raise ValueError("Participant not found in session")
        
        # Update participant status
        participant["left_at"] = datetime.now().isoformat()
        
        # Add leave event
        session["events"].append({
            "type": "leave",
            "timestamp": datetime.now().isoformat(),
            "participant": {
                "id": participant["id"],
                "name": participant["name"],
                "role": participant["role"]
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Participant {participant['name']} left session {session_id}")
        return session
    
    async def add_document(self, session_id: str, document_data: Dict, uploaded_by: Dict) -> Dict:
        """
        Add a document to a virtual court session.
        
        Args:
            session_id: ID of the session
            document_data: Data about the document
            uploaded_by: Information about who uploaded the document
            
        Returns:
            Updated session
        """
        logger.info(f"Adding document to virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Create document entry
        document = {
            "id": str(uuid.uuid4()),
            "name": document_data.get("name"),
            "type": document_data.get("type"),
            "path": document_data.get("path"),
            "size_bytes": document_data.get("size_bytes"),
            "uploaded_at": datetime.now().isoformat(),
            "uploaded_by": {
                "id": uploaded_by.get("id"),
                "name": uploaded_by.get("name"),
                "role": uploaded_by.get("role")
            },
            "visibility": document_data.get("visibility", "all"),
            "metadata": document_data.get("metadata", {})
        }
        
        # Add document to session
        if "documents" not in session:
            session["documents"] = []
        
        session["documents"].append(document)
        
        # Add document event
        session["events"].append({
            "type": "document_added",
            "timestamp": datetime.now().isoformat(),
            "document": {
                "id": document["id"],
                "name": document["name"]
            },
            "uploaded_by": {
                "id": uploaded_by.get("id"),
                "name": uploaded_by.get("name"),
                "role": uploaded_by.get("role")
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Added document {document['name']} to session {session_id}")
        return session
    
    async def search_sessions(self, search_params: Dict) -> List[Dict]:
        """
        Search for virtual court sessions based on parameters.
        
        Args:
            search_params: Search parameters
            
        Returns:
            List of matching sessions
        """
        logger.info(f"Searching virtual court sessions with params: {search_params}")
        
        # Get all session files
        session_files = [f for f in os.listdir(self.storage_path) if f.endswith('.json')]
        
        # Load all sessions
        sessions = []
        for filename in session_files:
            try:
                with open(os.path.join(self.storage_path, filename), 'r') as f:
                    session = json.load(f)
                sessions.append(session)
            except Exception as e:
                logger.error(f"Error loading session file {filename}: {str(e)}")
        
        # Filter sessions based on search parameters
        filtered_sessions = sessions
        
        # Filter by status
        if "status" in search_params:
            filtered_sessions = [s for s in filtered_sessions if s.get("status") == search_params["status"]]
        
        # Filter by case number
        if "case_number" in search_params:
            filtered_sessions = [
                s for s in filtered_sessions 
                if s.get("case", {}).get("number") == search_params["case_number"]
            ]
        
        # Filter by judge
        if "judge_id" in search_params:
            filtered_sessions = [
                s for s in filtered_sessions 
                if s.get("presiding_judge", {}).get("id") == search_params["judge_id"]
            ]
        
        # Filter by date range
        if "date_from" in search_params:
            try:
                date_from = search_params["date_from"]
                filtered_sessions = [
                    s for s in filtered_sessions 
                    if s.get("schedule", {}).get("date", "") >= date_from
                ]
            except ValueError:
                logger.warning(f"Invalid date_from format: {search_params['date_from']}")
        
        if "date_to" in search_params:
            try:
                date_to = search_params["date_to"]
                filtered_sessions = [
                    s for s in filtered_sessions 
                    if s.get("schedule", {}).get("date", "") <= date_to
                ]
            except ValueError:
                logger.warning(f"Invalid date_to format: {search_params['date_to']}")
        
        # Filter by participant
        if "participant_name" in search_params:
            participant_name = search_params["participant_name"].lower()
            filtered_sessions = [
                s for s in filtered_sessions 
                if any(participant_name in p.get("name", "").lower() for p in s.get("participants", []))
            ]
        
        # Sort results (default: newest first by scheduled date)
        sort_by = search_params.get("sort_by", "scheduled_date")
        sort_order = search_params.get("sort_order", "desc")
        
        if sort_by == "scheduled_date":
            filtered_sessions.sort(
                key=lambda s: f"{s.get('schedule', {}).get('date', '')}{s.get('schedule', {}).get('time', '')}", 
                reverse=(sort_order == "desc")
            )
        elif sort_by == "created_at":
            filtered_sessions.sort(
                key=lambda s: s.get("created_at", ""), 
                reverse=(sort_order == "desc")
            )
        
        # Limit results if specified
        limit = search_params.get("limit")
        if limit and limit > 0:
            filtered_sessions = filtered_sessions[:limit]
        
        logger.info(f"Found {len(filtered_sessions)} matching sessions")
        
        # Return simplified session data for search results
        return [
            {
                "id": session.get("id"),
                "status": session.get("status"),
                "case": session.get("case"),
                "schedule": session.get("schedule"),
                "presiding_judge": session.get("presiding_judge"),
                "participants_count": len(session.get("participants", [])),
                "metadata": session.get("metadata")
            }
            for session in filtered_sessions
        ]
    
    async def postpone_session(self, session_id: str, new_date: str, new_time: str, reason: str, judge_info: Dict) -> Dict:
        """
        Postpone a virtual court session.
        
        Args:
            session_id: ID of the session
            new_date: New session date
            new_time: New session time
            reason: Reason for postponement
            judge_info: Information about the presiding judge
            
        Returns:
            Updated session
        """
        logger.info(f"Postponing virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if judge is authorized
        if judge_info.get("id") != session["presiding_judge"].get("id"):
            logger.error(f"Unauthorized judge attempt to postpone session: {session_id}")
            raise ValueError("Only the presiding judge can postpone this session")
        
        # Check if session is in a state that can be postponed
        if session["status"] not in ["scheduled", "postponed"]:
            logger.error(f"Cannot postpone session in current state: {session['status']}")
            raise ValueError(f"Cannot postpone session in current state: {session['status']}")
        
        # Save original schedule for reference
        original_schedule = {
            "date": session["schedule"]["date"],
            "time": session["schedule"]["time"]
        }
        
        # Update session schedule
        session["schedule"]["date"] = new_date
        session["schedule"]["time"] = new_time
        
        # Update session state
        session["status"] = "postponed"
        
        # Add postponement event
        session["events"].append({
            "type": "postpone",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": judge_info.get("name"),
            "reason": reason,
            "original_schedule": original_schedule,
            "new_schedule": {
                "date": new_date,
                "time": new_time
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully postponed session {session_id} to {new_date} {new_time}")
        return session
    
    async def get_session_recording(self, session_id: str) -> Optional[Dict]:
        """
        Get recording information for a completed session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Recording information if available, None otherwise
        """
        logger.info(f"Retrieving recording for session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if recording is available
        if not session.get("recording", {}).get("enabled", False):
            logger.warning(f"Recording not enabled for session: {session_id}")
            return None
        
        if session.get("status") != "completed":
            logger.warning(f"Recording not available for incomplete session: {session_id}")
            return None
        
        if "started_at" not in session.get("recording", {}):
            logger.warning(f"Recording never started for session: {session_id}")
            return None
        
        # Return recording information
        recording_info = {
            "session_id": session_id,
            "case_title": session.get("case", {}).get("title"),
            "started_at": session.get("recording", {}).get("started_at"),
            "ended_at": session.get("recording", {}).get("ended_at"),
            "duration_seconds": session.get("recording", {}).get("duration_seconds"),
            "has_transcript": session.get("recording", {}).get("auto_transcription", False),
            "segments": session.get("recording", {}).get("segments", []),
            "download_url": f"/api/virtual-court/sessions/{session_id}/recording/download"
        }
        
        return recording_info
    
    async def get_session_events(self, session_id: str) -> List[Dict]:
        """
        Get all events for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of session events
        """
        logger.info(f"Retrieving events for session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Return events
        return session.get("events", [])
    
    async def generate_session_report(self, session_id: str) -> Dict:
        """
        Generate a comprehensive report for a completed session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session report
        """
        logger.info(f"Generating report for session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if session is completed
        if session.get("status") != "completed":
            logger.warning(f"Cannot generate report for incomplete session: {session_id}")
            raise ValueError("Cannot generate report for incomplete session")
        
        # Create report
        report = {
            "session_id": session_id,
            "report_generated_at": datetime.now().isoformat(),
            "case_information": {
                "number": session.get("case", {}).get("number"),
                "title": session.get("case", {}).get("title"),
                "type": session.get("case", {}).get("type")
            },
            "session_details": {
                "date": session.get("schedule", {}).get("date"),
                "time": session.get("schedule", {}).get("time"),
                "duration_minutes": session.get("schedule", {}).get("duration_minutes"),
                "actual_duration_seconds": session.get("recording", {}).get("duration_seconds")
            },
            "presiding_judge": session.get("presiding_judge"),
            "participants": self._summarize_participants(session.get("participants", [])),
            "events_summary": self._summarize_events(session.get("events", [])),
            "documents": [
                {
                    "id": doc.get("id"),
                    "name": doc.get("name"),
                    "type": doc.get("type"),
                    "uploaded_by": doc.get("uploaded_by", {}).get("name"),
                    "uploaded_at": doc.get("uploaded_at")
                }
                for doc in session.get("documents", [])
            ],
            "recording_info": session.get("recording", {}).get("enabled", False) and {
                "duration_seconds": session.get("recording", {}).get("duration_seconds"),
                "auto_transcription": session.get("recording", {}).get("auto_transcription", False),
                "started_at": session.get("recording", {}).get("started_at"),
                "ended_at": session.get("recording", {}).get("ended_at")
            }
        }
        
        return report
    
    def _summarize_participants(self, participants: List[Dict]) -> Dict:
        """Summarize participant information for the session report"""
        roles = {}
        
        # Count participants by role
        for participant in participants:
            role = participant.get("role", "unknown")
            if role not in roles:
                roles[role] = []
            
            # Include basic participant info
            participant_info = {
                "id": participant.get("id"),
                "name": participant.get("name"),
                "joined_at": participant.get("joined_at")
            }
            
            # Include leave time if available
            if "left_at" in participant:
                participant_info["left_at"] = participant.get("left_at")
            
            roles[role].append(participant_info)
        
        return {
            "by_role": roles,
            "total_count": len(participants)
        }
    
    def _summarize_events(self, events: List[Dict]) -> Dict:
        """Summarize events for the session report"""
        event_types = {}
        
        # Group events by type
        for event in events:
            event_type = event.get("type", "unknown")
            if event_type not in event_types:
                event_types[event_type] = []
            
            event_types[event_type].append(event)
        
        # Create summary
        summary = {
            "count_by_type": {event_type: len(events_list) for event_type, events_list in event_types.items()},
            "total_count": len(events)
        }
        
        # Add some specific event information
        if "start" in event_types and event_types["start"]:
            start_event = event_types["start"][0]
            summary["started_at"] = start_event.get("timestamp")
            summary["started_by"] = start_event.get("initiated_by")
        
        if "end" in event_types and event_types["end"]:
            end_event = event_types["end"][0]
            summary["ended_at"] = end_event.get("timestamp")
            summary["ended_by"] = end_event.get("initiated_by")
            summary["outcome"] = end_event.get("details")
        
        return summary"""
Virtual Court Service for NigeriaJustice.AI

This module provides functionality for managing virtual court sessions,
allowing remote participation in court proceedings with secure identity
verification.
"""

import logging
import os
import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import random
import string
import asyncio

from app.core.config import settings
from app.services.identity_verification import IdentityVerificationService

logger = logging.getLogger(__name__)

class VirtualCourtService:
    """
    Service for managing virtual court sessions.
    
    This service enables the creation, management, and execution of
    virtual court sessions with secure identity verification.
    """
    
    def __init__(self, storage_path: str = None, identity_service: Optional[IdentityVerificationService] = None):
        """
        Initialize the virtual court service.
        
        Args:
            storage_path: Path to store session data
            identity_service: Identity verification service instance
        """
        self.storage_path = storage_path or os.path.join("data", "virtual_sessions")
        self.identity_service = identity_service or IdentityVerificationService()
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        logger.info("Virtual Court Service initialized")
    
    async def create_session(self, session_data: Dict, judge_info: Dict) -> Dict:
        """
        Create a new virtual court session.
        
        Args:
            session_data: Data for the session
            judge_info: Information about the presiding judge
            
        Returns:
            Created session with ID and access codes
        """
        logger.info(f"Creating new virtual court session for case {session_data.get('case_number', 'unknown')}")
        
        # Validate required fields
        required_fields = ["case_number", "case_title", "scheduled_date", "scheduled_time"]
        for field in required_fields:
            if field not in session_data or not session_data[field]:
                logger.error(f"Missing required field for virtual session: {field}")
                raise ValueError(f"Missing required field for virtual session: {field}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Generate access codes for different roles
        access_codes = self._generate_access_codes()
        
        # Create session document
        session = {
            "id": session_id,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "case": {
                "number": session_data.get("case_number"),
                "title": session_data.get("case_title"),
                "type": session_data.get("case_type")
            },
            "schedule": {
                "date": session_data.get("scheduled_date"),
                "time": session_data.get("scheduled_time"),
                "duration_minutes": session_data.get("duration_minutes", 60)
            },
            "presiding_judge": {
                "id": judge_info.get("id"),
                "name": judge_info.get("name"),
                "court": judge_info.get("court")
            },
            "participants": session_data.get("participants", []),
            "access_codes": access_codes,
            "recording": {
                "enabled": session_data.get("recording_enabled", True),
                "auto_transcription": session_data.get("auto_transcription", True)
            },
            "documents": session_data.get("documents", []),
            "events": [],
            "metadata": {
                "court_room": session_data.get("court_room"),
                "jurisdiction": session_data.get("jurisdiction"),
                "public_access": session_data.get("public_access", False)
            }
        }
        
        # Save session to storage
        await self._save_session(session)
        
        logger.info(f"Created virtual court session with ID: {session_id}")
        return session
    
    def _generate_access_codes(self) -> Dict[str, str]:
        """Generate secure access codes for virtual court roles"""
        
        # Generate random 8-character alphanumeric codes
        def generate_code():
            chars = string.ascii_uppercase + string.digits
            return ''.join(random.choice(chars) for _ in range(8))
        
        # Create codes for different roles
        return {
            "judge": generate_code(),
            "prosecutor": generate_code(),
            "defense": generate_code(),
            "witness": generate_code(),
            "clerk": generate_code(),
            "public": generate_code() if settings.COURT_CONFIG.get("allow_public_access", False) else None
        }
    
    async def _save_session(self, session: Dict) -> None:
        """Save session to storage"""
        session_id = session.get("id")
        filename = os.path.join(self.storage_path, f"{session_id}.json")
        
        # Save as JSON file
        with open(filename, 'w') as f:
            json.dump(session, f, indent=2)
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get a virtual court session by ID.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session data if found, None otherwise
        """
        logger.info(f"Retrieving virtual court session with ID: {session_id}")
        
        # Check if session exists
        filename = os.path.join(self.storage_path, f"{session_id}.json")
        if not os.path.exists(filename):
            logger.warning(f"Session not found: {session_id}")
            return None
        
        # Load session from file
        try:
            with open(filename, 'r') as f:
                session = json.load(f)
            
            logger.info(f"Successfully retrieved session: {session_id}")
            return session
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, update_data: Dict) -> Dict:
        """
        Update a virtual court session.
        
        Args:
            session_id: ID of the session
            update_data: Data to update
            
        Returns:
            Updated session
        """
        logger.info(f"Updating virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Update session fields
        if "status" in update_data:
            session["status"] = update_data["status"]
        
        if "schedule" in update_data:
            for key, value in update_data["schedule"].items():
                session["schedule"][key] = value
        
        if "participants" in update_data:
            session["participants"] = update_data["participants"]
        
        if "documents" in update_data:
            session["documents"] = update_data["documents"]
        
        if "metadata" in update_data:
            for key, value in update_data["metadata"].items():
                session["metadata"][key] = value
        
        # Add update event
        session["events"].append({
            "type": "update",
            "timestamp": datetime.now().isoformat(),
            "details": "Session updated"
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully updated session: {session_id}")
        return session
    
    async def start_session(self, session_id: str, judge_info: Dict) -> Dict:
        """
        Start a virtual court session.
        
        Args:
            session_id: ID of the session
            judge_info: Information about the presiding judge
            
        Returns:
            Updated session
        """
        logger.info(f"Starting virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if judge is authorized
        if judge_info.get("id") != session["presiding_judge"].get("id"):
            logger.error(f"Unauthorized judge attempt to start session: {session_id}")
            raise ValueError("Only the presiding judge can start this session")
        
        # Check if session is in the right state
        if session["status"] not in ["scheduled", "postponed"]:
            logger.error(f"Cannot start session in current state: {session['status']}")
            raise ValueError(f"Cannot start session in current state: {session['status']}")
        
        # Update session state
        session["status"] = "in_progress"
        session["events"].append({
            "type": "start",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": judge_info.get("name"),
            "details": "Session started"
        })
        
        # For recording sessions, initialize recording data
        if session["recording"]["enabled"]:
            session["recording"]["started_at"] = datetime.now().isoformat()
            session["recording"]["segments"] = []
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully started session: {session_id}")
        return session
    
    async def end_session(self, session_id: str, judge_info: Dict, outcome: Optional[str] = None) -> Dict:
        """
        End a virtual court session.
        
        Args:
            session_id: ID of the session
            judge_info: Information about the presiding judge
            outcome: Optional outcome of the session
            
        Returns:
            Updated session
        """
        logger.info(f"Ending virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if judge is authorized
        if judge_info.get("id") != session["presiding_judge"].get("id"):
            logger.error(f"Unauthorized judge attempt to end session: {session_id}")
            raise ValueError("Only the presiding judge can end this session")
        
        # Check if session is in progress
        if session["status"] != "in_progress":
            logger.error(f"Cannot end session in current state: {session['status']}")
            raise ValueError(f"Cannot end session in current state: {session['status']}")
        
        # Update session state
        session["status"] = "completed"
        session["events"].append({
            "type": "end",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": judge_info.get("name"),
            "details": outcome or "Session ended"
        })
        
        # For recording sessions, finalize recording data
        if session["recording"]["enabled"] and "started_at" in session["recording"]:
            session["recording"]["ended_at"] = datetime.now().isoformat()
            
            # Calculate duration
            try:
                start_time = datetime.fromisoformat(session["recording"]["started_at"])
                end_time = datetime.fromisoformat(session["recording"]["ended_at"])
                duration_seconds = (end_time - start_time).total_seconds()
                session["recording"]["duration_seconds"] = duration_seconds
            except (ValueError, TypeError):
                logger.warning(f"Could not calculate recording duration for session {session_id}")
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully ended session: {session_id}")
        return session
    
    async def join_session(self, session_id: str, participant_data: Dict) -> Dict:
        """
        Join a virtual court session.
        
        Args:
            session_id: ID of the session
            participant_data: Data about the participant
            
        Returns:
            Session access information
        """
        logger.info(f"Participant joining virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if session is joinable
        if session["status"] not in ["scheduled", "in_progress"]:
            logger.error(f"Cannot join session in current state: {session['status']}")
            raise ValueError(f"Cannot join session in current state: {session['status']}")
        
        # Verify access code
        role = participant_data.get("role", "").lower()
        provided_code = participant_data.get("access_code")
        
        if role not in session["access_codes"] or not provided_code:
            logger.error(f"Invalid role or missing access code: {role}")
            raise ValueError("Invalid role or missing access code")
        
        if provided_code != session["access_codes"][role]:
            logger.error(f"Invalid access code for role {role}")
            raise ValueError("Invalid access code")
        
        # Check identity verification if required
        if role in ["judge", "prosecutor", "defense"] and settings.COURT_CONFIG.get("require_identity_verification", True):
            # Verify identity
            identity_verified = await self._verify_participant_identity(participant_data)
            if not identity_verified:
                logger.error(f"Identity verification failed for participant in role: {role}")
                raise ValueError("Identity verification failed")
        
        # Generate join token (would be a JWT in production)
        join_token = str(uuid.uuid4())
        
        # Add participant to session
        participant_entry = {
            "id": participant_data.get("id", str(uuid.uuid4())),
            "name": participant_data.get("name"),
            "role": role,
            "joined_at": datetime.now().isoformat()
        }
        
        # Update participants list if not already present
        participant_exists = False
        for i, p in enumerate(session["participants"]):
            if p.get("id") == participant_entry["id"]:
                session["participants"][i] = {**p, **participant_entry}
                participant_exists = True
                break
        
        if not participant_exists:
            session["participants"].append(participant_entry)
        
        # Add join event
        session["events"].append({
            "type": "join",
            "timestamp": datetime.now().isoformat(),
            "participant": {
                "id": participant_entry["id"],
                "name": participant_entry["name"],
                "role": participant_entry["role"]
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Participant {participant_entry['name']} joined session {session_id} as {role}")
        
        # Return access information
        return {
            "session_id": session_id,
            "case_title": session["case"]["title"],
            "access_token": join_token,
            "participant_id": participant_entry["id"],
            "role": role,
            "status": session["status"],
            "session_details": {
                "presiding_judge": session["presiding_judge"]["name"],
                "scheduled_time": f"{session['schedule']['date']} {session['schedule']['time']}",
                "participants_count": len(session["participants"])
            }
        }
    
    async def _verify_participant_identity(self, participant_data: Dict) -> bool:
        """Verify the identity of a participant"""
        # In production, this would use the identity verification service
        # For now, check if the required identity info is provided
        
        if not participant_data.get("identity"):
            logger.warning("No identity data provided for verification")
            return False
        
        identity_data = participant_data["identity"]
        
        # Check for NIN or passport
        if "nin" in identity_data:
            # Verify NIN using identity service
            is_verified, _ = await self.identity_service.verify_nin(identity_data["nin"])
            return is_verified
        elif "passport" in identity_data:
            # Verify passport using identity service
            is_verified, _ = await self.identity_service.verify_passport(identity_data["passport"])
            return is_verified
        elif "court_official_id" in identity_data:
            # Verify court official using identity service
            is_verified, _ = await self.identity_service.verify_court_official(
                identity_data["court_official_id"], 
                identity_data.get("expected_role")
            )
            return is_verified
        else:
            logger.warning("No recognized identity credential provided")
            return False
    
    async def leave_session(self, session_id: str, participant_id: str) -> Dict:
        """
        Leave a virtual court session.
        
        Args:
            session_id: ID of the session
            participant_id: ID of the participant
            
        Returns:
            Updated session
        """
        logger.info(f"Participant leaving virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Find participant
        participant = None
        for p in session["participants"]:
            if p.get("id") == participant_id:
                participant = p
                break
        
        if not participant:
            logger.error(f"Participant not found in session: {participant_id}")
            raise ValueError("Participant not found in session")
        
        # Update participant status
        participant["left_at"] = datetime.now().isoformat()
        
        # Add leave event
        session["events"].append({
            "type": "leave",
            "timestamp": datetime.now().isoformat(),
            "participant": {
                "id": participant["id"],
                "name": participant["name"],
                "role": participant["role"]
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Participant {participant['name']} left session {session_id}")
        return session
    
    async def add_document(self, session_id: str, document_data: Dict, uploaded_by: Dict) -> Dict:
        """
        Add a document to a virtual court session.
        
        Args:
            session_id: ID of the session
            document_data: Data about the document
            uploaded_by: Information about who uploaded the document
            
        Returns:
            Updated session
        """
        logger.info(f"Adding document to virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Create document entry
        document = {
            "id": str(uuid.uuid4()),
            "name": document_data.get("name"),
            "type": document_data.get("type"),
            "path": document_data.get("path"),
            "size_bytes": document_data.get("size_bytes"),
            "uploaded_at": datetime.now().isoformat(),
            "uploaded_by": {
                "id": uploaded_by.get("id"),
                "name": uploaded_by.get("name"),
                "role": uploaded_by.get("role")
            },
            "visibility": document_data.get("visibility", "all"),
            "metadata": document_data.get("metadata", {})
        }
        
        # Add document to session
        if "documents" not in session:
            session["documents"] = []
        
        session["documents"].append(document)
        
        # Add document event
        session["events"].append({
            "type": "document_added",
            "timestamp": datetime.now().isoformat(),
            "document": {
                "id": document["id"],
                "name": document["name"]
            },
            "uploaded_by": {
                "id": uploaded_by.get("id"),
                "name": uploaded_by.get("name"),
                "role": uploaded_by.get("role")
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Added document {document['name']} to session {session_id}")
        return session
    
    async def search_sessions(self, search_params: Dict) -> List[Dict]:
        """
        Search for virtual court sessions based on parameters.
        
        Args:
            search_params: Search parameters
            
        Returns:
            List of matching sessions
        """
        logger.info(f"Searching virtual court sessions with params: {search_params}")
        
        # Get all session files
        session_files = [f for f in os.listdir(self.storage_path) if f.endswith('.json')]
        
        # Load all sessions
        sessions = []
        for filename in session_files:
            try:
                with open(os.path.join(self.storage_path, filename), 'r') as f:
                    session = json.load(f)
                sessions.append(session)
            except Exception as e:
                logger.error(f"Error loading session file {filename}: {str(e)}")
        
        # Filter sessions based on search parameters
        filtered_sessions = sessions
        
        # Filter by status
        if "status" in search_params:
            filtered_sessions = [s for s in filtered_sessions if s.get("status") == search_params["status"]]
        
        # Filter by case number
        if "case_number" in search_params:
            filtered_sessions = [
                s for s in filtered_sessions 
                if s.get("case", {}).get("number") == search_params["case_number"]
            ]
        
        # Filter by judge
        if "judge_id" in search_params:
            filtered_sessions = [
                s for s in filtered_sessions 
                if s.get("presiding_judge", {}).get("id") == search_params["judge_id"]
            ]
        
        # Filter by date range
        if "date_from" in search_params:
            try:
                date_from = search_params["date_from"]
                filtered_sessions = [
                    s for s in filtered_sessions 
                    if s.get("schedule", {}).get("date", "") >= date_from
                ]
            except ValueError:
                logger.warning(f"Invalid date_from format: {search_params['date_from']}")
        
        if "date_to" in search_params:
            try:
                date_to = search_params["date_to"]
                filtered_sessions = [
                    s for s in filtered_sessions 
                    if s.get("schedule", {}).get("date", "") <= date_to
                ]
            except ValueError:
                logger.warning(f"Invalid date_to format: {search_params['date_to']}")
        
        # Filter by participant
        if "participant_name" in search_params:
            participant_name = search_params["participant_name"].lower()
            filtered_sessions = [
                s for s in filtered_sessions 
                if any(participant_name in p.get("name", "").lower() for p in s.get("participants", []))
            ]
        
        # Sort results (default: newest first by scheduled date)
        sort_by = search_params.get("sort_by", "scheduled_date")
        sort_order = search_params.get("sort_order", "desc")
        
        if sort_by == "scheduled_date":
            filtered_sessions.sort(
                key=lambda s: f"{s.get('schedule', {}).get('date', '')}{s.get('schedule', {}).get('time', '')}", 
                reverse=(sort_order == "desc")
            )
        elif sort_by == "created_at":
            filtered_sessions.sort(
                key=lambda s: s.get("created_at", ""), 
                reverse=(sort_order == "desc")
            )
        
        # Limit results if specified
        limit = search_params.get("limit")
        if limit and limit > 0:
            filtered_sessions = filtered_sessions[:limit]
        
        logger.info(f"Found {len(filtered_sessions)} matching sessions")
        
        # Return simplified session data for search results
        return [
            {
                "id": session.get("id"),
                "status": session.get("status"),
                "case": session.get("case"),
                "schedule": session.get("schedule"),
                "presiding_judge": session.get("presiding_judge"),
                "participants_count": len(session.get("participants", [])),
                "metadata": session.get("metadata")
            }
            for session in filtered_sessions
        ]
    
    async def postpone_session(self, session_id: str, new_date: str, new_time: str, reason: str, judge_info: Dict) -> Dict:
        """
        Postpone a virtual court session.
        
        Args:
            session_id: ID of the session
            new_date: New session date
            new_time: New session time
            reason: Reason for postponement
            judge_info: Information about the presiding judge
            
        Returns:
            Updated session
        """
        logger.info(f"Postponing virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if judge is authorized
        if judge_info.get("id") != session["presiding_judge"].get("id"):
            logger.error(f"Unauthorized judge attempt to postpone session: {session_id}")
            raise ValueError("Only the presiding judge can postpone this session")
        
        # Check if session is in a state that can be postponed
        if session["status"] not in ["scheduled", "postponed"]:
            logger.error(f"Cannot postpone session in current state: {session['status']}")
            raise ValueError(f"Cannot postpone session in current state: {session['status']}")
        
        # Save original schedule for reference
        original_schedule = {
            "date": session["schedule"]["date"],
            "time": session["schedule"]["time"]
        }
        
        # Update session schedule
        session["schedule"]["date"] = new_date
        session["schedule"]["time"] = new_time
        
        # Update session state
        session["status"] = "postponed"
        
        # Add postponement event
        session["events"].append({
            "type": "postpone",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": judge_info.get("name"),
            "reason": reason,
            "original_schedule": original_schedule,
            "new_schedule": {
                "date": new_date,
                "time": new_time
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully postponed session {session_id} to {new_date} {new_time}")
        return session
    
    async def get_session_recording(self, session_id: str) -> Optional[Dict]:
        """
        Get recording information for a completed session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Recording information if available, None otherwise
        """
        logger.info(f"Retrieving recording for session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if recording is available
        if not session.get("recording", {}).get("enabled", False):
            logger.warning(f"Recording not enabled for session: {session_id}")
            return None
        
        if session.get("status") != "completed":
            logger.warning(f"Recording not available for incomplete session: {session_id}")
            return None
        
        if "started_at" not in session.get("recording", {}):
            logger.warning(f"Recording never started for session: {session_id}")
            return None
        
        # Return recording information
        recording_info = {
            "session_id": session_id,
            "case_title": session.get("case", {}).get("title"),
            "started_at": session.get("recording", {}).get("started_at"),
            "ended_at": session.get("recording", {}).get("ended_at"),
            "duration_seconds": session.get("recording", {}).get("duration_seconds"),
            "has_transcript": session.get("recording", {}).get("auto_transcription", False),
            "segments": session.get("recording", {}).get("segments", []),
            "download_url": f"/api/virtual-court/sessions/{session_id}/recording/download"
        }
        
        return recording_info
    
    async def get_session_events(self, session_id: str) -> List[Dict]:
        """
        Get all events for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of session events
        """
        logger.info(f"Retrieving events for session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Return events
        return session.get("events", [])
    
    async def generate_session_report(self, session_id: str) -> Dict:
        """
        Generate a comprehensive report for a completed session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session report
        """
        logger.info(f"Generating report for session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if session is completed
        if session.get("status") != "completed":
            logger.warning(f"Cannot generate report for incomplete session: {session_id}")
            raise ValueError("Cannot generate report for incomplete session")
        
        # Create report
        report = {
            "session_id": session_id,
            "report_generated_at": datetime.now().isoformat(),
            "case_information": {
                "number": session.get("case", {}).get("number"),
                "title": session.get("case", {}).get("title"),
                "type": session.get("case", {}).get("type")
            },
            "session_details": {
                "date": session.get("schedule", {}).get("date"),
                "time": session.get("schedule", {}).get("time"),
                "duration_minutes": session.get("schedule", {}).get("duration_minutes"),
                "actual_duration_seconds": session.get("recording", {}).get("duration_seconds")
            },
            "presiding_judge": session.get("presiding_judge"),
            "participants": self._summarize_participants(session.get("participants", [])),
            "events_summary": self._summarize_events(session.get("events", [])),
            "documents": [
                {
                    "id": doc.get("id"),
                    "name": doc.get("name"),
                    "type": doc.get("type"),
                    "uploaded_by": doc.get("uploaded_by", {}).get("name"),
                    "uploaded_at": doc.get("uploaded_at")
                }
                for doc in session.get("documents", ["""
Virtual Court Service for NigeriaJustice.AI

This module provides functionality for managing virtual court sessions,
allowing remote participation in court proceedings with secure identity
verification.
"""

import logging
import os
import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import random
import string
import asyncio

from app.core.config import settings
from app.services.identity_verification import IdentityVerificationService

logger = logging.getLogger(__name__)

class VirtualCourtService:
    """
    Service for managing virtual court sessions.
    
    This service enables the creation, management, and execution of
    virtual court sessions with secure identity verification.
    """
    
    def __init__(self, storage_path: str = None, identity_service: Optional[IdentityVerificationService] = None):
        """
        Initialize the virtual court service.
        
        Args:
            storage_path: Path to store session data
            identity_service: Identity verification service instance
        """
        self.storage_path = storage_path or os.path.join("data", "virtual_sessions")
        self.identity_service = identity_service or IdentityVerificationService()
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        logger.info("Virtual Court Service initialized")
    
    async def create_session(self, session_data: Dict, judge_info: Dict) -> Dict:
        """
        Create a new virtual court session.
        
        Args:
            session_data: Data for the session
            judge_info: Information about the presiding judge
            
        Returns:
            Created session with ID and access codes
        """
        logger.info(f"Creating new virtual court session for case {session_data.get('case_number', 'unknown')}")
        
        # Validate required fields
        required_fields = ["case_number", "case_title", "scheduled_date", "scheduled_time"]
        for field in required_fields:
            if field not in session_data or not session_data[field]:
                logger.error(f"Missing required field for virtual session: {field}")
                raise ValueError(f"Missing required field for virtual session: {field}")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Generate access codes for different roles
        access_codes = self._generate_access_codes()
        
        # Create session document
        session = {
            "id": session_id,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "case": {
                "number": session_data.get("case_number"),
                "title": session_data.get("case_title"),
                "type": session_data.get("case_type")
            },
            "schedule": {
                "date": session_data.get("scheduled_date"),
                "time": session_data.get("scheduled_time"),
                "duration_minutes": session_data.get("duration_minutes", 60)
            },
            "presiding_judge": {
                "id": judge_info.get("id"),
                "name": judge_info.get("name"),
                "court": judge_info.get("court")
            },
            "participants": session_data.get("participants", []),
            "access_codes": access_codes,
            "recording": {
                "enabled": session_data.get("recording_enabled", True),
                "auto_transcription": session_data.get("auto_transcription", True)
            },
            "documents": session_data.get("documents", []),
            "events": [],
            "metadata": {
                "court_room": session_data.get("court_room"),
                "jurisdiction": session_data.get("jurisdiction"),
                "public_access": session_data.get("public_access", False)
            }
        }
        
        # Save session to storage
        await self._save_session(session)
        
        logger.info(f"Created virtual court session with ID: {session_id}")
        return session
    
    def _generate_access_codes(self) -> Dict[str, str]:
        """Generate secure access codes for virtual court roles"""
        
        # Generate random 8-character alphanumeric codes
        def generate_code():
            chars = string.ascii_uppercase + string.digits
            return ''.join(random.choice(chars) for _ in range(8))
        
        # Create codes for different roles
        return {
            "judge": generate_code(),
            "prosecutor": generate_code(),
            "defense": generate_code(),
            "witness": generate_code(),
            "clerk": generate_code(),
            "public": generate_code() if settings.COURT_CONFIG.get("allow_public_access", False) else None
        }
    
    async def _save_session(self, session: Dict) -> None:
        """Save session to storage"""
        session_id = session.get("id")
        filename = os.path.join(self.storage_path, f"{session_id}.json")
        
        # Save as JSON file
        with open(filename, 'w') as f:
            json.dump(session, f, indent=2)
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get a virtual court session by ID.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session data if found, None otherwise
        """
        logger.info(f"Retrieving virtual court session with ID: {session_id}")
        
        # Check if session exists
        filename = os.path.join(self.storage_path, f"{session_id}.json")
        if not os.path.exists(filename):
            logger.warning(f"Session not found: {session_id}")
            return None
        
        # Load session from file
        try:
            with open(filename, 'r') as f:
                session = json.load(f)
            
            logger.info(f"Successfully retrieved session: {session_id}")
            return session
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {str(e)}")
            raise
    
    async def update_session(self, session_id: str, update_data: Dict) -> Dict:
        """
        Update a virtual court session.
        
        Args:
            session_id: ID of the session
            update_data: Data to update
            
        Returns:
            Updated session
        """
        logger.info(f"Updating virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Update session fields
        if "status" in update_data:
            session["status"] = update_data["status"]
        
        if "schedule" in update_data:
            for key, value in update_data["schedule"].items():
                session["schedule"][key] = value
        
        if "participants" in update_data:
            session["participants"] = update_data["participants"]
        
        if "documents" in update_data:
            session["documents"] = update_data["documents"]
        
        if "metadata" in update_data:
            for key, value in update_data["metadata"].items():
                session["metadata"][key] = value
        
        # Add update event
        session["events"].append({
            "type": "update",
            "timestamp": datetime.now().isoformat(),
            "details": "Session updated"
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully updated session: {session_id}")
        return session
    
    async def start_session(self, session_id: str, judge_info: Dict) -> Dict:
        """
        Start a virtual court session.
        
        Args:
            session_id: ID of the session
            judge_info: Information about the presiding judge
            
        Returns:
            Updated session
        """
        logger.info(f"Starting virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if judge is authorized
        if judge_info.get("id") != session["presiding_judge"].get("id"):
            logger.error(f"Unauthorized judge attempt to start session: {session_id}")
            raise ValueError("Only the presiding judge can start this session")
        
        # Check if session is in the right state
        if session["status"] not in ["scheduled", "postponed"]:
            logger.error(f"Cannot start session in current state: {session['status']}")
            raise ValueError(f"Cannot start session in current state: {session['status']}")
        
        # Update session state
        session["status"] = "in_progress"
        session["events"].append({
            "type": "start",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": judge_info.get("name"),
            "details": "Session started"
        })
        
        # For recording sessions, initialize recording data
        if session["recording"]["enabled"]:
            session["recording"]["started_at"] = datetime.now().isoformat()
            session["recording"]["segments"] = []
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully started session: {session_id}")
        return session
    
    async def end_session(self, session_id: str, judge_info: Dict, outcome: Optional[str] = None) -> Dict:
        """
        End a virtual court session.
        
        Args:
            session_id: ID of the session
            judge_info: Information about the presiding judge
            outcome: Optional outcome of the session
            
        Returns:
            Updated session
        """
        logger.info(f"Ending virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if judge is authorized
        if judge_info.get("id") != session["presiding_judge"].get("id"):
            logger.error(f"Unauthorized judge attempt to end session: {session_id}")
            raise ValueError("Only the presiding judge can end this session")
        
        # Check if session is in progress
        if session["status"] != "in_progress":
            logger.error(f"Cannot end session in current state: {session['status']}")
            raise ValueError(f"Cannot end session in current state: {session['status']}")
        
        # Update session state
        session["status"] = "completed"
        session["events"].append({
            "type": "end",
            "timestamp": datetime.now().isoformat(),
            "initiated_by": judge_info.get("name"),
            "details": outcome or "Session ended"
        })
        
        # For recording sessions, finalize recording data
        if session["recording"]["enabled"] and "started_at" in session["recording"]:
            session["recording"]["ended_at"] = datetime.now().isoformat()
            
            # Calculate duration
            try:
                start_time = datetime.fromisoformat(session["recording"]["started_at"])
                end_time = datetime.fromisoformat(session["recording"]["ended_at"])
                duration_seconds = (end_time - start_time).total_seconds()
                session["recording"]["duration_seconds"] = duration_seconds
            except (ValueError, TypeError):
                logger.warning(f"Could not calculate recording duration for session {session_id}")
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Successfully ended session: {session_id}")
        return session
    
    async def join_session(self, session_id: str, participant_data: Dict) -> Dict:
        """
        Join a virtual court session.
        
        Args:
            session_id: ID of the session
            participant_data: Data about the participant
            
        Returns:
            Session access information
        """
        logger.info(f"Participant joining virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Check if session is joinable
        if session["status"] not in ["scheduled", "in_progress"]:
            logger.error(f"Cannot join session in current state: {session['status']}")
            raise ValueError(f"Cannot join session in current state: {session['status']}")
        
        # Verify access code
        role = participant_data.get("role", "").lower()
        provided_code = participant_data.get("access_code")
        
        if role not in session["access_codes"] or not provided_code:
            logger.error(f"Invalid role or missing access code: {role}")
            raise ValueError("Invalid role or missing access code")
        
        if provided_code != session["access_codes"][role]:
            logger.error(f"Invalid access code for role {role}")
            raise ValueError("Invalid access code")
        
        # Check identity verification if required
        if role in ["judge", "prosecutor", "defense"] and settings.COURT_CONFIG.get("require_identity_verification", True):
            # Verify identity
            identity_verified = await self._verify_participant_identity(participant_data)
            if not identity_verified:
                logger.error(f"Identity verification failed for participant in role: {role}")
                raise ValueError("Identity verification failed")
        
        # Generate join token (would be a JWT in production)
        join_token = str(uuid.uuid4())
        
        # Add participant to session
        participant_entry = {
            "id": participant_data.get("id", str(uuid.uuid4())),
            "name": participant_data.get("name"),
            "role": role,
            "joined_at": datetime.now().isoformat()
        }
        
        # Update participants list if not already present
        participant_exists = False
        for i, p in enumerate(session["participants"]):
            if p.get("id") == participant_entry["id"]:
                session["participants"][i] = {**p, **participant_entry}
                participant_exists = True
                break
        
        if not participant_exists:
            session["participants"].append(participant_entry)
        
        # Add join event
        session["events"].append({
            "type": "join",
            "timestamp": datetime.now().isoformat(),
            "participant": {
                "id": participant_entry["id"],
                "name": participant_entry["name"],
                "role": participant_entry["role"]
            }
        })
        
        # Save updated session
        await self._save_session(session)
        
        logger.info(f"Participant {participant_entry['name']} joined session {session_id} as {role}")
        
        # Return access information
        return {
            "session_id": session_id,
            "case_title": session["case"]["title"],
            "access_token": join_token,
            "participant_id": participant_entry["id"],
            "role": role,
            "status": session["status"],
            "session_details": {
                "presiding_judge": session["presiding_judge"]["name"],
                "scheduled_time": f"{session['schedule']['date']} {session['schedule']['time']}",
                "participants_count": len(session["participants"])
            }
        }
    
    async def _verify_participant_identity(self, participant_data: Dict) -> bool:
        """Verify the identity of a participant"""
        # In production, this would use the identity verification service
        # For now, check if the required identity info is provided
        
        if not participant_data.get("identity"):
            logger.warning("No identity data provided for verification")
            return False
        
        identity_data = participant_data["identity"]
        
        # Check for NIN or passport
        if "nin" in identity_data:
            # Verify NIN using identity service
            is_verified, _ = await self.identity_service.verify_nin(identity_data["nin"])
            return is_verified
        elif "passport" in identity_data:
            # Verify passport using identity service
            is_verified, _ = await self.identity_service.verify_passport(identity_data["passport"])
            return is_verified
        elif "court_official_id" in identity_data:
            # Verify court official using identity service
            is_verified, _ = await self.identity_service.verify_court_official(
                identity_data["court_official_id"], 
                identity_data.get("expected_role")
            )
            return is_verified
        else:
            logger.warning("No recognized identity credential provided")
            return False
    
    async def leave_session(self, session_id: str, participant_id: str) -> Dict:
        """
        Leave a virtual court session.
        
        Args:
            session_id: ID of the session
            participant_id: ID of the participant
            
        Returns:
            Updated session
        """
        logger.info(f"Participant leaving virtual court session: {session_id}")
        
        # Get the session
        session = await self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError(f"Session not found: {session_id}")
        
        # Find participant
        participant = None
        for p in session["participants"]:
            if p.get("id") == participant_id:
                participant = p
                break
        
        if not participant:
            logger.error(f"Participant not found in session: {participant_id}")
            raise ValueError("Participant not found in session")
        
        # Update participant status
        participant["left_at"] = datetime.now().isoformat()
        
        # Add leave event
        session["events"].append({
            "type": "leave",
            "timestamp": datetime.now().isoformat(),
            "participant": {
                "id": participant["id"],
