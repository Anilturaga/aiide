import inspect
from PIL import Image
from pandas.api.extensions import register_dataframe_accessor


def find_inner_classes(cls, base_class=None):
    inner_classes = []
    # print("base class", base_class)
    for name, obj in inspect.getmembers(cls):
        if inspect.isclass(obj) and obj.__module__ == cls.__module__:
            # Check if the class is defined inside the given class (not imported)
            if hasattr(obj, "__qualname__") and obj.__qualname__.startswith(
                cls.__qualname__ + "."
            ):
                if base_class is None or issubclass(obj, base_class):
                    inner_classes.append({"class": obj, "type": "agent"})
                else:
                    inner_classes.append({"class": obj, "type": "tool"})

    return inner_classes

def image_to_base64(image):
    import io
    import base64
    from PIL import Image
    buffer = io.BytesIO()
    format = "JPEG"
    image.save(buffer, format=format)
    image_bytes = buffer.getvalue()
    base64_str = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/{format.lower()};base64,{base64_str}"

def base64_to_image(base64_image: str):
    from PIL import Image
    import io
    import base64
    base64_image = base64_image.split(",")[1]
    image = Image.open(io.BytesIO(base64.b64decode(base64_image)))
    return image

def create_messages_dataframe(messages):
    import pandas as pd

    df_messages = pd.DataFrame(
        {
            "role": [],
            "content": [],
            "arguments": [],
            "response": [],
        }
    )
    if not messages:
        return df_messages
    # iterate through the messages
    for each_message in messages:
        if "role" in each_message:
            if each_message["role"] == "user" or each_message["role"] == "system":
                if type(each_message["content"]) == str:
                    df_messages = pd.concat(
                        [
                            df_messages,
                            pd.DataFrame(
                                {
                                    "role": [each_message["role"]],
                                    "content": [each_message["content"]],
                                    "arguments": [None],
                                    "response": [None],
                                },
                            ),
                        ]
                    )
                elif type(each_message["content"]) == list:
                    user_content = []
                    for each_content in each_message["content"]:
                        if each_content["type"] == "text":
                            user_content.append(each_content["text"])
                        elif each_content["type"] == "image_url":
                            # converting the image base64 url to a PIL image, "url": f"data:image/jpeg;base64,{base64_image}"
                            # convert the base64 image to a PIL image
                            image = base64_to_image(each_content["url"])

                            user_content.append(image)
                    df_messages = pd.concat(
                        [
                            df_messages,
                            pd.DataFrame(
                                {
                                    "role": [each_message["role"]],
                                    "content": [user_content],
                                    "arguments": [None],
                                    "response": [None],
                                },
                            ),
                        ]
                    )
            elif each_message["role"] == "assistant":
                if each_message["content"]:
                    df_messages = pd.concat(
                        [
                            df_messages,
                            pd.DataFrame(
                                {
                                    "role": [each_message["role"]],
                                    "content": [each_message["content"]],
                                    "arguments": [None],
                                    "response": [None],
                                },
                            ),
                        ]
                    )
                if "tool_calls" in each_message and len(each_message["tool_calls"]) > 0:
                    for each_tool_call in each_message["tool_calls"]:
                        df_messages = pd.concat(
                            [
                                df_messages,
                                pd.DataFrame(
                                    {
                                        "role": ["tool"],
                                        "content": [
                                            {
                                                "id": each_tool_call["id"],
                                                "name": each_tool_call["tool"],
                                            }
                                        ],
                                        "arguments": [each_tool_call["arguments"]],
                                        "response": [each_tool_call["response"]],
                                    },
                                ),
                            ]
                        )
        # reset the index
        df_messages.reset_index(drop=True, inplace=True)
    return df_messages
def content_transformer(content):
    if type(content) == str:
        return content
    elif isinstance(content, Image.Image):
        return [{"type": "image_url", "image_url":{"url": image_to_base64(content)}}]
    
    elif type(content) == list:
        rcontent = []
        for each_content in content:
            if type(each_content) == str:
                rcontent.append({"type": "text", "text": each_content})
            elif isinstance(each_content, Image.Image):
                # convert the PIL image to base64
                rcontent.append(
                    {
                        "type": "image_url",
                        "image_url":{"url": image_to_base64(each_content)},
                    }
                )
        return rcontent
    elif type(content) == dict:
        rcontent = []
        for key, value in content.items():
            if isinstance(value, Image.Image):
                rcontent.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": image_to_base64(value)},
                    }
                )
            elif type(value) == str:
                rcontent.append({"type": "text", "text": value})
            else:
                raise ValueError(f"Invalid type {type(value)}")
        return rcontent

@register_dataframe_accessor("aiide")
class CustomConverter:
    def __init__(self, pandas_obj):
        self.df_messages = pandas_obj  # Reference to the DataFrame
        # reset index
        self.df_messages.reset_index(drop=True, inplace=True)

    def to_openai_dict(self):
        openai_json = {
            "messages": [],
        }
        for index, row in self.df_messages.iterrows():
            if row["role"] == "user" or row["role"] == "system":
                content = content_transformer(row["content"])
                openai_json["messages"].append(
                    {
                        "role": row["role"],
                        "content": content,
                    }
                )
            elif row["role"] == "assistant":
                openai_json["messages"].append(
                    {
                        "role": "assistant",
                        "content": row["content"],
                        "tool_calls": None,
                    }
                )
            elif row["role"] == "tool":
                # finding the index of the last assistant message
                i = 0
                for i in range(len(openai_json["messages"]) - 1, -1, -1):
                    if openai_json["messages"][i]["role"] == "user":
                        i = 0
                        break
                    if openai_json["messages"][i]["role"] == "assistant":
                        break
                if i == 0:
                    # adding an assistant message if there is no assistant message
                    print("adding an assistant message")
                    openai_json["messages"].append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": None,
                        }
                    )
                    i = len(openai_json["messages"]) - 1
                # checking if tool_calls is None
                if openai_json["messages"][i]["tool_calls"] is None:
                    openai_json["messages"][i]["tool_calls"] = []
                openai_json["messages"][i]["tool_calls"].append(
                    {
                        "id": row["content"]["id"],
                        "function": {
                            "name": row["content"]["name"],
                            "arguments": row["arguments"],
                        },
                        "type": "function",
                    }
                )
                openai_json["messages"].append(
                    {
                        "role": "tool",
                        "tool_call_id": row["content"]["id"],
                        "name": row["content"]["name"],
                        "content": content_transformer(row["response"]),
                    }
                )
        return openai_json["messages"]
