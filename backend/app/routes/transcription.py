"""
API routes for the transcription functionality of NigeriaJustice.AI.

This module defines the API endpoints for court transcription services,
including real-time transcription, speaker identification, and transcript
management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, List, Optional
import logging
import os
import json
from datetime import datetime
import uuid

from app.services.transcription import TranscriptionService
from app.services.identity_verification import IdentityVerificationService
from app.core.security import get_current_user, verify_court_role
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
transcription_service = TranscriptionService(
    model_path=settings.TRANSCRIPTION_MODEL_PATH,
    speaker_model_path=settings.SPEAKER_MODEL_PATH
)

identity_service = IdentityVerificationService(
    config_path=settings.IDENTITY_CONFIG_PATH
)

@router.post("/real-time", response_model=Dict)
async def transcribe_real_time(
    audio_file: UploadFile = File(...),
    session_metadata: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    authorized: bool = Depends(verify_court_role(["judge", "stenographer", "clerk"]))
):
    """
    Transcribe a real-time audio segment from court proceedings.
    
    Args:
        audio_file: Audio data from the court proceeding
        session_metadata: Metadata about the court session
        
    Returns:
        Transcription results
    """
    if not authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access real-time transcription"
        )
    
    try:
        # Read audio data
        audio_data = await audio_file.read()
        
        # Add additional metadata
        full_metadata = {
            **session_metadata,
            "timestamp": datetime.now().isoformat(),
            "user_id": current_user.get("id"),
            "user_role": current_user.get("role")
        }
        
        # Process the audio
        result = await transcription_service.transcribe_audio(
            audio_data=audio_data,
            metadata=full_metadata
        )
        
        logger.info(f"Successfully transcribed audio segment for session {session_metadata.get('session_id')}")
        return result
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/identify-speaker", response_model=Dict)
async def identify_speaker(
    audio_file: UploadFile = File(...),
    known_speakers: List[Dict] = Body(...),
    current_user: Dict = Depends(get_current_user),
    authorized: bool = Depends(verify_court_role(["judge", "stenographer", "clerk"]))
):
    """
    Identify the speaker in an audio segment.
    
    Args:
        audio_file: Audio segment containing speech from a single speaker
        known_speakers: List of known speakers with voice embeddings
        
    Returns:
        Speaker identification results
    """
    if not authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to identify speakers"
        )
    
    try:
        # Read audio data
        audio_data = await audio_file.read()
        
        # Identify the speaker
        result = await transcription_service.identify_speaker(
            audio_segment=audio_data,
            known_speakers=known_speakers
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Speaker not identified")
        
        logger.info(f"Successfully identified speaker: {result.get('id')}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error identifying speaker: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/anonymize", response_model=Dict)
async def anonymize_transcript(
    transcript: str = Body(..., embed=True),
    entities_to_anonymize: List[str] = Body(...),
    current_user: Dict = Depends(get_current_user),
    authorized: bool = Depends(verify_court_role(["judge", "stenographer", "clerk"]))
):
    """
    Anonymize sensitive information in a transcript.
    
    Args:
        transcript: The transcript text to anonymize
        entities_to_anonymize: List of entity types to anonymize
        
    Returns:
        Anonymized transcript
    """
    if not authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to anonymize transcripts"
        )
    
    try:
        # Anonymize the transcript
        anonymized = await transcription_service.anonymize_transcript(
            transcript=transcript,
            entities_to_anonymize=entities_to_anonymize
        )
        
        logger.info(f"Successfully anonymized transcript with {len(entities_to_anonymize)} entity types")
        return {"anonymized_transcript": anonymized}
    
    except Exception as e:
        logger.error(f"Error anonymizing transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save", response_model=Dict)
async def save_transcript(
    transcript_data: Dict = Body(...),
    output_format: str = Body("json"),
    current_user: Dict = Depends(get_current_user),
    authorized: bool = Depends(verify_court_role(["judge", "stenographer", "clerk"]))
):
    """
    Save a transcript to file.
    
    Args:
        transcript_data: Transcript data to save
        output_format: Format to save in ("json", "txt", "docx")
        
    Returns:
        Path to the saved file
    """
    if not authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to save transcripts"
        )
    
    try:
        # Add metadata
        full_transcript_data = {
            **transcript_data,
            "saved_by": current_user.get("id"),
            "saved_at": datetime.now().isoformat()
        }
        
        # Save the transcript
        output_path = await transcription_service.save_transcript(
            transcript_data=full_transcript_data,
            output_format=output_format
        )
        
        logger.info(f"Successfully saved transcript to {output_path}")
        return {"file_path": output_path}
    
    except Exception as e:
        logger.error(f"Error saving transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-full-audio", response_model=Dict)
async def process_full_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    case_metadata: Dict = Body(...),
    current_user: Dict = Depends(get_current_user),
    authorized: bool = Depends(verify_court_role(["judge", "stenographer", "clerk"]))
):
    """
    Process a full audio recording of a court session.
    
    This endpoint handles larger audio files asynchronously in the background.
    
    Args:
        audio_file: Full audio recording of a court session
        case_metadata: Metadata about the case and session
        
    Returns:
        Job ID for tracking the processing status
    """
    if not authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to upload full audio recordings"
        )
    
    try:
        # Generate a job ID
        job_id = str(uuid.uuid4())
        
        # Create directory for the job if it doesn't exist
        job_dir = f"uploads/transcription_jobs/{job_id}"
        os.makedirs(job_dir, exist_ok=True)
        
        # Save the audio file
        audio_path = f"{job_dir}/audio.wav"
        with open(audio_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Save metadata
        metadata_path = f"{job_dir}/metadata.json"
        with open(metadata_path, "w") as f:
            json.dump({
                **case_metadata,
                "job_id": job_id,
                "submitted_by": current_user.get("id"),
                "submitted_at": datetime.now().isoformat(),
                "status": "pending"
            }, f)
        
        # TODO: Add background task for processing the audio file
        # background_tasks.add_task(process_audio_job, job_id, audio_path, metadata_path)
        
        logger.info(f"Submitted full audio processing job {job_id}")
        return {
            "job_id": job_id,
            "status": "pending",
            "estimated_completion_time": "15 minutes"
        }
    
    except Exception as e:
        logger.error(f"Error submitting full audio processing job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}", response_model=Dict)
async def get_job_status(
    job_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the status of a transcription job.
    
    Args:
        job_id: ID of the transcription job
        
    Returns:
        Status of the job
    """
    try:
        # Check if job exists
        job_dir = f"uploads/transcription_jobs/{job_id}"
        if not os.path.exists(job_dir):
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Read metadata
        metadata_path = f"{job_dir}/metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Check if user has access to this job
        if current_user.get("role") not in ["admin", "judge"] and metadata.get("submitted_by") != current_user.get("id"):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this job"
            )
        
        # Return job status
        return {
            "job_id": job_id,
            "status": metadata.get("status", "unknown"),
            "progress": metadata.get("progress", 0),
            "submitted_at": metadata.get("submitted_at"),
            "completed_at": metadata.get("completed_at"),
            "result_available": os.path.exists(f"{job_dir}/transcript.json")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}/result", response_model=Dict)
async def get_job_result(
    job_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the result of a completed transcription job.
    
    Args:
        job_id: ID of the transcription job
        
    Returns:
        Transcription result
    """
    try:
        # Check if job exists
        job_dir = f"uploads/transcription_jobs/{job_id}"
        if not os.path.exists(job_dir):
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Read metadata
        metadata_path = f"{job_dir}/metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Check if user has access to this job
        if current_user.get("role") not in ["admin", "judge"] and metadata.get("submitted_by") != current_user.get("id"):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this job"
            )
        
        # Check if job is completed
        if metadata.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job is not completed. Current status: {metadata.get('status')}"
            )
        
        # Check if result exists
        result_path = f"{job_dir}/transcript.json"
        if not os.path.exists(result_path):
            raise HTTPException(
                status_code=404,
                detail="Result not found"
            )
        
        # Read and return result
        with open(result_path, "r") as f:
            result = json.load(f)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job result: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/job/{job_id}", response_model=Dict)
async def delete_job(
    job_id: str,
    current_user: Dict = Depends(get_current_user),
    authorized: bool = Depends(verify_court_role(["admin", "judge"]))
):
    """
    Delete a transcription job.
    
    Args:
        job_id: ID of the transcription job
        
    Returns:
        Success message
    """
    if not authorized:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to delete transcription jobs"
        )
    
    try:
        # Check if job exists
        job_dir = f"uploads/transcription_jobs/{job_id}"
        if not os.path.exists(job_dir):
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Read metadata
        metadata_path = f"{job_dir}/metadata.json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Check if user has access to delete this job
        if current_user.get("role") != "admin" and metadata.get("submitted_by") != current_user.get("id"):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete this job"
            )
        
        # Delete job files
        import shutil
        shutil.rmtree(job_dir)
        
        logger.info(f"Deleted transcription job {job_id}")
        return {"message": "Job deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
