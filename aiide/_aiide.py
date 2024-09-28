import copy
import json
import os
from openai import OpenAI, NotGiven
from ._utils import find_inner_classes, create_messages_dataframe, CustomConverter
import warnings
from litellm import completion as litellm_completion
import litellm
import abc
import pandas as pd

litellm.drop_params = True


class Tool(abc.ABC):
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
        return {}

    @abc.abstractmethod
    def main(self):
        """
        The main method of the TOOL class.
        """
        return str("")


class Aiide:
    """
    The AIIDE class is the main class for the AIIDE module
    """

    # def __init__(self):
    # self.system_message = "You are a helpful assistant."
    # self.model = "gpt-3.5-turbo"
    # self.temperature = 0.2

    def setup(
        self,
        system_message: str | None = None,
        model: str = "gpt-4o-mini-2024-07-18",
        temperature: float = 1.0,
        api_key: str | None = None,
        **kwargs
    ):
        """
        Setup the AIIDE instance.
        Takes the following arguments:
        - system_message: The system message for the LLM.
        - model: The model to use for the conversation.
        - temperature: The temperature to use for the conversation.
        - api_key: The API key to use for the conversation.
        - kwargs: Additional arguments that are compatible with the LiteLLM API.
        """
        self._api_key = api_key
        self._setup = True
        self._model = model
        self._temperature = temperature
        self._messages: list = [{"role": "system", "content": system_message}]
        self.messages = create_messages_dataframe(self._messages)
        self._kwargs = kwargs
        # if not hasattr(self,"ENV"):
        # warnings.warn("ENV is not defined. AIIDE will still continue to work without the RL-type features")

    def restore_conversation(self, messages: pd.DataFrame | list):
        """
        Restore the AIIDE instance with the previous messages.

        Args:
            messages (list | pd.DataFrame): Either an aiide DataFrame or a list of messages compatible with OpenAI schema.
        """
        if type(messages) == list:
            self._messages = messages
            self.messages = create_messages_dataframe(messages)
        elif type(messages) == pd.DataFrame:
            self.messages = messages
            self._messages = messages.aiide.to_openai_dict()

    def structured_ouputs(self):
        """
        Structured Outputs is a feature that ensures the model will always generate responses in a specific format. Return JSON Schema definition for the generation.
        """
        return {}

    def chat(
        self,
        user_message: str | list | dict | None = None,
        completion: str | None = None,
        tools: list | None = None,
        stop_words: list | None = None,
        tool_choice: str = "auto",
        json_mode: bool = False,
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
            response_format = {"type": "json_schema"}
        else:
            response_format = None
        if not hasattr(self, "_setup"):
            raise Exception("Please call self.setup() in __init__")
        # self.setup()
        if completion and user_message:
            self._messages.extend(
                [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": completion},
                ]
            )
            # adding new row to the messages dataframe
            self.messages = pd.concat(
                [
                    self.messages,
                    pd.DataFrame(
                        {
                            "role": ["user", "assistant"],
                            "content": [user_message, completion],
                            "arguments": [None, None],
                            "response": [None, None],
                        }
                    ),
                ]
            )
        elif completion and not user_message:
            self._messages.extend(
                [
                    {"role": "assistant", "content": completion},
                ]
            )
            self.messages = pd.concat(
                [
                    self.messages,
                    pd.DataFrame(
                        {
                            "role": ["assistant"],
                            "content": [completion],
                            "arguments": [None],
                            "response": [None],
                        }
                    ),
                ]
            )
        else:
            self._messages.extend(
                [
                    {"role": "user", "content": user_message},
                ]
            )
            self.messages = pd.concat(
                [
                    self.messages,
                    pd.DataFrame(
                        {
                            "role": ["user"],
                            "content": [user_message],
                            "arguments": [None],
                            "response": [None],
                        }
                    ),
                ]
            )

        # print(self.messages.aiide.to_openai_dict())
        while True:
            tool_runs = 0
            # getting tools
            if tools and len(tools) > 0:
                __tool_definations = []
                __tool_function_mapping = {}
                for each_tool_instance in tools:
                    __tool_definations.append(each_tool_instance.tool_def())
                    __tool_function_mapping[
                        each_tool_instance.tool_def()["function"]["name"]
                    ] = each_tool_instance

            else:
                __tool_definations = None
                tool_choice = None  # type: ignore
                # print("->",tools__)
            # print(active_messages)
            if json_mode:
                # calling structured_output function
                schema = self.structured_ouputs()
                if schema != {}:
                    response_format["json_schema"] = schema  # type: ignore
                    # response_format["strict"] = True

            response_generator = litellm_completion(
                model=self._model,
                # model="gpt-4-1106-preview",
                messages=self.messages.aiide.to_openai_dict(),
                tools=__tool_definations,
                tool_choice=tool_choice,  # auto is default, but we'll be explicit
                # max_tokens=4096,
                stream=True,
                temperature=self._temperature,
                stop=stop_words,
                response_format=response_format,
                api_key=self._api_key,
                # adding kwargs
                **self._kwargs,
                # parallel_tool_calls=True,
            )
            response_text = ""
            temp_function_call = []
            tool_yield = None
            for response_chunk in response_generator:
                self.messages.reset_index(drop=True, inplace=True)

                deltas = response_chunk.choices[0].delta  # type: ignore
                # print("deltas",deltas)
                if deltas.content:
                    # print(deltas.content)
                    response_text += deltas.content
                    if self.messages.iloc[-1]["role"] == "assistant":
                        # append the new response to the last row
                        # print("appending")
                        self.messages.loc[self.messages.index[-1], "content"] = (
                            response_text
                        )
                    else:
                        # print("creating")
                        # add a new row to the df_messages
                        self.messages = pd.concat(
                            [
                                self.messages,
                                pd.DataFrame(
                                    {
                                        "role": ["assistant"],
                                        "content": [response_text],
                                        "arguments": [None],
                                        "response": [None],
                                    }
                                ),
                            ]
                        )
                    yield {
                        "type": "text",
                        "content": response_text,
                        "delta": deltas.content,
                    }
                temp_assistant_response = {
                    "role": "assistant",
                    "content": response_text,
                    "tool_calls": [],
                }
                if deltas.tool_calls:
                    # print("func call")
                    if deltas.tool_calls[0].function.name:
                        if tool_yield:
                            # adding the tool call row to self.messages
                            self.messages = pd.concat(
                                [
                                    self.messages,
                                    pd.DataFrame(
                                        {
                                            "role": ["tool"],
                                            "content": [
                                                {
                                                    "name": temp_function_call[-1][
                                                        "name"
                                                    ],
                                                    "id": temp_function_call[-1][
                                                        "tool_call_id"
                                                    ],
                                                }
                                            ],
                                            "arguments": [
                                                temp_function_call[-1]["arguments"]
                                            ],
                                            "response": [None],
                                        }
                                    ),
                                ]
                            )
                            yield {
                                "type": "tool_call",
                                "name": temp_function_call[-1]["name"],
                                "arguments": temp_function_call[-1]["arguments"],
                                "finish": False,
                            }
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
                        temp_function_call[-1]["arguments"] += deltas.tool_calls[
                            0
                        ].function.arguments
                        tool_yield = True

                if response_chunk.choices[0].finish_reason:  # type: ignore
                    if tool_yield:
                        # adding the tool call row to self.messages
                        self.messages = pd.concat(
                            [
                                self.messages,
                                pd.DataFrame(
                                    {
                                        "role": ["tool"],
                                        "content": [
                                            {
                                                "name": temp_function_call[-1]["name"],
                                                "id": temp_function_call[-1][
                                                    "tool_call_id"
                                                ],
                                            }
                                        ],
                                        "arguments": [
                                            temp_function_call[-1]["arguments"]
                                        ],
                                        "response": [None],
                                    }
                                ),
                            ]
                        )
                        yield {
                            "type": "tool_call",
                            "name": temp_function_call[-1]["name"],
                            "arguments": temp_function_call[-1]["arguments"],
                            "finish": True,
                        }
                        tool_yield = None
                    # print("finish_reason",response_chunk.choices[0].finish_reason)
                    if response_chunk.choices[0].finish_reason == "tool_calls":  # type: ignore
                        # calling functions
                        # print("calling funcs", temp_function_call)
                        temp_func_call_reponses = []

                        for each_func_call in temp_function_call:
                            #! Temporarily disabled yielding of tool calls right before execution
                            # yield {"type":"tool","name":each_func_call["name"],"arguments":each_func_call["arguments"]}

                            function_to_call = __tool_function_mapping[  # type: ignore
                                each_func_call["name"]
                            ].main
                            try:
                                function_args = json.loads(each_func_call["arguments"])
                                function_response = function_to_call(**function_args)
                            except Exception as e:
                                # remove prefix string upto first () from error message
                                e = str(e).split(')', 1)[1]
                                function_response = (
                                    "Error in function call:\n"
                                    + str(e)
                                    + "\nPlease call the function with the correct format of arguments."
                                )
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
                            # finding the tool call row in the self.messages dataframe and adding the response
                            # iterating over rows
                            for index, row in self.messages.iterrows():
                                if (
                                    row["role"] == "tool"
                                    and row["content"]["id"]
                                    == each_func_call["tool_call_id"]
                                ):
                                    # updating the response
                                    self.messages.loc[index, "response"] = (  # type: ignore
                                        function_response
                                    )
                                    break
                            yield {
                                "type": "tool_response",
                                "name": each_func_call["name"],
                                "arguments": each_func_call["arguments"],
                                "response": function_response,
                            }
                        self._messages.append(temp_assistant_response)
                        self._messages.extend(temp_func_call_reponses)
                        if type(tool_choice) == dict or tool_choice == "required":
                            # If a tool has been forcefully called for more than 100 times, we exit after the final tool execution to avoid usage blowup
                            if tool_runs > 0:
                                # warnings.warn("Tools have been called 100 times consecutively. If this is the expected behaviour, please raise an issue on our GitHub Repository!")
                                return
                    elif response_chunk.choices[0].finish_reason == "length":  # type: ignore
                        self._messages.append(temp_assistant_response)
                        warnings.warn(
                            "Output token limit reached. Continuing the generation."
                        )
                    else:
                        # print("!!!!!!!GPT STOP")
                        if len(temp_assistant_response["tool_calls"]) == 0:
                            del temp_assistant_response["tool_calls"]
                        self._messages.append(temp_assistant_response)

                        return
        return
