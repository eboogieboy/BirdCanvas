from openai import OpenAI

from config import IMAGE_MODEL, IMAGE_SIZE


class ImageGenerator:

    def __init__(self, client: OpenAI):
        self.client = client

    def generate(self, prompt: str, output_path: str):
        """
        Generate an image and save it to output_path.
        """

        # We'll paste your existing generation code here.
        pass