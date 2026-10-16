"""
llm.py
Pluggable LLM backend, selected with the LLM_PROVIDER environment variable:

    gemini        (default) Google Gemini via the google-genai SDK
    azure_openai  Azure OpenAI via the openai SDK

rag.py and agent.py call this module instead of a vendor SDK directly, so the
retrieval code, prompts, tools and API stay identical across providers.
Provider errors are normalized to UpstreamError so main.py can map them to
HTTP status codes without knowing which vendor is in use.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI = "gemini"
AZURE_OPENAI = "azure_openai"
PROVIDERS = (GEMINI, AZURE_OPENAI)

GEMINI_MODEL = "gemini-3.6-flash"
AZURE_API_VERSION = "2024-10-21"

_clients = {}


class UpstreamError(Exception):
    """A failed call to the model provider. code is its HTTP status, or None
    when the provider could not be reached at all."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def provider() -> str:
    name = os.getenv("LLM_PROVIDER", GEMINI).strip().lower()
    if name not in PROVIDERS:
        raise ValueError(f"LLM_PROVIDER must be one of {PROVIDERS}, got {name!r}")
    return name


def model_name() -> str:
    """Gemini model id, or the Azure OpenAI deployment name."""
    if provider() == AZURE_OPENAI:
        return os.environ["AZURE_OPENAI_DEPLOYMENT"]
    return GEMINI_MODEL


def get_client():
    """Create the client for the active provider once and reuse it."""
    name = provider()
    if name not in _clients:
        if name == AZURE_OPENAI:
            from openai import AzureOpenAI

            _clients[name] = AzureOpenAI(
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", AZURE_API_VERSION),
            )
        else:
            from google import genai

            _clients[name] = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _clients[name]


def to_upstream_error(e: Exception):
    """Return an UpstreamError for a provider SDK exception, or None if e is not one."""
    try:
        from google.genai import errors as genai_errors

        if isinstance(e, genai_errors.APIError):
            return UpstreamError(e.code, e.message)
    except ImportError:
        pass
    try:
        import openai

        if isinstance(e, openai.APIStatusError):
            return UpstreamError(e.status_code, e.message)
        if isinstance(e, openai.APIConnectionError):  # includes timeouts
            return UpstreamError(None, str(e))
    except ImportError:
        pass
    return None


def generate(prompt: str) -> str:
    """Single-turn text completion with the active provider."""
    try:
        if provider() == AZURE_OPENAI:
            response = get_client().chat.completions.create(
                model=model_name(),
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        response = get_client().models.generate_content(model=model_name(), contents=prompt)
        return response.text or ""
    except Exception as e:
        upstream = to_upstream_error(e)
        if upstream:
            raise upstream from e
        raise
