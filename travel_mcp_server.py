import os
import json
import uuid
import datetime
import operator
from typing import Annotated, TypedDict, Optional

from groq import Groq
from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from mcp.server.fastmcp import FastMCP

from agents.tools.flights_finder import flights_finder, FlightsInput
from agents.tools.hotels_finder import hotels_finder, HotelsInput
from agents.tools.weather_checker import weather_checker, WeatherInput
from agents.tools.map_generator import map_generator, MapInput

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
CURRENT_YEAR = datetime.datetime.now().year
mcp = FastMCP("ai-travel-agent")


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    tool_call_count: int


TOOLS_SYSTEM_PROMPT = """You are a travel agent with four tools.

TOOL 1: flights_finder
TOOL: flights_finder
ARGS: { "departure_airport": "MAD", "arrival_airport": "AMS", "outbound_date": "YYYY-MM-DD", "return_date": "YYYY-MM-DD" }

TOOL 2: hotels_finder
TOOL: hotels_finder
ARGS: { "q": "Amsterdam", "check_in_date": "YYYY-MM-DD", "check_out_date": "YYYY-MM-DD", "hotel_class": "4" }

TOOL 3: weather_checker
TOOL: weather_checker
ARGS: { "city": "Amsterdam", "date": "YYYY-MM-DD" }

TOOL 4: map_generator
TOOL: map_generator
ARGS: { "destination_city": "Amsterdam", "origin_city": "Madrid", "hotels": "[{\"name\": \"Hotel V Nesplein\"}]" }

RULES:
- Always call flights_finder first, then hotels_finder, then weather_checker, then map_generator
- One tool per response. Wait for result before calling next.
- Never repeat a tool that already returned results.
- Format final summary nicely. Stop calling tools after map_generator.
""" + f"Current year: {CURRENT_YEAR}"

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
                msgs.append({"role": "user", "content": f"Tool result: {str(msg.content)[:2000]}"})
            else:
                msgs.append({"role": "assistant", "content": msg.content})

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
            tool_name, args = None, {}
            for line in last.split("\n"):
                if line.startswith("TOOL:"):
                    tool_name = line.replace("TOOL:", "").strip()
                elif line.startswith("ARGS:"):
                    args = json.loads(line.replace("ARGS:", "").strip())
            result = (
                TOOLS_MAP[tool_name].invoke({"params": args})
                if tool_name in TOOLS_MAP
                else f"Tool not found: {tool_name}"
            )
        except Exception as e:
            result = f"Tool error: {str(e)}"

        return {
            "messages": [ToolMessage(
                tool_call_id=str(count),
                name=tool_name or "unknown",
                content=str(result)
            )],
            "tool_call_count": count + 1
        }


def run_agent(query: str) -> str:
    agent = Agent()
    result = agent.graph.invoke(
        {"messages": [HumanMessage(content=query)], "tool_call_count": 0},
        config={"configurable": {"thread_id": str(uuid.uuid4())}}
    )
    return result["messages"][-1].content


# ── MCP TOOLS ──

@mcp.tool()
def plan_trip(query: str) -> str:
    """
    Plan a full trip with flights, hotels, weather and map using natural language.
    Example: Flights from Madrid to Amsterdam and a 4-star hotel Oct 1-7
    """
    return run_agent(query)


@mcp.tool()
def find_flights(
    departure_airport: str,
    arrival_airport: str,
    outbound_date: str,
    return_date: Optional[str] = None
) -> str:
    """
    Find flights between two airports.
    departure_airport: IATA code e.g. MAD
    arrival_airport: IATA code e.g. AMS
    outbound_date: YYYY-MM-DD
    return_date: YYYY-MM-DD optional
    """
    params = FlightsInput(
        departure_airport=departure_airport,
        arrival_airport=arrival_airport,
        outbound_date=outbound_date,
        return_date=return_date
    )
    result = flights_finder.invoke({"params": params})
    return json.dumps(result, indent=2)


@mcp.tool()
def find_hotels(
    city: str,
    check_in_date: str,
    check_out_date: str,
    hotel_class: Optional[str] = None
) -> str:
    """
    Find hotels in a city for specific dates.
    city: City name e.g. Amsterdam
    check_in_date: YYYY-MM-DD
    check_out_date: YYYY-MM-DD
    hotel_class: Star rating e.g. 4 optional
    """
    params = HotelsInput(
        q=city,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        hotel_class=hotel_class
    )
    result = hotels_finder.invoke({"params": params})
    return json.dumps(result, indent=2)


@mcp.tool()
def check_weather(city: str, date: str) -> str:
    """
    Check weather forecast for a city on a specific date.
    city: City name e.g. Amsterdam
    date: YYYY-MM-DD
    """
    params = WeatherInput(city=city, date=date)
    result = weather_checker.invoke({"params": params})
    return json.dumps(result, indent=2)


@mcp.tool()
def generate_map(
    destination_city: str,
    origin_city: Optional[str] = None,
    hotels: Optional[str] = None
) -> str:
    """
    Generate an interactive map showing flight route and hotel locations.
    destination_city: e.g. Amsterdam
    origin_city: e.g. Madrid optional
    hotels: JSON string e.g. '[{"name": "Hotel V"}]' optional
    """
    params = MapInput(
        destination_city=destination_city,
        origin_city=origin_city,
        hotels=hotels
    )
    result = map_generator.invoke({"params": params})
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run()