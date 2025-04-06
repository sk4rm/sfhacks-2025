from dotenv import load_dotenv
import os
import pathlib

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from google import genai

import xml.etree.ElementTree as ET

import models
from models import DailyAverageRecord

#
# Environmental variables
#

load_dotenv()
ATLAS_DB_USERNAME = os.getenv("ATLAS_DB_USERNAME")
ATLAS_DB_PASSWORD = os.getenv("ATLAS_DB_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

URI = f"mongodb+srv://{ATLAS_DB_USERNAME}:{ATLAS_DB_PASSWORD}@sfhacks-2025-dev.3lwtvjo.mongodb.net/?retryWrites=true&w=majority&appName=sfhacks-2025-dev"

#
# API connections
#

# mongo = MongoClient(URI, server_api=ServerApi("1"))
#
# try:
#     mongo.admin.command("ping")
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)
#     exit(1)

genai = genai.Client(api_key=GEMINI_API_KEY)
prompt = """Analyse the following health data export from Apple HealthKit.
Look out for potential trends that may indicate any deficiency or future health risks.
Then, suggest supplements that could help address those deficiencies.
The user wants personalized suggestions on health supplements to improve their health based *specifically* on this data summary.
Focus on trends, consistency, and suggest realistic ways to maintain or better their health.
Keep the tone encouraging and supportive.
IMPORTANT: Do NOT give medical advice. Frame suggestions as general wellness tips related to health. Output should be formatted using Markdown."""

#
# Parse and process Apple HealthKit data exported in XML
#

file = pathlib.Path(__file__).parent / "data" / "export" / "apple_health_export" / "export.xml"
tree = ET.parse(file)
root = tree.getroot()
dailyAverages = {}

def main():
    for element in root.iter("Record"):
        endDate = element.get("endDate").split(" ")[0]

        value = element.get("value")
        if not value.replace(".", "", 1).isdigit():
            continue

        identifier = element.get("type")
        if "Identifier" in identifier:
            identifier = identifier.split("Identifier")[1]

        unit = element.get("unit")

        key = f"{endDate}:{identifier}"
        if not dailyAverages.get(key):
            dailyAverages[key] = DailyAverageRecord(identifier, unit, endDate)
        dailyAverages[key].update(float(value))

    processed_file = pathlib.Path(__file__).parent / "data" / "processed.txt"
    with open(processed_file, "w") as file:
        output = ""
        for key in dailyAverages.keys():
            output += f"{dailyAverages[key]}\n"
        file.write(output)

    #
    # Upload files to Gemini for analysis
    #

    try:
        xml = genai.files.upload(file=processed_file)
        processed_file.unlink()
        response = genai.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=[prompt, xml]
        )
    except Exception as e:
        print(e)
        return

    for chunk in response:
        print(chunk.text, end="")

if __name__ == "__main__":
    main()