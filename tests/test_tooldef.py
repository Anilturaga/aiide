from aiide.schema import *

def test_weather_tooldef():
    aiide_tooldef = tool_def_gen(
                name="get_current_weather",
                description="Get the current weather in a given location",
                properties=[
                    Str(
                        name="location",
                        description="The city and state, e.g. San Francisco, CA",
                    ),
                    Str(name="unit", enums=["celsius", "fahrenheit"]),
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