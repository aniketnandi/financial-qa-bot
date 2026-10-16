"""
agent.py
A lightweight function-calling agent over the Financial Document Q&A Bot.

Instead of a single retrieve-then-answer RAG call, the model is given tools
(retrieve_context, calculate_growth, calculate_margin) and decides, turn by
turn, which tool to call - chaining multiple calls when a question needs it,
e.g. "What was revenue growth and how does margin compare to last year?"
requires: retrieve current + prior figures, then two separate calculations.

The tools are declared once (TOOL_SPECS) and translated to each provider's
function-calling format. The loop runs on Gemini (google-genai) by default or
on Azure OpenAI (chat completions tool calls), per LLM_PROVIDER in llm.py.
"""

import json

import llm
from rag import NO_ANSWER
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

# Provider-neutral tool declarations: (name, description, {param: type})
TOOL_SPECS = [
    ("retrieve_context",
     "Retrieve relevant passages from the ingested financial filings for a query.",
     {"query": "string"}),
    ("calculate_growth",
     "Calculate percentage growth between a previous and current numeric value.",
     {"current": "number", "previous": "number"}),
    ("calculate_margin",
     "Calculate profit margin as a percentage of revenue.",
     {"profit": "number", "revenue": "number"}),
]

TOOL_FUNCTIONS = {
    "retrieve_context": retrieve_context,
    "calculate_growth": calculate_growth,
    "calculate_margin": calculate_margin,
}

MAX_STEPS = 8
MAX_STEPS_ANSWER = "Reached maximum reasoning steps without a final answer."


def json_schema(params: dict) -> dict:
    return {
        "type": "object",
        "properties": {name: {"type": t} for name, t in params.items()},
        "required": list(params),
    }


def gemini_tools():
    from google.genai import types

    return [types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name=name,
            description=desc,
            parameters={
                "type": "OBJECT",
                "properties": {p: {"type": t.upper()} for p, t in params.items()},
                "required": list(params),
            },
        )
        for name, desc, params in TOOL_SPECS
    ])]


def openai_tools():
    return [
        {"type": "function",
         "function": {"name": name, "description": desc, "parameters": json_schema(params)}}
        for name, desc, params in TOOL_SPECS
    ]


def execute_tool(name: str, args: dict, trace: list) -> str:
    """Run one tool call, record it in the trace, and return its result.
    Errors are returned to the model as text instead of failing the request."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        result = f"Unknown tool: {name}"
    else:
        try:
            result = fn(**args)
        except Exception as e:
            result = f"Tool error: {type(e).__name__}: {e}"
    trace.append({"tool": name, "args": args, "result": result})
    return result


def run_agent(question: str) -> dict:
    """Runs the multi-step tool-calling loop for a single question.

    Returns {"answer": str, "trace": list} where trace records every tool
    call made along the way (name, args, result) - useful both for debugging
    and for demonstrating the agent's reasoning steps.
    """
    loop = run_azure_openai if llm.provider() == llm.AZURE_OPENAI else run_gemini
    try:
        return loop(question)
    except Exception as e:
        upstream = llm.to_upstream_error(e)
        if upstream:
            raise upstream from e
        raise


def run_gemini(question: str) -> dict:
    from google.genai import types

    client = llm.get_client()
    config = types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, tools=gemini_tools())
    contents = [types.Content(role="user", parts=[types.Part(text=question)])]
    trace = []

    for _ in range(MAX_STEPS):
        response = client.models.generate_content(model=llm.model_name(), contents=contents, config=config)

        candidate = response.candidates[0]
        function_calls = [
            part.function_call for part in candidate.content.parts if part.function_call
        ]

        if not function_calls:
            return {"answer": response.text or NO_ANSWER, "trace": trace}

        # Record the model's turn (its tool-call requests) in the conversation
        contents.append(candidate.content)

        # Execute each requested tool call and feed the results back to the model
        function_response_parts = [
            types.Part.from_function_response(
                name=fc.name,
                response={"result": execute_tool(fc.name, dict(fc.args or {}), trace)},
            )
            for fc in function_calls
        ]
        contents.append(types.Content(role="user", parts=function_response_parts))

    return {"answer": MAX_STEPS_ANSWER, "trace": trace}


def run_azure_openai(question: str) -> dict:
    client = llm.get_client()
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": question},
    ]
    trace = []

    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=llm.model_name(), messages=messages, tools=openai_tools(),
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return {"answer": message.content or NO_ANSWER, "trace": trace}

        # Record the model's turn (its tool-call requests) in the conversation
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in message.tool_calls
            ],
        })

        # Execute each requested tool call and feed the results back to the model
        for tc in message.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = execute_tool(tc.function.name, args, trace)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

    return {"answer": MAX_STEPS_ANSWER, "trace": trace}
