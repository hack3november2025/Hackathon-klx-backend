import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import pymongo
from pymongo import MongoClient
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, or specify a list of allowed domains
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Set OpenAI API Key directly
openai.api_key = "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"

# MongoDB connection setup
client = MongoClient("mongodb+srv://hamza_jedidi:qWFf86xJXLX9pwOg@hackathon-klx-bd.jjvq6kg.mongodb.net/?appName=hackathon-klx-db")
db = client['hackathon_klx_db']  # Use the 'hackathon' database
job_offers_collection = db.job_offers  # The collection to store job offers

# Input validation class
class JobOfferRequest(BaseModel):
    summary: str
    tone: str = "inclusive"  # Default tone
    department: str = None
    location: str = None
    employment_type: str = None
    salary_range: str = None

# Endpoint to generate job offer
@app.post("/generate-job-offer")
async def generate_job_offer(request: JobOfferRequest):
    try:
        # Prepare the prompt for OpenAI
        prompt = f"""
        You are an HR expert with a deep understanding of language and recruitment. Given the following job description, generate a complete job offer in the following JSON format:

        {{
            "job_title": "(Inferred from the description)",
            "department": "(Inferred or provided)",
            "location": {{
                "city": "(Inferred or provided)",
                "work_type": "(Inferred or provided)"
            }},
            "employment_type": "(Full-time, part-time, etc.)",
            "salary_range": {{
                "min": "(inferred or provided)",
                "max": "(inferred or provided)",
                "currency": "(USD or local currency)"
            }},
            "job_summary": "(Inferred summary of the role)",
            "key_responsibilities": [
                .....
            ],
            "required_skills": [
                .....
            ],
            "required_skills_keywords": [
                .....
            ],
            "preferred_skills": [
                .....
            ],
            "preferred_skills_keywords": [
                .....
            ],
            "soft_skills": [
                .....
            ],
            "soft_skills_keywords": [
                .....
            ],
            "company_values_and_culture": {{
                "collaboration": "(Inferred or provided)",
                "ownership": "(Inferred or provided)",
                "diversity_and_inclusion": "(Inferred or provided)",
                "continuous_improvement": "(Inferred or provided)",
                "transparency": "(Inferred or provided)"
            }},
            "application_encouragement": "(Inferred or provided)"
        }}

        Tone: {request.tone}
        
        Role description: {request.summary}

        Department: {request.department if request.department else "Not provided"}
        Location: {request.location if request.location else "Not provided"}
        Employment Type: {request.employment_type if request.employment_type else "Not provided"}
        Salary Range: {request.salary_range if request.salary_range else "Not provided"}
        """

        # Request OpenAI API
        response = openai.responses.create(
            model="gpt-5.1",  # Make sure to use the correct model
            input=prompt  # Structured message input
        )
        # Extract generated content from OpenAI response
       # job_offer = response['choices'][0]['message']['content'].strip()

        # Step 2: Create the outer JSON object and embed job_offer_data
        outer_json = {
            "job_offer": response.output_text
        }

        # Step 3: Convert the outer JSON back to a string for further use or printing
        json_text = json.dumps(outer_json, indent=2)

        # Parse the outer JSON

        outer_json = json.loads(json_text)

        # Now parse the 'job_offer' key's value, which is another JSON string
        job_offer = json.loads(outer_json["job_offer"])

        job_offer_document = {
            "job_offer": job_offer,
            "department": request.department,
            "location": request.location,
            "employment_type": request.employment_type,
            "salary_range": request.salary_range,
            "tone": request.tone,
            "summary": request.summary
        }

        inserted_job_offer = job_offers_collection.insert_one(job_offer_document)
        return {"job_offer_id": str(inserted_job_offer.inserted_id), "job_offer": job_offer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
