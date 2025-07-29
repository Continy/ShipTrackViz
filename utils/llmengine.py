import openai
import os
from google.genai import types
from google import genai
from utils.cfg import build_cfg


class LLMEngine:

    def __init__(self,
                 model_name: str = 'gemini-1.5-flex',
                 yaml_path: str = './llm/data.yaml'):
        self.model_name = model_name
        self.yaml_path = yaml_path
        self.cfg = build_cfg(yaml_path)
        self.temperature = self.cfg.temperature if 'temperature' in self.cfg else 0.3
        self.top_p = self.cfg.top_p if 'top_p' in self.cfg else 0.95
        self.OPENAI_URLS = {
            'deepseek': 'https://api.deepseek.com',
            'openai': 'https://api.openai.com',
        }
        self.enginelist = ['gemini', 'openai']
        self.type = self.model_type()

    def model_type(self):
        if self.model_name.startswith('gemini'):
            return self.enginelist[0]
        elif self.model_name.startswith(tuple(self.OPENAI_URLS.keys())):
            return self.enginelist[1]

    def __call__(self, prompt: str):
        if self.type == 'gemini':
            return self.call_gemini(prompt)
        elif self.type == 'openai':
            return self.call_openai(prompt)
        else:
            raise ValueError(f"Unsupported model type: {self.model_name}")

    def call_gemini(self, prompt: str):
        client = genai.Client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                temperature=self.temperature,
                top_p=self.top_p))
        return response.text

    def call_openai(self, prompt: str):
        client = openai.OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'),
                               base_url='https://api.deepseek.com')
        response = client.chat.completions.create(model=self.model_name,
                                                  messages=[{
                                                      "role": "user",
                                                      "content": prompt
                                                  }],
                                                  stream=False,
                                                  temperature=self.temperature,
                                                  top_p=self.top_p)
        return response.choices[0].message.content if response.choices else ""
