from aiide.tools import *

def test_weather_tooldef():
    aiide_tooldef = TOOL_DEF(
                name="get_current_weather",
                description="Get the current weather in a given location",
                properties=[
                    STR(
                        name="location",
                        description="The city and state, e.g. San Francisco, CA",
                    ),
                    STR(name="unit", enums=["celsius", "fahrenheit"]),
                ],
                required=["location"]
            )
    assert aiide_tooldef =={
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }