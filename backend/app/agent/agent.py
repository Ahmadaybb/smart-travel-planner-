import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.tools.rag_tool import rag_tool, RAGToolInput
from app.tools.classifier_tool import classifier_tool, ClassifierToolInput
from app.tools.live_conditions_tool import live_conditions_tool, LiveConditionsInput

settings = get_settings()

# Two models — cheap for extraction, strong for synthesis
cheap_llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_CHEAP_MODEL,
    temperature=0
)

strong_llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_STRONG_MODEL,
    temperature=0.7
)

# Tool allowlist
TOOL_ALLOWLIST = {"rag_tool", "classifier_tool", "live_conditions_tool"}

# Tool definitions for the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "rag_tool",
            "description": "Retrieve destination knowledge from the travel database",
            "parameters": RAGToolInput.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "classifier_tool",
            "description": "Classify a destination travel style using the ML model",
            "parameters": ClassifierToolInput.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "live_conditions_tool",
            "description": "Fetch live weather and conditions for a destination",
            "parameters": LiveConditionsInput.model_json_schema()
        }
    }
]


async def run_tool(tool_name: str, tool_args: dict, db: AsyncSession) -> str:
    # Enforce allowlist
    if tool_name not in TOOL_ALLOWLIST:
        return json.dumps({"error": f"Tool {tool_name} is not allowed"})

    try:
        if tool_name == "rag_tool":
            result = await rag_tool(RAGToolInput(**tool_args), db)
        elif tool_name == "classifier_tool":
            result = await classifier_tool(ClassifierToolInput(**tool_args))
        elif tool_name == "live_conditions_tool":
            result = await live_conditions_tool(LiveConditionsInput(**tool_args))
        return json.dumps(result)

    except Exception as e:
        # Return error to LLM so it can reason about it
        return json.dumps({"error": str(e)})


async def run_agent(user_query: str, db: AsyncSession) -> dict:
    messages = [
        SystemMessage(content="""You are a smart travel planning assistant.
You have three tools: rag_tool, classifier_tool, and live_conditions_tool.
Use them together to answer the user's travel question.
Always retrieve destination knowledge first, then classify travel style,
then check live conditions. Synthesize all results into one coherent plan.
If tools return conflicting information, acknowledge the tension explicitly."""),
        HumanMessage(content=user_query)
    ]

    tool_calls_log = []
    token_usage = {"cheap": 0, "strong": 0}

    # Step 1 — cheap model extracts tool calls
    cheap_response = await cheap_llm.ainvoke(
        messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    token_usage["cheap"] += cheap_response.usage_metadata.get("total_tokens", 0)

    # Step 2 — execute tool calls
    if cheap_response.tool_calls:
        messages.append(cheap_response)

        for tool_call in cheap_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool_result = await run_tool(tool_name, tool_args, db)

            tool_calls_log.append({
                "tool_name": tool_name,
                "tool_input": json.dumps(tool_args),
                "tool_output": tool_result
            })

            messages.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call["id"]
                )
            )

    # Step 3 — strong model synthesizes final answer
    messages.append(
        HumanMessage(content="Now synthesize everything into a clear, actionable trip plan.")
    )

    strong_response = await strong_llm.ainvoke(messages)
    token_usage["strong"] += strong_response.usage_metadata.get("total_tokens", 0)

    return {
        "answer": strong_response.content,
        "tool_calls": tool_calls_log,
        "token_usage": token_usage
    }