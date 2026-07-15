import os
from google import genai
from google.genai import types

# Assuming the environment has a GEMINI_API_KEY or we can mock one
# For this test, let's see if the SDK is available and can be instantiated.
try:
    client = genai.Client() # picks up GEMINI_API_KEY from env
    print("GenAI client initialized!")
except Exception as e:
    print("Error initializing client:", e)
