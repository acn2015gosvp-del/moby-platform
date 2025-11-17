from openai import OpenAI

# Lazy loading: config는 실제 사용 시점에 로드
def _get_settings():
    from .schemas.models.core.config import settings
    return settings

def _get_client():
    settings = _get_settings()
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def summarize_alert(data: dict) -> str:
    client = _get_client()
    prompt = f"Summarize this alert: {data}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]
