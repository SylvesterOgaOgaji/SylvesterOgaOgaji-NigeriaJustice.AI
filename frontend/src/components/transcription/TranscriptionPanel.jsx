/**
 * TranscriptionPanel Component
 * 
 * A real-time court transcription panel that displays transcriptions
 * with speaker identification and manages audio recording.
 */

import React, { useState, useEffect, useRef } from 'react';
import SpeakerIdentification from './SpeakerIdentification';
import { useAuth } from '../../hooks/useAuth';
import api from '../../services/api';
import { formatTimestamp, playAudioBeep } from '../../utils/helpers';
import './TranscriptionPanel.css';

const TranscriptionPanel = ({ 
  sessionId, 
  caseId, 
  language = 'en-NG',
  courtRoom = 'FCT High Court 5',
  knownSpeakers = []
}) => {
  const [transcript, setTranscript] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [currentSpeaker, setCurrentSpeaker] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState(null);
  const [audioPermission, setAudioPermission] = useState(false);
  
  const { user } = useAuth();
  const transcriptEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  
  // Scroll to bottom of transcript
  const scrollToBottom = () => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  // Initialize audio permissions and setup
  useEffect(() => {
    const initializeAudio = async () => {
      try {
        // Request microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setAudioPermission(true);
        
        // Setup media recorder
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        
        // Handle data available event
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
            handleAudioData();
          }
        };
        
        // Handle recording stopped
        mediaRecorder.onstop = () => {
          console.log('Recording stopped');
        };
        
        // Handle recording errors
        mediaRecorder.onerror = (event) => {
          console.error('Media recorder error:', event.error);
          setError('Error with audio recording device.');
          setIsRecording(false);
        };
        
      } catch (err) {
        console.error('Error accessing microphone:', err);
        setError('Unable to access microphone. Please check permissions.');
        setAudioPermission(false);
      }
    };
    
    initializeAudio();
    
    // Cleanup on unmount
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);
  
  // Scroll transcript to bottom when updated
  useEffect(() => {
    scrollToBottom();
  }, [transcript]);
  
  // Handle recording time counter
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prevTime => prevTime + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording]);
  
  // Process audio chunks and send to API
  const handleAudioData = async () => {
    try {
      if (audioChunksRef.current.length === 0) return;
      
      // Create blob from chunks
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      audioChunksRef.current = [];
      
      // Create form data
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      
      // Add metadata
      const metadata = {
        session_id: sessionId,
        case_id: caseId,
        timestamp: new Date().toISOString(),
        court_role: currentSpeaker?.role || 'unknown',
        language: language,
        court_room: courtRoom,
        known_speakers: knownSpeakers
      };
      
      formData.append('session_metadata', JSON.stringify(metadata));
      
      // Send to API
      const response
