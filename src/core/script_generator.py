"""Generate podcast scripts from documentation using Azure OpenAI."""

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from ..config import Config

SINGLE_NARRATOR_PROMPT = """You are a professional podcast narrator. Convert the following Azure documentation
into an engaging single-narrator podcast script. Guidelines:
- Start with a brief, catchy introduction of the topic
- Explain concepts clearly as if speaking to a developer audience
- Use conversational tone while remaining technically accurate
- Add transitions between sections ("Now let's look at...", "Moving on to...")
- End with a concise summary and key takeaways
- Keep the script to about 3-5 minutes of speaking time (~600-1000 words)
- Do NOT include any stage directions, sound effects, or non-spoken text
- Output ONLY the spoken words the narrator should say"""

TWO_HOST_PROMPT = """You are writing a script for a two-host tech podcast. Convert the following Azure documentation
into an engaging conversational dialogue between two hosts:
- **Alex**: The knowledgeable host who explains the concepts
- **Sam**: The curious co-host who asks great questions and adds insights

Guidelines:
- Start with both hosts greeting the audience and introducing the topic
- Make it feel like a natural conversation, not a lecture
- Sam should ask questions a developer audience would have
- Alex should explain clearly with examples when possible
- Include moments of genuine enthusiasm about cool features
- End with both hosts summarizing key takeaways
- Keep the script to about 5-7 minutes of speaking time (~1000-1500 words)
- Format each line as "Alex: ..." or "Sam: ..."
- Do NOT include any stage directions, sound effects, or non-spoken text
- Output ONLY the dialogue lines"""


def generate_script(docs_content: dict, style: str = "single") -> str:
    """Generate a podcast script from documentation content.

    Args:
        docs_content: Dict with 'title', 'description', 'content' from scraper.
        style: 'single' for single narrator, 'conversation' for two-host.

    Returns:
        The generated podcast script text.
    """
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )

    client = AzureOpenAI(
        azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
        azure_ad_token_provider=token_provider,
        api_version="2024-06-01",
    )

    system_prompt = SINGLE_NARRATOR_PROMPT if style == "single" else TWO_HOST_PROMPT

    user_message = f"""Topic: {docs_content['title']}
Description: {docs_content['description']}

Documentation Content:
{docs_content['content']}"""

    response = client.chat.completions.create(
        model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_completion_tokens=4000,
    )

    return response.choices[0].message.content or ""
