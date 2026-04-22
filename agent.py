import datetime
import operator
import os
import json

from typing import Annotated, TypedDict
from dotenv import load_dotenv
from groq import Groq
from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agents.tools.flights_finder import flights_finder
from agents.tools.hotels_finder import hotels_finder
from agents.tools.weather_checker import weather_checker
from agents.tools.map_generator import map_generator



# Load environment variables
load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
CURRENT_YEAR = datetime.datetime.now().year


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    tool_call_count: int


TOOLS_SYSTEM_PROMPT = f"""You are a travel agent with four tools.

STRICT OUTPUT FORMAT FOR TOOL CALLS — follow exactly:
TOOL: flights_finder
ARGS: {{ "departure_airport": "MAD", "arrival_airport": "AMS", "outbound_date": "YYYY-MM-DD", "return_date": "YYYY-MM-DD" }}

TOOL: hotels_finder
ARGS: {{ "q": "Amsterdam", "check_in_date": "YYYY-MM-DD", "check_out_date": "YYYY-MM-DD", "hotel_class": "4" }}

TOOL: weather_checker
ARGS: {{ "city": "Amsterdam", "date": "YYYY-MM-DD" }}

TOOL: map_generator
ARGS: {{ "destination_city": "Amsterdam", "origin_city": "Madrid", "hotels": "[{{\\"name\\": \\"Hotel V Nesplein\\"}}]" }}

CRITICAL RULES:
- Write TOOL: on one line, ARGS: on the next line — nothing else on those lines
- Call ONE tool at a time and wait for result
- Order: flights_finder → hotels_finder → weather_checker → map_generator
- Never repeat a tool that already returned results
- After all 4 tools have results give final formatted summary

OUTPUT FORMAT:
## Travel Plan: <Origin> to <Destination>

### ✈️ Flight Options
**Option 1** - Airline, times, duration, price
**Option 2** - Airline, times, duration, price
**Option 3** - Airline, times, duration, price

### 🏨 Hotel Options
**Option 1: Hotel Name** - location, price/night, highlights
**Option 2: Hotel Name** - location, price/night, highlights
**Option 3: Hotel Name** - location, price/night, highlights

### 🌤️ Weather Forecast
- Temperature, description, humidity, wind

### 🗺️ Map
- Map has been generated showing your route and hotels

### ⭐ Our Recommendation
### 👉 Next Steps

Current year: {CURRENT_YEAR}
"""


TOOLS_MAP = {
    "flights_finder": flights_finder,
    "hotels_finder": hotels_finder,
    "weather_checker": weather_checker,
    "map_generator": map_generator
}


class Agent:
    def __init__(self):
        builder = StateGraph(AgentState)

        builder.add_node("call_llm", self.call_llm)
        builder.add_node("invoke_tools", self.invoke_tools)

        builder.set_entry_point("call_llm")

        builder.add_conditional_edges(
            "call_llm",
            Agent.exists_action,
            {"tool": "invoke_tools", "end": END}
        )

        builder.add_edge("invoke_tools", "call_llm")

        self.graph = builder.compile(checkpointer=MemorySaver())

    @staticmethod
    def exists_action(state):
        last = state["messages"][-1].content
        count = state.get("tool_call_count", 0)
        return "tool" if "TOOL:" in last and count < 8 else "end"

    def call_llm(self, state):
        recent = state["messages"][-8:]

        msgs = [{"role": "system", "content": TOOLS_SYSTEM_PROMPT}]

        for msg in recent:
            if isinstance(msg, HumanMessage):
                msgs.append({"role": "user", "content": msg.content})

            elif isinstance(msg, ToolMessage):
                msgs.append({
                    "role": "user",
                    "content": f"Tool result: {str(msg.content)[:2000]}"
                })

            else:
                msgs.append({"role": "assistant", "content": msg.content})

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=msgs,
            max_tokens=1024
        )

        result = response.choices[0].message.content
        print("Groq:", result[:100])

        return {"messages": [HumanMessage(content=result)]}

    def invoke_tools(self, state):
        last = state["messages"][-1].content
        count = state.get("tool_call_count", 0)

        try:
            tool_name = None
            args = {}

            for line in last.split("\n"):
                line = line.strip()

                # Handle TOOL lines
                if line.startswith("TOOL") and ":" in line and not line.startswith("TOOL_"):
                    parts = line.split(":", 1)
                    potential_tool = parts[1].strip()

                    if potential_tool and not potential_tool.startswith("{"):
                        tool_name = potential_tool

                # Handle ARGS
                elif line.startswith("ARGS:"):
                    args = json.loads(line.replace("ARGS:", "").strip())

            if tool_name in TOOLS_MAP:
                result = TOOLS_MAP[tool_name].invoke({"params": args})
            else:
                result = f"Tool not found: {tool_name}"

        except Exception as e:
            result = f"Tool error: {str(e)}"

        print(f"Tool: {tool_name} | Result: {str(result)[:200]}")

        return {
            "messages": [
                ToolMessage(
                    tool_call_id=str(count),
                    name=tool_name or "unknown",
                    content=str(result)
                )
            ],
            "tool_call_count": count + 1
        }