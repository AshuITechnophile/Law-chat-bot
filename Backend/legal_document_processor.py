import os
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import nltk
from google.cloud import aiplatform
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalDocumentProcessor:
    """Handles all legal document processing operations including analysis, monitoring, and generation."""
    
    def __init__(self):
        """Initialize the document processor with necessary configurations."""
        self.monitored_documents = {}  # In production, this would be a database
        self.document_templates = self._load_document_templates()
        
    def summarize_document(self, document_text: str, document_type: str = 'general') -> Dict[str, Any]:
        """
        Analyze a legal document and provide a plain language explanation.
        
        Args:
            document_text (str): The text content of the legal document
            document_type (str): Type of document (e.g., 'contract', 'nda', 'will')
            
        Returns:
            Dict containing the analysis results
        """
        try:
            # Create a prompt for the model based on document type
            prompt = f"""
            Analyze the following {document_type} and provide:
            1. A plain language summary
            2. Key terms and their explanations
            3. Important dates and deadlines
            4. Obligations and responsibilities
            5. Potential risks or concerns
            
            Document:
            {document_text}
            
            Analysis:
            """
            
            # Use Vertex AI for analysis
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.3
            )
            
            return {
                "status": "success",
                "analysis": response.text,
                "document_type": document_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            raise
    
    def register_document_for_monitoring(
        self,
        document_id: str,
        document_text: str,
        document_type: str,
        legal_areas: List[str],
        jurisdiction: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Register a document for monitoring legal changes.
        
        Args:
            document_id (str): Unique identifier for the document
            document_text (str): The text content of the document
            document_type (str): Type of document
            legal_areas (List[str]): Areas of law relevant to the document
            jurisdiction (str): Legal jurisdiction
            user_id (str): ID of the user registering the document
            
        Returns:
            Dict containing registration confirmation
        """
        try:
            # Extract key legal concepts and requirements
            prompt = f"""
            Analyze this {document_type} and identify:
            1. Key legal concepts
            2. Regulatory requirements
            3. Compliance obligations
            4. Time-sensitive elements
            
            Document:
            {document_text}
            
            Analysis:
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            analysis = model.predict(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.3
            ).text
            
            # Store document information (in production, this would go to a database)
            self.monitored_documents[document_id] = {
                "document_text": document_text,
                "document_type": document_type,
                "legal_areas": legal_areas,
                "jurisdiction": jurisdiction,
                "user_id": user_id,
                "analysis": analysis,
                "last_checked": datetime.utcnow().isoformat(),
                "last_update": None
            }
            
            return {
                "status": "success",
                "message": "Document registered for monitoring",
                "document_id": document_id,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error registering document: {str(e)}")
            raise
    
    def check_legal_updates(self, document_id: str) -> Dict[str, Any]:
        """
        Check for legal updates affecting a monitored document.
        
        Args:
            document_id (str): ID of the document to check
            
        Returns:
            Dict containing update information
        """
        try:
            if document_id not in self.monitored_documents:
                raise ValueError("Document not found in monitoring system")
            
            doc_info = self.monitored_documents[document_id]
            
            # Simulate checking for legal updates (in production, this would query legal databases)
            prompt = f"""
            Given a {doc_info['document_type']} in {doc_info['jurisdiction']} 
            covering these legal areas: {', '.join(doc_info['legal_areas'])},
            identify any relevant legal changes or updates that might affect it.
            
            Document analysis:
            {doc_info['analysis']}
            
            Relevant updates:
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            updates = model.predict(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.3
            ).text
            
            # Update last checked timestamp
            self.monitored_documents[document_id]["last_checked"] = datetime.utcnow().isoformat()
            
            return {
                "status": "success",
                "document_id": document_id,
                "updates": updates,
                "last_checked": self.monitored_documents[document_id]["last_checked"]
            }
            
        except Exception as e:
            logger.error(f"Error checking updates: {str(e)}")
            raise
    
    def generate_document(
        self,
        document_type: str,
        parameters: Dict[str, Any],
        jurisdiction: str = 'US'
    ) -> Dict[str, Any]:
        """
        Generate a legal document based on provided parameters.
        
        Args:
            document_type (str): Type of document to generate
            parameters (Dict[str, Any]): Parameters for document generation
            jurisdiction (str): Legal jurisdiction
            
        Returns:
            Dict containing the generated document
        """
        try:
            template = self.document_templates.get(document_type)
            if not template:
                raise ValueError(f"No template found for document type: {document_type}")
            
            # Validate required parameters
            missing_params = [
                param["name"] for param in template["parameters"]
                if param["required"] and param["name"] not in parameters
            ]
            if missing_params:
                raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
            
            # Create prompt for document generation
            prompt = f"""
            Generate a {document_type} for {jurisdiction} jurisdiction with these parameters:
            {parameters}
            
            The document should:
            1. Use standard legal language
            2. Include all necessary clauses
            3. Be properly formatted
            4. Include any required disclaimers
            
            Generated document:
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            document = model.predict(
                prompt=prompt,
                max_output_tokens=2048,
                temperature=0.2
            ).text
            
            return {
                "status": "success",
                "document_type": document_type,
                "jurisdiction": jurisdiction,
                "content": document,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating document: {str(e)}")
            raise
    
    def suggest_document_updates(
        self,
        document_id: str,
        document_text: str,
        legal_changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest updates to a document based on legal changes.
        
        Args:
            document_id (str): ID of the document
            document_text (str): Current text of the document
            legal_changes (List[Dict[str, Any]]): List of relevant legal changes
            
        Returns:
            Dict containing suggested updates
        """
        try:
            # Create prompt for update suggestions
            changes_text = "\n".join([
                f"- {change.get('description', '')}" for change in legal_changes
            ])
            
            prompt = f"""
            Given this document:
            {document_text}
            
            And these legal changes:
            {changes_text}
            
            Suggest specific updates to the document to maintain compliance.
            Include:
            1. Sections requiring updates
            2. Suggested new language
            3. Explanation of changes
            4. Any additional clauses needed
            
            Suggestions:
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            suggestions = model.predict(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.3
            ).text
            
            return {
                "status": "success",
                "document_id": document_id,
                "suggestions": suggestions,
                "timestamp": datetime.utcnow().isoformat(),
                "legal_changes": legal_changes
            }
            
        except Exception as e:
            logger.error(f"Error suggesting updates: {str(e)}")
            raise
    
    def _load_document_templates(self) -> Dict[str, Any]:
        """Load document templates (in production, this would load from a database)."""
        return {
            "nda": {
                "name": "Non-Disclosure Agreement",
                "parameters": [
                    {"name": "party_a", "type": "string", "required": True, "description": "Name of the disclosing party"},
                    {"name": "party_b", "type": "string", "required": True, "description": "Name of the receiving party"},
                    {"name": "purpose", "type": "string", "required": True, "description": "Purpose of disclosure"},
                    {"name": "term", "type": "string", "required": True, "description": "Duration of the agreement"},
                    {"name": "jurisdiction", "type": "string", "required": False, "description": "Governing jurisdiction"}
                ]
            },
            "contract": {
                "name": "Service Contract",
                "parameters": [
                    {"name": "party_a", "type": "string", "required": True, "description": "Service provider"},
                    {"name": "party_b", "type": "string", "required": True, "description": "Client"},
                    {"name": "services", "type": "string", "required": True, "description": "Description of services"},
                    {"name": "payment_terms", "type": "string", "required": True, "description": "Payment details"},
                    {"name": "term", "type": "string", "required": True, "description": "Duration of contract"},
                    {"name": "jurisdiction", "type": "string", "required": False, "description": "Governing jurisdiction"}
                ]
            },
            "will": {
                "name": "Last Will and Testament",
                "parameters": [
                    {"name": "testator_name", "type": "string", "required": True, "description": "Name of person making the will"},
                    {"name": "executor_name", "type": "string", "required": True, "description": "Name of executor"},
                    {"name": "beneficiaries", "type": "array", "required": True, "description": "List of beneficiaries"},
                    {"name": "assets", "type": "array", "required": True, "description": "List of assets to distribute"},
                    {"name": "jurisdiction", "type": "string", "required": False, "description": "Governing jurisdiction"}
                ]
            }
        }

# For testing
if __name__ == "__main__":
    # This would be for local testing
    processor = LegalDocumentProcessor()
    
    # Test document summarization
    test_doc = """THIS CONSULTING AGREEMENT (the "Agreement") is made and entered into as of January 1, 2023 (the "Effective Date"), by and between ABC Corporation, a Delaware corporation with its principal place of business at 123 Main St, Anytown, USA ("Company"), and John Smith, an individual residing at 456 Oak Lane, Somewhere, USA ("Consultant").

    WHEREAS, Company desires to engage Consultant to provide certain services as set forth herein, and Consultant desires to provide such services to Company;

    NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, the parties agree as follows:

    1. SERVICES. Consultant shall provide strategic business consulting services to Company as described in Exhibit A (the "Services").

    2. TERM. The term of this Agreement shall commence on the Effective Date and continue for a period of twelve (12) months, unless earlier terminated as provided herein.

    3. COMPENSATION. As compensation for the Services, Company shall pay Consultant a fee of $10,000 per month, payable within fifteen (15) days of receipt of Consultant's invoice.

    4. TERMINATION. Either party may terminate this Agreement upon thirty (30) days written notice to the other party."""
    
    result = processor.summarize_document(test_doc, "contract")
    print(json.dumps(result, indent=2)) 