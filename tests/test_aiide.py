from aiide import AIIDE
import json
from aiide.tools import *
def test_aiide_instance():
    class Agent(AIIDE):
        def __init__(self):
            # super().__init__()
            self.outer_var = 15
            self.setup(messages=[{"role":"system","content":"You are a helpful assistant."}])
            self.ENV =[]

        class Tool:
            def __init__(self):
                self.bool = False
                print(self.parent.outer_var)
                self.tool_def = TOOL_DEF(
                    name="get_current_weather",
                    description="Get the current weather in a given location",
                    properties=[
                        STR(
                            name="location",
                            description="The city and state, e.g. San Francisco, CA",
                        ),
                        STR(name="unit", enums=["celsius", "fahrenheit"]),
                    ],
                )

            def main(self,location,unit="default"):
                if self.bool:
                    return json.dumps({"error":404})
                else:
                    if "tokyo" in location.lower():
                        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
                    elif "san francisco" in location.lower():
                        return json.dumps(
                            {"location": "San Francisco", "temperature": "72", "unit": unit}
                        )
                    elif "paris" in location.lower():
                        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
                    else:
                        return json.dumps({"location": location, "temperature": "unknown"})

    agent = Agent()
    for each in agent.chat("What's the weather like in San Francisco, Tokyo, and Paris?",completion="Hello. I am",tools=["get_current_weather"]):
        print(each)
        if each["type"] == "tool" and "tokyo" in each["tool_arguments"].lower():
            agent.Tool.bool = True
        else:
            agent.Tool.bool = False


# Test none for tool choice
# Test for no ENV
# Test for single tool choice
# Test for none for tools