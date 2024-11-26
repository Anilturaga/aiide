import copy
import json
import os
from openai import OpenAI, NotGiven
from ._utils import find_inner_classes, create_messages_dataframe, CustomConverter, parse_json
import warnings
from litellm import completion as litellm_completion
from litellm import stream_chunk_builder as litellm_stream_chunk_builder
from litellm.cost_calculator import cost_per_token as litellm_cost_per_token
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
    def setup(
        self,
        system_message: str | None = None,
        model: str = "gpt-4o-mini-2024-07-18",
        temperature: float = 1.0,
        api_key: str | None = None,
        history_openai_format: list | None = None,
        **kwargs
    ):
        """
        Setup the AIIDE instance.
        Takes the following arguments:
        - system_message: The system message for the LLM.
        - model: The model to use for the conversation.
        - temperature: The temperature to use for the conversation.
        - api_key: The API key to use for the conversation.
        - history_openai_format: The history of the conversation in OpenAI format. Useful got migrating from OpenAI to AIIDE.
        - kwargs: Additional arguments that are compatible with the LiteLLM API.
        """
        self._api_key = api_key
        self._setup = True
        self._model = model
        self._temperature = temperature
        self.messages: pd.DataFrame = create_messages_dataframe(history_openai_format)
        
        self.usage = {
            "prompt_tokens": 0.0,
            "completion_tokens": 0.0,
            "usd": 0.0,
        }
        if system_message:
            self.messages.loc[len(self.messages)] = { # type: ignore
                "role": "system",
                "content": system_message,
                "arguments": None,
                "response": None,
            }
        self._kwargs = kwargs

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
        if completion:
            if user_message:
                self.messages = pd.concat([
                    self.messages,
                    pd.DataFrame({
                        "role": ["user", "assistant"],
                        "content": [user_message, completion],
                        "arguments": [None, None],
                        "response": [None, None],
                    })
                ])
            else:
                self.messages = pd.concat([
                    self.messages,
                    pd.DataFrame({
                        "role": ["assistant"],
                        "content": [completion],
                        "arguments": [None],
                        "response": [None],
                    })
                ])
        elif user_message:
            self.messages = pd.concat([
                self.messages,
                pd.DataFrame({
                    "role": ["user"],
                    "content": [user_message],
                    "arguments": [None],
                    "response": [None],
                })
            ])

        # print(self.messages.aiide.to_openai_dict())
        while True:
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
            if json_mode:
                # calling structured_output function
                schema = self.structured_ouputs()
                if schema != {}:
                    response_format["json_schema"] = schema  # type: ignore
                    # response_format["strict"] = True
            messages_prev = copy.deepcopy(self.messages.aiide.to_openai_dict())
            response_generator = litellm_completion(
                model=self._model,
                messages=self.messages.aiide.to_openai_dict(),
                tools=__tool_definations,
                tool_choice=tool_choice,  # auto is default, but we'll be explicit
                stream=True,
                temperature=self._temperature,
                stop=stop_words,
                response_format=response_format,
                api_key=self._api_key,
                # adding kwargs
                **self._kwargs,
                # max_tokens=4096,
                # parallel_tool_calls=True,
            )
            response_text = ""
            temp_function_call = []
            chunks = []
            for response_chunk in response_generator:
                chunks.append(response_chunk)
                self.messages.reset_index(drop=True, inplace=True)
                deltas = response_chunk.choices[0].delta  # type: ignore
                finish_reason = response_chunk.choices[0].finish_reason  # type: ignore
                # print("deltas",deltas)
                if deltas.content:
                    response_text += deltas.content
                    if json_mode == True and self.structured_ouputs() != {}:
                        yield_response_text = parse_json(response_text)
                    else:
                        yield_response_text = response_text
                    if self.messages.iloc[-1]["role"] == "assistant":
                        self.messages.loc[self.messages.index[-1], "content"] = response_text
                    else:
                        self.messages = pd.concat([
                            self.messages,
                            pd.DataFrame({
                                "role": ["assistant"],
                                "content": [response_text],
                                "arguments": [None],
                                "response": [None],
                            })
                        ])
                    yield {"type": "text", "content": yield_response_text, "delta": deltas.content}
                
                #! Temporarily disabled yielding of tool calls as they are generated
                # # to yield a tool call, we first check if tool calls have been created, and if so, we check if if the model is actively creating a tool call or if it has finished. hopefully, we can simplify this logic in the future
                # if len(temp_function_call) > 0 and ((deltas.tool_calls != None and deltas.tool_calls[0].function.name) or finish_reason!= None):
                #     # adding the tool call row to self.messages
                #     self.messages.loc[len(self.messages)] = { # type: ignore
                #         "role": "tool",
                #         "content": {
                #             "name": temp_function_call[-1]["name"],
                #             "id": temp_function_call[-1]["tool_call_id"],
                #         },
                #         "arguments": temp_function_call[-1]["arguments"],
                #         "response": None,
                #     } 
                #     yield {
                #         "type": "tool_call",
                #         "name": temp_function_call[-1]["name"],
                #         "arguments": temp_function_call[-1]["arguments"],
                #         "finish": bool(finish_reason),
                #     }
                if deltas.tool_calls != None:
                    # print("tool_calls")
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
                        # print("adding arguments", deltas.tool_calls[0].function.arguments)
                        temp_function_call[-1]["arguments"] += deltas.tool_calls[0].function.arguments

                if finish_reason:  # type: ignore
                    # print("finish_reason", finish_reason)
                    if finish_reason == "tool_calls":  # type: ignore
                        # calling functions
                        # print("calling funcs", temp_function_call)

                        for tool_index,each_func_call in enumerate(temp_function_call):
                            self.messages.reset_index(drop=True, inplace=True)
                            # adding the tool call row to self.messages
                            self.messages.loc[len(self.messages)] = { # type: ignore
                                "role": "tool",
                                "content": {
                                    "name": each_func_call["name"],
                                    "id": each_func_call["tool_call_id"],
                                },
                                "arguments": each_func_call["arguments"],
                                "response": None,
                            } 
                            yield {
                                "type": "tool_call",
                                "name": each_func_call["name"],
                                "arguments": each_func_call["arguments"],
                                "finish": True if tool_index == len(temp_function_call)-1 else False,
                            }

                            function_to_call = __tool_function_mapping[each_func_call["name"]].main # type: ignore
                            try:
                                function_args = json.loads(each_func_call["arguments"])
                                function_response = function_to_call(**function_args)
                            except Exception as e:
                                # remove prefix string upto first () from error message
                                e = str(e).split(')', 1)[1]
                                function_response = ("Error in function call:\n"+ str(e)+ "\nPlease call the function with the correct format of arguments.")
                            # finding the tool call row in the self.messages dataframe and adding the response
                            # iterating over rows
                            for index, row in self.messages.iterrows():
                                if row["role"] == "tool" and row["content"]["id"] == each_func_call["tool_call_id"]:
                                    # updating the response
                                    self.messages.at[index, "response"] = function_response
                                    break
                            yield {
                                "type": "tool_response",
                                "name": each_func_call["name"],
                                "arguments": each_func_call["arguments"],
                                "response": function_response,
                            }
                        if type(tool_choice) == dict or tool_choice == "required":
                            # If a tool has been forcefully called for more than 100 times, we exit after the final tool execution to avoid usage blowup
                                # warnings.warn("Tools have been called 100 times consecutively. If this is the expected behaviour, please raise an issue on our GitHub Repository!")
                            self.usage["prompt_tokens"] += litellm_stream_chunk_builder(chunks, messages_prev)['usage']["prompt_tokens"]
                            self.usage["completion_tokens"] += litellm_stream_chunk_builder(chunks, messages_prev)['usage']["completion_tokens"]
                            self.usage["usd"] += sum(litellm_cost_per_token(model=self._model, prompt_tokens=self.usage["prompt_tokens"], completion_tokens=self.usage["completion_tokens"]))
                            return
                    elif finish_reason == "length":  # type: ignore
                        warnings.warn("Output token limit reached. Continuing the generation.")
                    else:
                        # print("!!!!!!!GPT STOP")
                        self.usage["prompt_tokens"] += litellm_stream_chunk_builder(chunks, messages_prev)['usage']["prompt_tokens"]
                        self.usage["completion_tokens"] += litellm_stream_chunk_builder(chunks, messages_prev)['usage']["completion_tokens"]
                        self.usage["usd"] += sum(litellm_cost_per_token(model=self._model, prompt_tokens=self.usage["prompt_tokens"], completion_tokens=self.usage["completion_tokens"]))
                        return
            self.usage["prompt_tokens"] += litellm_stream_chunk_builder(chunks, messages_prev)['usage']["prompt_tokens"]
            self.usage["completion_tokens"] += litellm_stream_chunk_builder(chunks, messages_prev)['usage']["completion_tokens"]
            self.usage["usd"] += sum(litellm_cost_per_token(model=self._model, prompt_tokens=self.usage["prompt_tokens"], completion_tokens=self.usage["completion_tokens"]))
        return
