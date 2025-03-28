"""
API routes for anonymization functionality of NigeriaJustice.AI.

This module defines the API endpoints for anonymizing sensitive information
in court documents, transcripts, and case files.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import logging

from app.services.anonymization import AnonymizationService
from app.core.security import get_current_user, verify_court_role, has_permission
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
anonymization_service = AnonymizationService()

@router.post("/text", response_model=Dict)
async def anonymize_text(
    text: str = Body(..., embed=True),
    entities_to_anonymize: Optional[List[str]] = Body(None),
    current_user: Dict = Depends(get_current_user)
):
    """
    Anonymize sensitive information in text.
    
    Args:
        text: Text to anonymize
        entities_to_anonymize: Optional list of entity types to anonymize
        
    Returns:
        Anonymized text
    """
    try:
        anonymized = anonymization_service.anonymize_text(
            text=text,
            entities_to_anonymize=entities_to_anonymize
        )
        
        logger.info(f"Successfully anonymized text for user {current_user.get('id')}")
        return {"anonymized_text": anonymized}
    
    except Exception as e:
        logger.error(f"Error anonymizing text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document", response_model=Dict)
async def anonymize_document(
    document: Dict = Body(...),
    entities_to_anonymize: Optional[List[str]] = Body(None),
    text_fields: Optional[List[str]] = Body(None),
    current_user: Dict = Depends(get_current_user)
):
    """
    Anonymize sensitive information in a document structure.
    
    Args:
        document: Document dictionary to anonymize
        entities_to_anonymize: Optional list of entity types to anonymize
        text_fields: Optional list of fields containing text to anonymize
        
    Returns:
        Anonymized document
    """
    try:
        anonymized = anonymization_service.anonymize_document(
            document=document,
            entities_to_anonymize=entities_to_anonymize,
            text_fields=text_fields
        )
        
        logger.info(f"Successfully anonymized document for user {current_user.get('id')}")
        return anonymized
    
    except Exception as e:
        logger.error(f"Error anonymizing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcript", response_model=Dict)
async def anonymize_transcript(
    transcript: Dict = Body(...),
    entities_to_anonymize: Optional[List[str]] = Body(None),
    current_user: Dict = Depends(get_current_user)
):
    """
    Anonymize a court transcript.
    
    Args:
        transcript: Transcript dictionary with entries
        entities_to_anonymize: Optional list of entity types to anonymize
        
    Returns:
        Anonymized transcript
    """
    try:
        anonymized = anonymization_service.anonymize_transcript(
            transcript=transcript,
            entities_to_anonymize=entities_to_anonymize
        )
        
        logger.info(f"Successfully anonymized transcript for user {current_user.get('id')}")
        return anonymized
    
    except Exception as e:
        logger.error(f"Error anonymizing transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deanonymize/transcript", response_model=Dict)
async def deanonymize_transcript(
    anonymized_transcript: Dict = Body(...),
    original_entities: Dict = Body(...),
    access_level: str = Query("standard"),
    current_user: Dict = Depends(get_current_user),
    has_deanonymize_permission: bool = Depends(has_permission("deanonymize_transcripts"))
):
    """
    Deanonymize a court transcript for authorized users.
    
    Args:
        anonymized_transcript: Anonymized transcript dictionary
        original_entities: Dictionary mapping redacted text to original text
        access_level: Access level for deanonymization ("standard", "elevated", "full")
        
    Returns:
        Partially or fully deanonymized transcript
    """
    # Verify access level based on user role
    user_role = current_user.get("role", "").lower()
    
    # Only judges and admins can access full deanonymization
    if access_level == "full" and user_role not in ["judge", "admin"]:
        logger.warning(f"Unauthorized attempt to use full deanonymization by {user_role} role")
        raise HTTPException(
            status_code=403,
            detail="Only judges and administrators can access full deanonymization"
        )
    
    # Only authorized roles can access elevated deanonymization
    if access_level == "elevated" and user_role not in ["judge", "admin", "prosecutor", "clerk"]:
        logger.warning(f"Unauthorized attempt to use elevated deanonymization by {user_role} role")
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access elevated deanonymization"
        )
    
    try:
        deanonymized = anonymization_service.deanonymize_transcript(
            anonymized_transcript=anonymized_transcript,
            original_entities=original_entities,
            access_level=access_level
        )
        
        logger.info(f"Successfully deanonymized transcript for user {current_user.get('id')} with {access_level} access")
        return deanonymized
    
    except Exception as e:
        logger.error(f"Error deanonymizing transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entity-types", response_model=List[Dict])
async def get_entity_types(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the list of available entity types for anonymization.
    
    Returns:
        List of entity type information
    """
    try:
        entity_types = anonymization_service.get_available_entity_types()
        return entity_types
    
    except Exception as e:
        logger.error(f"Error getting entity types: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/default-entities", response_model=List[str])
async def get_default_entities(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the default list of entity types to anonymize.
    
    Returns:
        List of default entity types
    """
    try:
        default_entities = anonymization_service.get_default_entities_to_anonymize()
        return default_entities
    
    except Exception as e:
        logger.error(f"Error getting default entities: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
