import os
import pathlib

from dotenv import load_dotenv
from google import genai
import xml.etree.ElementTree as ET

from models import DailyAverageRecord

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")


def generate_json(xml_in, json_out):
    """
    Parse and process Apple HealthKit data exported in XML
    :param xml_in: The path to the XML file containing data from Apple HealthKit
    :param json_out: The path to the JSON file to be generated
    """
    tree = ET.parse(xml_in)
    root = tree.getroot()
    daily_averages = {}

    for element in root.iter("Record"):
        end_date = element.get("endDate").split(" ")[0]

        value = element.get("value")
        if not value.replace(".", "", 1).isdigit():
            continue

        identifier = element.get("type")
        if "Identifier" in identifier:
            identifier = identifier.split("Identifier")[1]

        unit = element.get("unit")

        key = f"{end_date}:{identifier}"
        if not daily_averages.get(key):
            daily_averages[key] = DailyAverageRecord(identifier, unit, end_date)
        daily_averages[key].update(float(value))

    with open(json_out, "w") as outfile:
        output = ""
        for key in daily_averages.keys():
            output += f"{daily_averages[key]}\n"
        outfile.write(output)


def gemini_suggest(json_path, api_key=GEMINI_API_KEY):
    """
    Upload files to Gemini for analysis

    :param json_path: The path to the data JSON file
    :param api_key: The API key to use
    """
    client = genai.Client(api_key=api_key)
    prompt = """Analyse the following health data export from Apple HealthKit.
    Look out for potential trends that may indicate any deficiency or future health risks.
    Then, suggest supplements that could help address those deficiencies.
    The user wants personalized suggestions on health supplements to improve their health based *specifically* on this data summary.
    Focus on trends, consistency, and suggest realistic ways to maintain or better their health.
    Keep the tone encouraging and supportive.
    IMPORTANT: Do NOT give medical advice. Frame suggestions as general wellness tips related to health. Output should be formatted using Markdown."""

    try:
        uploaded_file = client.files.upload(file=json_path)
        response = client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=[prompt, uploaded_file]
        )
    except Exception as e:
        print(e)
        return

    for chunk in response:
        print(chunk.text, end="")


if __name__ == "__main__":
    xml_path = pathlib.Path(__file__).parent / "data" / "export" / "apple_health_export" / "export.xml"
    json_path = pathlib.Path(__file__).parent / "data" / "data.txt"

    with open(xml_path, "r") as file:
        generate_json(
            xml_in=xml_path,
            json_out=json_path
        )

        gemini_suggest(json_path, api_key=GEMINI_API_KEY)
