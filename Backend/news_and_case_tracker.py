import os
import json
import logging
import uuid
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google.cloud import aiplatform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalNewsAndCaseTracker:
    """Service for legal news updates and case tracking features."""
    
    def __init__(self, vertex_ai_client=None):
        """Initialize the news and case tracker service."""
        self.vertex_ai_client = vertex_ai_client
        
        # For demonstration, we'll use in-memory storage
        self.news_subscriptions = {}
        self.tracked_cases = {}
        self.legal_updates = self._initialize_sample_updates()
        self.user_deadlines = {}
    
    def _initialize_sample_updates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize sample legal news/updates for demonstration."""
        current_date = datetime.now()
        
        # Sample updates by category
        updates = {
            "family_law": [
                {
                    "id": "FL001",
                    "title": "New Child Support Guidelines Effective Next Month",
                    "summary": "The state has revised its child support calculation guidelines, which will take effect on the first of next month. The changes include adjustments to income considerations and shared custody calculations.",
                    "source": "State Legislature",
                    "url": "https://example.com/family-law-update",
                    "date": (current_date - timedelta(days=5)).isoformat(),
                    "jurisdiction": "California",
                    "impact_level": "high"
                },
                {
                    "id": "FL002",
                    "title": "Supreme Court Decision on Parental Rights",
                    "summary": "The Supreme Court has issued a landmark decision expanding the definition of parental rights for non-biological parents in certain circumstances.",
                    "source": "Supreme Court",
                    "url": "https://example.com/sc-decision",
                    "date": (current_date - timedelta(days=12)).isoformat(),
                    "jurisdiction": "Federal",
                    "impact_level": "high"
                }
            ],
            "tax_law": [
                {
                    "id": "TL001",
                    "title": "IRS Issues New Guidelines for Home Office Deductions",
                    "summary": "The IRS has released new guidelines clarifying home office deduction requirements for remote workers. The guidelines specify what qualifies as a dedicated home workspace.",
                    "source": "Internal Revenue Service",
                    "url": "https://example.com/irs-guidelines",
                    "date": (current_date - timedelta(days=3)).isoformat(),
                    "jurisdiction": "Federal",
                    "impact_level": "medium"
                }
            ],
            "employment_law": [
                {
                    "id": "EL001",
                    "title": "New Paid Family Leave Laws in Multiple States",
                    "summary": "Several states have enacted new paid family leave legislation that expands benefits for workers. The changes include longer leave periods and broader coverage of family members.",
                    "source": "Department of Labor",
                    "url": "https://example.com/family-leave",
                    "date": (current_date - timedelta(days=7)).isoformat(),
                    "jurisdiction": "Multiple States",
                    "impact_level": "high"
                },
                {
                    "id": "EL002",
                    "title": "Updated Workplace Safety Regulations",
                    "summary": "Federal workplace safety agency has updated regulations regarding remote work environments, clarifying employer responsibilities for home office safety standards.",
                    "source": "Occupational Safety and Health Administration",
                    "url": "https://example.com/osha-update",
                    "date": (current_date - timedelta(days=14)).isoformat(),
                    "jurisdiction": "Federal",
                    "impact_level": "medium"
                }
            ],
            "real_estate_law": [
                {
                    "id": "RE001",
                    "title": "New Rent Control Measures in Major Cities",
                    "summary": "Several major cities have enacted new rent control ordinances that cap annual rent increases and provide additional tenant protections.",
                    "source": "Municipal Governments",
                    "url": "https://example.com/rent-control",
                    "date": (current_date - timedelta(days=10)).isoformat(),
                    "jurisdiction": "Various Cities",
                    "impact_level": "high"
                }
            ],
            "intellectual_property": [
                {
                    "id": "IP001",
                    "title": "Patent Office Announces New Application Process",
                    "summary": "The US Patent and Trademark Office has streamlined the patent application process, introducing new digital tools and faster review procedures for certain categories.",
                    "source": "USPTO",
                    "url": "https://example.com/uspto-changes",
                    "date": (current_date - timedelta(days=6)).isoformat(),
                    "jurisdiction": "Federal",
                    "impact_level": "medium"
                }
            ]
        }
        
        return updates
    
    def subscribe_to_updates(self, 
                           user_id: str, 
                           legal_areas: List[str],
                           jurisdictions: List[str] = None) -> Dict[str, Any]:
        """Subscribe a user to legal updates in specific areas and jurisdictions."""
        try:
            # Create a subscription
            subscription_id = str(uuid.uuid4())
            
            subscription = {
                "subscription_id": subscription_id,
                "user_id": user_id,
                "legal_areas": legal_areas,
                "jurisdictions": jurisdictions or ["Federal"],
                "created_at": datetime.now().isoformat(),
                "last_update_sent": None
            }
            
            # Save the subscription
            self.news_subscriptions[subscription_id] = subscription
            
            # Get initial updates to return to the user
            updates = self.get_legal_updates(user_id, subscription_id)
            
            return {
                "status": "success",
                "message": "Successfully subscribed to legal updates",
                "subscription": subscription,
                "initial_updates": updates.get("updates", [])
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to updates: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to subscribe to updates: {str(e)}"
            }
    
    def get_legal_updates(self, user_id: str, subscription_id: str) -> Dict[str, Any]:
        """Get legal updates for a user's subscription."""
        try:
            # Check if subscription exists
            if subscription_id not in self.news_subscriptions:
                return {
                    "status": "error",
                    "message": "Subscription not found"
                }
            
            subscription = self.news_subscriptions[subscription_id]
            
            # Verify the subscription belongs to the user
            if subscription.get("user_id") != user_id:
                return {
                    "status": "error",
                    "message": "Unauthorized access to this subscription"
                }
            
            # Get relevant updates based on subscription
            legal_areas = subscription.get("legal_areas", [])
            jurisdictions = subscription.get("jurisdictions", ["Federal"])
            
            # Filter updates by legal area and jurisdiction
            relevant_updates = []
            
            for area in legal_areas:
                area_key = area.lower().replace(" ", "_")
                
                if area_key in self.legal_updates:
                    for update in self.legal_updates[area_key]:
                        # Check if jurisdiction matches
                        update_jurisdiction = update.get("jurisdiction", "")
                        if (update_jurisdiction in jurisdictions or 
                            update_jurisdiction == "Federal" or
                            update_jurisdiction == "All" or
                            "Multiple" in update_jurisdiction or
                            "Various" in update_jurisdiction):
                            relevant_updates.append(update)
            
            # Sort updates by date (newest first)
            relevant_updates.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            # Update last update sent timestamp
            subscription["last_update_sent"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "subscription_id": subscription_id,
                "updates": relevant_updates,
                "total_updates": len(relevant_updates)
            }
            
        except Exception as e:
            logger.error(f"Error getting legal updates: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get legal updates: {str(e)}"
            }
    
    def summarize_news(self, update_ids: List[str]) -> Dict[str, Any]:
        """Summarize selected legal news updates."""
        try:
            # Find the updates with the given IDs
            updates_to_summarize = []
            
            for area, updates in self.legal_updates.items():
                for update in updates:
                    if update.get("id") in update_ids:
                        updates_to_summarize.append(update)
            
            if not updates_to_summarize:
                return {
                    "status": "error",
                    "message": "No updates found with the provided IDs"
                }
            
            # Format updates for summarization
            updates_text = "\n\n".join([
                f"TITLE: {update.get('title')}\n"
                f"SUMMARY: {update.get('summary')}\n"
                f"SOURCE: {update.get('source')}\n"
                f"JURISDICTION: {update.get('jurisdiction')}\n"
                f"DATE: {update.get('date')}"
                for update in updates_to_summarize
            ])
            
            # Generate a comprehensive summary
            prompt = f"""
            Summarize the following legal news updates into a comprehensive overview.
            Highlight the key changes, their implications, and how they might affect different stakeholders.
            Include recommendations for what readers should consider doing in response to these legal changes.
            
            UPDATES:
            {updates_text}
            
            COMPREHENSIVE SUMMARY:
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=2048,
                temperature=0.3
            )
            
            return {
                "status": "success",
                "summary": response.text,
                "updates_summarized": len(updates_to_summarize),
                "update_ids": update_ids
            }
            
        except Exception as e:
            logger.error(f"Error summarizing news: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to summarize news: {str(e)}"
            }
    
    def track_legal_case(self, 
                        user_id: str, 
                        case_info: Dict[str, Any]) -> Dict[str, Any]:
        """Track a legal case for updates and progress."""
        try:
            # Extract case information
            case_number = case_info.get("case_number")
            case_title = case_info.get("case_title")
            court = case_info.get("court")
            case_type = case_info.get("case_type")
            key_dates = case_info.get("key_dates", {})
            
            if not case_number or not case_title or not court:
                return {
                    "status": "error",
                    "message": "Missing required case information"
                }
            
            # Create case tracking record
            case_id = str(uuid.uuid4())
            
            case = {
                "case_id": case_id,
                "user_id": user_id,
                "case_number": case_number,
                "case_title": case_title,
                "court": court,
                "case_type": case_type,
                "key_dates": key_dates,
                "status": "active",
                "last_update": datetime.now().isoformat(),
                "history": [
                    {
                        "date": datetime.now().isoformat(),
                        "event": "Case tracking initialized",
                        "details": "Case added to tracking system"
                    }
                ]
            }
            
            # Save the tracked case
            self.tracked_cases[case_id] = case
            
            # Extract deadlines from key dates
            if key_dates:
                for event, date_str in key_dates.items():
                    try:
                        date_obj = datetime.fromisoformat(date_str)
                        
                        # Create a deadline
                        deadline_id = str(uuid.uuid4())
                        
                        deadline = {
                            "deadline_id": deadline_id,
                            "user_id": user_id,
                            "case_id": case_id,
                            "title": f"{event} - {case_title}",
                            "date": date_str,
                            "description": f"Deadline for {event} in case {case_number}",
                            "status": "upcoming"
                        }
                        
                        # Save the deadline
                        self.user_deadlines[deadline_id] = deadline
                    except:
                        pass
            
            return {
                "status": "success",
                "message": "Case successfully tracked",
                "case": case
            }
            
        except Exception as e:
            logger.error(f"Error tracking case: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to track case: {str(e)}"
            }
    
    def get_case_updates(self, user_id: str, case_id: str) -> Dict[str, Any]:
        """Get updates for a tracked legal case."""
        try:
            # Check if case exists
            if case_id not in self.tracked_cases:
                return {
                    "status": "error",
                    "message": "Case not found"
                }
            
            case = self.tracked_cases[case_id]
            
            # Verify the case belongs to the user
            if case.get("user_id") != user_id:
                return {
                    "status": "error",
                    "message": "Unauthorized access to this case"
                }
            
            # In a real implementation, this would query court records or APIs
            # For demonstration, generate a simulated update
            
            # Generate a simulated update based on case type
            case_type = case.get("case_type", "").lower()
            case_title = case.get("case_title", "")
            court = case.get("court", "")
            
            update_templates = {
                "civil": [
                    "Motion {action} filed by {party}",
                    "Case scheduling conference set for {date}",
                    "Discovery deadline extended to {date}",
                    "Settlement conference scheduled for {date}",
                    "Summary judgment motion {action}"
                ],
                "criminal": [
                    "New evidence submitted by {party}",
                    "Bail hearing scheduled for {date}",
                    "Motion to suppress evidence {action}",
                    "Plea offer {action} by defendant",
                    "Trial date set for {date}"
                ],
                "family": [
                    "Custody evaluation completed",
                    "Child support modification hearing set for {date}",
                    "Mediation session scheduled for {date}",
                    "Guardian ad litem report submitted",
                    "Temporary orders {action}"
                ],
                "bankruptcy": [
                    "Creditors meeting scheduled for {date}",
                    "Proof of claim deadline set for {date}",
                    "Discharge hearing scheduled for {date}",
                    "Trustee report filed",
                    "Repayment plan {action}"
                ]
            }
            
            # Get appropriate templates for the case type
            templates = update_templates.get(case_type, update_templates["civil"])
            
            # Generate a random update (in a real system, this would be real data)
            import random
            
            update_template = random.choice(templates)
            action_options = ["granted", "denied", "pending", "scheduled", "filed"]
            party_options = ["plaintiff", "defendant", "the court", "a third party"]
            
            # Future date within 30 days
            future_date = (datetime.now() + timedelta(days=random.randint(7, 30))).strftime("%Y-%m-%d")
            
            update_text = update_template.format(
                action=random.choice(action_options),
                party=random.choice(party_options),
                date=future_date
            )
            
            # Add the update to case history
            case["history"].append({
                "date": datetime.now().isoformat(),
                "event": "Case update",
                "details": update_text
            })
            
            case["last_update"] = datetime.now().isoformat()
            
            # Also generate next steps using Vertex AI
            prompt = f"""
            Based on this legal case update, suggest 3 possible next steps or actions that might be needed.
            Provide practical advice for someone following this case.
            
            Case Type: {case_type}
            Case Title: {case_title}
            Court: {court}
            Update: {update_text}
            
            Next Steps:
            """
            
            model = aiplatform.TextGenerationModel.from_pretrained("text-bison@002")
            response = model.predict(
                prompt=prompt,
                max_output_tokens=512,
                temperature=0.3
            )
            
            return {
                "status": "success",
                "case_id": case_id,
                "case_title": case_title,
                "latest_update": update_text,
                "update_date": datetime.now().isoformat(),
                "case_history": case["history"],
                "suggested_next_steps": response.text
            }
            
        except Exception as e:
            logger.error(f"Error getting case updates: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get case updates: {str(e)}"
            }
    
    def add_deadline(self, 
                    user_id: str, 
                    deadline_info: Dict[str, Any]) -> Dict[str, Any]:
        """Add a legal deadline for tracking."""
        try:
            # Extract deadline information
            title = deadline_info.get("title")
            date_str = deadline_info.get("date")
            description = deadline_info.get("description", "")
            case_id = deadline_info.get("case_id")  # Optional
            
            if not title or not date_str:
                return {
                    "status": "error",
                    "message": "Missing required deadline information"
                }
            
            # Validate the date format
            try:
                date_obj = datetime.fromisoformat(date_str)
            except:
                return {
                    "status": "error",
                    "message": "Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"
                }
            
            # Create deadline
            deadline_id = str(uuid.uuid4())
            
            deadline = {
                "deadline_id": deadline_id,
                "user_id": user_id,
                "title": title,
                "date": date_str,
                "description": description,
                "case_id": case_id,
                "status": "upcoming",
                "created_at": datetime.now().isoformat(),
                "reminders_sent": []
            }
            
            # Save the deadline
            self.user_deadlines[deadline_id] = deadline
            
            return {
                "status": "success",
                "message": "Deadline successfully added",
                "deadline": deadline
            }
            
        except Exception as e:
            logger.error(f"Error adding deadline: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to add deadline: {str(e)}"
            }
    
    def get_upcoming_deadlines(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get upcoming deadlines for a user within a specified timeframe."""
        try:
            today = datetime.now()
            cutoff_date = today + timedelta(days=days)
            
            # Find the user's deadlines
            user_deadlines = [
                deadline for deadline in self.user_deadlines.values()
                if deadline.get("user_id") == user_id
            ]
            
            # Filter for upcoming deadlines
            upcoming_deadlines = []
            
            for deadline in user_deadlines:
                try:
                    deadline_date = datetime.fromisoformat(deadline.get("date", ""))
                    
                    # Check if deadline is in the future and within the specified timeframe
                    if today <= deadline_date <= cutoff_date:
                        # Calculate days remaining
                        days_remaining = (deadline_date - today).days
                        
                        deadline_copy = deadline.copy()
                        deadline_copy["days_remaining"] = days_remaining
                        
                        upcoming_deadlines.append(deadline_copy)
                except:
                    pass
            
            # Sort by date (soonest first)
            upcoming_deadlines.sort(key=lambda x: x.get("date", ""))
            
            return {
                "status": "success",
                "user_id": user_id,
                "days_range": days,
                "deadlines": upcoming_deadlines,
                "total_deadlines": len(upcoming_deadlines)
            }
            
        except Exception as e:
            logger.error(f"Error getting upcoming deadlines: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get upcoming deadlines: {str(e)}"
            }
    
    def generate_calendar_integration(self, user_id: str) -> Dict[str, Any]:
        """Generate calendar integration data for user's deadlines and appointments."""
        try:
            # Get all the user's deadlines
            user_deadlines = [
                deadline for deadline in self.user_deadlines.values()
                if deadline.get("user_id") == user_id
            ]
            
            # Format deadlines as calendar events
            calendar_events = []
            
            for deadline in user_deadlines:
                calendar_events.append({
                    "id": deadline.get("deadline_id"),
                    "title": deadline.get("title"),
                    "start": deadline.get("date"),
                    "end": deadline.get("date"),  # Same as start for deadlines
                    "description": deadline.get("description", ""),
                    "type": "deadline"
                })
            
            # In a real implementation, this would generate an iCal file or integration data
            # For demonstration, we'll return the events in a format suitable for calendar widgets
            
            return {
                "status": "success",
                "user_id": user_id,
                "calendar_events": calendar_events,
                "total_events": len(calendar_events),
                "ical_available": True,  # Simulated
                "integration_instructions": "In a real implementation, you would add these events to your calendar by subscribing to the provided iCal URL or downloading the calendar file."
            }
            
        except Exception as e:
            logger.error(f"Error generating calendar integration: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to generate calendar integration: {str(e)}"
            }

# For testing
if __name__ == "__main__":
    # This would be for local testing
    service = LegalNewsAndCaseTracker()
    
    # Test legal updates
    user_id = str(uuid.uuid4())
    result = service.subscribe_to_updates(user_id, ["family_law", "tax_law"])
    print(json.dumps(result, indent=2)) 