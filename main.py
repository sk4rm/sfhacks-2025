import pathlib

from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import json
import re, os
from datetime import datetime
from bson.objectid import ObjectId

# MongoDB related imports (ensure these are set up correctly in your project)
from configuration import collection
from database.schemas import all_tasks
from database.models import Todo

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY not found in environment variables.")

# Configure your Gemini API key and model
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Initialize FastAPI app and set up Jinja2 templates (adjust templates directory as needed)
app = FastAPI()
templates = Jinja2Templates(directory=pathlib.Path(__file__).parent / "templates")
router = APIRouter()
app.include_router(router)
# ---------------- Gemini Functionality ----------------

# #####FETCHING DATA FROM MONGODB#####
@router.get("/fetch_test2_data")
async def fetch_test2_data():
    """
    Fetches all documents from the test2_data collection in MongoDB.
    """
    try:
        # Fetch all documents from the test2_data collection
        data = list(collection.find({}, {"_id": 0}))  # Exclude the _id field if not needed     
        if not data:
            raise HTTPException(status_code=404, detail="No data found in the test2_data collection.")
        return {"status_code": 200, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from MongoDB: {e}")
# #######################



###Handling form submission######
@router.post("/submit_health_form")
async def submit_health_form(data: dict):
    """
    Handles the submission of the health form and processes the data.
    """
    try:
        # Log the received data
        print("Received data:", data)

        # Delete all previous data in the collection
        collection.delete_many({})  # Deletes all documents in the collection

        # Save the data to MongoDB
        result = collection.insert_one(data)

        # Return a success response
        return {"status_code": 200, "message": "Form submitted successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")



########dispay health form in root######
# filepath: /Users/hlathirinaing/CS/GitHub/sfhacks-2025/main.py
@router.get("/", response_class=HTMLResponse)
async def display_health_form(request: Request):
    """
    Displays the health form HTML page.
    """
    return templates.TemplateResponse("health_form.html", {"request": request})


@router.get("/recommendations", response_class=HTMLResponse)
async def get_recommendations(request: Request):
    try:
        # Fetch all documents without any filter
        health_cases = list(collection.find({}))
        if not health_cases:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "recommendations": [],
                "message": "No health cases found in the database."
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from MongoDB: {e}")

    recommendations = []
    # Process each health case to generate recommendations
    for i, case in enumerate(health_cases, start=1):
        case.pop('_id', None)
        prompt = (
            "Please act like a medical advisor since I just use the information you provide as a reference. "
            "Based on the following health data, what are daily supplements that you would recommend "
            "(provide only one to explain each supplement you suggest and focus only on supplements, no extra text)?\n"
        )
        for key, value in case.items():
            prompt += f"- {key.replace('_', ' ').title()}: {value}\n"

        try:
            response = model.generate_content(prompt)
            supplements = response.text.strip().splitlines()

            # Filter out unwanted lines:
            # Remove any line starting with "Case" (like "Case 1:")
            # and any line starting with an introductory phrase like "Okay, based on"
            supplements = [
                line for line in supplements 
                if not re.match(r"^Case\s*\d+:", line.strip()) 
                   and not line.strip().lower().startswith("okay, based on")
            ]
            
            # Further clean up bullet points and markdown formatting
            supplements = [re.sub(r'^\*\*\s?|\*\*\s?', '', supp.strip()) for supp in supplements]
            supplements = [re.sub(r'^\* ', '', supp) for supp in supplements]

            recommendations.append({
                # Remove case numbering if not needed in the output:
                'supplements': supplements
            })
        except Exception as e:
            print(f"Error processing case {i}: {e}")
            continue

    return templates.TemplateResponse("index.html", {
        "request": request,
        "recommendations": recommendations
    })



# @router.get("/recommendations/{id}", response_class=HTMLResponse)
# async def get_recommendations(request: Request, id: int):
#     """
#     Fetches health data for a specific user_id from MongoDB, generates supplement recommendations
#     using Gemini AI, and renders an HTML page with the recommendations.
#     """
#     try:
#         # Fetch data for the specific user_id from the MongoDB collection
#         health_case = collection.find_one({"id": id}, {"_id": 0})  # Exclude the _id field if not needed
#         if not health_case:
#             raise HTTPException(status_code=404, detail=f"No data found for id {id}.")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching data from MongoDB: {e}")

#     # Build the prompt using the case data
#     prompt = (
#         "Please act like a medical advisor since I just use the information you provide as a reference. "
#         "Based on the following health data, what are daily supplements that you would recommend (provide only one to explain each supplement you suggest and also focus only on supplements no extra text)?\n"
#     )
#     for key, value in health_case.items():
#         prompt += f"- {key.replace('_', ' ').title()}: {value}\n"

#     # Generate recommendations from Gemini
#     try:
#         response = model.generate_content(prompt)
#         supplements = response.text.strip().splitlines()

#         # Clean up the list items by removing bullet points and markdown formatting
#         supplements = [re.sub(r'^\*\*\s?|\*\*\s?', '', supp.strip()) for supp in supplements]
#         supplements = [re.sub(r'^\* ', '', supp) for supp in supplements]

#         recommendations = {
#             'id': id,
#             'supplements': supplements
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating recommendations: {e}")

#     # Render the recommendations using an HTML template (index.html)
#     return templates.TemplateResponse("index.html", {"request": request, "recommendations": [recommendations]})



# #### GETTING ALL USERS DATA FROM JSON FILE AND DISPLAYING ALL CASES OUTPUT ######
# @router.get("/recommendations", response_class=HTMLResponse)
# async def get_recommendations(request: Request):
#     """
#     Reads health data from a JSON file, generates supplement recommendations
#     using Gemini AI, and renders an HTML page with the recommendations.
#     """
#     try:
#         # Fetch data from the MongoDB collection
#         health_cases = list(collection.find({"is_deleted": False}, {"_id": 0}))  # Exclude the _id field if not needed
#         if not health_cases:
#             return templates.TemplateResponse("index.html", {"request": request, "recommendations": [], "message": "No health cases found in the database."})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching data from MongoDB: {e}")

#     case_num = 0
#     recommendations = []
    
#     for case in health_cases:
#         case_num += 1
#         # Build the prompt using the case data
#         prompt = (
#             "Please act like a medical advisor since I just use the information you provide as a reference. "
#             "Based on the following health data, what are daily supplements that you would recommend (provide only one to explain each supplement you suggest and also focus only on supplements no extra text)?\n"
#         )
#         for key, value in case.items():
#             prompt += f"- {key.replace('_', ' ').title()}: {value}\n"

#         # Generate recommendations from Gemini
#         response = model.generate_content(prompt)
#         supplements = response.text.strip().splitlines()

#         # Clean up the list items by removing bullet points and markdown formatting
#         supplements = [re.sub(r'^\*\*\s?|\*\*\s?', '', supp.strip()) for supp in supplements]
#         supplements = [re.sub(r'^\* ', '', supp) for supp in supplements]

#         recommendations.append({
#             'case_num': case_num,
#             'supplements': supplements
#         })

#     # Render the recommendations using an HTML template (index.html)
#     print(recommendations)
#     return templates.TemplateResponse("index.html", {"request": request, "recommendations": recommendations})

# ---------------- MongoDB Endpoints ----------------
@router.get("/get_todos")
async def get_all_todos():
    """
    Retrieves all non-deleted todo tasks from the MongoDB collection.
    """
    data = collection.find({"is_deleted": False})
    return all_tasks(data)

@router.post("/create_task")
async def create_task(new_task: Todo):
    """
    Creates a new todo task.
    """
    try:
        resp = collection.insert_one(dict(new_task))
        return {"status_code": 200, "id": str(resp.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Some error occurred: {e}")

@router.put("/update/{task_id}")
async def update_task(task_id: str, updated_task: Todo):
    """
    Updates an existing task identified by task_id.
    """
    try:
        _id = ObjectId(task_id)
        existing_doc = collection.find_one({"_id": _id, "is_deleted": False})
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Task does not exist")
        updated_task.updated_at = datetime.timestamp(datetime.now())
        collection.update_one({"_id": _id}, {"$set": dict(updated_task)})
        return {"status_code": 200, "message": "Task updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task update failed: {e}")

@router.delete("/delete/{task_id}")
async def delete_task(task_id: str):
    """
    Soft-deletes a task by setting is_deleted to True.
    """
    try:
        _id = ObjectId(task_id)
        existing_doc = collection.find_one({"_id": _id, "is_deleted": False})
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Task does not exist")
        collection.update_one({"_id": _id}, {"$set": {"is_deleted": True}})
        return {"status_code": 200, "message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task deletion failed: {e}")

# Include the MongoDB router in the main FastAPI app
app.include_router(router)

# ---------------- Application Startup ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


#------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------

# from fastapi import FastAPI, APIRouter, HTTPException
# from configuration import collection
# from database.schemas import all_tasks
# from database.models import Todo
# from bson.objectid import ObjectId
# from datetime import datetime

# app = FastAPI()
# router = APIRouter()
# @router.get("/")
# async def get_all_todos():
#     data = collection.find({"is_deleted": False}) #if we just wanna pass id - put id in () - here we wanna get all the data so left it blank
#     return all_tasks (data)

# @router.post("/")
# async def create_task(new_task: Todo):#the data should be type todo
#     try:
#         resp = collection.insert_one(dict(new_task))
#         return {"status_code": 200, "id": str(resp.inserted_id)}
#     except Exception as e:
#         return HTTPException(status_code=500, detail= f"Some error occurred{e}")

# @router.put("/{task_id}")
# async def update_task(task_id:str,updated_task: Todo):
#     try:
#         id = ObjectId(task_id)
#         existing_doc = collection.find_one ({"_id": id, "is_deleted": False})
#         if not existing_doc:
#             return HTTPException(status_code=404, detail= f"Task does not exist")
#         updated_task.updated_at = datetime.timestamp(datetime.now())
#         resp = collection.update_one({"_id": id}, {"$set": dict(updated_task)})
#         return {"status_code":200, "message": "Task updated successfully"}

#     except Exception as e:
#         return HTTPException(status_code=500, detail= f"Task does not exist{e}")

# @router.delete("/{task_id}")
# async def delete_task (task_id:str):
#     try:
#         id = ObjectId(task_id)
#         existing_doc = collection.find_one ({"_id": id, "is_deleted": False})
#         if not existing_doc:
#             return HTTPException(status_code=404, detail= f"Task does not exist")
#         resp = collection.update_one({"_id": id}, {"$set": {"is_deleted": True}})
#         return {"status_code":200, "message": "Task deleted successfully"}

#     except Exception as e:
#         return HTTPException(status_code=500, detail= f"Task does not exist{e}")

# app.include_router(router)