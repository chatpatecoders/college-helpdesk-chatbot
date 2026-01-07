import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()


##if not api_key:
    # Agar .env fail ho jaye toh direct yahan paste karke test karo
    #api_key = "AIzaSyAXCkA5BXxrzKh3Mv-idIrDfik4QmhnQkE"
MY_API_KEY = "AIzaSyAXCkA5BXxrzKh3Mv-idIrDfik4QmhnQkE"

    
# --- GEMINI SETUP ---
try:
    genai.configure(api_key=MY_API_KEY)
    model = genai.GenerativeModel('gemini-3-flash-preview')
    print("✅ Gemini System Initialized")
except Exception as e:
    print(f"❌ Gemini Setup Error: {e}")
app = Flask(__name__)

# --- FIREBASE SETUP ---
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# 💡 Ye variable pichle matches ko yaad rakhega
pending_options = {}

def search_firebase(user_question):
    try:
        user_question = user_question.lower().strip()
        docs = db.collection("faq").get()
        matches = []
        for doc in docs:
            data = doc.to_dict()
            if user_question in data.get("question", "").lower():
                matches.append(data)
        return matches
    except Exception as e:
        print(f"Error: {e}")
        return []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global pending_options
    try:
        user_input = request.json.get("message", "").strip()

        # 1. Check karo kya user ne koi Number (1, 2, 3) type kiya hai?
        if user_input.isdigit() and pending_options:
            choice = int(user_input) - 1
            if 0 <= choice < len(pending_options):
                answer = pending_options[choice]['answer']
                pending_options = {} # Answer dene ke baad clear kar do
                return jsonify({"reply": answer})
            else:
                return jsonify({"reply": "Invalid choice. Please select a valid number from the list."})

        # 2. Normal Search logic
        matches = search_firebase(user_input)

        if len(matches) == 1:
            pending_options = {} 
            return jsonify({"reply": matches[0]["answer"]})

        if len(matches) > 1:
            pending_options = matches # Options ko save kar lo
            response_text = "I found multiple related questions. Please type the number of your choice:\n\n"
            for i, item in enumerate(matches, 1):
                response_text += f"{i}. {item['question']}\n"
            return jsonify({"reply": response_text})

        # 3. AI Fallback
        pending_options = {} # Reset if no match
        response = model.generate_content(f"Answer as a University of Allahabad helpdesk, You only have to answer related to University of Allahabad: {user_input}")
        return jsonify({"reply": response.text})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Sorry bro, abhi mera AI dimaag thoda thaka hua hai. Baad mein try karo!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
