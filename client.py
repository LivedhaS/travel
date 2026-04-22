import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():

    server_params = StdioServerParameters(
        command="python",
        args=["travel_mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "plan_trip",
                {"query": "Plan a trip from Madrid to Amsterdam for 5 days next month"}
            )

            print(result)


if __name__ == "__main__":
    asyncio.run(main())