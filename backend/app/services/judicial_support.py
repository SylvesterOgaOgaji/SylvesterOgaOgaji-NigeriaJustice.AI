"""
Judicial Decision Support Service for NigeriaJustice.AI

This module provides AI-powered decision support for judges by analyzing
case details, finding relevant precedents, and suggesting potential
judicial outcomes based on Nigerian law and previous similar cases.
"""

import logging
import json
import os
from typing import Dict, List, Optional, Tuple, Any
import re
from datetime import datetime
import random
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

class PrecedentMatch(BaseModel):
    """Model for a matching legal precedent"""
    case_number: str
    case_title: str
    court: str
    date: str
    citation: str
    relevance_score: float
    key_points: List[str]
    summary: str
    holding: str
    category: str
    judge: Optional[str] = None

class RecommendationModel(BaseModel):
    """Model for a judicial recommendation"""
    recommendation_type: str
    description: str
    justification: str
    confidence_score: float
    based_on: List[str]
    alternative_considerations: Optional[List[str]] = None
    caveats: Optional[List[str]] = None
    legal_references: Optional[List[str]] = None

class JudicialSupportService:
    """
    Service for providing AI-powered decision support to judges.
    
    This service analyzes case details, finds relevant precedents,
    and suggests potential judicial outcomes based on Nigerian law
    and previous similar cases.
    """
    
    def __init__(self, precedent_db_path: str = None, legal_model_path: str = None):
        """
        Initialize the judicial support service.
        
        Args:
            precedent_db_path: Path to the legal precedent database
            legal_model_path: Path to the legal NLP model
        """
        self.precedent_db_path = precedent_db_path or os.path.join(
            "data", "precedents", "nigerian_legal_precedents.json"
        )
        self.legal_model_path = legal_model_path or settings.NLP_MODEL_PATH
        self.precedents_db = {}
        self.statutes_db = {}
        
        # Load precedent database
        self._load_precedent_database()
        
        # Load statutes database
        self._load_statutes_database()
        
        logger.info("Judicial Support Service initialized")
    
    def _load_precedent_database(self):
        """Load legal precedent database from file"""
        try:
            if os.path.exists(self.precedent_db_path):
                with open(self.precedent_db_path, 'r') as f:
                    self.precedents_db = json.load(f)
                logger.info(f"Loaded {len(self.precedents_db.get('cases', []))} legal precedents")
            else:
                logger.warning(f"Precedent database not found: {self.precedent_db_path}")
                # Initialize with a minimal set of mock precedents for development
                self._initialize_mock_precedents()
        except Exception as e:
            logger.error(f"Error loading precedent database: {e}")
            self._initialize_mock_precedents()
    
    def _load_statutes_database(self):
        """Load Nigerian statutes database from file"""
        statutes_path = os.path.join(os.path.dirname(self.precedent_db_path), "nigerian_statutes.json")
        try:
            if os.path.exists(statutes_path):
                with open(statutes_path, 'r') as f:
                    self.statutes_db = json.load(f)
                logger.info(f"Loaded {len(self.statutes_db.get('statutes', []))} Nigerian statutes")
            else:
                logger.warning(f"Statutes database not found: {statutes_path}")
                # Initialize with a minimal set of mock statutes for development
                self._initialize_mock_statutes()
        except Exception as e:
            logger.error(f"Error loading statutes database: {e}")
            self._initialize_mock_statutes()
    
    def _initialize_mock_precedents(self):
        """Initialize a minimal set of mock precedents for development"""
        self.precedents_db = {
            "metadata": {
                "source": "Mock Database for Development",
                "version": "0.1",
                "last_updated": datetime.now().isoformat()
            },
            "cases": [
                {
                    "case_number": "SC.123/2019",
                    "case_title": "Federal Republic of Nigeria v. John Doe",
                    "court": "Supreme Court of Nigeria",
                    "date": "2019-05-15",
                    "citation": "(2019) LPELR-12345",
                    "category": "Criminal Law",
                    "subcategory": ["Fraud", "Corruption"],
                    "judge": "Hon. Justice Ibrahim Tanko Muhammad, CJN",
                    "summary": "Case involving government fraud and misappropriation of public funds.",
                    "facts": "The defendant was accused of misappropriating N500 million in public funds while serving as a government official.",
                    "issues": [
                        "Whether the prosecution proved the case beyond reasonable doubt",
                        "Whether the funds in question were actually misappropriated"
                    ],
                    "holding": "The Supreme Court upheld the conviction, finding that the prosecution had successfully established all elements of the offense beyond reasonable doubt.",
                    "reasoning": "The Court found that documentary evidence and witness testimony clearly established the defendant's guilt.",
                    "key_points": [
                        "Proof beyond reasonable doubt established through documentary evidence",
                        "Public officials have a fiduciary duty to manage public funds appropriately",
                        "Intent can be inferred from pattern of transactions"
                    ],
                    "statutes_cited": ["Criminal Code Act", "Economic and Financial Crimes Commission Act"],
                    "precedents_cited": ["FRN v. James Ibori", "FRN v. Olabode George"]
                },
                {
                    "case_number": "SC.456/2020",
                    "case_title": "Chidinma Okeke v. Sunshine Properties Ltd",
                    "court": "Supreme Court of Nigeria",
                    "date": "2020-11-23",
                    "citation": "(2020) LPELR-23456",
                    "category": "Property Law",
                    "subcategory": ["Land Dispute", "Certificate of Occupancy"],
                    "judge": "Hon. Justice Kudirat Kekere-Ekun, JSC",
                    "summary": "Dispute over rightful ownership of land with competing certificates of occupancy.",
                    "facts": "The appellant and respondent both claimed ownership of the same piece of land, with both parties possessing seemingly valid certificates of occupancy.",
                    "issues": [
                        "Which certificate of occupancy takes precedence",
                        "Whether the governor has the power to revoke a certificate of occupancy and issue a new one for the same land"
                    ],
                    "holding": "The Supreme Court held that the earlier certificate of occupancy takes precedence when there is no evidence of proper revocation.",
                    "reasoning": "The Court found that the power of the governor to revoke a certificate of occupancy must be exercised in strict compliance with the Land Use Act.",
                    "key_points": [
                        "First in time principle applies to certificates of occupancy",
                        "Revocation of certificate of occupancy must follow due process",
                        "Notice of revocation must be properly served on the holder"
                    ],
                    "statutes_cited": ["Land Use Act", "Evidence Act"],
                    "precedents_cited": ["Ogunleye v. Oni", "Savannah Bank v. Ajilo"]
                },
                {
                    "case_number": "CA/L/789/2021",
                    "case_title": "Zenith Bank PLC v. Emeka Enterprises Ltd",
                    "court": "Court of Appeal, Lagos Division",
                    "date": "2021-07-10",
                    "citation": "(2021) LPELR-34567",
                    "category": "Commercial Law",
                    "subcategory": ["Banking", "Debt Recovery"],
                    "judge": "Hon. Justice Joseph Ikyegh, JCA",
                    "summary": "Dispute over loan repayment and alleged breach of loan agreement.",
                    "facts": "The appellant bank sought to recover a loan from the respondent company, which had defaulted on repayments. The respondent claimed that the bank had unilaterally increased interest rates contrary to the loan agreement.",
                    "issues": [
                        "Whether the bank could unilaterally increase interest rates",
                        "Whether the customer was properly notified of changes to the loan terms"
                    ],
                    "holding": "The Court of Appeal held that banks cannot unilaterally increase interest rates without proper notice and agreement by the customer.",
                    "reasoning": "The Court found that the principle of freedom of contract requires mutual consent for any variation of contract terms.",
                    "key_points": [
                        "Banks cannot unilaterally alter fundamental terms of loan agreements",
                        "Proper notice of changes to loan terms is essential",
                        "Banking regulations require transparency in customer dealings"
                    ],
                    "statutes_cited": ["Central Bank of Nigeria Act", "Banks and Other Financial Institutions Act"],
                    "precedents_cited": ["UBA v. Tejumola & Sons", "First Bank v. Afribank"]
                }
            ]
        }
        logger.info("Initialized mock precedent database with 3 sample cases")
    
    def _initialize_mock_statutes(self):
        """Initialize a minimal set of mock statutes for development"""
        self.statutes_db = {
            "metadata": {
                "source": "Mock Database for Development",
                "version": "0.1",
                "last_updated": datetime.now().isoformat()
            },
            "statutes": [
                {
                    "name": "Criminal Code Act",
                    "citation": "Cap C38 Laws of the Federation of Nigeria 2004",
                    "date_enacted": "1916",
                    "date_last_amended": "2004",
                    "summary": "The Criminal Code Act is the primary criminal law statute applicable in Southern Nigeria.",
                    "sections": [
                        {
                            "section": "Section 383",
                            "title": "Definition of Stealing",
                            "content": "A person who fraudulently takes anything capable of being stolen, or fraudulently converts to his own use or to the use of any other person anything capable of being stolen, is said to steal that thing."
                        },
                        {
                            "section": "Section 419",
                            "title": "Obtaining Property by False Pretenses",
                            "content": "Any person who by any false pretence, and with intent to defraud, obtains from any other person anything capable of being stolen, or induces any other person to deliver to any person anything capable of being stolen, is guilty of a felony, and is liable to imprisonment for three years."
                        }
                    ]
                },
                {
                    "name": "Evidence Act",
                    "citation": "Evidence Act, 2011",
                    "date_enacted": "2011",
                    "date_last_amended": "2011",
                    "summary": "The Evidence Act governs the admissibility of evidence in Nigerian courts.",
                    "sections": [
                        {
                            "section": "Section 1",
                            "title": "Application",
                            "content": "This Act shall apply to all judicial proceedings in or before any court established in the Federal Republic of Nigeria but it shall not apply to proceedings before an arbitrator."
                        },
                        {
                            "section": "Section 39",
                            "title": "Admissibility of Documentary Evidence",
                            "content": "Subject to the provisions of this or any other Act, a document which is produced in evidence may be admissible notwithstanding that its execution or existence has not been proved."
                        }
                    ]
                },
                {
                    "name": "Land Use Act",
                    "citation": "Cap L5 Laws of the Federation of Nigeria 2004",
                    "date_enacted": "1978",
                    "date_last_amended": "2004",
                    "summary": "The Land Use Act vests all land in the territory of each state in the governor of that state, to be held in trust for the people.",
                    "sections": [
                        {
                            "section": "Section 1",
                            "title": "Vesting of Land in the Governor",
                            "content": "Subject to the provisions of this Act, all land comprised in the territory of each State in the Federation are hereby vested in the Governor of that State and such land shall be held in trust and administered for the use and common benefit of all Nigerians in accordance with the provisions of this Act."
                        },
                        {
                            "section": "Section 28",
                            "title": "Power of Governor to Revoke Rights of Occupancy",
                            "content": "The Governor may revoke a right of occupancy for overriding public interest."
                        }
                    ]
                }
            ]
        }
        logger.info("Initialized mock statutes database with 3 sample statutes")
    
    async def find_relevant_precedents(self, case_details: Dict, limit: int = 5) -> List[PrecedentMatch]:
        """
        Find legal precedents relevant to the current case.
        
        Args:
            case_details: Details of the current case
            limit: Maximum number of precedents to return
            
        Returns:
            List of relevant precedents with similarity scores
        """
        logger.info(f"Searching for precedents relevant to case {case_details.get('case_number', 'unknown')}")
        
        # In a production system, this would use sophisticated NLP and vector similarity search
        # For now, we'll implement a simple keyword-based search for demonstration
        
        # Extract key information from the case
        case_type = case_details.get("case_type", "")
        charges = case_details.get("charges", [])
        facts = case_details.get("facts", "")
        keywords = case_details.get("keywords", [])
        
        # Combine all searchable text
        search_text = f"{case_type} {' '.join(charges)} {facts} {' '.join(keywords)}".lower()
        
        # Create a simplified search function for demonstration
        def calculate_relevance(precedent: Dict) -> float:
            relevance = 0.0
            
            # Check category match
            if precedent.get("category", "").lower() == case_type.lower():
                relevance += 0.3
            
            # Check subcategory/charges match
            subcategories = [s.lower() for s in precedent.get("subcategory", [])]
            for charge in charges:
                if charge.lower() in subcategories:
                    relevance += 0.2
            
            # Check keyword matches in summary and facts
            precedent_text = f"{precedent.get('summary', '')} {precedent.get('facts', '')}".lower()
            for keyword in keywords:
                if keyword.lower() in precedent_text:
                    relevance += 0.1
            
            # Add some randomness for demonstration
            relevance += random.uniform(0, 0.2)
            
            # Cap at 0.99
            return min(relevance, 0.99)
        
        # Get all precedents
        all_precedents = self.precedents_db.get("cases", [])
        
        # Calculate relevance scores
        precedents_with_scores = []
        for precedent in all_precedents:
            relevance = calculate_relevance(precedent)
            if relevance > 0.3:  # Only include somewhat relevant precedents
                precedents_with_scores.append((precedent, relevance))
        
        # Sort by relevance and limit results
        precedents_with_scores.sort(key=lambda x: x[1], reverse=True)
        top_precedents = precedents_with_scores[:limit]
        
        # Format results
        results = []
        for precedent, score in top_precedents:
            results.append(PrecedentMatch(
                case_number=precedent.get("case_number", ""),
                case_title=precedent.get("case_title", ""),
                court=precedent.get("court", ""),
                date=precedent.get("date", ""),
                citation=precedent.get("citation", ""),
                relevance_score=score,
                key_points=precedent.get("key_points", []),
                summary=precedent.get("summary", ""),
                holding=precedent.get("holding", ""),
                category=precedent.get("category", ""),
                judge=precedent.get("judge")
            ))
        
        logger.info(f"Found {len(results)} relevant precedents")
        return results
    
    async def find_applicable_statutes(self, case_details: Dict, limit: int = 5) -> List[Dict]:
        """
        Find statutes applicable to the current case.
        
        Args:
            case_details: Details of the current case
            limit: Maximum number of statutes to return
            
        Returns:
            List of applicable statutes with relevant sections
        """
        logger.info(f"Searching for statutes applicable to case {case_details.get('case_number', 'unknown')}")
        
        # Extract key information from the case
        case_type = case_details.get("case_type", "")
        charges = case_details.get("charges", [])
        facts = case_details.get("facts", "")
        keywords = case_details.get("keywords", [])
        
        # Combine all searchable text
        search_text = f"{case_type} {' '.join(charges)} {facts} {' '.join(keywords)}".lower()
        
        # Get all statutes
        all_statutes = self.statutes_db.get("statutes", [])
        
        # Simple matching function for demonstration
        def is_relevant_statute(statute: Dict) -> bool:
            statute_name = statute.get("name", "").lower()
            statute_summary = statute.get("summary", "").lower()
            
            # Check if case type or charges mention the statute
            if case_type.lower() in statute_name or case_type.lower() in statute_summary:
                return True
                
            for charge in charges:
                if charge.lower() in statute_name or charge.lower() in statute_summary:
                    return True
            
            # Check for keyword matches
            for keyword in keywords:
                if keyword.lower() in statute_name or keyword.lower() in statute_summary:
                    return True
            
            return False
        
        # Find relevant statutes
        relevant_statutes = []
        for statute in all_statutes:
            if is_relevant_statute(statute):
                # Find relevant sections
                relevant_sections = []
                for section in statute.get("sections", []):
                    section_content = section.get("content", "").lower()
                    section_title = section.get("title", "").lower()
                    
                    # Check if section is relevant
                    is_relevant = False
                    for keyword in keywords:
                        if keyword.lower() in section_content or keyword.lower() in section_title:
                            is_relevant = True
                            break
                    
                    if is_relevant:
                        relevant_sections.append(section)
                
                # Include statute if it has relevant sections
                if relevant_sections:
                    relevant_statutes.append({
                        "name": statute.get("name", ""),
                        "citation": statute.get("citation", ""),
                        "summary": statute.get("summary", ""),
                        "relevant_sections": relevant_sections
                    })
        
        # Sort by number of relevant sections (more is better)
        relevant_statutes.sort(key=lambda x: len(x.get("relevant_sections", [])), reverse=True)
        
        logger.info(f"Found {len(relevant_statutes[:limit])} applicable statutes")
        return relevant_statutes[:limit]
    
    async def get_decision_recommendations(self, case_details: Dict) -> List[RecommendationModel]:
        """
        Generate judicial decision recommendations based on case details and precedents.
        
        Args:
            case_details: Details of the current case
            
        Returns:
            List of decision recommendations
        """
        logger.info(f"Generating decision recommendations for case {case_details.get('case_number', 'unknown')}")
        
        # Find relevant precedents
        precedents = await self.find_relevant_precedents(case_details)
        
        # Find applicable statutes
        statutes = await self.find_applicable_statutes(case_details)
        
        # In a production system, this would use an advanced legal reasoning model
        # For demonstration, we'll generate simple recommendations based on precedents and statutes
        
        recommendations = []
        
        # Extract case type
        case_type = case_details.get("case_type", "").lower()
        
        # Generate different types of recommendations based on case type
        if "criminal" in case_type:
            # Criminal case recommendations
            recommendations.append(self._generate_criminal_recommendation(case_details, precedents, statutes))
        elif "civil" in case_type or "land" in case_type or "property" in case_type:
            # Civil case recommendations
            recommendations.append(self._generate_civil_recommendation(case_details, precedents, statutes))
        elif "commercial" in case_type or "contract" in case_type:
            # Commercial case recommendations
            recommendations.append(self._generate_commercial_recommendation(case_details, precedents, statutes))
        
        # Add procedural recommendations for all case types
        recommendations.append(self._generate_procedural_recommendation(case_details))
        
        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _generate_criminal_recommendation(self, case_details: Dict, 
                                         precedents: List[PrecedentMatch],
                                         statutes: List[Dict]) -> RecommendationModel:
        """Generate recommendation for criminal cases"""
        # For development purposes, we'll create a template recommendation
        
        # Extract key precedent information
        precedent_citations = [p.case_title for p in precedents[:2]]
        precedent_holdings = [p.holding for p in precedents[:2]]
        
        # Extract key statute information
        statute_references = []
        for statute in statutes:
            for section in statute.get("relevant_sections", [])[:2]:
                statute_references.append(f"{statute['name']} {section.get('section', '')}")
        
        # Create recommendation
        return RecommendationModel(
            recommendation_type="Criminal Case Decision",
            description="Consider the elements of the offense and the standard of proof",
            justification=("Based on similar precedents, the court should carefully evaluate whether "
                          "all elements of the alleged offense have been proven beyond reasonable doubt. "
                          "The evidence presented should be scrutinized for reliability and consistency."),
            confidence_score=0.85,
            based_on=precedent_citations + statute_references,
            alternative_considerations=[
                "Consider mitigating factors if guilt is established",
                "Evaluate the credibility of witness testimony"
            ],
            caveats=[
                "This recommendation is based on limited case information",
                "The court should consider any unique circumstances not captured in the case summary"
            ],
            legal_references=precedent_holdings
        )
    
    def _generate_civil_recommendation(self, case_details: Dict, 
                                      precedents: List[PrecedentMatch],
                                      statutes: List[Dict]) -> RecommendationModel:
        """Generate recommendation for civil cases"""
        # For development purposes, we'll create a template recommendation
        
        # Extract key precedent information
        precedent_citations = [p.case_title for p in precedents[:2]]
        precedent_holdings = [p.holding for p in precedents[:2]]
        
        # Extract key statute information
        statute_references = []
        for statute in statutes:
            for section in statute.get("relevant_sections", [])[:2]:
                statute_references.append(f"{statute['name']} {section.get('section', '')}")
        
        # Create recommendation
        return RecommendationModel(
            recommendation_type="Civil Case Decision",
            description="Evaluate preponderance of evidence and applicable legal principles",
            justification=("Based on similar precedents, the court should determine which party has presented "
                          "more convincing evidence and arguments. The applicable legal principles from "
                          "precedent cases should guide the interpretation of the current dispute."),
            confidence_score=0.78,
            based_on=precedent_citations + statute_references,
            alternative_considerations=[
                "Consider equitable remedies if appropriate",
                "Evaluate potential for settlement or alternative dispute resolution"
            ],
            caveats=[
                "This recommendation is based on limited case information",
                "The court should consider any unique circumstances not captured in the case summary"
            ],
            legal_references=precedent_holdings
        )
    
    def _generate_commercial_recommendation(self, case_details: Dict, 
                                           precedents: List[PrecedentMatch],
                                           statutes: List[Dict]) -> RecommendationModel:
        """Generate recommendation for commercial cases"""
        # For development purposes, we'll create a template recommendation
        
        # Extract key precedent information
        precedent_citations = [p.case_title for p in precedents[:2]]
        precedent_holdings = [p.holding for p in precedents[:2]]
        
        # Extract key statute information
        statute_references = []
        for statute in statutes:
            for section in statute.get("relevant_sections", [])[:2]:
                statute_references.append(f"{statute['name']} {section.get('section', '')}")
        
        # Create recommendation
        return RecommendationModel(
            recommendation_type="Commercial Case Decision",
            description="Evaluate contractual obligations and commercial practices",
            justification=("Based on similar precedents, the court should carefully interpret the contractual "
                          "terms and evaluate whether parties fulfilled their obligations. Industry standards "
                          "and commercial practices should be considered in the context of the dispute."),
            confidence_score=0.82,
            based_on=precedent_citations + statute_references,
            alternative_considerations=[
                "Consider the potential economic impact of the decision",
                "Evaluate whether specific performance or damages is the appropriate remedy"
            ],
            caveats=[
                "This recommendation is based on limited case information",
                "The court should consider any unique circumstances not captured in the case summary"
            ],
            legal_references=precedent_holdings
        )
    
    def _generate_procedural_recommendation(self, case_details: Dict) -> RecommendationModel:
        """Generate procedural recommendation applicable to all case types"""
        # For development purposes, we'll create a template recommendation
        
        return RecommendationModel(
            recommendation_type="Procedural Consideration",
            description="Ensure procedural fairness and due process",
            justification=("The court should ensure that all parties have had adequate opportunity to present "
                          "their case and that all procedural requirements have been satisfied. This includes "
                          "proper notice, opportunity to be heard, and adherence to court rules."),
            confidence_score=0.95,
            based_on=["Nigerian Constitution", "Court of Appeal Rules", "High Court Civil Procedure Rules"],
            alternative_considerations=[
                "Consider whether additional evidence or submissions are needed",
                "Evaluate whether any procedural irregularities have prejudiced either party"
            ],
            caveats=[
                "Procedural requirements may vary based on court jurisdiction and case type"
            ]
        )
    
    async def get_case_summary(self, case_details: Dict) -> Dict:
        """
        Generate a comprehensive summary of the case.
        
        Args:
            case_details: Details of the current case
            
        Returns:
            Summary of the case with key information highlighted
        """
        logger.info(f"Generating case summary for case {case_details.get('case_number', 'unknown')}")
        
        # In a production system, this would use advanced NLP to summarize the case
        # For demonstration, we'll create a structured summary from the available fields
        
        # Extract key information
        case_number = case_details.get("case_number", "Unknown")
        case_title = case_details.get("case_title", "Unknown")
        case_type = case_details.get("case_type", "Unknown")
        charges = case_details.get("charges", [])
        facts = case_details.get("facts", "No facts provided")
        plaintiff = case_details.get("plaintiff", "Unknown")
        defendant = case_details.get("defendant", "Unknown")
        court = case_details.get("court", "Unknown")
        judge = case_details.get("judge", "Unknown")
        filing_date = case_details.get("filing_date", "Unknown")
        status = case_details.get("status", "Unknown")
        
        # Create summary
        summary = {
            "case_identification": {
                "case_number": case_number,
                "case_title": case_title,
                "court": court,
                "judge": judge,
                "filing_date": filing_date,
                "status": status
            },
            "case_classification": {
                "case_type": case_type,
                "charges": charges
            },
            "parties": {
                "plaintiff": plaintiff,
                "defendant": defendant
            },
            "case_overview": {
                "summary": self._generate_brief_summary(case_details),
                "key_facts": self._extract_key_facts(facts),
                "legal_issues": self._identify_legal_issues(case_details)
            },
            "procedural_history": self._extract_procedural_history(case_details),
            "key_evidence": self._identify_key_evidence(case_details)
        }
        
        logger.info(f"Generated case summary for case {case_number}")
        return summary
    
    def _generate_brief_summary(self, case_details: Dict) -> str:
        """Generate a brief summary of the case"""
        case_type = case_details.get("case_type", "")
        plaintiff = case_details.get("plaintiff", "The plaintiff")
        defendant = case_details.get("defendant", "the defendant")
        charges = case_details.get("charges", [])
        
        if charges:
            charge_text = f"involving {', '.join(charges)}"
        else:
            charge_text = ""
        
        return f"This is a {case_type} case {charge_text} where {plaintiff} has brought action against {defendant}. {case_details.get('summary', '')}"
    
    def _extract_key_facts(self, facts: str) -> List[str]:
        """Extract key facts from the fact narrative"""
        # In a production system, this would use NLP to identify key facts
        # For demonstration, we'll split the text into sentences
        
        if not facts:
            return ["No facts available"]
        
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', facts)
        
        # Filter out very short sentences
        key_facts = [s for s in sentences if len(s) > 20]
        
        # Limit to 5 facts
        return key_facts[:5]
    
    def _identify_legal_issues(self, case_details: Dict) -> List[str]:
        """Identify key legal issues in the case"""
        # In a production system, this would analyze the case to identify legal issues
        # For demonstration, we'll use provided issues or generate generic ones
        
        issues = case_details.get("issues", [])
        if issues:
            return issues
        
        # Generate generic issues based on case type
        case_type = case_details.get("case_type", "").lower()
        
        if "criminal" in case_type:
            return [
                "Whether the prosecution has proven all elements of the offense beyond reasonable doubt",
                "Whether the evidence presented is admissible and sufficient",
                "Whether the defendant's rights were respected throughout the investigation and trial"
            ]
        elif "civil" in case_type or "land" in case_type or "property" in case_type:
            return [
                "Whether the plaintiff has established the legal elements of their claim",
                "Whether the defendant has valid defenses to the claim",
                "What remedies are appropriate if liability is established"
            ]
        elif "commercial" in case_type or "contract" in case_type:
            return [
                "Whether a valid contract existed between the parties",
                "Whether there was a breach of contractual obligations",
                "What damages or remedies are appropriate"
            ]
        else:
            return [
                "What legal principles apply to this case",
                "What factual determinations are necessary to resolve the dispute",
                "What remedies or penalties are appropriate"
            ]
    
    def _extract_procedural_history(self, case_details: Dict) -> List[Dict]:
        """Extract the procedural history of the case"""
        # In a production system, this would extract actual procedural history
        # For demonstration, we'll use provided history or generate a basic timeline
        
        history = case_details.get("procedural_history", [])
        if history:
            return history
        
        # Generate a basic timeline based on available dates
        timeline = []
        
        filing_date = case_details.get("filing_date")
        if filing_date:
            timeline.append({
                "date": filing_date,
                "event": "Case filed",
                "description": f"Case filed by {case_details.get('plaintiff', 'plaintiff')}"
            })
        
        arraignment_date = case_details.get("arraignment_date")
        if arraignment_date:
            timeline.append({
                "date": arraignment_date,
                "event": "Arraignment",
                "description": f"Defendant arraigned and pleaded {case_details.get('plea', 'not guilty')}"
            })
        
        hearing_dates = case_details.get("hearing_dates", [])
        for i, date in enumerate(hearing_dates):
            timeline.append({
                "date": date,
                "event": f"Hearing {i+1}",
                "description": "Court hearing"
            })
        
        # Sort by date
        timeline.sort(key=lambda x: x.get("date", ""))
        
        return timeline
    
    def _identify_key_evidence(self, case_details: Dict) -> List[Dict]:
        """Identify key evidence in the case"""
        # In a production system, this would analyze the case to identify key evidence
        # For demonstration, we'll use provided evidence or generate generic placeholders
        
        evidence = case_details.get("evidence", [])
        if evidence:
            return evidence
        
        # Generate generic evidence based on case type
        case_type = case_details.get("case_type", "").lower()
        
        if "criminal" in case_type:
            return [
                {"type": "Witness Testimony", "description": "Testimony from key witnesses"},
                {"type": "Documentary Evidence", "description": "Relevant documents supporting the charges"},
                {"type": "Expert Reports", "description": "Expert analysis and opinions"}
            ]
        elif "civil" in case_type or "land" in case_type:
            return [
                {"type": "Documentary Evidence", "description": "Contracts, agreements, or title documents"},
                {"type": "Witness Testimony", "description": "Testimony from relevant parties"},
                {"type": "Expert Reports", "description": "Expert opinions on property valuation or land surveys"}
            ]
        else:
            return [
                {"type": "Documentary Evidence", "description": "Relevant documents and records"},
                {"type": "Witness Testimony", "description": "Testimony from involved parties"},
                {"type": "Legal Precedents", "description": "Relevant previous judgments"}
            ]
    
    async def analyze_case_progress(self, case_details: Dict) -> Dict:
        """
        Analyze case progress and identify potential delays or issues.
        
        Args:
            case_details: Details of the current case
            
        Returns:
            Analysis of case progress with recommendations
        """
        logger.info(f"Analyzing case progress for case {case_details.get('case_number', 'unknown')}")
        
        # Extract timeline information
        filing_date = case_details.get("filing_date")
        current_date = datetime.now().strftime("%Y-%m-%d")
        status = case_details.get("status", "Unknown")
        procedural_history = self._extract_procedural_history(case_details)
        
        # Calculate case age
        case_age_days = 0
        if filing_date:
            try:
                filing_datetime = datetime.strptime(filing_date, "%Y-%m-%d")
                current_datetime = datetime.now()
                case_age_days = (current_datetime - filing_datetime).days
            except ValueError:
                logger.warning(f"Invalid filing date format: {filing_date}")
        
        # Identify delays
        delay_threshold_days = 90  # 3 months
        is_delayed = case_age_days > delay_threshold_days and status.lower() not in ["closed", "decided", "judgment delivered"]
        
        # Count hearings
        hearing_count = len([p for p in procedural_history if "hearing" in p.get("event", "").lower()])
        
        # Identify excessive adjournments
        adjournment_count = len([p for p in procedural_history if "adjourn" in p.get("event", "").lower()])
        excessive_adjournments = adjournment_count > 3
        
        # Analyze next steps
        next_steps = []
        if status.lower() == "awaiting judgment":
            next_steps.append("Deliver judgment")
        elif status.lower() == "awaiting hearing":
            next_steps.append("Conduct hearing")
        elif status.lower() == "awaiting witnesses":
            next_steps.append("Hear witness testimony")
        elif status.lower() == "awaiting evidence":
            next_steps.append("Receive and examine evidence")
        
        # Generate recommendations
        recommendations = []
        if is_delayed:
            recommendations.append("Prioritize this case to reduce backlog")
        if excessive_adjournments:
            recommendations.append("Consider limiting further adjournments")
        if case_age_days > 365:  # 1 year
            recommendations.append("Expedite proceedings due to case age")
        
        # Create analysis
        analysis = {
            "case_age": {
                "days": case_age_days,
                "months": case_age_days // 30,
                "years": case_age_days // 365
            },
            "status": status,
            "is_delayed": is_delayed,
            "hearing_count": hearing_count,
            "adjournment_count": adjournment_count,
            "excessive_adjournments": excessive_adjournments,
            "next_steps": next_steps,
            "recommendations": recommendations,
            "efficiency_rating": self._calculate_efficiency_rating(case_details),
            "estimated_completion": self._estimate_completion_time(case_details)
        }
        
        logger.info(f"Completed case progress analysis for case {case_details.get('case_number', 'unknown')}")
        return analysis
    
    def _calculate_efficiency_rating(self, case_details: Dict) -> Dict:
        """Calculate efficiency rating for the case"""
        # Extract timeline information
        filing_date = case_details.get("filing_date")
        current_date = datetime.now().strftime("%Y-%m-%d")
        status = case_details.get("status", "Unknown")
        procedural_history = self._extract_procedural_history(case_details)
        case_type = case_details.get("case_type", "").lower()
        
        # Calculate case age
        case_age_days = 0
        if filing_date:
            try:
                filing_datetime = datetime.strptime(filing_date, "%Y-%m-%d")
                current_datetime = datetime.now()
                case_age_days = (current_datetime - filing_datetime).days
            except ValueError:
                logger.warning(f"Invalid filing date format: {filing_date}")
        
        # Define expected duration based on case type
        expected_duration = 0
        if "criminal" in case_type:
            expected_duration = 365  # 1 year
        elif "civil" in case_type:
            expected_duration = 545  # 1.5 years
        elif "commercial" in case_type:
            expected_duration = 456  # 1.25 years
        else:
            expected_duration = 456  # Default: 1.25 years
        
        # Calculate efficiency score (lower is better)
        efficiency_score = 0
        if expected_duration > 0:
            efficiency_score = min(100, int((case_age_days / expected_duration) * 100))
        
        # Adjust for case status
        if status.lower() in ["closed", "decided", "judgment delivered"]:
            efficiency_score = min(100, efficiency_score)
        
        # Categorize efficiency
        efficiency_category = "Unknown"
        if efficiency_score < 33:
            efficiency_category = "High"
        elif efficiency_score < 66:
            efficiency_category = "Medium"
        else:
            efficiency_category = "Low"
        
        return {
            "score": efficiency_score,
            "category": efficiency_category,
            "expected_duration_days": expected_duration,
            "actual_duration_days": case_age_days
        }
    
    def _estimate_completion_time(self, case_details: Dict) -> Dict:
        """Estimate when the case might be completed"""
        # Extract timeline information
        filing_date = case_details.get("filing_date")
        current_date = datetime.now().strftime("%Y-%m-%d")
        status = case_details.get("status", "Unknown")
        procedural_history = self._extract_procedural_history(case_details)
        case_type = case_details.get("case_type", "").lower()
        
        # Calculate case age
        case_age_days = 0
        if filing_date:
            try:
                filing_datetime = datetime.strptime(filing_date, "%Y-%m-%d")
                current_datetime = datetime.now()
                case_age_days = (current_datetime - filing_datetime).days
            except ValueError:
                logger.warning(f"Invalid filing date format: {filing_date}")
        
        # Define expected total duration based on case type
        expected_total_duration = 0
        if "criminal" in case_type:
            expected_total_duration = 365  # 1 year
        elif "civil" in case_type:
            expected_total_duration = 545  # 1.5 years
        elif "commercial" in case_type:
            expected_total_duration = 456  # 1.25 years
        else:
            expected_total_duration = 456  # Default: 1.25 years
        
        # Estimate remaining time based on status
        remaining_days = 0
        if status.lower() in ["closed", "decided", "judgment delivered"]:
            remaining_days = 0
        elif status.lower() == "awaiting judgment":
            remaining_days = 30  # 1 month
        elif status.lower() == "awaiting closing arguments":
            remaining_days = 60  # 2 months
        elif status.lower() == "evidence presentation":
            remaining_days = 120  # 4 months
        elif status.lower() == "just filed" or status.lower() == "awaiting first hearing":
            remaining_days = expected_total_duration
        else:
            # Default: estimate based on expected duration and case age
            remaining_days = max(0, expected_total_duration - case_age_days)
        
        # Calculate estimated completion date
        estimated_completion_date = (datetime.now() + timedelta(days=remaining_days)).strftime("%Y-%m-%d")
        
        return {
            "estimated_completion_date": estimated_completion_date,
            "estimated_remaining_days": remaining_days,
            "confidence": "medium"  # This would be calculated based on more factors in a real system
        }
    
    async def get_judicial_workload_analytics(self, court_id: str, judge_id: Optional[str] = None) -> Dict:
        """
        Get analytics about judicial workload for a court or specific judge.
        
        Args:
            court_id: ID of the court
            judge_id: Optional ID of a specific judge
            
        Returns:
            Workload analytics
        """
        logger.info(f"Generating workload analytics for court {court_id}" + 
                   (f", judge {judge_id}" if judge_id else ""))
        
        # In a production system, this would query a database of cases
        # For demonstration, we'll generate mock data
        
        # Generate mock caseload data
        pending_cases = random.randint(50, 200)
        cases_filed_this_month = random.randint(10, 30)
        cases_resolved_this_month = random.randint(5, 25)
        average_case_age = random.randint(90, 365)
        
        # Generate case type distribution
        case_types = {
            "Criminal": random.randint(30, 50),
            "Civil": random.randint(20, 40),
            "Commercial": random.randint(10, 30),
            "Family": random.randint(5, 15),
            "Land": random.randint(5, 15)
        }
        
        # Generate monthly trend data
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        current_month = datetime.now().month - 1  # 0-indexed
        
        trend_data = []
        for i in range(12):
            month_index = (current_month - i) % 12
            trend_data.append({
                "month": months[month_index],
                "cases_filed": random.randint(10, 30),
                "cases_resolved": random.randint(5, 25),
                "pending_end_of_month": pending_cases + random.randint(-5, 10)
            })
        
        # Reverse to get chronological order
        trend_data.reverse()
        
        analytics = {
            "court_id": court_id,
            "judge_id": judge_id,
            "as_of_date": datetime.now().strftime("%Y-%m-%d"),
            "caseload_summary": {
                "pending_cases": pending_cases,
                "cases_filed_this_month": cases_filed_this_month,
                "cases_resolved_this_month": cases_resolved_this_month,
                "clearance_rate": round(cases_resolved_this_month / max(cases_filed_this_month, 1), 2),
                "average_case_age_days": average_case_age
            },
            "case_type_distribution": case_types,
            "monthly_trend": trend_data,
            "efficiency_metrics": {
                "average_time_to_disposition_days": random.randint(150, 400),
                "average_hearings_per_case": random.uniform(3.0, 8.0),
                "adjournment_rate": random.uniform(0.1, 0.4)
            },
            "recommendations": [
                "Focus on reducing case backlog by prioritizing older cases",
                "Consider implementing case management techniques to improve efficiency",
                "Monitor adjournment rates and implement policies to reduce unnecessary delays"
            ]
        }
        
        logger.info(f"Generated workload analytics for court {court_id}")
        return analytics
