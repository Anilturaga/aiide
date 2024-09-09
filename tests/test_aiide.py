from aiide import Aiide, Tool
import json
from aiide.tools import *


def test_aiide_instance():
    class Tool1(Tool):
        def __init__(self, parent):
            self.bool = False
            print(parent.outer_var)

        def tool_def(self):
            # return toolDef(
            #     name="get_current_weather",
            #     description="Get the current weather in a given location",
            #     properties=[
            #         Str(
            #             name="location",
            #             description="The city and state, e.g. San Francisco, CA",
            #         ),
            #         Str(name="unit", enums=["celsius", "fahrenheit"]),
            #     ],
            # )

            return tool_def_gen(
                "get_current_weather",
                "Get the current weather in a given location",
                properties=[
                    AnyOf(
                        "location",
                        [
                            Str(
                                "location", "The city and state, e.g. San Francisco, CA"
                            ),
                            Array(
                                "location",
                                "A list locations. e.g. [San Francisco, CA, Tokyo, Japan]",
                                item=Str(
                                    "item", "The city and state, e.g. San Francisco, CA"
                                ),
                            ),
                        ],
                    ),
                    Str(name="unit", enums=["celsius", "fahrenheit"]),
                ],
                required=["location", "unit"],
            )

        def main(self, **kwargs):
            print(kwargs)
            # returning random number
            import random

            if type(kwargs["location"]) == str:
                return json.dumps(
                    {
                        "temperature": random.randint(0, 100),
                    }
                )
            else:
                return json.dumps(
                    {
                        "temperature": [
                            random.randint(0, 100) for each in kwargs["location"]
                        ],
                    }
                )

        # def main(self, location, unit="default"):
        #     if self.bool:
        #         return json.dumps({"error": 404})
        #     else:
        #         if "tokyo" in location.lower():
        #             return json.dumps(
        #                 {"location": "Tokyo", "temperature": "10", "unit": unit}
        #             )
        #         elif "san francisco" in location.lower():
        #             return json.dumps(
        #                 {"location": "San Francisco", "temperature": "72", "unit": unit}
        #             )
        #         elif "paris" in location.lower():
        #             return json.dumps(
        #                 {"location": "Paris", "temperature": "22", "unit": unit}
        #             )
        #         else:
        #             return json.dumps({"location": location, "temperature": "unknown"})

    class Agent(Aiide):
        def __init__(self):
            # super().__init__()
            self.outer_var = 15
            self.tool1 = Tool1(self)
            self.setup(
                system_message="You are a helpful assistant.",
            )

    agent = Agent()
    for each in agent.chat(
        # "What's the weather like in San Francisco, Tokyo, and Paris?\nCall the tool only once with all three locations.",
        "What's the weather like in San Francisco, Tokyo, and Paris?\nCall the tool three times with all three locations.",
        completion="Hello. I am",
        tools=[agent.tool1],
        json_mode=False,
        tool_choice="required",
    ):
        print(each)
        if each["type"] == "tool" and "tokyo" in each["arguments"].lower():
            agent.tool1.bool = True
        else:
            agent.tool1.bool = False


def test_aiide_image_input():
    class Agent(Aiide):
        def __init__(self):
            # super().__init__()
            self.setup(
                system_message="You are a helpful assistant.",
            )

    agent = Agent()
    # getting a random image
    import requests
    import shutil
    from PIL import Image
    import os

    image = Image.open(requests.get("https://picsum.photos/200/300", stream=True).raw)
    for each in agent.chat(
        [image, "Annotate the attached image"],
        # "What's the weather like in San Francisco, Tokyo, and Paris?\nCall the tool three times with all three locations.",
        completion="Hello",
        json_mode=False,
    ):
        print(each)


def test_aiide_structured_output():
    class Agent(Aiide):
        def __init__(self):
            # super().__init__()
            self.setup(
                system_message="You are a helpful assistant.",
            )

        def structured_ouputs(self):
            return structured_outputs_gen(
                name="annotation",
                properties=[
                    Str(name="image_description"),
                    Array(
                        name="tags",
                        description="List of hashtags for the image",
                        item=Str(name="tag", description="Every tag starts with a #"),
                    ),
                ],
                required=["image_description","tags"]
            )

    agent = Agent()
    # getting a random image
    import requests
    import shutil
    from PIL import Image
    import os

    image = Image.open(requests.get("https://picsum.photos/200/300", stream=True).raw)
    for each in agent.chat(
        [image, "Annotate the attached image"],
        # "What's the weather like in San Francisco, Tokyo, and Paris?\nCall the tool three times with all three locations.",
        # completion="Hello",
        json_mode=True,
    ):
        print(each)


def test_aiide_input_dict():
    class Agent(Aiide):
        def __init__(self):
            # super().__init__()
            self.setup(
                system_message="You are a helpful assistant.",
            )

        def structured_ouputs(self):
            return structured_outputs_gen(
                name="annotation",
                properties=[
                    Str(name="image_description"),
                    Array(
                        name="tags",
                        description="List of hashtags for the image",
                        item=Str(name="tag", description="Every tag starts with a #"),
                    ),
                ],
                required=["image_description","tags"]
            )

    agent = Agent()
    # getting a random image
    import requests
    import shutil
    from PIL import Image
    import os

    image = Image.open(requests.get("https://picsum.photos/200/300", stream=True).raw)
    for each in agent.chat(
        # [image, "Annotate the attached image"],
        {
            "image": image,
            "user_query": "Annotate the attached image",
            "additional_info": "Your tone should be formal and heavily poetic",
        },
        # "What's the weather like in San Francisco, Tokyo, and Paris?\nCall the tool three times with all three locations.",
        # completion="Hello",
        json_mode=False,
    ):
        print(each)


# Test none for tool choice
# Test for no ENV
# Test for single tool choice
# Test for none for tools
