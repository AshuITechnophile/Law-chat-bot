import os
import json
import logging
import uuid
import hashlib
import base64
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from google.cloud import aiplatform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceService:
    """Service for ensuring legal compliance, security, and bias mitigation."""
    
    def __init__(self, vertex_ai_client=None):
        """Initialize the compliance service."""
        self.vertex_ai_client = vertex_ai_client
        
        # For PII detection
        self.pii_patterns = {
            "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "phone": r'\b(?:\+\d{1,3}[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "address": r'\b\d+\s+[A-Za-z\s]+(?:Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Parkway|Pkwy)\b',
        }
        
        # For bias detection
        self.bias_categories = [
            "racial", "gender", "age", "religious", "political", 
            "socioeconomic", "national origin", "disability"
        ]
    
    def detect_pii(self, text: str) -> Dict[str, Any]:
        """Detect personally identifiable information (PII) in text."""
        try:
            findings = {}
            
            # Check for PII using regex patterns
            for pii_type, pattern in self.pii_patterns.items():
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if pii_type not in findings:
                        findings[pii_type] = []
                    
                    # Get position and context
                    start = match.start()
                    end = match.end()
                    value = match.group()
                    
                    # Add some context for validation
                    context_start = max(0, start - 30)
                    context_end = min(len(text), end + 30)
                    context = text[context_start:context_end]
                    
                    findings[pii_type].append({
                        "value": value,
                        "position": (start, end),
                        "context": context
                    })
            
            # Use Vertex AI for additional PII detection
            prompt = f"""
            Analyze the following text for personally identifiable information (PII) that I might have missed.
            Look for names, dates of birth, government IDs, financial information, or other sensitive personal data.
            Return a JSON array of findings, each with "type" and "description".
            
            Text to analyze: "{text[:5000]}"
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.2
            )
            
            # Parse AI findings
            try:
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    ai_findings = json.loads(json_str)
                    
                    for finding in ai_findings:
                        pii_type = finding.get("type", "other_pii").lower().replace(" ", "_")
                        
                        if pii_type not in findings:
                            findings[pii_type] = []
                        
                        findings[pii_type].append({
                            "value": "AI-detected",  # Don't expose the actual PII
                            "description": finding.get("description", "")
                        })
            except:
                pass
            
            return {
                "status": "success",
                "has_pii": bool(findings),
                "findings": findings,
                "total_findings": sum(len(items) for items in findings.values())
            }
            
        except Exception as e:
            logger.error(f"Error detecting PII: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to detect PII: {str(e)}"
            }
    
    def redact_pii(self, text: str) -> Dict[str, Any]:
        """Redact personally identifiable information from text."""
        try:
            # First, detect PII
            detection_result = self.detect_pii(text)
            
            if detection_result.get("status") == "error":
                return detection_result
            
            # No PII found
            if not detection_result.get("has_pii", False):
                return {
                    "status": "success",
                    "redacted_text": text,
                    "redactions_made": 0,
                    "original_text": text
                }
            
            # Perform redaction
            redacted_text = text
            redaction_count = 0
            
            # Track positions to adjust for length changes during redaction
            position_offset = 0
            
            # Process direct regex matches first
            for pii_type, findings in detection_result.get("findings", {}).items():
                for finding in findings:
                    if "position" in finding:
                        start, end = finding["position"]
                        value = finding["value"]
                        
                        # Adjust positions for previous redactions
                        adj_start = start + position_offset
                        adj_end = end + position_offset
                        
                        # Replace with redaction marker
                        redaction_marker = f"[REDACTED:{pii_type}]"
                        
                        redacted_text = (
                            redacted_text[:adj_start] + 
                            redaction_marker + 
                            redacted_text[adj_end:]
                        )
                        
                        # Update offset for length difference
                        position_offset += len(redaction_marker) - (adj_end - adj_start)
                        redaction_count += 1
            
            # Use Vertex AI for a final pass
            prompt = f"""
            Redact any remaining personally identifiable information (PII) from this text.
            Replace PII with [REDACTED] markers.
            
            Text: "{redacted_text}"
            
            Redacted text:
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=2048,
                temperature=0.1
            )
            
            ai_redacted_text = response.text
            
            # Count additional redactions
            additional_redactions = ai_redacted_text.count("[REDACTED]") + ai_redacted_text.count("[REDACTED:")
            redaction_count += additional_redactions
            
            return {
                "status": "success",
                "redacted_text": ai_redacted_text if additional_redactions > 0 else redacted_text,
                "redactions_made": redaction_count,
                "original_text": text
            }
            
        except Exception as e:
            logger.error(f"Error redacting PII: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to redact PII: {str(e)}"
            }
    
    def encrypt_sensitive_data(self, data: str) -> Dict[str, Any]:
        """Encrypt sensitive data (simplified demo implementation)."""
        try:
            # Generate a simple encryption key (in a real system, this would use proper key management)
            salt = os.urandom(16)
            key = hashlib.pbkdf2_hmac('sha256', 'demo-key'.encode(), salt, 100000)
            
            # For demonstration only - in production, use proper cryptographic libraries
            # This is NOT secure encryption and is just for demonstration
            encrypted = base64.b64encode(bytes([a ^ b for a, b in zip(data.encode(), key)]))
            
            return {
                "status": "success",
                "encrypted_data": encrypted.decode(),
                "salt": base64.b64encode(salt).decode(),
                "message": "Data encrypted (demonstration only, not secure)"
            }
            
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to encrypt data: {str(e)}"
            }
    
    def detect_bias(self, text: str) -> Dict[str, Any]:
        """Detect potential bias in legal content."""
        try:
            # Use Vertex AI to analyze for bias
            prompt = f"""
            Analyze the following legal text for potential bias across these categories:
            {', '.join(self.bias_categories)}
            
            For each type of bias, provide:
            1. Whether bias is present (yes/no)
            2. Confidence level (low, medium, high)
            3. Specific examples or phrases that indicate bias
            4. Suggested neutral alternatives
            
            Return a JSON object with bias_found (boolean) and categories (object) with details for each category.
            
            Text to analyze: "{text[:10000]}"
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=2048,
                temperature=0.2
            )
            
            # Parse the bias analysis
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    bias_analysis = json.loads(json_str)
                else:
                    bias_analysis = {
                        "bias_found": False,
                        "categories": {}
                    }
            except:
                bias_analysis = {
                    "bias_found": False,
                    "categories": {}
                }
            
            return {
                "status": "success",
                "bias_analysis": bias_analysis
            }
            
        except Exception as e:
            logger.error(f"Error detecting bias: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to detect bias: {str(e)}"
            }
    
    def mitigate_bias(self, text: str) -> Dict[str, Any]:
        """Mitigate bias in legal content."""
        try:
            # First, detect bias
            detection_result = self.detect_bias(text)
            
            if detection_result.get("status") == "error":
                return detection_result
            
            bias_analysis = detection_result.get("bias_analysis", {})
            
            # If no bias found, return original text
            if not bias_analysis.get("bias_found", False):
                return {
                    "status": "success",
                    "mitigated_text": text,
                    "changes_made": 0,
                    "original_text": text
                }
            
            # Create prompt for bias mitigation
            prompt = f"""
            The following legal text contains potential bias. Rewrite it to be more neutral and balanced,
            while preserving the legal meaning and accuracy. Ensure the rewriting:
            
            1. Uses inclusive and neutral language
            2. Maintains legal precision
            3. Preserves the original intent
            4. Presents balanced perspectives
            
            Original text: "{text[:10000]}"
            
            Neutralized text:
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=4096,
                temperature=0.2
            )
            
            mitigated_text = response.text
            
            # Count changes (simple approximation)
            changes_made = abs(len(text) - len(mitigated_text)) / max(len(text), 1) * 100
            
            return {
                "status": "success",
                "mitigated_text": mitigated_text,
                "changes_made": int(changes_made),
                "original_text": text,
                "bias_analysis": bias_analysis
            }
            
        except Exception as e:
            logger.error(f"Error mitigating bias: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to mitigate bias: {str(e)}"
            }
    
    def check_gdpr_compliance(self, text: str) -> Dict[str, Any]:
        """Check for GDPR compliance issues in text."""
        try:
            # Use Vertex AI to analyze for GDPR compliance
            prompt = f"""
            Analyze the following text for potential GDPR compliance issues. Look for:
            1. Unauthorized collection of personal data
            2. Missing consent mechanisms
            3. Lack of data processing transparency
            4. Insufficient data protection measures
            5. Missing data subject rights information
            
            Return a JSON object with:
            - compliance_issues (array of issues found)
            - risk_level (low, medium, high)
            - recommendations (array of recommendations)
            
            Text to analyze: "{text[:10000]}"
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=2048,
                temperature=0.2
            )
            
            # Parse the compliance analysis
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    compliance_analysis = json.loads(json_str)
                else:
                    compliance_analysis = {
                        "compliance_issues": [],
                        "risk_level": "low",
                        "recommendations": []
                    }
            except:
                compliance_analysis = {
                    "compliance_issues": [],
                    "risk_level": "low",
                    "recommendations": []
                }
            
            return {
                "status": "success",
                "gdpr_compliance": compliance_analysis
            }
            
        except Exception as e:
            logger.error(f"Error checking GDPR compliance: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to check GDPR compliance: {str(e)}"
            }
    
    def generate_privacy_policy(self, company_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a GDPR-compliant privacy policy."""
        try:
            company_name = company_info.get("name", "Company")
            data_collected = company_info.get("data_collected", [])
            data_usage = company_info.get("data_usage", [])
            data_sharing = company_info.get("data_sharing", [])
            contact_info = company_info.get("contact_info", {})
            
            # Format the inputs for the prompt
            data_collected_text = ", ".join(data_collected) if data_collected else "No data specified"
            data_usage_text = ", ".join(data_usage) if data_usage else "No usage specified"
            data_sharing_text = ", ".join(data_sharing) if data_sharing else "No sharing specified"
            
            contact_email = contact_info.get("email", "contact@example.com")
            contact_address = contact_info.get("address", "Not specified")
            
            prompt = f"""
            Generate a comprehensive, GDPR-compliant privacy policy for {company_name}.
            Include all required sections for GDPR compliance.
            
            Company Information:
            - Name: {company_name}
            - Data Collected: {data_collected_text}
            - Data Usage: {data_usage_text}
            - Data Sharing: {data_sharing_text}
            - Contact Email: {contact_email}
            - Contact Address: {contact_address}
            
            The privacy policy should cover:
            1. Types of personal data collected
            2. Purpose of data processing
            3. Legal basis for processing
            4. Data retention periods
            5. Data subject rights
            6. Data security measures
            7. International transfers
            8. Use of cookies
            9. Third-party sharing
            10. Changes to privacy policy
            11. Contact information for data protection inquiries
            
            Format as a complete, professional privacy policy document.
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=4096,
                temperature=0.2
            )
            
            return {
                "status": "success",
                "privacy_policy": response.text,
                "company_name": company_name,
                "generated_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating privacy policy: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to generate privacy policy: {str(e)}"
            }

# For testing
if __name__ == "__main__":
    # This would be for local testing
    service = ComplianceService()
    
    # Test PII detection
    test_text = "My name is John Smith and my email is john.smith@example.com. Call me at 555-123-4567."
    result = service.detect_pii(test_text)
    print(json.dumps(result, indent=2))
    
    # Test PII redaction
    redacted = service.redact_pii(test_text)
    print(redacted.get("redacted_text", "")) 