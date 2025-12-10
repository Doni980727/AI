# main.py

import os
import random
from typing import Optional, Literal

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mistralai import Mistral

# ========= 1. API keys & clients =========

# Mistral (text)
API_KEY = os.environ.get("MISTRAL_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "MISTRAL_API_KEY is not set. "
        "In PowerShell, run:  $env:MISTRAL_API_KEY = 'your_key_here'"
    )

MODEL_NAME = "mistral-small-latest"
client = Mistral(api_key=API_KEY)

# Stability (images)
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")
if not STABILITY_API_KEY:
    raise RuntimeError(
        "STABILITY_API_KEY is not set. "
        "In PowerShell, run:  $env:STABILITY_API_KEY = 'your_stability_key_here'"
    )

# Stable Diffusion XL text-to-image endpoint
STABILITY_ENDPOINT = (
    "https://api.stability.ai/v2beta/stable-image/generate/sd3"
)

# ========= 2. FastAPI app + CORS =========

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= 3. Data models =========


class ScenarioPersona(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender_identity: str
    social_class: Optional[str] = None
    occupation: Optional[str] = None


class ScenarioContext(BaseModel):
    region: str
    country_or_area: str
    year_from: int
    year_to: int
    urban_or_rural: Optional[Literal["urban", "rural", "mixed"]] = None


class ScenarioRequest(BaseModel):
    persona: ScenarioPersona
    context: ScenarioContext
    language: str = "english"
    word_count: int = 600


class SpinResult(BaseModel):
    persona: ScenarioPersona
    context: ScenarioContext
    # NEW: we send the image directly from /api/spin
    image_base64: Optional[str] = None


class CompareRequest(BaseModel):
    persona_a: ScenarioPersona
    context_a: ScenarioContext
    scenario_a: str

    persona_b: ScenarioPersona
    context_b: ScenarioContext
    scenario_b: str


# ========= 4. Helper function for Stability image =========


def generate_persona_image_base64(
    persona: ScenarioPersona, context: ScenarioContext
) -> Optional[str]:
    """
    Call to Stability AI (v2beta sd3).
    Sends multipart/form-data and tries to read the base64 image from the JSON response.
    """

    prompt = f"""
Portrait of a person from history, for an educational project about gender and society.

Details to capture:
- Gender identity (understood historically): {persona.gender_identity}
- Social class: {persona.social_class}
- Occupation: {persona.occupation}
- Region: {context.region}
- Country/area: {context.country_or_area}
- Time period: roughly {context.year_from}–{context.year_to}
- Setting: {context.urban_or_rural or "not specified"}

Art direction:
- Historically plausible clothing, hairstyle, and environment for this time and place.
- Respectful, documentary-style illustration; no sexualisation, no caricature, no stereotypes.
- Soft, natural lighting; neutral or thoughtful facial expression.
- Medium: semi-realistic illustration suitable for teaching materials.
"""

    # Important: *don't* set Content-Type ourselves, requests does it for us for multipart
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json",  # then we get base64 in JSON response
    }

    # multipart/form-data via files=
    files = {
        "prompt": (None, prompt),
        "output_format": (None, "png"),
        "aspect_ratio": (None, "1:1"),
        "mode": (None, "text-to-image"),
        # "model": (None, "sd3"),  # you can try commenting this out if your account doesn't require it
    }

    try:
        resp = requests.post(
            STABILITY_ENDPOINT,
            headers=headers,
            files=files,   # 👈 now we send multipart/form-data
            timeout=60,
        )
        print("Stability status:", resp.status_code)
        print("Stability raw response:", resp.text[:500])

        resp.raise_for_status()
        js = resp.json()

        # Try some common keys for the base64 field
        if "image" in js:              # e.g. {"image": "<base64>"}
            return js["image"]
        if "images" in js and isinstance(js["images"], list) and js["images"]:
            # e.g. {"images": ["<base64>", ...]}
            return js["images"][0]
        artifacts = js.get("artifacts") or []
        if artifacts:
            return artifacts[0].get("base64")

        print("No image field in Stability response JSON")
        return None
    except Exception as exc:
        print("Stability image generation failed:", exc)
        return None




# ========= 5. Simple health endpoint =========


@app.get("/health")
async def health():
    return {"status": "ok"}


# ========= 6. Spin-the-wheel endpoint =========


@app.post("/api/spin", response_model=SpinResult)
async def spin_wheel():
    """
    Randomly generate a persona + historical context.
    This is your 'Spin the Wheel' result.
    """

    genders = [
        "woman",
        "man",
        "non-binary person",
    ]

    regions = [
        ("Western Europe", "United Kingdom"),
        ("Northern Europe", "Sweden"),
        ("East Asia", "Japan"),
        ("South Asia", "India"),
        ("North Africa", "Egypt"),
        ("West Africa", "Nigeria"),
        ("Latin America", "Mexico"),
    ]

    time_periods = [
        (1850, 1890),
        (1900, 1930),
        (1950, 1970),
        (1980, 2000),
        (2000, 2020),
    ]

    social_classes = [
        "elite / upper class",
        "middle class",
        "working class",
        "peasant / rural labourer",
    ]

    occupations = [
        "domestic worker",
        "factory worker",
        "merchant",
        "school teacher",
        "farmer",
        "artisan",
        "office clerk",
        "student",
    ]

    urban_choices = ["urban", "rural", "mixed"]

    gender = random.choice(genders)
    region, country = random.choice(regions)
    year_from, year_to = random.choice(time_periods)
    social_class = random.choice(social_classes)
    occupation = random.choice(occupations)
    urban = random.choice(urban_choices)

    # Rough age at the "now" of the story
    age = random.randint(15, 40)

    persona = ScenarioPersona(
        name=None,  # let the model invent a historically fitting name
        age=age,
        gender_identity=gender,
        social_class=social_class,
        occupation=occupation,
    )

    context = ScenarioContext(
        region=region,
        country_or_area=country,
        year_from=year_from,
        year_to=year_to,
        urban_or_rural=urban,
    )

    # NEW: generate image directly on spin första med bild andra utan
    # image_b64 = generate_persona_image_base64(persona, context)
    image_b64 = None  # Skip image generation to save credits

    return SpinResult(persona=persona, context=context, image_base64=image_b64)


# ========= 7. Generate scenario (timeline-style) =========


@app.post("/api/generate-scenario")
async def generate_scenario(req: ScenarioRequest):
    """
    Generate a life scenario as a timeline (childhood, adolescence, adulthood, reflection)
    based on a persona + historical context.
    """

    p = req.persona
    c = req.context

    prompt = f"""
You are helping create educational, historically informed narratives about gender across time and cultures.

Write ONE life story for a fictional person, using the persona and context below.

PERSONA
- Name (you may invent a historically plausible name if missing): {p.name}
- Age at the time of narration: {p.age}
- Gender identity (understood in the terms of the period and culture): {p.gender_identity}
- Social class: {p.social_class}
- Occupation: {p.occupation}

HISTORICAL CONTEXT
- Region: {c.region}
- Country/area: {c.country_or_area}
- Time period: roughly {c.year_from}–{c.year_to}
- Setting: {c.urban_or_rural or "not specified"}

GOAL
- Show how gender norms and expectations in this time and place shape this person's life,
  opportunities, risks, relationships, and self-understanding.

STRUCTURE YOUR OUTPUT AS A TIMELINE WITH CLEAR HEADINGS:

1. Childhood (0–12)
   - Briefly describe family situation, community, and basic expectations related to gender.
2. Adolescence (13–19)
   - A specific scene (e.g. at home, at work, at school, in a ritual or community gathering)
     that reveals gender norms. Include at least two lines of dialogue.
3. Early adulthood (20–35)
   - Another specific situation (e.g. work, marriage, migration, activism, parenthood).
     Include at least two lines of dialogue.
4. Reflection
   - A short reflective section in first person ("I") where the character thinks about how their life
     is shaped by gender norms, and wonders how things might be different under different norms.

EPISTEMIC HUMILITY
- If this combination of time, place, and gender identity is poorly documented historically,
  explicitly note where you are speculating.
- Do not use stereotypes or sensationalism; focus on structural conditions and everyday experiences.

Write in {req.language}. Use clear headings and paragraphs. Aim for about {req.word_count} words total.
"""

    response = client.chat.complete(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You write nuanced, historically sensitive educational narratives. "
                    "You avoid stereotypes, respect all genders and cultures, and clearly distinguish "
                    "speculation from well-supported historical patterns."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    scenario_text = response.choices[0].message.content
    return {"scenario": scenario_text}


# ========= 8. Compare two scenarios =========


@app.post("/api/compare")
async def compare_scenarios(req: CompareRequest):
    """
    Compare two generated scenarios and explain similarities/differences.
    """

    prompt = f"""
You are comparing two fictional life narratives designed to teach about gender, history, and culture.

For each persona, you have:

Persona A
- {req.persona_a}

Context A
- {req.context_a}

Persona B
- {req.persona_b}

Context B
- {req.context_b}

Here are their stories:

[SCENARIO A]
{req.scenario_a}

[SCENARIO B]
{req.scenario_b}

TASK
- In clear, accessible English, compare how gender norms, time period, and place shape:
  1) Their childhoods and family expectations,
  2) Their opportunities and constraints in adolescence and early adulthood,
  3) The risks and pressures they face,
  4) The ways they understand themselves.

- Highlight both similarities and differences.
- Avoid stereotypes; focus on structures (laws, norms, institutions) as well as individual experiences.
- End with 2–3 open reflection questions for learners (e.g. “What surprised you?”).
"""

    response = client.chat.complete(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You explain social differences clearly and respectfully for an educational audience.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    comparison_text = response.choices[0].message.content
    return {"comparison": comparison_text}
