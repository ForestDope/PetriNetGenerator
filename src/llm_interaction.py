# src/llm_interaction.py
import google.generativeai as genai
import google.generativeai.types as genai_types
import json
from config import GOOGLE_API_KEY, LLM_MODEL_GEMINI

# --- Configure Gemini API ---
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        GOOGLE_API_KEY = None  # Disable further calls if config fails
else:
    print("Warning: GOOGLE_API_KEY not found. LLM interaction will be disabled.")


def get_llm_response(
    prompt_text,
    system_instruction=None,
    model_name=LLM_MODEL_GEMINI,
    temperature=0.2,
    json_mode=False,
):
    """
    Gets a response from the Gemini LLM.

    Args:
        prompt_text (str): The main user prompt/query.
        system_instruction (str, optional): High-level instructions for the model's behavior.
        model_name (str): The specific Gemini model to use.
        temperature (float): Controls randomness (0.0-1.0). Lower is more deterministic.
        json_mode (bool): If True, instructs the model to output JSON.

    Returns:
        str or dict: The model's response (string, or dictionary if json_mode is True and successful).
                     Returns None on failure.
    """
    if not GOOGLE_API_KEY:
        print("Error: Gemini API key not configured. LLM calls disabled.")
        return None

    try:
        model_instance = genai.GenerativeModel(
            model_name,
            system_instruction=system_instruction if system_instruction else None,
        )

        generation_config_args = {"temperature": temperature}
        if json_mode:
            generation_config_args["response_mime_type"] = "application/json"

        current_generation_config = genai_types.GenerationConfig(
            **generation_config_args
        )

        print(f"\nSending prompt to Gemini ({model_name})")
        print(f"Temperature: {temperature}, JSON Mode: {json_mode}")

        response = model_instance.generate_content(
            prompt_text, generation_config=current_generation_config
        )

        if not response.parts:
            print("Warning: Gemini response contained no parts.")
            if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                print(f"Prompt Feedback: {response.prompt_feedback}")
            return None

        response_text = response.text

        if json_mode:
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Error: LLM output was not valid JSON: {e}")
                return None
        return response_text

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None
