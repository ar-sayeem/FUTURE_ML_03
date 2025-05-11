from flask import Flask, render_template, request
import json
import random
import datetime
import re

app = Flask(__name__)

# Load intents
with open('data/intents.json') as file:
    intents = json.load(file)

@app.route('/')
def home():
    # Pass current time to the template for the welcome message timestamp
    current_time = datetime.datetime.now().strftime('%I:%M %p')
    return render_template('index.html', current_time=current_time)

@app.route('/get', methods=['POST'])
def chatbot_response():
    user_input = request.form['msg'].lower()
    response = get_response(user_input)
    return response

def get_response(user_input):
    user_input = user_input.lower()
    
    # Check for exact matches or very close matches first
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            pattern_lower = pattern.lower()
            # Check for exact match
            if pattern_lower == user_input:
                return random.choice(intent['responses'])
            # Check for nearly exact match (user input contains pattern exactly)
            elif pattern_lower in user_input and len(pattern_lower) > 3:  # Avoid matching very short patterns
                # Calculate what percentage of the user input the pattern represents
                match_ratio = len(pattern_lower) / len(user_input)
                if match_ratio > 0.7:  # If pattern is at least 70% of user input
                    return random.choice(intent['responses'])
    
    # Then check for word-by-word matches
    user_words = set(re.findall(r'\b\w+\b', user_input))
    
    best_match = None
    highest_score = 0
    
    for intent in intents['intents']:
        intent_score = 0
        intent_match_count = 0
        
        for pattern in intent['patterns']:
            pattern_words = set(re.findall(r'\b\w+\b', pattern.lower()))
            
            # Skip empty patterns
            if not pattern_words:
                continue
                
            # Calculate how many words match
            matching_words = user_words.intersection(pattern_words)
            
            if matching_words:
                # Calculate match score as percentage of pattern words that matched
                pattern_score = len(matching_words) / len(pattern_words)
                
                # Boost score for longer matches
                if len(matching_words) > 1:
                    pattern_score *= (1 + 0.2 * len(matching_words))
                
                # Further boost score for key words (might be more important in the pattern)
                key_words = ['order', 'shipping', 'return', 'product', 'payment', 'help']
                for word in matching_words:
                    if word in key_words:
                        pattern_score *= 1.2
                        break
                
                # Track best score for this intent
                if pattern_score > intent_score:
                    intent_score = pattern_score
                    intent_match_count += 1
        
        # Final score combines best pattern match with how many patterns matched
        final_score = intent_score * (1 + (0.1 * min(intent_match_count, 3)))
        
        # Check if this is a better match than our current best
        if final_score > highest_score:
            highest_score = final_score
            best_match = intent
    
    # If we found a good match (more than 40% match), use it
    # Lowered threshold to catch more potential matches
    if highest_score >= 0.4 and best_match:
        return random.choice(best_match['responses'])
    
    # Handle specific keywords for common queries
    keyword_responses = {
        'order status': "To check your order status, please provide your order number and I can look that up for you.",
        'track': "You can track your order by going to the 'Orders' section in your account or by using the tracking number provided in your shipping confirmation email.",
        'return': "Our return policy allows returns within 30 days of purchase. Would you like more details about the return process?",
        'refund': "Refunds are typically processed within 5-7 business days after we receive your returned item. Is there a specific refund you're inquiring about?",
        'shipping': "We offer standard shipping (3-5 business days), express shipping (1-2 business days), and same-day delivery in select areas. Which shipping option would you like to know more about?",
        'delivery': "Delivery times vary depending on your location and chosen shipping method. Standard delivery takes 3-5 business days, while express shipping delivers in 1-2 business days.",
        'payment': "We accept all major credit cards, PayPal, Apple Pay, and Google Pay. Are you having issues with a payment method?",
        'contact': "You can reach our customer service team at support@example.com or call us at 1-800-123-4567 during business hours (9 AM - 5 PM EST).",
        'hours': "We're open Monday through Friday from 9 AM to 8 PM, and weekends from 10 AM to 6 PM.",
        'price': "Our prices vary by product. Could you specify which item you're interested in?",
        'discount': "We currently offer a 10% discount for first-time customers, and seasonal sales throughout the year. Would you like to join our mailing list to be notified of upcoming promotions?",
        'help': "I'm here to help! Please let me know what specific information or assistance you need.",
        'products': "We offer a wide range of products including smartphones, laptops, tablets, smart home devices, audio equipment, and accessories. Our most popular categories are gaming laptops and wireless earbuds.",
        'sell': "We offer a wide range of products including smartphones, laptops, tablets, smart home devices, audio equipment, and accessories. Is there a specific category you're interested in?",
        'store': "We have stores in major cities across the country. You can also shop online with home delivery or in-store pickup options. Would you like to find the nearest store to you?"
    }
    
    # Check if any keywords appear in the user input
    for keyword, response in keyword_responses.items():
        if keyword in user_input:
            return response
    
    # If we get here, we need a fallback response
    # Look for default intent for fallback responses
    default_responses = next((intent['responses'] for intent in intents['intents'] if intent['tag'] == 'default'), None)
    
    if default_responses:
        return random.choice(default_responses)
    else:
        # Ultimate fallback if no default intent exists
        return "I'm not sure I understand. Could you rephrase that or let me know what specific information you need help with?"

if __name__ == '__main__':
    app.run(debug=True)