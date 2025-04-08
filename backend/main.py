import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import openai
import random

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# CORS enabled for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # Create images directory if needed (for future use)
# os.makedirs("images", exist_ok=True)

# Mount images directory to make them accessible via URL
app.mount("/api/images", StaticFiles(directory="images"), name="images")

@app.get("/api/news")
async def get_ai_news():
    prompt = """
    Give me 3 short current news articles in the following JSON format only.
    Each article should have a category (like Technology, Lifestyle, Business, Design, etc).
    Do not add explanation or markdown. Just give pure JSON as shown:

    [
      {
        "headline": "Tech Giants Battle Over AI Chips",
        "summary": "NVIDIA, AMD, and Intel are all unveiling new chips this week designed for high-performance AI processing.",
        "image_description": "Futuristic circuit board glowing with blue light",
        "category": "Technology"
      },
      {
        "headline": "Wildfires Spread in California",
        "summary": "Record heat and wind are fueling wildfires across Northern California, prompting evacuations.",
        "image_description": "Flames and smoke rising from a forest under an orange sky",
        "category": "Environment" 
      }
    ]
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    content = response.choices[0].message.content.strip()

    try:
        news_data = json.loads(content)
        author_images = ["author-1.jpg", "author-2.jpg", "author-3.jpg", "author-4.jpg"]
        
        # Generate DALL-E images for each news item and use direct URLs
        for i, item in enumerate(news_data):
            try:
                # Create a better prompt for DALL-E
                enhanced_prompt = f"Create a photorealistic image for a news article about: {item['headline']}. Description: {item['image_description']}. The image should be high quality and suitable for a news website."
                
                # Generate image with DALL-E
                image_response = client.images.generate(
                    model="dall-e-3",  # You can use "dall-e-2" which is cheaper
                    prompt=enhanced_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                
                # Use the image URL directly without downloading
                item["image_url"] = image_response.data[0].url
            except Exception as img_error:
                # If DALL-E generation fails, use a fallback image
                print(f"Image generation failed: {img_error}")
                item["image_url"] = f"https://picsum.photos/seed/{i+100}/550/660"
            
            # Author image from local assets
            item["author_image"] = f"./assets/images/{random.choice(author_images)}"
            
            # Ensure we have the necessary fields
            if "category" not in item:
                item["category"] = ["Lifestyle", "Technology", "Business", "Design"][random.randint(0, 3)]
            
            # Add second category if needed
            item["second_category"] = ["Lifestyle", "Technology", "Business", "Design"][random.randint(0, 3)]
            while item["second_category"] == item["category"]:
                item["second_category"] = ["Lifestyle", "Technology", "Business", "Design"][random.randint(0, 3)]
            
        return {"news": news_data}
    except Exception as e:
        return {
            "error": "Failed to process request.",
            "details": str(e),
            "raw": content
        }