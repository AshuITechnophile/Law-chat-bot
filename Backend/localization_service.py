import os
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from google.cloud import aiplatform
from google.cloud import translate_v2 as translate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalizationService:
    """Service for providing jurisdiction-specific legal guidance and multi-language support."""
    
    def __init__(self, vertex_ai_client=None, translate_client=None):
        """Initialize the localization service."""
        self.vertex_ai_client = vertex_ai_client
        self.translate_client = translate_client or translate.Client()
        
        # Load jurisdiction data
        self.jurisdictions = self._initialize_jurisdiction_data()
        
        # Supported languages
        self.supported_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "zh": "Chinese (Simplified)",
            "hi": "Hindi",
            "ar": "Arabic",
            "ru": "Russian"
        }
    
    def _initialize_jurisdiction_data(self) -> Dict[str, Dict[str, Any]]:
        """Initialize jurisdiction data for legal localization."""
        # In a real implementation, this would load from a database
        # For demonstration, we'll use hardcoded data
        
        jurisdictions = {
            "US": {
                "name": "United States (Federal)",
                "legal_system": "Common Law",
                "courts": ["Supreme Court", "Circuit Courts of Appeals", "District Courts"],
                "key_legal_codes": ["U.S. Constitution", "U.S. Code", "Code of Federal Regulations"],
                "states": {
                    "CA": {
                        "name": "California",
                        "courts": ["California Supreme Court", "Courts of Appeal", "Superior Courts"],
                        "key_legal_codes": ["California Constitution", "California Codes"]
                    },
                    "NY": {
                        "name": "New York",
                        "courts": ["New York Court of Appeals", "Supreme Court Appellate Division", "Supreme Court"],
                        "key_legal_codes": ["New York Constitution", "New York Consolidated Laws"]
                    },
                    "TX": {
                        "name": "Texas",
                        "courts": ["Texas Supreme Court", "Courts of Appeals", "District Courts"],
                        "key_legal_codes": ["Texas Constitution", "Texas Statutes"]
                    }
                    # More states would be included in a real implementation
                }
            },
            "UK": {
                "name": "United Kingdom",
                "legal_system": "Common Law",
                "courts": ["Supreme Court", "Court of Appeal", "High Court", "Crown Court", "County Court"],
                "key_legal_codes": ["Acts of Parliament", "Statutory Instruments"]
            },
            "CA": {
                "name": "Canada",
                "legal_system": "Common Law (except Quebec: Civil Law)",
                "courts": ["Supreme Court of Canada", "Federal Courts", "Provincial Courts"],
                "key_legal_codes": ["Constitution Act", "Federal Statutes", "Provincial Statutes"]
            },
            "AU": {
                "name": "Australia",
                "legal_system": "Common Law",
                "courts": ["High Court", "Federal Court", "State Supreme Courts"],
                "key_legal_codes": ["Australian Constitution", "Federal Acts", "State Acts"]
            },
            "IN": {
                "name": "India",
                "legal_system": "Common Law",
                "courts": ["Supreme Court", "High Courts", "District Courts"],
                "key_legal_codes": ["Constitution of India", "Indian Penal Code", "Code of Civil Procedure"]
            }
            # More countries would be included in a real implementation
        }
        
        return jurisdictions
    
    def detect_jurisdiction_from_query(self, query: str) -> Dict[str, Any]:
        """Detect relevant jurisdiction from user query."""
        try:
            prompt = f"""
            Analyze the following legal query and determine the most relevant jurisdiction (country and/or state/province).
            Return a JSON object with:
            - country_code: 2-letter country code (e.g., "US", "UK", "CA")
            - state_code: state/province code if applicable (e.g., "CA" for California)
            - confidence: confidence level (low, medium, high)
            - reasoning: brief explanation of why this jurisdiction was chosen
            
            If the jurisdiction is not mentioned or unclear, default to a generic response with low confidence.
            
            Query: "{query}"
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=512,
                temperature=0.2
            )
            
            # Parse the jurisdiction information
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    jurisdiction_info = json.loads(json_str)
                else:
                    jurisdiction_info = {
                        "country_code": "US",  # Default
                        "state_code": None,
                        "confidence": "low",
                        "reasoning": "No specific jurisdiction detected in query"
                    }
            except:
                jurisdiction_info = {
                    "country_code": "US",  # Default
                    "state_code": None,
                    "confidence": "low",
                    "reasoning": "No specific jurisdiction detected in query"
                }
            
            # Add jurisdiction name for reference
            country_code = jurisdiction_info.get("country_code", "US")
            state_code = jurisdiction_info.get("state_code")
            
            if country_code in self.jurisdictions:
                jurisdiction_info["country_name"] = self.jurisdictions[country_code]["name"]
                
                if state_code and country_code == "US" and state_code in self.jurisdictions["US"]["states"]:
                    jurisdiction_info["state_name"] = self.jurisdictions["US"]["states"][state_code]["name"]
            
            return jurisdiction_info
            
        except Exception as e:
            logger.error(f"Error detecting jurisdiction: {str(e)}")
            return {
                "country_code": "US",  # Default
                "state_code": None,
                "confidence": "low",
                "reasoning": "Error in jurisdiction detection"
            }
    
    def get_jurisdictional_response(self, 
                                   query: str, 
                                   jurisdiction: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a legal response tailored to a specific jurisdiction."""
        try:
            # If jurisdiction not provided, detect it
            if not jurisdiction:
                jurisdiction = self.detect_jurisdiction_from_query(query)
            
            country_code = jurisdiction.get("country_code", "US")
            state_code = jurisdiction.get("state_code")
            
            # Get jurisdiction data
            jurisdiction_data = {}
            
            if country_code in self.jurisdictions:
                jurisdiction_data = self.jurisdictions[country_code]
                
                if state_code and country_code == "US" and state_code in jurisdiction_data["states"]:
                    # Merge country and state data
                    state_data = jurisdiction_data["states"][state_code]
                    jurisdiction_name = f"{state_data['name']}, {jurisdiction_data['name']}"
                    legal_system = jurisdiction_data["legal_system"]
                    courts = state_data["courts"] + jurisdiction_data["courts"]
                    legal_codes = state_data["key_legal_codes"] + jurisdiction_data["key_legal_codes"]
                else:
                    jurisdiction_name = jurisdiction_data["name"]
                    legal_system = jurisdiction_data.get("legal_system", "")
                    courts = jurisdiction_data.get("courts", [])
                    legal_codes = jurisdiction_data.get("key_legal_codes", [])
            else:
                # Default to US federal if jurisdiction not found
                jurisdiction_data = self.jurisdictions["US"]
                jurisdiction_name = jurisdiction_data["name"]
                legal_system = jurisdiction_data.get("legal_system", "")
                courts = jurisdiction_data.get("courts", [])
                legal_codes = jurisdiction_data.get("key_legal_codes", [])
            
            # Create jurisdiction context
            jurisdiction_context = f"""
            JURISDICTION: {jurisdiction_name}
            LEGAL SYSTEM: {legal_system}
            RELEVANT COURTS: {', '.join(courts)}
            KEY LEGAL CODES: {', '.join(legal_codes)}
            """
            
            # Generate jurisdiction-specific response
            prompt = f"""
            You are a legal assistant providing information specific to {jurisdiction_name}.
            
            Jurisdiction Context:
            {jurisdiction_context}
            
            User Query: "{query}"
            
            Provide a legal response that is accurate and specific to this jurisdiction.
            If the query involves an area where laws significantly differ by jurisdiction, highlight this fact.
            Include references to specific laws, codes, or precedents when possible.
            Always include a disclaimer that this is not legal advice.
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=1024,
                temperature=0.2
            )
            
            return {
                "status": "success",
                "jurisdiction": jurisdiction,
                "response": response.text,
                "disclaimer": "This information is jurisdiction-specific but still general in nature. Laws change frequently, and this should not be considered legal advice. Consult with a qualified attorney licensed in your jurisdiction."
            }
            
        except Exception as e:
            logger.error(f"Error generating jurisdictional response: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to generate jurisdictional response: {str(e)}"
            }
    
    def translate_text(self, text: str, target_language: str) -> Dict[str, Any]:
        """Translate text to a target language."""
        try:
            if target_language not in self.supported_languages:
                return {
                    "status": "error",
                    "message": f"Language {target_language} is not supported"
                }
            
            # Translate using Google Cloud Translation API
            translation = self.translate_client.translate(
                text,
                target_language=target_language
            )
            
            return {
                "status": "success",
                "source_language": translation.get("detectedSourceLanguage", "en"),
                "target_language": target_language,
                "translated_text": translation.get("translatedText", ""),
                "original_text": text
            }
            
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to translate text: {str(e)}"
            }
    
    def get_multi_language_response(self, 
                                   query: str, 
                                   target_language: str,
                                   jurisdiction: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a legal response in a specific language and jurisdiction."""
        try:
            # First, translate the query to English for processing if not already in English
            if target_language != "en":
                detected_language = self.translate_client.detect_language(query)
                
                if detected_language["language"] != "en":
                    translation = self.translate_client.translate(
                        query,
                        target_language="en"
                    )
                    english_query = translation.get("translatedText", query)
                else:
                    english_query = query
            else:
                english_query = query
            
            # Get jurisdictional response in English
            response_data = self.get_jurisdictional_response(english_query, jurisdiction)
            
            if response_data.get("status") == "error":
                return response_data
            
            english_response = response_data.get("response", "")
            
            # If target language is not English, translate the response
            if target_language != "en":
                translation_data = self.translate_text(english_response, target_language)
                
                if translation_data.get("status") == "error":
                    return translation_data
                
                translated_response = translation_data.get("translated_text", "")
                
                # Also translate the disclaimer
                disclaimer_translation = self.translate_text(
                    response_data.get("disclaimer", ""),
                    target_language
                )
                
                translated_disclaimer = disclaimer_translation.get("translated_text", "")
                
                return {
                    "status": "success",
                    "jurisdiction": response_data.get("jurisdiction", {}),
                    "language": self.supported_languages.get(target_language, target_language),
                    "response": translated_response,
                    "original_response": english_response,
                    "disclaimer": translated_disclaimer
                }
            else:
                # If target language is English, return the original response
                return response_data
            
        except Exception as e:
            logger.error(f"Error generating multi-language response: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to generate multi-language response: {str(e)}"
            }
    
    def get_supported_languages(self) -> Dict[str, Any]:
        """Get a list of supported languages."""
        return {
            "status": "success",
            "supported_languages": self.supported_languages
        }
    
    def get_supported_jurisdictions(self) -> Dict[str, Any]:
        """Get a list of supported jurisdictions."""
        # Format jurisdictions for API response
        formatted_jurisdictions = {}
        
        for code, data in self.jurisdictions.items():
            formatted_jurisdictions[code] = {
                "name": data.get("name", ""),
                "legal_system": data.get("legal_system", "")
            }
            
            # Add states for US
            if code == "US" and "states" in data:
                formatted_jurisdictions[code]["states"] = {
                    state_code: {"name": state_data.get("name", "")}
                    for state_code, state_data in data["states"].items()
                }
        
        return {
            "status": "success",
            "supported_jurisdictions": formatted_jurisdictions
        }

# For testing
if __name__ == "__main__":
    # This would be for local testing
    service = LocalizationService()
    
    # Test jurisdiction detection
    query = "I have a question about tenant rights in California."
    result = service.detect_jurisdiction_from_query(query)
    print(json.dumps(result, indent=2))
    
    # Test jurisdictional response
    response = service.get_jurisdictional_response(query, result)
    print(response.get("response", "")) 