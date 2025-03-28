"""
Anonymization Service for NigeriaJustice.AI

This module provides functionality for anonymizing sensitive information
in court documents, transcripts, and case files to protect the identity
of defendants, victims, witnesses, and minors.
"""

import logging
import re
from typing import Dict, List, Set, Tuple, Optional, Pattern
import json
import os
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class AnonymizationService:
    """
    Service for anonymizing sensitive information in text content.
    
    This service identifies and redacts entities like names, addresses, phone numbers,
    and other personally identifiable information (PII) from court documents.
    """
    
    def __init__(self, entities_config_path: str = None):
        """
        Initialize the anonymization service.
        
        Args:
            entities_config_path: Path to configuration file with entity patterns
        """
        self.entities_config_path = entities_config_path
        self.entity_patterns = {}
        self.default_entities = ["DEFENDANT", "VICTIM", "WITNESS", "MINOR"]
        
        # Load entity patterns from configuration
        self._initialize_entity_patterns()
        
        logger.info("Anonymization service initialized")
    
    def _initialize_entity_patterns(self):
        """Initialize entity recognition patterns from configuration"""
        # Load from config file if provided
        if self.entities_config_path and os.path.exists(self.entities_config_path):
            try:
                with open(self.entities_config_path, 'r') as f:
                    self.entity_patterns = json.load(f)
                logger.info(f"Loaded entity patterns from {self.entities_config_path}")
            except Exception as e:
                logger.error(f"Failed to load entity patterns: {e}")
                self._initialize_default_patterns()
        else:
            self._initialize_default_patterns()
    
    def _initialize_default_patterns(self):
        """Initialize default entity recognition patterns"""
        # Default patterns for common PII
        self.entity_patterns = {
            "DEFENDANT": [
                r"\b(?:defendant|accused|perpetrator|suspect)\b",
                # Add commonly used Nigerian names patterns
                r"\b(?:Adebayo|Chukwu|Mohammed|Oluwaseun|Ibrahim)\b"
            ],
            "VICTIM": [
                r"\b(?:victim|complainant|injured party)\b",
                # Add commonly used Nigerian names patterns
                r"\b(?:Adesola|Chioma|Ahmed|Oluwafemi|Fatima)\b"
            ],
            "WITNESS": [
                r"\b(?:witness|eyewitness|bystander)\b",
                r"\b(?:first|second|third|fourth|fifth) witness\b",
                r"\b(?:prosecution|defense) witness\b"
            ],
            "MINOR": [
                r"\b(?:child|minor|juvenile|underage)\b",
                r"\b(?:boy|girl|teenager|infant|baby)\b"
            ],
            "ADDRESS": [
                r"\b\d+\s+[A-Za-z]+\s+(?:Street|Avenue|Road|Lane|Drive|Close|Crescent)\b",
                r"\b(?:Estate|Compound|Quarters)\b"
            ],
            "PHONE": [
                r"\b(?:\+234|0)\d{10}\b",  # Nigerian phone numbers
                r"\b\d{4}[-\s]?\d{3}[-\s]?\d{4}\b"
            ],
            "EMAIL": [
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            ],
            "NIN": [
                r"\b\d{11}\b"  # NIN is 11 digits
            ],
            "PASSPORT": [
                r"\b[A-Z]\d{8}\b"  # Nigerian passport format
            ]
        }
    
    def anonymize_text(self, text: str, entities_to_anonymize: List[str] = None) -> str:
        """
        Anonymize sensitive information in text.
        
        Args:
            text: The text to anonymize
            entities_to_anonymize: List of entity types to anonymize
                                   (defaults to DEFENDANT, VICTIM, WITNESS, MINOR)
            
        Returns:
            Anonymized text
        """
        if not text:
            return text
            
        # Use default entities if none specified
        if not entities_to_anonymize:
            entities_to_anonymize = self.default_entities
        
        logger.info(f"Anonymizing text with entity types: {entities_to_anonymize}")
        
        # Track all replacements to ensure consistency (same entity gets same replacement)
        replacements = {}
        anonymized_text = text
        
        # Process each entity type
        for entity_type in entities_to_anonymize:
            if entity_type not in self.entity_patterns:
                logger.warning(f"Unknown entity type: {entity_type}")
                continue
            
            # Get patterns for this entity type
            patterns = self.entity_patterns[entity_type]
            
            # Apply each pattern
            for pattern in patterns:
                # Find all matches
                matches = re.finditer(pattern, anonymized_text, re.IGNORECASE)
                
                # Replace each match
                for match in matches:
                    original = match.group(0)
                    
                    # If we've seen this text before, use the same replacement
                    if original in replacements:
                        replacement = replacements[original]
                    else:
                        # Otherwise, create a new replacement
                        replacement = f"[REDACTED-{entity_type}]"
                        replacements[original] = replacement
                    
                    # Replace in the text (preserve case)
                    anonymized_text = anonymized_text.replace(original, replacement)
        
        return anonymized_text
    
    def anonymize_document(self, document: Dict, entities_to_anonymize: List[str] = None,
                           text_fields: List[str] = None) -> Dict:
        """
        Anonymize sensitive information in a document structure.
        
        Args:
            document: Document dictionary to anonymize
            entities_to_anonymize: List of entity types to anonymize
            text_fields: List of fields containing text to anonymize
                        (defaults to ["content", "text", "description", "notes"])
            
        Returns:
            Anonymized document
        """
        if not document:
            return document
            
        # Use default text fields if none specified
        if not text_fields:
            text_fields = ["content", "text", "description", "notes", "statement", "testimony"]
        
        # Use default entities if none specified
        if not entities_to_anonymize:
            entities_to_anonymize = self.default_entities
        
        logger.info(f"Anonymizing document with entity types: {entities_to_anonymize}")
        
        # Create a deep copy to avoid modifying the original
        anonymized_doc = json.loads(json
