"""
Mock implementations of service classes for local development
"""
import uuid

class LegalDocumentProcessor:
    def analyze_document(self, document_text, document_type=None):
        """Mock document analysis"""
        return {
            "summary": "This is a mock document analysis summary.",
            "key_points": ["Mock key point 1", "Mock key point 2"],
            "legal_provisions": ["Mock provision 1", "Mock provision 2"],
            "risks": ["Mock risk 1", "Mock risk 2"],
            "recommendations": ["Mock recommendation 1", "Mock recommendation 2"]
        }
    
    def get_document_templates(self):
        """Mock document templates"""
        return [
            {"id": "contract_nda", "name": "Non-Disclosure Agreement", "category": "Contracts"},
            {"id": "letter_demand", "name": "Demand Letter", "category": "Letters"},
            {"id": "will_simple", "name": "Simple Will", "category": "Estate Planning"}
        ]
    
    def generate_document(self, template_id, parameters):
        """Mock document generation"""
        return {
            "document_text": "This is a mock generated document based on the template.",
            "document_id": f"mock-doc-{uuid.uuid4().hex[:8]}"
        }

class LawyerConnectService:
    def get_available_lawyers(self, specialty=None, location=None):
        """Mock lawyer listing"""
        return [
            {"id": "lawyer1", "name": "Jane Smith", "specialty": "Family Law", "available": True},
            {"id": "lawyer2", "name": "John Doe", "specialty": "Corporate Law", "available": False},
            {"id": "lawyer3", "name": "Alice Johnson", "specialty": "Criminal Defense", "available": True}
        ]
    
    def schedule_consultation(self, lawyer_id, user_id, time_slot, topic):
        """Mock consultation scheduling"""
        return {
            "booking_id": f"mock-booking-{uuid.uuid4().hex[:8]}",
            "status": "confirmed",
            "lawyer_id": lawyer_id,
            "time": time_slot
        }

class LocalizationService:
    def get_available_jurisdictions(self):
        """Mock jurisdiction listing"""
        return [
            {"id": "us_federal", "name": "United States (Federal)"},
            {"id": "us_ca", "name": "California, USA"},
            {"id": "us_ny", "name": "New York, USA"},
            {"id": "uk", "name": "United Kingdom"},
            {"id": "ca", "name": "Canada"}
        ]
    
    def get_jurisdiction_specific_info(self, jurisdiction_id, legal_topic):
        """Mock jurisdiction-specific information"""
        return {
            "jurisdiction": jurisdiction_id,
            "topic": legal_topic,
            "information": "This is mock jurisdiction-specific information.",
            "resources": ["Mock resource 1", "Mock resource 2"]
        }

class ComplianceService:
    def check_compliance(self, document_text, jurisdiction, document_type):
        """Mock compliance check"""
        return {
            "compliant": True,
            "issues": [],
            "recommendations": ["Mock compliance recommendation 1", "Mock compliance recommendation 2"]
        }
    
    def get_compliance_requirements(self, jurisdiction, business_type, activity):
        """Mock compliance requirements"""
        return {
            "requirements": ["Mock requirement 1", "Mock requirement 2"],
            "forms": ["Mock form 1", "Mock form 2"],
            "deadlines": ["Mock deadline 1", "Mock deadline 2"]
        }

class LegalNewsAndCaseTracker:
    def get_recent_cases(self, topic=None, jurisdiction=None):
        """Mock recent cases"""
        return [
            {"id": "case1", "title": "Mock Case 1", "date": "2023-01-15", "summary": "Mock case summary 1"},
            {"id": "case2", "title": "Mock Case 2", "date": "2023-02-20", "summary": "Mock case summary 2"}
        ]
    
    def get_legal_news(self, topic=None, jurisdiction=None):
        """Mock legal news"""
        return [
            {"id": "news1", "title": "Mock Legal News 1", "date": "2023-03-10", "summary": "Mock news summary 1"},
            {"id": "news2", "title": "Mock Legal News 2", "date": "2023-03-15", "summary": "Mock news summary 2"}
        ]
    
    def register_for_updates(self, user_id, topics, jurisdictions):
        """Mock update registration"""
        return {
            "registration_id": f"mock-reg-{uuid.uuid4().hex[:8]}",
            "status": "active",
            "topics": topics,
            "jurisdictions": jurisdictions
        } 