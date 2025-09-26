"""
Mock implementations of Google Cloud services for local development
"""

class MockCredentials:
    @classmethod
    def from_service_account_file(cls, file_path):
        return cls()

class TextGenerationModel:
    @classmethod
    def from_pretrained(cls, model_name):
        return cls()
    
    def predict(self, prompt, **kwargs):
        """Mock text generation"""
        response = MockResponse()
        
        # Simple mock responses based on the prompt
        if "legal" in prompt.lower():
            response.text = "This is a mock legal response. Please note this is not legal advice."
        elif "health" in prompt.lower():
            response.text = "The backend server is operational and ready to handle requests."
        else:
            response.text = "I'm a mock AI response. In a real environment, this would come from Google Vertex AI."
        
        return response

class MockResponse:
    def __init__(self):
        self.text = ""

class aiplatform:
    TextGenerationModel = TextGenerationModel
    
    @staticmethod
    def init(project=None, location=None, credentials=None):
        """Mock initialization of AI Platform"""
        print(f"Mock AI Platform initialized with project: {project}, location: {location}")
        return True 