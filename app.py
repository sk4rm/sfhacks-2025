from flask import Flask, render_template, jsonify
import google.generativeai as genai
import json
import re
# Initialize Flask app
app = Flask(__name__)

# Configure your Gemini API key
genai.configure(api_key="AIzaSyCB_5DqZ5Q3HiHgKqSexXhQ_A2TqI71KOk")
model = genai.GenerativeModel("gemini-2.0-flash")

@app.route('/')
def index():
    # Read data from the data.json file
    with open('data.json', 'r') as file:
        health_cases = json.load(file)

    # Process each health case and generate recommendations
    case_num = 0
    recommendations = []
    for case in health_cases:
        case_num += 1
        # Turn the case data into a prompt
        prompt = "Please act like a medical advisor since I just use the information you provide as a reference. Based on the following health data, what are daily supplements that you would recommend (provide only one to explain each supplement you suggest and also focus only on supplements no extra text)?\n"
        for key, value in case.items():
            prompt += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        # Send the prompt to Gemini AI and get the response
        response = model.generate_content(prompt)
        
        supplements = response.text.strip().splitlines()

        # Remove bullet points (*) and bold markdown (**)
        supplements = [re.sub(r'^\*\*\s?|\*\*\s?', '', supplement.strip()) for supplement in supplements]
        supplements = [re.sub(r'^\* ', '', supplement) for supplement in supplements]  # Remove leading '*'
        
        recommendations.append({
            'case_num': case_num,
            'supplements': supplements
        })
    
    # Render the template with the health cases and supplement recommendations
    return render_template('index.html', recommendations=recommendations)

if __name__ == '__main__':
    app.run(debug=True)
