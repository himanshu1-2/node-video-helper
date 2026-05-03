import os

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from openai import OpenAI
from qdrant_client import QdrantClient



def get_openai_client():
    print("Initializing OpenAI client...",os.getenv("OPENAI_API_KEY"))
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding_model():
    return OpenAIEmbeddings(model="text-embedding-3-large")


def get_vector_db():
    client = QdrantClient(url="http://localhost:6333")

    return QdrantVectorStore(
        client=client,
        collection_name="learning_rag",
        embedding=get_embedding_model()
    )


def process_query(query:str):
    # search_results=get_vector_db().simarity_search(query=query)
    # context=[f"Page Content:{result.page_content}\nPage Number:{result.metadata['page_label']}\nFile Location:{result.metadata['source']}" for result in search_results]
    # SYSTEM_PROMPT=f"""
    # You are a helpfull AI Assistant who answeres user query based on the available context retrieved from a PDF file along with page_contents and page number.

    # You should only ans the user based on the following context and navigate the user to open the right page number to know more.

    #  Context:
    # {context}
    # """
    # response=get_openai_client().chat.completions.create(model="gpt-5",messages=[{"role":"system","content":SYSTEM_PROMPT} ,{"role":"user","content":query}])
 
    return "Mock response: " + query