import os

from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, web_scraping_url
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Model Setup  (choose the provider with LLM_PROVIDER in your .env file)
#
#   LLM_PROVIDER   default model                 key needed in .env
#   -------------  ----------------------------  --------------------
#   gemini         gemini-3.5-flash       (free) GOOGLE_API_KEY
#   groq           openai/gpt-oss-120b    (free) GROQ_API_KEY
#   mistral        mistral-small-2506            MISTRAL_API_KEY
#
# Set LLM_MODEL in .env to override the default model of any provider.
# ---------------------------------------------------------------------------
DEFAULT_MODELS = {
    "gemini": "gemini-3.5-flash",
    "groq": "openai/gpt-oss-120b",
    "mistral": "mistral-small-2506",
}


def _need_key(*names: str) -> str:
    """Return the first env var that is set, or raise a clear error."""
    for name in names:
        val = os.getenv(name)
        if val:
            return val
    raise ValueError(
        f"Missing API key: set {' or '.join(names)} in your .env file "
        f"(LLM_PROVIDER={os.getenv('LLM_PROVIDER', 'gemini')})."
    )


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    if provider not in DEFAULT_MODELS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Choose one of: {', '.join(DEFAULT_MODELS)}"
        )
    model = os.getenv("LLM_MODEL") or DEFAULT_MODELS[provider]

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Gemini 3 models work best at their default temperature, so none is set.
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=_need_key("GOOGLE_API_KEY", "GEMINI_API_KEY"),
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=model, temperature=0, api_key=_need_key("GROQ_API_KEY"))

    # mistral
    from langchain_mistralai import ChatMistralAI

    return ChatMistralAI(model=model, temperature=0, api_key=_need_key("MISTRAL_API_KEY"))


llm = get_llm()


# Built Search Agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
    )


# Built Reader Agent
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[web_scraping_url],
    )


# Writer Chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert research writer. Write clear, structured and insightful reports."""),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusions
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# Critic Chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
