import copy
import json
import os
from openai import OpenAI, NotGiven
from ._utils import find_inner_classes

class AIIDE:
    """
    Provide LLMs with live components.
    """
    def __init__(self):
        self.system_message = "You are a helpful assistant."
        # self.model = "gpt-3.5-turbo"
        # self.temperature = 0.2

    def setup(self, messages = [],model="gpt-3.5-turbo",temperature=1.0,api_key=None):
        self.tools_ = {}
        # if not hasattr(self, "_cold_start"):
        classes = find_inner_classes(self.__class__, AIIDE)
        for each_class in classes:
            "Setting parent as self for all classes"
            exec("self." + each_class["class"].__name__ + ".parent = self")
            "Creating instance for each tool sub class"
            exec("self." + each_class["class"].__name__ + "= each_class['class']()")
            "Check if the main function exist in the class"
            if not hasattr(eval("self." + each_class["class"].__name__), "main") or not hasattr(eval("self." + each_class["class"].__name__), "tool_def"):
                raise NotImplementedError(
                    "main function or tool_def not implemented in class: "
                    + "self."
                    + each_class["class"].__name__
                )
            toolName = "self." + each_class["class"].__name__ + ".main"
            toolName = "self." + each_class["class"].__name__ + ".tool_def['function']['name']"
            self.tools_[eval(toolName)] = eval("self." + each_class["class"].__name__)

            # print("tool func",inspect.isgeneratorfunction(eval(toolName)))
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")

        if api_key is None:
            raise Exception(
                "Expected an api_key argument or the OPENAI_API_KEY environment variable to be set!"
            )
        self.client = OpenAI(api_key=api_key)
        self._setup = True
        # else:
            # print("")
        self.model = model
        self.temperature = temperature
        self.messages = messages

    def chat(
        self,
        user_message="",
        completion=None,
        tools=None,
        stop_words=None,
        tool_choice="auto",
    ):
        if not hasattr(self, "_setup"):
            raise KeyError("Please call self.setup() in __init__")
        # self.setup()
        if completion:
            self.messages.extend(
                [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": completion},
                ]
            )

        else:
            self.messages.extend(
                [
                    {"role": "user", "content": user_message},
                ]
            )
        # print(self.messages)
        while True:
            # print("WHILE")
            active_messages = copy.deepcopy(self.messages)
            if hasattr(self,"ENV"):
                if len(self.ENV) != 0:
                    added = False
                    for index, each_active_message in reversed(list(enumerate(active_messages))):
                        if each_active_message["role"] == "tool":
                            active_messages[index]["content"] = (
                                active_messages[index]["content"] + "\n" + '\n'.join(self.ENV)
                            )
                            added = True
                            break
                    if added == False:
                        active_messages[0]["content"] += "\n" + '\n'.join(self.ENV)
            if tools and len(tools)>0:
                tools__ = [self.tools_[key].tool_def for key in tools if key in self.tools_]
                # print("->",tools__)
                response_generator = self.client.chat.completions.create(
                        model=self.model,
                        # model="gpt-4-1106-preview",
                        messages=active_messages,
                        tools=tools__,
                        tool_choice=tool_choice,  # auto is default, but we'll be explicit
                        max_tokens=4096,
                        stream=True,
                        temperature=self.temperature,
                        stop = stop_words
                )
            else:
                response_generator = self.client.chat.completions.create(
                        model=self.model,
                        # model="gpt-4-1106-preview",
                        messages=active_messages,
                        # tools=tools,
                        # tool_choice=tool_choice,  # auto is default, but we'll be explicit
                        max_tokens=4096,
                        stream=True,
                        temperature=self.temperature,
                        stop = stop_words
                )

            response_text = ""
            temp_function_call = []
            for response_chunk in response_generator:
                deltas = response_chunk.choices[0].delta
                if deltas.content:
                    # print(deltas.content)
                    response_text += deltas.content
                    yield {"type":"text","content":response_text,"delta":deltas.content}
                temp_assistant_response = {
                    "role": "assistant",
                    "content": response_text,
                    "tool_calls": [],
                }
                if deltas.tool_calls:
                    # print("func call")
                    if deltas.tool_calls[0].function.name:
                        # new function called
                        temp_function_call.append(
                            {
                                "tool_call_id": deltas.tool_calls[0].id,
                                "name": deltas.tool_calls[0].function.name,
                                "arguments": "",
                            }
                        )
                    if deltas.tool_calls[0].function.arguments != "":
                        temp_function_call[-1]["arguments"] += deltas.tool_calls[0].function.arguments
                if response_chunk.choices[0].finish_reason:
                    if response_chunk.choices[0].finish_reason == "tool_calls":
                        # calling functions
                        # print("calling funcs", temp_function_call)
                        temp_func_call_reponses = []

                        for each_func_call in temp_function_call:
                            yield {"type":"tool","tool_name":each_func_call["name"],"tool_arguments":each_func_call["arguments"]}

                            sub = ""
                            # console. print((each_tool["function"]['arguments']))
                            args = json.loads(each_func_call["arguments"])
                            function_to_call = self.tools_[
                                each_func_call["name"]
                            ].main
                            function_args = json.loads(each_func_call["arguments"])
                            function_response = function_to_call(**function_args)
                            temp_assistant_response["tool_calls"].append(
                                {
                                    "id": each_func_call["tool_call_id"],
                                    "function": {
                                        "arguments": each_func_call["arguments"],
                                        "name": each_func_call["name"],
                                    },
                                    "type": "function",
                                }
                            )
                            temp_func_call_reponses.append(
                                {
                                    "tool_call_id": each_func_call["tool_call_id"],
                                    "role": "tool",
                                    "name": each_func_call["name"],
                                    "content": function_response,
                                }
                            )
                            yield {"type":"tool_response","tool_name":each_func_call["name"],"tool_arguments":each_func_call["arguments"],"tool_response":function_response}
                        self.messages.append(temp_assistant_response)
                        self.messages.extend(temp_func_call_reponses)

                    else:
                        # print("!!!!!!!GPT STOP")
                        if len(temp_assistant_response["tool_calls"]) == 0:
                            del temp_assistant_response["tool_calls"]
                        self.messages.append(temp_assistant_response)
                        return
        return