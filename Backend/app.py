from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import re
from datetime import datetime
import random
import time
import uuid
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import logging
import traceback

# Import Vertex AI functions from main.py
from main import (
    init_vertex_ai, 
    process_legal_query, 
    summarize_chat_history,
    voice_to_text,
    text_to_speech
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='../Front-End')
CORS(app)  # Enable Cross-Origin Resource Sharing

# Download NLTK resources (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Load legal database (placeholder for demonstration)
def load_legal_database():
    # In a real application, this might connect to an actual database
    # For demonstration, we'll use a simple dictionary
    return {
        "cases": {
            "smith_v_jones": {
                "title": "Smith v. Jones (2019)",
                "summary": "The court ruled that employers must provide reasonable accommodations for employees with disabilities.",
                "ruling": "In favor of the plaintiff",
                "precedent": "Established that the burden of proof lies with the employer to show undue hardship."
            },
            "patel_v_city_council": {
                "title": "Patel v. City Council (2020)",
                "summary": "Challenge to a municipal zoning ordinance that restricted home-based businesses.",
                "ruling": "In favor of the plaintiff",
                "precedent": "Municipalities must show a compelling public interest for restricting home-based businesses."
            },
            "johnson_v_department_of_health": {
                "title": "Johnson v. Department of Health (2018)",
                "summary": "Dispute over medical privacy violations by a government agency.",
                "ruling": "In favor of the plaintiff",
                "precedent": "Government agencies must implement specific safeguards for handling medical information."
            },
            "rodriguez_v_state": {
                "title": "Rodriguez v. State (2021)",
                "summary": "Constitutional challenge to evidence collection procedures.",
                "ruling": "In favor of the defendant",
                "precedent": "Established new guidelines for digital evidence collection in criminal cases."
            }
        },
        "legal_topics": {
            "employment_law": {
                "title": "Employment Law",
                "subtopics": ["Discrimination", "Harassment", "Wrongful Termination", "Workers' Compensation"],
                "general_advice": "Employment law covers the rights and obligations of employers and employees. Common issues include discrimination, harassment, fair wages, and workplace safety."
            },
            "family_law": {
                "title": "Family Law",
                "subtopics": ["Divorce", "Child Custody", "Adoption", "Child Support", "Alimony"],
                "general_advice": "Family law addresses legal issues related to family relationships, including marriage, divorce, child custody, and adoption proceedings."
            },
            "property_law": {
                "title": "Property Law",
                "subtopics": ["Real Estate", "Landlord-Tenant", "Property Rights", "Zoning"],
                "general_advice": "Property law governs the various forms of ownership and tenancy in real property and personal property."
            },
            "criminal_law": {
                "title": "Criminal Law",
                "subtopics": ["Felonies", "Misdemeanors", "Criminal Procedure", "Rights of the Accused"],
                "general_advice": "Criminal law deals with behavior that is considered harmful to society and is prosecuted by the state."
            }
        }
    }

# Initialize the legal database
legal_database = load_legal_database()

# Initialize chat history storage
# In a production environment, this would be a database
chat_histories = {}

# Anxiety keywords for emotion detection
anxiety_keywords = [
    'worried', 'scared', 'afraid', 'anxious', 'stressed', 'fear', 'nervous', 'panic', 
    'terrified', 'concerned', 'frightened', 'help', 'don\'t know what to do'
]

# Initialize Vertex AI
try:
    # Check for credentials file
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'service-account-key.json')
    init_vertex_ai(credentials_path if os.path.exists(credentials_path) else None)
    logger.info("Vertex AI initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Vertex AI: {str(e)}")
    logger.error(traceback.format_exc())
    # We'll continue running even if Vertex AI fails to initialize
    # and fall back to basic functionality

# Serve the frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# API endpoint for chat (enhanced with Vertex AI)
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    use_vertex_ai = data.get('use_vertex_ai', True)  # Allow client to toggle between basic and advanced
    
    # Initialize session if new
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    
    # Add user message to history
    chat_histories[session_id].append({
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.now().isoformat()
    })
    
    try:
        if use_vertex_ai:
            # Use advanced Vertex AI processing
            result = process_legal_query(user_message, session_id, chat_histories[session_id])
            response = result['response']
            
            # Add metadata to the response
            metadata = result['metadata']
            response_type = result['response_type']
        else:
            # Fallback to basic processing
            response = generate_response(user_message, session_id)
            metadata = {}
            response_type = "basic"
    
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        logger.error(traceback.format_exc())
        # Fallback to basic processing if Vertex AI fails
        response = generate_response(user_message, session_id)
        metadata = {"error": str(e)}
        response_type = "error_fallback"
    
    # Add bot response to history
    chat_histories[session_id].append({
        'role': 'bot',
        'content': response,
        'timestamp': datetime.now().isoformat(),
        'response_type': response_type
    })
    
    return jsonify({
        'response': response,
        'session_id': session_id,
        'response_type': response_type,
        'metadata': metadata
    })

# API endpoint to get chat history
@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id):
    if session_id in chat_histories:
        return jsonify({
            'history': chat_histories[session_id]
        })
    else:
        return jsonify({
            'history': [],
            'error': 'Session not found'
        }), 404

# Enhanced API endpoint to get chat history summary
@app.route('/api/summary/<session_id>', methods=['GET'])
def get_summary(session_id):
    if session_id not in chat_histories:
        return jsonify({
            'summary': '',
            'error': 'Session not found'
        }), 404
    
    try:
        summary = summarize_chat_history(chat_histories[session_id])
        return jsonify({
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error summarizing chat: {str(e)}")
        return jsonify({
            'summary': 'Unable to generate summary at this time.',
            'error': str(e)
        }), 500

# API endpoint to search chat history
@app.route('/api/search', methods=['POST'])
def search_history():
    data = request.json
    session_id = data.get('session_id', '')
    query = data.get('query', '').lower()
    
    if not session_id or session_id not in chat_histories:
        return jsonify({
            'results': [],
            'error': 'Session not found'
        }), 404
    
    results = []
    for message in chat_histories[session_id]:
        if query in message['content'].lower():
            results.append(message)
    
    return jsonify({
        'results': results
    })

# API endpoint for case law lookup
@app.route('/api/case-law', methods=['POST'])
def case_law_lookup():
    data = request.json
    query = data.get('query', '').lower()
    
    results = []
    for case_id, case_data in legal_database['cases'].items():
        if query in case_id.lower() or query in case_data['title'].lower() or query in case_data['summary'].lower():
            results.append(case_data)
    
    return jsonify({
        'results': results
    })

# API endpoint for legal topic information
@app.route('/api/legal-topics', methods=['POST'])
def legal_topics():
    data = request.json
    query = data.get('query', '').lower()
    
    results = []
    for topic_id, topic_data in legal_database['legal_topics'].items():
        if query in topic_id.lower() or query in topic_data['title'].lower() or any(query in subtopic.lower() for subtopic in topic_data['subtopics']):
            results.append(topic_data)
    
    return jsonify({
        'results': results
    })

# Voice processing endpoints
@app.route('/api/voice-to-text', methods=['POST'])
def handle_voice_to_text():
    """Handle voice to text conversion"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    # Save the audio file temporarily
    temp_path = f"temp_audio_{uuid.uuid4()}.wav"
    audio_file.save(temp_path)
    
    try:
        # Process with Vertex AI
        text = voice_to_text(temp_path)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify({'text': text})
    except Exception as e:
        logger.error(f"Error in voice-to-text: {str(e)}")
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify({'error': str(e)}), 500

@app.route('/api/text-to-speech', methods=['POST'])
def handle_text_to_speech():
    """Handle text to speech conversion"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Process with Vertex AI
        audio_path = text_to_speech(text)
        
        # In a real implementation, this would return a URL to the generated audio
        # For now, we'll return a placeholder
        return jsonify({'audio_url': audio_path})
    except Exception as e:
        logger.error(f"Error in text-to-speech: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Generate a response based on the user's message (basic fallback method)
def generate_response(message, session_id):
    # Check for anxiety indicators
    if contains_anxiety_keywords(message):
        return generate_empathetic_response(message)
    
    # Check for case law queries
    if any(keyword in message.lower() for keyword in ['case', 'v.', 'vs', 'precedent']):
        return generate_case_law_response(message)
    
    # Check for specific legal topics
    for topic_id, topic_data in legal_database['legal_topics'].items():
        if topic_id.replace('_', ' ') in message.lower() or topic_data['title'].lower() in message.lower():
            return generate_topic_response(topic_data)
    
    # Generate a generic response
    return generate_generic_response(message)

# Check if the message contains anxiety keywords
def contains_anxiety_keywords(message):
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in anxiety_keywords)

# Generate an empathetic response for anxious users
def generate_empathetic_response(message):
    empathetic_responses = [
        "I understand this might be causing you stress. Let's break this down into manageable steps.",
        "It's completely normal to feel anxious about legal matters. Let me help you understand the basics first.",
        "I can see you're concerned about this situation. Let's approach this calmly and methodically.",
        "Legal processes can be intimidating, but I'm here to help you understand what might happen next."
    ]
    
    response = random.choice(empathetic_responses)
    
    # Add a disclaimer
    response += "\n\nPlease remember that I'm providing general information, not legal advice. For specific guidance on your situation, it's best to consult with a licensed attorney."
    
    return response

# Generate a response about case law
def generate_case_law_response(message):
    # Extract potential case names (simplified method)
    words = message.split()
    potential_cases = []
    
    for i, word in enumerate(words):
        if word.lower() == 'v.' or word.lower() == 'vs' and i > 0 and i < len(words) - 1:
            potential_case = f"{words[i-1]} {word} {words[i+1]}"
            potential_cases.append(potential_case)
    
    # If a specific case is mentioned, try to match it
    for case_id, case_data in legal_database['cases'].items():
        case_title = case_data['title'].lower()
        if any(potential_case.lower() in case_title for potential_case in potential_cases):
            return f"Regarding {case_data['title']}: {case_data['summary']} The ruling was {case_data['ruling']}. {case_data['precedent']}\n\nPlease note that this is a simplified summary. Real legal analysis would require examining the full case text and subsequent interpretations."
    
    # If no specific case is found, provide a generic response
    return "Based on the case law you're inquiring about, I would need to research the specific precedents to provide accurate information. In a real legal database, I would be able to access comprehensive case law summaries. Please consult with a legal professional for detailed analysis of specific cases."

# Generate a response about a legal topic
def generate_topic_response(topic_data):
    response = f"Regarding {topic_data['title']}: {topic_data['general_advice']}\n\n"
    response += f"This topic includes the following subtopics: {', '.join(topic_data['subtopics'])}.\n\n"
    response += "Please note that this is general information only. Legal situations vary widely based on jurisdiction and specific circumstances."
    return response

# Generate a generic response
def generate_generic_response(message):
    # Analyze the message to determine intent
    tokens = word_tokenize(message.lower())
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    
    # Count word frequencies to identify key topics
    word_counts = Counter(filtered_tokens)
    common_words = word_counts.most_common(3)
    
    # Generic responses based on common legal queries
    if any(word in ['sue', 'lawsuit', 'litigation'] for word in filtered_tokens):
        return "Regarding lawsuits and litigation: Before initiating a lawsuit, it's typically advisable to attempt resolution through demand letters or alternative dispute resolution. The litigation process generally involves filing a complaint, discovery, potential motions, and either settlement or trial. Timelines and procedures vary significantly by jurisdiction and case type. Please consult with an attorney to discuss your specific situation."
    
    if any(word in ['contract', 'agreement', 'sign'] for word in filtered_tokens):
        return "Regarding contracts: A valid contract generally requires an offer, acceptance, consideration (something of value exchanged), legal purpose, and competent parties. Before signing any contract, it's important to carefully review all terms, understand your obligations, and consider having it reviewed by an attorney. Be particularly attentive to termination clauses, liability limitations, and dispute resolution mechanisms."
    
    if any(word in ['divorce', 'custody', 'alimony', 'marriage'] for word in filtered_tokens):
        return "Regarding family law matters: Family law issues such as divorce, child custody, and support arrangements vary significantly by jurisdiction. Most jurisdictions consider factors such as the best interests of the child for custody determinations. These matters often benefit from mediation to reach amicable agreements. Given the personal and complex nature of family law, consulting with a family law attorney is highly recommended."
    
    # Default response if no specific topic is identified
    return "I understand you're seeking legal information. To provide more relevant guidance, could you please specify what legal topic or situation you're interested in? For example, you might ask about employment law, property disputes, family law, or contract issues. Remember that I can only provide general information, not legal advice tailored to your specific circumstances."

# Add health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Backend server is running"}), 200

# Main entry point
if __name__ == '__main__':
    app.run(debug=True, port=5000)
