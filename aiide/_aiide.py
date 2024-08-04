import copy
import json
import os
from openai import OpenAI, NotGiven
from ._utils import find_inner_classes
import warnings
from litellm import completion as litellm_completion
import litellm
import abc
litellm.drop_params=True
class TOOL(abc.ABC):
    """
    This is a base class for tools in the AIIDE module.
    """

    @abc.abstractmethod
    def __init__(self, parent):
        """
        Initializes a new instance of the TOOL class.

        Parameters:
            parent (object): The parent class.

        """
        pass

    @abc.abstractmethod
    def tool_def(self):
        """
        This method is called every time an LLM call is made.
        """
        pass

    @abc.abstractmethod
    def main(self):
        """
        The main method of the TOOL class.
        """
        pass

class AIIDE:
    """
    Provide LLMs with live components.
    """
    def __init__(self):
        self.system_message = "You are a helpful assistant."
        # self.model = "gpt-3.5-turbo"
        # self.temperature = 0.2

    def setup(self, messages = [],model="gpt-4o",temperature=1.0,api_key=None):
        self.api_key = api_key
        self._setup = True
        # else:
            # print("")
        self.model = model
        self.temperature = temperature
        self.messages = messages
        # if not hasattr(self,"ENV"):
            # warnings.warn("ENV is not defined. AIIDE will still continue to work without the RL-type features")

    def chat(
        self,
        user_message=None,
        completion=None,
        tools=None,
        stop_words=None,
        tool_choice="auto",
        json_mode = False
    ):
        """
    Conversation with AIIDE.

    Args:
        user_message (str, optional): The message from the user to be processed.
        completion (str, optional): The completion of the Agent.
        tools (list, optional): A list of tool instances to be used in the conversation.
        stop_words (list, optional): A list of words that should be considered as stop words for the agent response.
        tool_choice (str, optional): The strategy for choosing which tool to use. Can be "auto", "none", or "required". Defaults to "auto".
        json_mode (bool, optional): If True, the function will return the response in JSON format. Defaults to False.

    Returns:
        yields dictionary with one of the following schema based on response type\n
        if agent response:
            {
                "type":"text",
                "content":"",
                "delta":""
            }
        if tool call:
            {
                "type":"tool",
                "name":"",
                "arguments":""
            }
        if tool response:
            {
                "type":"tool_response",
                "name":"",
                "arguments":""
                "response":""
            }
    """
        if json_mode:
            response_format = { "type": "json_object" }
        else:
            response_format = None
        if not hasattr(self, "_setup"):
            raise Exception("Please call self.setup() in __init__")
        # self.setup()
        if completion and user_message:
            self.messages.extend(
                [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": completion},
                ]
            )
        elif completion and not user_message:
            self.messages.extend(
                [
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
        tool_runs = 0
        while True:
            # print("WHILE")
            active_messages = copy.deepcopy(self.messages)
            # if hasattr(self,"ENV"):
            #     if len(self.ENV) != 0:
            #         added = False
            #         for index, each_active_message in reversed(list(enumerate(active_messages))):
            #             if each_active_message["role"] == "tool":
            #                 active_messages[index]["content"] = (
            #                     active_messages[index]["content"] + "\n" + '\n'.join(self.ENV)
            #                 )
            #                 added = True
            #                 break
            #         if added == False:
            #             active_messages[0]["content"] += "\n" + '\n'.join(self.ENV)
            # getting tools
            if tools and len(tools)>0:
                __tool_definations = []
                __tool_function_mapping = {}
                # for var in vars(self):
                #     if isinstance(vars(self)[var],Tool):
                #         # print(f"Tool found: {var}")
                #         # calling tool_def
                #         tool_definition_json = vars(self)[var].tool_def()
                #         if tool_definition_json["function"]["name"] in tools:
                #             __tool_definations.append(tool_definition_json)
                #             # checking if ENV variable is present in the tool class
                #         if hasattr(vars(self)[var],"ENV"):
                #             if len(vars(self)[var].ENV) != 0:
                #                 # adding one element at a time of ENV to the tool responses in the active messages
                #                 env_idx = 0
                #                 for index, each_active_message in reversed(list(enumerate(active_messages))):
                #                     if each_active_message["role"] == "tool" and each_active_message["name"] == tool_definition_json["function"]["name"]:
                #                         active_messages[index]["content"] = (
                #                             active_messages[index]["content"] + "\n" + vars(self)[var].ENV[env_idx]
                #                         )
                #                         env_idx += 1
                #                         if env_idx == len(vars(self)[var].ENV):
                #                             break
                #         __tool_function_mapping[tool_definition_json["function"]["name"]] = vars(self)[var]
                for each_tool_instance in tools:
                    __tool_definations.append(each_tool_instance.tool_def())
                    __tool_function_mapping[each_tool_instance.tool_def()["function"]["name"]] = each_tool_instance
                    if hasattr(each_tool_instance,"ENV"):
                        if len(each_tool_instance.ENV) != 0:
                            reversed_env = each_tool_instance.ENV[::-1]
                            # adding one element at a time of ENV to the tool responses in the active messages
                            env_idx = 0
                            for index, each_active_message in reversed(list(enumerate(active_messages))):
                                if each_active_message["role"] == "tool" and each_active_message["name"] == each_tool_instance.tool_def()["function"]["name"]:
                                    active_messages[index]["content"] = (
                                        active_messages[index]["content"] + "\n" + reversed_env[env_idx]
                                    )
                                    env_idx += 1
                                    if env_idx == len(reversed_env):
                                        break
                            if env_idx == 0:
                                active_messages[0]["content"] += "\n" + '\n'.join(reversed_env)
            else:
                __tool_definations = None
                tool_choice = None
                # print("->",tools__)
            # print(active_messages)
            response_generator = litellm_completion(
                    model=self.model,
                    # model="gpt-4-1106-preview",
                    messages=active_messages,
                    tools=__tool_definations,
                    tool_choice=tool_choice,  # auto is default, but we'll be explicit
                    max_tokens=4096,
                    stream=True,
                    temperature=self.temperature,
                    stop = stop_words,
                    response_format=response_format,
                    api_key = self.api_key,
                    # parallel_tool_calls=True,

            )
            response_text = ""
            temp_function_call = []
            tool_yield = None
            for response_chunk in response_generator:
                deltas = response_chunk.choices[0].delta
                # print("deltas",deltas)
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
                        if tool_yield:
                            yield {"type":"tool_call","name":temp_function_call[-1]["name"],"arguments":temp_function_call[-1]["arguments"],"finish":False}
                            tool_yield = None
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
                        tool_yield = True
                # if len(temp_function_call)> 0 and deltas.tools_calls[0].index != tool_index:
                #     yield {"type":"tool","name":temp_function_call[-1]["name"],"arguments":temp_function_call[-1]["arguments"]}
                #     tool_index = deltas.tools_calls[0].index

                if response_chunk.choices[0].finish_reason:
                    if tool_yield:
                        yield {"type":"tool_call","name":temp_function_call[-1]["name"],"arguments":temp_function_call[-1]["arguments"],"finish":True}
                        tool_yield = None
                    # print("finish_reason",response_chunk.choices[0].finish_reason)
                    if response_chunk.choices[0].finish_reason == "tool_calls":
                        # calling functions
                        # print("calling funcs", temp_function_call)
                        temp_func_call_reponses = []

                        for each_func_call in temp_function_call:
                            #! Temporarily disabled yielding of tool calls right before execution
                            # yield {"type":"tool","name":each_func_call["name"],"arguments":each_func_call["arguments"]}

                            # sub = ""
                            # args = json.loads(each_func_call["arguments"])
                            # function_to_call = self.tools_[
                            #     each_func_call["name"]
                            # ].main
                            function_to_call = __tool_function_mapping[each_func_call["name"]].main
                            try:
                                function_args = json.loads(each_func_call["arguments"])
                                function_response = function_to_call(**function_args)
                            except Exception as e:
                                # remove prefix string upto first () from error message
                                e = str(e).split(")", 1)[1]
                                function_response = "Error in function call:\n" + str(e) + "\nPlease call the function with the correct format of arguments."
                            tool_runs += 1
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
                            yield {"type":"tool_response","name":each_func_call["name"],"arguments":each_func_call["arguments"],"response":function_response}
                        self.messages.append(temp_assistant_response)
                        self.messages.extend(temp_func_call_reponses)
                        if type(tool_choice) == dict or tool_choice == "required":
                            # If a tool has been forcefully called for more than 100 times, we exit after the final tool execution to avoid usage blowup
                            if tool_runs > 100:
                                warnings.warn("Tools have been called 100 times consecutively. If this is the expeceted behaviour, please raise an issue in GitHub!")
                                return
                    elif response_chunk.choices[0].finish_reason == "length":
                        self.messages.append(temp_assistant_response)
                        warnings.warn("Output token limit reached. Continuing the generation.")
                    else:
                        # print("!!!!!!!GPT STOP")
                        if len(temp_assistant_response["tool_calls"]) == 0:
                            del temp_assistant_response["tool_calls"]
                        self.messages.append(temp_assistant_response)
                        return
        return