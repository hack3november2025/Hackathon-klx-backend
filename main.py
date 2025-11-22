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
        generated_json_str = response.output_text.strip()

        job_offer = json.loads(generated_json_str)

        # Parse the outer JSON
        return job_offer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Pydantic model to validate the incoming job offer data
class GeneratedJobOffer(BaseModel):
    job_title: str
    department: str
    location: dict  # This will be a nested dictionary
    employment_type: str
    salary_range: dict  # This will also be a nested dictionary
    job_summary: str
    key_responsibilities: list[str]
    required_skills: list[str]
    required_skills_keywords: list[str]
    preferred_skills: list[str]
    preferred_skills_keywords: list[str]
    soft_skills: list[str]
    soft_skills_keywords: list[str]
    company_values_and_culture: dict  # Nested dictionary for company values and culture
    application_encouragement: str

@app.post("/save-job-offer")
async def save_job_offer(job_offer_document: GeneratedJobOffer):
    try:
        # Convert the Pydantic model instance to a dictionary
        job_offer_data = job_offer_document.dict()

        # Insert into MongoDB
        inserted = job_offers_collection.insert_one(job_offer_data)

        # Return the inserted document's ID
        return {
            "job_offer_id": str(inserted.inserted_id)
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=e)
