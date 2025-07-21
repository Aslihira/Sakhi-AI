import os
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import google.generativeai as genai
import datetime
import time
import json
import random
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-pcod-key' # IMPORTANT: Change this to a strong, unique secret key for production!
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configure API Key securely
API_key = os.getenv("GEMINI_API_KEY")
if not API_key:
    print("Warning: GEMINI_API_KEY environment variable not set. Please set it for production.")
    # For local testing, you can temporarily hardcode it here, but REMOVE FOR DEPLOYMENT!
    API_key = "AIzaSyBOYiOdvlrP2PGjbqYr5mrHgQoMy7lhn44" # Replace with your actual key if testing locally without environment variable
genai.configure(api_key=API_key)

# Initialize the model
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Create user profile storage (in-memory for this demo)
# For a production app, you'd use a proper database (SQL, NoSQL)
user_profiles = {}

# Helper functions for PCOD/PCOS
def create_pcod_user_profile(name):
    """Create a new user profile for PCOD/PCOS context"""
    user_profiles[name] = {
        "name": name,
        "symptom_history": [],
        "period_logs": [],
        "lifestyle_preferences": {},
        "last_interaction": None,
        "mood_scores": [] # Could still be useful for general well-being
    }
    return user_profiles[name]

def symptom_assessment(user_name, symptoms_data):
    """Assess PCOD/PCOS symptoms and provide guidance."""
    if user_name not in user_profiles:
        create_pcod_user_profile(user_name)
    
    user_profile = user_profiles[user_name]
    user_profile["symptom_history"].append({
        "date": datetime.datetime.now().isoformat(),
        "symptoms": symptoms_data
    })
    
    # Construct a descriptive string of symptoms for the prompt
    symptom_list = []
    if symptoms_data.get('irregular_periods') == 'irregular':
        symptom_list.append("irregular periods")
    if symptoms_data.get('irregular_periods') == 'absent':
        symptom_list.append("absent periods")
    if symptoms_data.get('excess_hair'):
        symptom_list.append("excessive hair growth")
    if symptoms_data.get('acne'):
        symptom_list.append("persistent acne")
    if symptoms_data.get('weight_gain'):
        symptom_list.append("unexplained weight gain")
    if symptoms_data.get('hair_loss'):
        symptom_list.append("hair thinning or loss")
    if symptoms_data.get('fatigue'):
        symptom_list.append("fatigue")
    if symptoms_data.get('mood_swings'):
        symptom_list.append("mood swings or anxiety/depression")
    if symptoms_data.get('other_symptoms'):
        symptom_list.append(f"other concerns like: {symptoms_data['other_symptoms']}")

    symptoms_description = "You haven't reported any specific PCOD/PCOS-related symptoms at this time, which is great!"
    if symptom_list:
        symptoms_description = f"You've mentioned experiencing: {', '.join(symptom_list)}."

    prompt = f"""
    You are a compassionate, non-judgmental AI PCOD/PCOS support agent named Aura. Your purpose is to provide early, private, and empathetic guidance.
    {user_name}, you've used the symptom checker. {symptoms_description}

    Provide a warm and understanding response. Use a conversational tone and natural emojis like 🌸, ✨, 💡. Do NOT use bullet points or numbered lists.

    Your response should:
    1.  Acknowledge their input empathetically.
    2.  Gently explain that these symptoms are commonly associated with PCOD/PCOS, but that only a doctor can diagnose it.
    3.  Strongly encourage them to consider consulting a healthcare professional (e.g., a gynecologist or endocrinologist) for proper diagnosis and personalized advice. Emphasize that seeking medical opinion is a proactive and positive step.
    4.  Offer one very general, empowering self-care tip (e.g., observing their body, mindful living).
    5.  Assure them that they are not alone and you are here to provide information and support on their journey.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def period_logging(user_name, period_data):
    """Log period details and provide brief insights."""
    if user_name not in user_profiles:
        create_pcod_user_profile(user_name)
    
    user_profile = user_profiles[user_name]
    user_profile["period_logs"].append({
        "date": period_data.get('date'),
        "severity": period_data.get('severity'),
        "duration": period_data.get('duration'),
        "notes": period_data.get('notes')
    })
    
    prompt = f"""
    You are a supportive and understanding AI PCOD/PCOS companion named Aura, helping {user_name} track their cycle.
    {user_name}, you've just logged your period starting on {period_data.get('date')} with a {period_data.get('severity')} flow, lasting {period_data.get('duration')} days. You noted: "{period_data.get('notes')}".

    Provide an encouraging and informative response. Use a conversational tone and natural emojis like 📅, ✅, 💖. Do NOT use bullet points or numbered lists.

    Your response should:
    1.  Acknowledge the successful logging of their period.
    2.  Gently explain why tracking periods is particularly helpful for PCOD/PCOS (e.g., identifying patterns, providing data for doctors).
    3.  Suggest continuing to track, and mention other symptoms that could be logged alongside (e.g., mood, energy levels, pain).
    4.  End with an encouraging message about taking charge of their health journey.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def lifestyle_tips(user_name, lifestyle_data):
    """Generate personalized lifestyle and diet tips for PCOD/PCOS."""
    if user_name not in user_profiles:
        create_pcod_user_profile(user_name)
    
    user_profile = user_profiles[user_name]
    user_profile["lifestyle_preferences"] = lifestyle_data
    
    diet_info = lifestyle_data.get('diet_habits', 'You did not specify your diet habits.')
    exercise_info = lifestyle_data.get('exercise_frequency', 'You did not specify your exercise frequency.')

    prompt = f"""
    You are a helpful and practical AI PCOD/PCOS support agent named Aura, providing lifestyle guidance to {user_name}.
    {user_name}, you shared that your diet habits are: "{diet_info}" and your exercise frequency is: "{exercise_info}".

    Provide 3-4 actionable and encouraging lifestyle and diet tips relevant to PCOD/PCOS. Present them conversationally. Use encouraging emojis like 🌱, 🏃‍♀, 🧘‍♀. Do NOT use bullet points or numbered lists.

    Include tips related to:
    1.  Balanced eating (e.g., focusing on whole foods, specific food groups to consider).
    2.  Regular movement (e.g., types of exercise beneficial).
    3.  Stress management (e.g., simple practices).
    4.  Consistency and patience.

    Emphasize that these are general tips and a healthcare professional or nutritionist can provide tailored advice.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def understanding_pcod_pcos(user_name):
    """Provide educational information about PCOD/PCOS."""
    prompt = f"""
    You are an informative and clear AI PCOD/PCOS support agent named Aura, explaining PCOD/PCOS to {user_name}.
    Provide a concise, easy-to-understand overview of PCOD/PCOS. Use simple language and natural emojis like 💡, ✨, 📚. Do NOT use bullet points or numbered lists.

    Include:
    1.  A brief definition of PCOD/PCOS and its nature as a hormonal condition.
    2.  Key common symptoms.
    3.  A gentle note on its prevalence.
    4.  Emphasize that it's manageable and understanding it is the first step.
    5.  Suggest that this information is for awareness and not a substitute for medical diagnosis.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def connect_with_experts(user_name):
    """Provide information on connecting with healthcare professionals."""
    prompt = f"""
    You are a helpful and responsible AI PCOD/PCOS support agent named Aura, guiding {user_name} towards professional support.
    It's wonderful that you're exploring options to connect with experts for your PCOD/PCOS journey, {user_name}.

    Clearly outline 2-3 types of healthcare professionals who can help with PCOD/PCOS. Use a supportive and encouraging tone. Use emojis like 👩‍⚕, 🩺, 🌱. Do NOT use bullet points or numbered lists.

    For each type of professional, briefly explain their role.
    Conclude by advising them to discuss their symptoms with their primary care doctor for referrals or to seek out specialists directly, emphasizing that this is a positive step.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def general_pcod_chat(user_name, message):
    """Handle general chat messages related to PCOD/PCOS."""
    base_instructions = "You are a warm, empathetic, and encouraging AI PCOD/PCOS companion named Aura. Your responses should feel like a supportive friend talking. Use a conversational tone, be gentle, and integrate relevant emojis naturally to convey emotion and warmth, but don't overdo them. Do NOT use bullet points, asterisks, or numbered lists. Introduce suggestions smoothly within paragraphs."

    message_lower = message.lower()
    
    if any(word in message_lower for word in ['symptoms', 'what are pcos symptoms']):
        prompt_template = f"""
        {base_instructions}

        {user_name} has just asked about PCOD/PCOS symptoms.

        Your response should:
        1.  Briefly list 3-4 common symptoms of PCOD/PCOS.
        2.  Explain that these symptoms can vary and not everyone experiences all of them.
        3.  Gently suggest using the "Symptom Checker" feature for a more structured assessment.
        4.  Reinforce that self-assessment is for awareness and professional diagnosis is key.
        """
    elif any(word in message_lower for word in ['diet', 'what to eat', 'food for pcos']):
        prompt_template = f"""
        {base_instructions}

        {user_name} has just asked about diet for PCOD/PCOS.

        Your response should:
        1.  Provide 2-3 general principles for PCOD/PCOS friendly eating (e.g., whole foods, limiting processed items).
        2.  Mention that dietary changes can significantly impact management.
        3.  Gently suggest using the "Lifestyle & Diet Tips" feature for more personalized guidance.
        4.  Advise consulting a nutritionist for a tailored plan.
        """
    elif any(word in message_lower for word in ['exercise', 'workouts', 'physical activity']):
        prompt_template = f"""
        {base_instructions}

        {user_name} has just asked about exercise for PCOD/PCOS.

        Your response should:
        1.  Suggest 2-3 types of beneficial exercise (e.g., moderate intensity, strength training).
        2.  Explain the benefits (e.g., insulin sensitivity, weight management, mood).
        3.  Emphasize consistency and finding enjoyable activities.
        4.  Gently suggest using the "Lifestyle & Diet Tips" feature for more personalized guidance.
        """
    elif any(word in message_lower for word in ['irregular periods', 'missed periods']):
        prompt_template = f"""
        {base_instructions}

        {user_name} has just mentioned irregular or missed periods.

        Your response should:
        1.  Validate their concern, noting that irregular periods are a common sign of PCOD/PCOS.
        2.  Briefly explain why this happens (hormonal imbalance).
        3.  Suggest using the "Period Tracker" feature to log their cycles.
        4.  Strongly recommend seeing a doctor for evaluation.
        """
    elif any(word in message_lower for word in ['weight gain', 'losing weight']):
        prompt_template = f"""
        {base_instructions}

        {user_name} has just asked about weight gain or losing weight with PCOD/PCOS.

        Your response should:
        1.  Acknowledge that weight management can be challenging with PCOD/PCOS due to insulin resistance.
        2.  Offer gentle encouragement about sustainable lifestyle changes.
        3.  Briefly mention the importance of diet and exercise, and potentially stress management.
        4.  Suggest consulting a doctor or nutritionist for tailored advice.
        """
    elif any(word in message_lower for word in ['hair growth', 'acne', 'hair loss']):
        prompt_template = f"""
        {base_instructions}

        {user_name} has just mentioned skin/hair concerns like {message_lower}.

        Your response should:
        1.  Validate their feelings about these symptoms.
        2.  Explain that these are common androgen-related symptoms of PCOD/PCOS.
        3.  Suggest that effective management often involves a holistic approach (diet, lifestyle, and medical treatments).
        4.  Strongly recommend consulting a dermatologist or endocrinologist for specific treatment options.
        """
    else:
        # Default general conversational prompt if no specific keyword is detected
        prompt_template = f"""
        {base_instructions}

        {user_name} said: "{message}".

        Respond in a thoughtful and engaging way. Ask a gentle follow-up question if appropriate to keep the conversation flowing. Remember you are an AI and cannot give medical advice.
        """
    
    response_text = model.generate_content(prompt_template).text.strip()
    return response_text


# Web API endpoints
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle general chat messages related to PCOD/PCOS"""
    data = request.json
    message = data.get('message', '')
    
    user_name = session.get('user_name', data.get('user_name', 'Friend'))
    session['user_name'] = user_name 
    
    response_text = general_pcod_chat(user_name, message)
    
    return jsonify({
        'response': response_text,
        'type': 'general_pcod_chat',
        'user_name': user_name
    })

@app.route('/api/assess_symptoms', methods=['POST'])
def api_assess_symptoms():
    """Handle symptom checker submission"""
    data = request.json
    user_name = data.get('user_name', session.get('user_name', 'Friend'))
    session['user_name'] = user_name

    symptoms_data = {
        "last_period_date": data.get('last_period_date'),
        "irregular_periods": data.get('period_regularity'),
        "excess_hair": data.get('excess_hair'),
        "acne": data.get('acne'),
        "weight_gain": data.get('weight_gain'),
        "hair_loss": data.get('hair_loss'),
        "fatigue": data.get('fatigue'),
        "mood_swings": data.get('mood_swings'),
        "other_symptoms": data.get('other_symptoms')
    }
    
    response = symptom_assessment(user_name, symptoms_data)
    return jsonify({'response': response})

@app.route('/api/log_period', methods=['POST'])
def api_log_period():
    """Handle period tracker submission"""
    data = request.json
    user_name = data.get('user_name', session.get('user_name', 'Friend'))
    session['user_name'] = user_name

    period_data = {
        "date": data.get('date'),
        "severity": data.get('severity'),
        "duration": data.get('duration'),
        "notes": data.get('notes')
    }
    
    response = period_logging(user_name, period_data)
    return jsonify({'response': response})

@app.route('/api/get_lifestyle_tips', methods=['POST'])
def api_get_lifestyle_tips():
    """Handle lifestyle tips request"""
    data = request.json
    user_name = data.get('user_name', session.get('user_name', 'Friend'))
    session['user_name'] = user_name

    lifestyle_data = {
        "diet_habits": data.get('diet_habits'),
        "exercise_frequency": data.get('exercise_frequency')
    }
    
    response = lifestyle_tips(user_name, lifestyle_data)
    return jsonify({'response': response})

@app.route('/api/understanding_pcos', methods=['POST'])
def api_understanding_pcos():
    """Provide information on understanding PCOD/PCOS"""
    data = request.json
    user_name = data.get('user_name', session.get('user_name', 'Friend'))
    session['user_name'] = user_name
    
    response = understanding_pcod_pcos(user_name)
    return jsonify({'response': response})

@app.route('/api/expert_connect', methods=['POST'])
def api_expert_connect():
    """Provide information on connecting with experts"""
    data = request.json # This endpoint doesn't strictly need user_name, but keeping for consistency
    user_name = data.get('user_name', session.get('user_name', 'Friend'))
    session['user_name'] = user_name

    response = connect_with_experts(user_name)
    return jsonify({'response': response})


@app.route('/api/user-profile', methods=['GET'])
def get_user_pcod_profile():
    """Get current user profile for PCOD context"""
    user_name = session.get('user_name', 'Friend')
    if user_name in user_profiles:
        return jsonify(user_profiles[user_name])
    else:
        return jsonify(create_pcod_user_profile(user_name))

if __name__ == '__main__':
    print("🌸 AI PCOD/PCOS Support Agent - Web Version 🌸")
    print("Starting server...")
    # Make sure to set GEMINI_API_KEY as an environment variable or uncomment the hardcoded key for local testing.
    # In production, NEVER hardcode API keys.
    app.run(debug=True, host='0.0.0.0', port=5000)