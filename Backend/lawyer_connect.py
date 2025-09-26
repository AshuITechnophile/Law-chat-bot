import os
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
from google.cloud import aiplatform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LawyerConnectService:
    """Class to handle lawyer connection, appointment booking, and expert matching."""
    
    def __init__(self, vertex_ai_client=None):
        """Initialize the lawyer connection service."""
        self.vertex_ai_client = vertex_ai_client
        
        # In a real implementation, this would connect to a database
        # For demonstration, we'll use in-memory storage
        self.lawyers = self._initialize_sample_lawyers()
        self.appointments = {}
        self.chat_sessions = {}
    
    def _initialize_sample_lawyers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize sample lawyer data for demonstration."""
        sample_lawyers = {
            "L001": {
                "id": "L001",
                "name": "Sarah Johnson",
                "specialties": ["Family Law", "Divorce", "Child Custody"],
                "experience_years": 15,
                "languages": ["English", "Spanish"],
                "jurisdictions": ["California", "Oregon"],
                "availability": {
                    "Monday": ["09:00-12:00", "13:00-17:00"],
                    "Tuesday": ["09:00-12:00", "13:00-17:00"],
                    "Wednesday": ["09:00-12:00", "13:00-17:00"],
                    "Thursday": ["09:00-12:00", "13:00-17:00"],
                    "Friday": ["09:00-12:00", "13:00-15:00"]
                },
                "rating": 4.8
            },
            "L002": {
                "id": "L002",
                "name": "Michael Chen",
                "specialties": ["Corporate Law", "Contracts", "Startups"],
                "experience_years": 8,
                "languages": ["English", "Mandarin"],
                "jurisdictions": ["New York", "New Jersey"],
                "availability": {
                    "Monday": ["10:00-18:00"],
                    "Tuesday": ["10:00-18:00"],
                    "Wednesday": ["10:00-18:00"],
                    "Thursday": ["10:00-18:00"],
                    "Friday": ["10:00-16:00"]
                },
                "rating": 4.7
            },
            "L003": {
                "id": "L003",
                "name": "David Rodriguez",
                "specialties": ["Criminal Defense", "DUI", "Traffic Violations"],
                "experience_years": 12,
                "languages": ["English", "Spanish"],
                "jurisdictions": ["Texas", "Arizona"],
                "availability": {
                    "Monday": ["08:00-16:00"],
                    "Tuesday": ["08:00-16:00"],
                    "Wednesday": ["08:00-16:00"],
                    "Thursday": ["08:00-16:00"],
                    "Friday": ["08:00-16:00"]
                },
                "rating": 4.9
            },
            "L004": {
                "id": "L004",
                "name": "Aisha Patel",
                "specialties": ["Immigration Law", "Visas", "Naturalization"],
                "experience_years": 10,
                "languages": ["English", "Hindi", "Gujarati"],
                "jurisdictions": ["All US States"],
                "availability": {
                    "Monday": ["09:00-17:00"],
                    "Tuesday": ["09:00-17:00"],
                    "Wednesday": ["09:00-17:00"],
                    "Thursday": ["09:00-17:00"],
                    "Friday": ["09:00-15:00"]
                },
                "rating": 4.8
            },
            "L005": {
                "id": "L005",
                "name": "James Wilson",
                "specialties": ["Real Estate Law", "Property Disputes", "Landlord-Tenant"],
                "experience_years": 18,
                "languages": ["English"],
                "jurisdictions": ["Florida", "Georgia"],
                "availability": {
                    "Monday": ["08:30-16:30"],
                    "Tuesday": ["08:30-16:30"],
                    "Wednesday": ["08:30-16:30"],
                    "Thursday": ["08:30-16:30"],
                    "Friday": ["08:30-14:30"]
                },
                "rating": 4.6
            }
        }
        return sample_lawyers
    
    def find_lawyers(self, 
                    legal_issue: str, 
                    jurisdiction: Optional[str] = None,
                    language: Optional[str] = None) -> Dict[str, Any]:
        """Find lawyers that match the user's needs."""
        try:
            # In a real implementation, this would query a database
            # For now, we'll use AI to match the legal issue to specialties
            
            # First, classify the legal issue
            prompt = f"""
            Classify the following legal issue into specific legal categories and subcategories.
            Return a JSON object with:
            - primary_category: main legal category (e.g., "Family Law", "Criminal Law", "Corporate Law")
            - subcategories: specific legal areas within the primary category
            - keywords: important keywords that can help match with a lawyer
            
            Legal issue: "{legal_issue}"
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=512,
                temperature=0.2
            )
            
            # Parse the classification
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    classification = json.loads(json_str)
                else:
                    classification = {
                        "primary_category": "",
                        "subcategories": [],
                        "keywords": []
                    }
            except:
                classification = {
                    "primary_category": "",
                    "subcategories": [],
                    "keywords": []
                }
            
            # Match lawyers based on classification
            matched_lawyers = []
            
            for lawyer_id, lawyer in self.lawyers.items():
                # Match by specialty
                specialty_match = False
                for specialty in lawyer["specialties"]:
                    if (classification["primary_category"] in specialty or 
                        any(subcat in specialty for subcat in classification["subcategories"]) or
                        any(keyword in specialty for keyword in classification.get("keywords", []))):
                        specialty_match = True
                        break
                
                # Match by jurisdiction if specified
                jurisdiction_match = True
                if jurisdiction:
                    jurisdiction_match = False
                    for lawyer_jurisdiction in lawyer["jurisdictions"]:
                        if jurisdiction.lower() in lawyer_jurisdiction.lower() or lawyer_jurisdiction == "All US States":
                            jurisdiction_match = True
                            break
                
                # Match by language if specified
                language_match = True
                if language:
                    language_match = language.lower() in [lang.lower() for lang in lawyer["languages"]]
                
                # Add to results if all criteria match
                if specialty_match and jurisdiction_match and language_match:
                    matched_lawyers.append({
                        "id": lawyer["id"],
                        "name": lawyer["name"],
                        "specialties": lawyer["specialties"],
                        "experience_years": lawyer["experience_years"],
                        "languages": lawyer["languages"],
                        "jurisdictions": lawyer["jurisdictions"],
                        "rating": lawyer["rating"],
                        "match_score": random.randint(70, 99)  # Simulated match score
                    })
            
            # Sort by match score
            matched_lawyers.sort(key=lambda x: x["match_score"], reverse=True)
            
            return {
                "status": "success",
                "issue_classification": classification,
                "lawyers": matched_lawyers,
                "total_matches": len(matched_lawyers)
            }
            
        except Exception as e:
            logger.error(f"Error finding lawyers: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to find lawyers: {str(e)}"
            }
    
    def get_available_slots(self, lawyer_id: str, date_range: int = 7) -> Dict[str, Any]:
        """Get available appointment slots for a lawyer."""
        if lawyer_id not in self.lawyers:
            return {
                "status": "error",
                "message": "Lawyer not found"
            }
        
        lawyer = self.lawyers[lawyer_id]
        
        # Generate available slots for the next 'date_range' days
        available_slots = {}
        
        today = datetime.now()
        
        for i in range(date_range):
            date = today + timedelta(days=i)
            weekday = date.strftime("%A")
            
            # Skip if lawyer doesn't work on this day
            if weekday not in lawyer["availability"]:
                continue
            
            # Get time slots for this day
            day_slots = []
            for time_range in lawyer["availability"][weekday]:
                start_time, end_time = time_range.split("-")
                
                # Generate 30-minute slots
                start_hour, start_minute = map(int, start_time.split(":"))
                end_hour, end_minute = map(int, end_time.split(":"))
                
                current_time = datetime(date.year, date.month, date.day, start_hour, start_minute)
                end_datetime = datetime(date.year, date.month, date.day, end_hour, end_minute)
                
                while current_time < end_datetime:
                    slot_time = current_time.strftime("%H:%M")
                    
                    # Check if slot is already booked
                    slot_key = f"{date.strftime('%Y-%m-%d')} {slot_time}"
                    is_booked = any(
                        appt.get("lawyer_id") == lawyer_id and 
                        appt.get("appointment_time") == slot_key
                        for appt in self.appointments.values()
                    )
                    
                    if not is_booked:
                        day_slots.append(slot_time)
                    
                    current_time += timedelta(minutes=30)
            
            if day_slots:
                available_slots[date.strftime("%Y-%m-%d")] = day_slots
        
        return {
            "status": "success",
            "lawyer_id": lawyer_id,
            "lawyer_name": lawyer["name"],
            "available_slots": available_slots
        }
    
    def book_appointment(self, 
                        user_id: str,
                        lawyer_id: str,
                        appointment_date: str,
                        appointment_time: str,
                        issue_description: str) -> Dict[str, Any]:
        """Book an appointment with a lawyer."""
        if lawyer_id not in self.lawyers:
            return {
                "status": "error",
                "message": "Lawyer not found"
            }
        
        # Validate the appointment slot is available
        slot_key = f"{appointment_date} {appointment_time}"
        
        is_booked = any(
            appt.get("lawyer_id") == lawyer_id and 
            appt.get("appointment_time") == slot_key
            for appt in self.appointments.values()
        )
        
        if is_booked:
            return {
                "status": "error",
                "message": "This appointment slot is no longer available"
            }
        
        # Create the appointment
        appointment_id = str(uuid.uuid4())
        
        appointment = {
            "appointment_id": appointment_id,
            "user_id": user_id,
            "lawyer_id": lawyer_id,
            "lawyer_name": self.lawyers[lawyer_id]["name"],
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "appointment_datetime": slot_key,
            "issue_description": issue_description,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        # Save the appointment
        self.appointments[appointment_id] = appointment
        
        return {
            "status": "success",
            "message": "Appointment booked successfully",
            "appointment": appointment
        }
    
    def get_user_appointments(self, user_id: str) -> Dict[str, Any]:
        """Get all appointments for a user."""
        user_appointments = [
            appt for appt in self.appointments.values()
            if appt.get("user_id") == user_id
        ]
        
        # Sort by appointment date/time
        user_appointments.sort(key=lambda x: x.get("appointment_datetime", ""))
        
        return {
            "status": "success",
            "user_id": user_id,
            "appointments": user_appointments,
            "total_appointments": len(user_appointments)
        }
    
    def cancel_appointment(self, appointment_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel an appointment."""
        if appointment_id not in self.appointments:
            return {
                "status": "error",
                "message": "Appointment not found"
            }
        
        appointment = self.appointments[appointment_id]
        
        # Verify the appointment belongs to the user
        if appointment.get("user_id") != user_id:
            return {
                "status": "error",
                "message": "Unauthorized access to this appointment"
            }
        
        # Update appointment status
        appointment["status"] = "cancelled"
        appointment["cancelled_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Appointment cancelled successfully",
            "appointment": appointment
        }
    
    def start_live_chat(self, user_id: str, lawyer_id: str) -> Dict[str, Any]:
        """Start a live chat session with a lawyer."""
        if lawyer_id not in self.lawyers:
            return {
                "status": "error",
                "message": "Lawyer not found"
            }
        
        # Create a new chat session
        session_id = str(uuid.uuid4())
        
        chat_session = {
            "session_id": session_id,
            "user_id": user_id,
            "lawyer_id": lawyer_id,
            "lawyer_name": self.lawyers[lawyer_id]["name"],
            "status": "waiting",  # waiting, active, ended
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        
        # Save the chat session
        self.chat_sessions[session_id] = chat_session
        
        return {
            "status": "success",
            "message": "Chat session created",
            "session_id": session_id,
            "lawyer_name": self.lawyers[lawyer_id]["name"]
        }
    
    def send_chat_message(self, 
                         session_id: str, 
                         sender_id: str, 
                         message: str) -> Dict[str, Any]:
        """Send a message in a live chat session."""
        if session_id not in self.chat_sessions:
            return {
                "status": "error",
                "message": "Chat session not found"
            }
        
        chat_session = self.chat_sessions[session_id]
        
        # Verify the sender is part of the chat
        is_user = sender_id == chat_session.get("user_id")
        is_lawyer = sender_id == chat_session.get("lawyer_id")
        
        if not (is_user or is_lawyer):
            return {
                "status": "error",
                "message": "Unauthorized access to this chat session"
            }
        
        # Add the message to the chat
        sender_type = "user" if is_user else "lawyer"
        
        chat_message = {
            "message_id": str(uuid.uuid4()),
            "sender_id": sender_id,
            "sender_type": sender_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        chat_session["messages"].append(chat_message)
        
        # Update session status if this is the first lawyer message
        if is_lawyer and chat_session["status"] == "waiting":
            chat_session["status"] = "active"
        
        return {
            "status": "success",
            "message": "Message sent",
            "chat_message": chat_message
        }
    
    def end_chat_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """End a live chat session."""
        if session_id not in self.chat_sessions:
            return {
                "status": "error",
                "message": "Chat session not found"
            }
        
        chat_session = self.chat_sessions[session_id]
        
        # Verify the user is part of the chat
        if user_id != chat_session.get("user_id") and user_id != chat_session.get("lawyer_id"):
            return {
                "status": "error",
                "message": "Unauthorized access to this chat session"
            }
        
        # Update session status
        chat_session["status"] = "ended"
        chat_session["ended_at"] = datetime.now().isoformat()
        
        # Generate a summary of the chat
        messages_text = "\n".join([
            f"{msg['sender_type'].capitalize()}: {msg['message']}"
            for msg in chat_session["messages"]
        ])
        
        prompt = f"""
        Summarize the following legal chat conversation between a user and a lawyer.
        Focus on the key legal questions asked, advice given, and any next steps.
        
        CHAT:
        {messages_text}
        
        SUMMARY:
        """
        
        try:
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=512,
                temperature=0.2
            )
            
            chat_session["summary"] = response.text
        except:
            chat_session["summary"] = "Summary generation failed"
        
        return {
            "status": "success",
            "message": "Chat session ended",
            "chat_summary": chat_session.get("summary", ""),
            "chat_session": chat_session
        }

# For testing
if __name__ == "__main__":
    # This would be for local testing
    service = LawyerConnectService()
    
    # Test finding lawyers
    result = service.find_lawyers("I'm going through a divorce and need help with child custody arrangements.")
    print(json.dumps(result, indent=2)) 