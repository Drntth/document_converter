"""
OpenAI API kommunikáció, retry logika.
A modul tartalmazza a RAG enrichment lépéseihez szükséges API-hívásokat.
"""

import time

from config.logging_config import structlog_logger
from config.settings import IMAGE_MODEL_NAME, OPENAI_API_KEY, TEXT_MODEL_NAME
from openai import OpenAI, OpenAIError
from tenacity import retry, stop_after_attempt, wait_exponential

client = OpenAI(api_key=OPENAI_API_KEY)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry_error_callback=lambda retry_state: structlog_logger.warning(
        "OpenAI API újrapróbálkozás",
        attempt=retry_state.attempt_number,
        error=str(retry_state.outcome.exception()),
        function="call_openai_api",
    ),
)
def call_openai_api(prompt: str, system_message: str) -> str:
    """
    Meghívja az OpenAI API-t a megadott prompttal és rendszerüzenettel.

    Args:
        prompt (str): A felhasználói prompt.
        system_message (str): A rendszerüzenet.

    Returns:
        str: Az OpenAI API válasza.

    Raises:
        OpenAIError: Ha az API hívás sikertelen.
    """
    logger = structlog_logger.bind(function="call_openai_api", model=TEXT_MODEL_NAME)
    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        logger.info(
            "OpenAI API hívás sikeres",
            response_length=len(content),
            prompt_length=len(prompt),
        )
        return content
    except OpenAIError as e:
        logger.error("OpenAI API hiba", error=str(e), exc_info=True)
        raise


def call_openai_vision_api(base64_image: str) -> str:
    """
    Meghívja az OpenAI Vision API-t egy base64 kódolt képpel.

    Args:
        base64_image (str): Base64 kódolt képadat.

    Returns:
        str: Az OpenAI Vision API válasza vagy hibaüzenet.
    """
    max_attempts: int = 5
    for attempt in range(1, max_attempts + 1):
        client = OpenAI()
        try:
            completion = client.chat.completions.create(
                model=IMAGE_MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Mi van a képen?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "low",  # low | high | auto
                                },
                            },
                        ],
                    }
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if (
                "429" in error_str or "rate_limit_exceeded" in error_str
            ) and attempt < max_attempts:
                wait_time = 10
                structlog_logger.warning(
                    "OpenAI Vision API rate limit, várakozás és újrapróbálkozás",
                    attempt=attempt,
                    error=error_str,
                    wait_time=wait_time,
                    function="call_openai_vision_api",
                )
                time.sleep(wait_time)
                continue
            return f"[Hiba az OpenAI Vision API hívásakor: {e}]"
