import os

import chainlit as cl
import openai
import qdrant_client
import base64
from dotenv import load_dotenv
import glob

from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.schema import ImageNode

from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index import StorageContext
from llama_index.indices.multi_modal.base import MultiModalVectorStoreIndex
from llama_index.callbacks.base import CallbackManager


from mm_pymu_pdf import PyMuPDFReader

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")

# Create a local Qdrant vector store
client = qdrant_client.QdrantClient(path="qdrant_db")

text_store = QdrantVectorStore(
    client=client, collection_name="text_collection"
)
image_store = QdrantVectorStore(
    client=client, collection_name="image_collection"
)
storage_context = StorageContext.from_defaults(vector_store=text_store)

loader = PyMuPDFReader()

# Create the MultiModal index
documents = []

for file in glob.glob("./data/*"):
    documents.extend(loader.load_data(file, captioning=True))

index = MultiModalVectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    image_vector_store=image_store,
    is_image_to_text=True,
)


def encode_image(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_image}"


@cl.on_chat_start
async def on_start():
    mm_llm = OpenAIMultiModal(
        model="gpt-4-vision-preview", temperature=0.8, max_new_tokens=300
    )

    retriever = index.as_query_engine(
        callback_manager=CallbackManager([cl.LlamaIndexCallbackHandler()])
    )

    cl.user_session.set("retriever", retriever)
    cl.user_session.set("mm_llm", mm_llm)


@cl.on_message
async def on_message(message):
    retriever = cl.user_session.get("retriever")
    response = retriever.stream_query(message.content)

    sources = response.source_nodes
    elements = []
    image_paths = []

    for node in sources:
        if isinstance(node.node, ImageNode):
            image_paths.append(node.node.image)
            # elements.append(
            #     cl.Image(name="image1", display="inline", path=)
            # )
    image_paths = set(image_paths)
    elements = [
        cl.Image(name="image1", display="inline", path=path)
        for path in image_paths
    ]

    response_message = cl.Message(content="", elements=elements)
    for token in response.response_gen:
        await response_message.stream_token(token=token.delta)

    await response_message.send()
