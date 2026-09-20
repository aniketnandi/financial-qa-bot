"""
agent.py
A lightweight function-calling agent over the Financial Document Q&A Bot.

Instead of a single retrieve-then-answer RAG call, the model is given tools
(retrieve_context, calculate_growth, calculate_margin) and decides, turn by
turn, which tool to call - chaining multiple calls when a question needs it,
e.g. "What was revenue growth and how does margin compare to last year?"
requires: retrieve current + prior figures, then two separate calculations.

Uses the same Gemini client/model as rag.py (via google-genai), just with
tools attached and a multi-step loop instead of one prompt-and-answer call.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from tools import retrieve_context, calculate_growth, calculate_margin

SYSTEM_INSTRUCTION = """You are a financial analysis agent. You have access to tools:
- retrieve_context: pull relevant passages from the ingested financial filings
- calculate_growth: compute % growth between two numeric values
- calculate_margin: compute profit margin as a percentage

Plan your steps: first retrieve any numbers you need from the filings, then use
the calculation tools if the question requires computed metrics. Use only
information returned by your tools - do not invent figures. If a needed number
cannot be found via retrieval, say so instead of guessing.

Be efficient: call retrieve_context at most twice for the same question. As
soon as a retrieved passage contains the specific figures you need (e.g. a
table with matching line items and years), stop retrieving and move directly
to the calculation tool or your final answer. Do not keep re-querying to find
a "cleaner" version of a number you already have."""

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="retrieve_context",
                description="Retrieve relevant passages from the ingested financial filings for a query.",
                parameters={
                    "type": "OBJECT",
                    "properties": {"query": {"type": "STRING"}},
                    "required": ["query"],
                },
            ),
            types.FunctionDeclaration(
                name="calculate_growth",
                description="Calculate percentage growth between a previous and current numeric value.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "current": {"type": "NUMBER"},
                        "previous": {"type": "NUMBER"},
                    },
                    "required": ["current", "previous"],
                },
            ),
            types.FunctionDeclaration(
                name="calculate_margin",
                description="Calculate profit margin as a percentage of revenue.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "profit": {"type": "NUMBER"},
                        "revenue": {"type": "NUMBER"},
                    },
                    "required": ["profit", "revenue"],
                },
            ),
        ]
    )
]

TOOL_FUNCTIONS = {
    "retrieve_context": retrieve_context,
    "calculate_growth": calculate_growth,
    "calculate_margin": calculate_margin,
}

MAX_STEPS = 8


def run_agent(question: str) -> dict:
    """Runs the multi-step tool-calling loop for a single question.

    Returns {"answer": str, "trace": list} where trace records every tool
    call made along the way (name, args, result) - useful both for debugging
    and for demonstrating the agent's reasoning steps.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    contents = [types.Content(role="user", parts=[types.Part(text=question)])]
    trace = []

    for _ in range(MAX_STEPS):
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=TOOLS,
            ),
        )

        candidate = response.candidates[0]
        function_calls = [
            part.function_call for part in candidate.content.parts if part.function_call
        ]

        if not function_calls:
            return {"answer": response.text, "trace": trace}

        # Record the model's turn (its tool-call requests) in the conversation
        contents.append(candidate.content)

        # Execute each requested tool call and feed the results back to the model
        function_response_parts = []
        for fc in function_calls:
            fn = TOOL_FUNCTIONS.get(fc.name)
            result = fn(**fc.args) if fn else f"Unknown tool: {fc.name}"

            trace.append({"tool": fc.name, "args": dict(fc.args), "result": result})
            function_response_parts.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response={"result": result},
                )
            )

        contents.append(types.Content(role="user", parts=function_response_parts))

    return {
        "answer": "Reached maximum reasoning steps without a final answer.",
        "trace": trace,
    }
