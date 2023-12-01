import os

import chainlit as cl
import openai
from dotenv import load_dotenv
import base64

from llama_index.schema import ImageDocument
from llama_index.multi_modal_llms.openai import OpenAIMultiModal


load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")


def encode_image(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_image}"


@cl.on_chat_start
async def on_start():
    mm_llm = OpenAIMultiModal(
        model="gpt-4-vision-preview", temperature=0.8, max_new_tokens=300
    )

    cl.user_session.set("mm_llm", mm_llm)
    cl.user_session.set("images", [])


@cl.on_message
async def on_message(message):
    mm_llm = cl.user_session.get("mm_llm")
    image_documents = cl.user_session.get("images")

    images = [file for file in message.elements if "image" in file.mime]
    if not message.content:
        response = "What you want to do with this image?"
    else:
        try:
            image_documents.append(
                ImageDocument(
                    image_url=encode_image(images[0].content),
                )
            )
        except Exception:
            pass

        cl.user_session.set("images", image_documents)
        response = mm_llm.stream_complete(
            prompt=message.content, image_documents=image_documents
        )

    response_message = cl.Message(content="")

    for token in response:
        await response_message.stream_token(token=token.delta)

    await response_message.send()
