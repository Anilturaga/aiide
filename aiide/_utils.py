import inspect
from PIL import Image
import json
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
                    # print("adding an assistant message")
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

def parse_json(s, strict=True):
    def on_extra_token(text, data, reminding):
        print('Parsed JSON with extra tokens:', {'text': text, 'data': data, 'reminding': reminding})

    def parse_space(s, e):
        return parse_any(s.strip(), e)

    def parse_array(s, e):
        s = s[1:]  # skip starting '['
        acc = []
        s = s.strip()
        while s:
            if s[0] == ']':
                s = s[1:]  # skip ending ']'
                break
            res, s = parse_any(s, e)
            acc.append(res)
            s = s.strip()
            if s.startswith(','):
                s = s[1:]
                s = s.strip()
        return acc, s

    def parse_object(s, e):
        s = s[1:]  # skip starting '{'
        acc = {}
        s = s.strip()
        while s:
            if s[0] == '}':
                s = s[1:]  # skip ending '}'
                break
            key, s = parse_any(s, e)
            s = s.strip()

            if not s or s[0] == '}':
                acc[key] = None
                break

            if s[0] != ':':
                raise e

            s = s[1:]  # skip ':'
            s = s.strip()

            if not s or s[0] in ',}':
                acc[key] = None
                if s.startswith(','):
                    s = s[1:]
                break

            value, s = parse_any(s, e)
            acc[key] = value
            s = s.strip()
            if s.startswith(','):
                s = s[1:]
                s = s.strip()
        return acc, s

    def parse_string(s, e):
        end = s.find('"', 1)
        while end != -1 and s[end - 1] == '\\':  # Handle escaped quotes
            end = s.find('"', end + 1)
        if end == -1:
            if not strict:
                return s[1:], ""
            else:
                return json.loads(f'"{s[1:]}"'), ""
        str_val = s[:end + 1]
        s = s[end + 1:]
        if not strict:
            return str_val[1:-1], s
        return json.loads(str_val), s

    def parse_number(s, e):
        i = 0
        while i < len(s) and s[i] in '0123456789.-':
            i += 1
        num_str = s[:i]
        s = s[i:]
        if not num_str or num_str == "-" or num_str == ".":
            return num_str, ""
        try:
            if num_str.endswith('.'):
                num = int(num_str[:-1])
            else:
                num = float(num_str) if '.' in num_str or 'e' in num_str or 'E' in num_str else int(num_str)
        except ValueError:
            raise e
        return num, s

    def parse_true(s, e):
        if s.startswith('t') or s.startswith('T'):
            return True, s[4:]
        raise e

    def parse_false(s, e):
        if s.startswith('f') or s.startswith('F'):
            return False, s[5:]
        raise e

    def parse_null(s, e):
        if s.startswith('n'):
            return None, s[4:]
        raise e

    def parse_any(s, e):
        if not s:
            raise e
        parser = parsers.get(s[0])
        if not parser:
            raise e
        return parser(s, e)

    parsers = {
        ' ': parse_space,
        '\r': parse_space,
        '\n': parse_space,
        '\t': parse_space,
        '[': parse_array,
        '{': parse_object,
        '"': parse_string,
        't': parse_true,
        'f': parse_false,
        'n': parse_null
    }
    
    for c in '0123456789.-':
        parsers[c] = parse_number

    if len(s) >= 1:
        try:
            return json.loads(s)
        except json.JSONDecodeError as e:
            data, reminding = parse_any(s, e)
            if on_extra_token and reminding:
                on_extra_token(s, data, reminding)
            return data
    else:
        return json.loads("{}")