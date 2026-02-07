# Add this file to your smart_meal_tracker repo: web_app/analyze_image.py
# Then in web_app/app.py add the two lines described in pi-integration/README.md
#
# Provides POST /api/analyze-image for the React app (Gemini or OpenAI vision).
# Requires: GEMINI_API_KEY and/or OPENAI_API_KEY in environment or .env at repo root.

import base64
import json
import os
from pathlib import Path

# Load .env from repo root (parent of web_app) so API keys are available
try:
    from dotenv import load_dotenv
    _repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(_repo_root / ".env")
except ImportError:
    pass

PROMPT_TEMPLATE = """Analyze this food image. Based on the provided weight of {weight_g} grams, estimate the nutritional values per this portion: calories, protein (g), carbs (g), fat (g), fiber (g). Return ONLY a single JSON object with keys "name" (string) and "nutrition" (object with keys: calories, protein, carbs, fat, fiber). No markdown, no code block."""


def _get_text_from_gemini_response(response):
    if hasattr(response, "text") and response.text:
        return response.text
    if hasattr(response, "candidates") and response.candidates:
        c = response.candidates[0]
        if hasattr(c, "content") and c.content and hasattr(c.content, "parts"):
            for p in c.content.parts:
                if hasattr(p, "text") and p.text:
                    return p.text
    return ""


def _parse_ai_json(text):
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty response from AI")
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    data = json.loads(text)
    name = data.get("name") or "Unknown food"
    nutrition = data.get("nutrition") or {}
    for key in ("calories", "protein", "carbs", "fat", "fiber"):
        if key not in nutrition:
            nutrition[key] = 0
    return {"name": name, "nutrition": nutrition}


def analyze_with_gemini(image_base64: str, weight_g: float) -> dict:
    import io
    import google.generativeai as genai
    from PIL import Image

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = PROMPT_TEMPLATE.format(weight_g=weight_g)

    image_data = base64.b64decode(image_base64)
    img = Image.open(io.BytesIO(image_data))

    response = model.generate_content(
        [prompt, img],
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
        ),
    )

    text = _get_text_from_gemini_response(response)
    return _parse_ai_json(text)


def analyze_with_openai(image_base64: str, weight_g: float) -> dict:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    prompt = PROMPT_TEMPLATE.format(weight_g=weight_g)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ],
            }
        ],
        max_tokens=500,
    )

    text = (response.choices[0].message.content or "").strip()
    return _parse_ai_json(text)


def register_analyze_image(app):
    """Call this from web_app/app.py with your Flask app to add POST /api/analyze-image."""
    from flask import request, jsonify

    try:
        from flask_cors import CORS
        CORS(app, origins=["*"])
    except ImportError:
        pass

    @app.route("/api/analyze-image", methods=["POST"])
    def api_analyze_image():
        try:
            body = request.get_json(force=True, silent=True) or {}
            image_base64 = (body.get("imageBase64") or "").strip()
            weight_g = body.get("weightGrams")
            provider = (body.get("provider") or "gemini").lower()
            if provider not in ("gemini", "openai"):
                return jsonify({"error": "provider must be gemini or openai"}), 400

            if not image_base64:
                return jsonify({"error": "imageBase64 is required"}), 400
            if weight_g is None:
                weight_g = 100.0
            try:
                weight_g = float(weight_g)
            except (TypeError, ValueError):
                return jsonify({"error": "weightGrams must be a number"}), 400

            if provider == "gemini":
                result = analyze_with_gemini(image_base64, weight_g)
            else:
                result = analyze_with_openai(image_base64, weight_g)

            return jsonify(result)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except json.JSONDecodeError as e:
            return jsonify({"error": f"Invalid JSON from AI: {e}"}), 502
        except Exception as e:
            return jsonify({"error": str(e)}), 500
