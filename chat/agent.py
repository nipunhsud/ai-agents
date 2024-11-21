import openai
import os
from langchain import OpenAI, LLMChain
from langchain.prompts import PromptTemplate
from django.conf import settings


class Agent:

    def __init__(self):
        self.llm = OpenAI()
        self.prompt_template = PromptTemplate(
            input_variables=["input"],
            template="You are an AI assistant. Based on the input: {input}, provide reasoning and an action."
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def run(self, user_input):
        # Run the chain with the user input
        response = self.chain.run({"input": user_input})
        return response
