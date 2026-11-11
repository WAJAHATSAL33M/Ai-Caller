import httpx
from app.config import settings

def build_instructions(lead) -> str:
    return (
        f"You are Alex, an AI sales development assistant for {settings.company_name}. "
        f"You are calling {lead.company_name}. Disclose that you are an AI at the start "
        "and ask permission to continue. Be consultative, truthful, and concise. Never "
        "invent pricing, customer references, guarantees, or service capabilities. If "
        "the person asks not to be contacted again, acknowledge and end the call. Do "
        "not take payment details or make binding commitments. Your goal is to understand "
        "their support or sales needs and, with permission, arrange a human follow-up. "
        "Do not claim an appointment is booked unless a calendar confirms it."
    )

async def start_sales_call(lead):
    payload = {
        "session": {
            "model": "gpt-live-1",
            "instructions": build_instructions(lead),
            "audio": {"output": {"voice": settings.sales_voice}},
        },
        "transport": {
            "type": "sip",
            "destination": lead.phone,
            "trunk": {
                "provider_url": settings.sip_provider_url,
                "auth": {"type": "digest", "username": settings.sip_username,
                         "password": settings.sip_password},
                "caller_number": settings.sip_caller_number,
            },
        },
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}",
               "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://api.openai.com/v1/live/sessions",
                                     headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
