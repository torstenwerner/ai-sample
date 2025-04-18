import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def generate():
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_API_KEY"),
    )

    # model = "gemma-3-27b-it"
    model = "gemma-3-12b-it"
    # model = "gemma-3-4b-it"
    # model = "gemma-3-1b-it"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""How to answer the greeting: \"how do you do?\""""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )

    for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
    ):
        print(chunk.text, end="")


if __name__ == "__main__":
    generate()
