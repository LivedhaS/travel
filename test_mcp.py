import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_mcp_tool(tool_name: str, arguments: dict):
    """Call an MCP tool and return the result"""
    
    # Path to your MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["travel_mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"\n📋 Available tools: {[t.name for t in tools.tools]}\n")
            
            # Call the tool
            result = await session.call_tool(tool_name, arguments=arguments)
            
            # Extract content
            if result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        return content.text
            return str(result.content)


async def plan_trip_example():
    """Example: Plan a complete trip"""
    print("🌍 Planning a trip from Madrid to Amsterdam...\n")
    
    result = await call_mcp_tool(
        "plan_trip",
        {
            "origin": "Madrid",
            "destination": "Amsterdam", 
            "departure_date": "2026-05-01",
            "return_date": "2026-05-07",
            "travelers": 2,
            "preferences": "4-star hotels, vegetarian food options"
        }
    )
    
    print("✈️ COMPLETE TRAVEL PLAN:\n")
    print(result)
    print("\n" + "="*80 + "\n")


async def find_flights_example():
    """Example: Find flights only"""
    print("✈️ Finding flights from Chennai to Bangalore...\n")
    
    result = await call_mcp_tool(
        "find_flights",
        {
            "departure_airport": "MAA",  # Chennai
            "arrival_airport": "BLR",     # Bangalore
            "outbound_date": "2026-05-15",
            "return_date": "2026-05-17"
        }
    )
    
    print("FLIGHT OPTIONS:\n")
    print(result)
    print("\n" + "="*80 + "\n")


async def find_hotels_example():
    """Example: Find hotels only"""
    print("🏨 Finding hotels in Paris...\n")
    
    result = await call_mcp_tool(
        "find_hotels",
        {
            "q": "Paris, France",
            "check_in_date": "2026-06-01",
            "check_out_date": "2026-06-05",
            "hotel_class": "5"
        }
    )
    
    print("HOTEL OPTIONS:\n")
    print(result)
    print("\n" + "="*80 + "\n")


async def check_weather_example():
    """Example: Check weather only"""
    print("🌤️ Checking weather in Amsterdam...\n")
    
    result = await call_mcp_tool(
        "check_weather",
        {
            "city": "Amsterdam",
            "date": "2026-05-01"
        }
    )
    
    print("WEATHER FORECAST:\n")
    print(result)
    print("\n" + "="*80 + "\n")


async def generate_map_example():
    """Example: Generate interactive map"""
    print("🗺️ Generating travel map...\n")
    
    result = await call_mcp_tool(
        "generate_map",
        {
            "destination_city": "Amsterdam",
            "origin_city": "Madrid",
            "hotels": json.dumps([
                {"name": "Hotel Okura Amsterdam", "lat": 52.3486, "lon": 4.8995},
                {"name": "Waldorf Astoria Amsterdam", "lat": 52.3702, "lon": 4.8952}
            ])
        }
    )
    
    print("MAP GENERATION RESULT:\n")
    print(result)
    print("\n" + "="*80 + "\n")


async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("MCP TRAVEL AGENT - STANDALONE EXAMPLES")
    print("="*80 + "\n")
    
    # Run different examples
    await plan_trip_example()
    await find_flights_example()
    await find_hotels_example()
    await check_weather_example()
    await generate_map_example()
    
    print("✅ All examples completed!\n")


if __name__ == "__main__":
    asyncio.run(main())