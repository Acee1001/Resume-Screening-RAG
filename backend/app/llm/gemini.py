from google import genai

from app.config import get_settings


_settings = get_settings()


def _get_client() -> genai.Client:
    """
    Create a Google GenAI client using the GEMINI_API_KEY from settings.
    """
    api_key = _settings.gemini_api_key
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment.")
    return genai.Client(api_key=api_key)


def ask_llm(prompt: str) -> str:
    """
    Send a prompt to Gemini LLM and return the text output.
    Uses the official google-genai Client and models.generate_content API.
    """
    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        # The Python SDK exposes the combined text via the .text helper property.
        return response.text or ""
    except Exception as e:
        return f"Error from Gemini LLM: {e}"
