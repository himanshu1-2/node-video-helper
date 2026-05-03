
# import json
# import os
# import tempfile

# import boto3
# from dotenv import load_dotenv
# from fastapi import Body, FastAPI, Query

# from .clients.rq_client import queue
# from .queues.worker import get_openai_client, get_vector_db, process_query

# load_dotenv()

# app = FastAPI()

# # Configure SQS client
# SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/your-queue-name')
# AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
# S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'ai-video-helper')

# sqs_client = boto3.client(
#     'sqs',
#     region_name=AWS_REGION,
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
# )

# s3_client = boto3.client(
#     's3',
#     region_name=AWS_REGION,
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
# )

# @app.get('/')
# def root():
#     return {"status":"server python"}

# @app.post('/chat')
# def chat(query:str=Query(...,description="User Query")):
#    job=queue.enqueue(process_query,query)
#    return { "status":"job queued", "job_id":job.id}

# @app.get('/job-status')
# def get_result(job_id:str=Query(...,description="Job ID")):
#     job=queue.fetch_job(job_id)
#     result=job.return_value()
#     return {"status":"job completed","result":result}

# # POST /sqs/consume - Consume SQS messages (long-polling endpoint)
# @app.post('/sqs/consume')
# def consume_sqs_messages(maxMessages: int = Query(1, description="Max messages to receive"), waitTimeSeconds: int = Query(20, description="Wait time in seconds")):
#     """
#     Long-poll SQS queue for messages (waits up to specified seconds if no messages).
#     Processes video processing requests by converting speech to text and storing in vector DB.
#     """
#     try:
#         response = sqs_client.receive_message(
#             QueueUrl=SQS_QUEUE_URL,
#             MaxNumberOfMessages=maxMessages,
#             WaitTimeSeconds=waitTimeSeconds,
#             MessageAttributeNames=['All'],
#             AttributeNames=['All']
#         )
        
#         if 'Messages' not in response or len(response['Messages']) == 0:
#             return {"message": "No messages available", "messages": []}
        
#         processed_messages = []
#         processed_videos = []
        
#         for message in response['Messages']:
#             try:
#                 message_body = json.loads(message['Body'])
#             except json.JSONDecodeError:
#                 message_body = message['Body']
            
#             # Check if it's a video processing request
#             video_id = None
#             s3_key = None

#             if isinstance(message_body, dict):
#                 video_id = message_body.get("videoId")
#                 s3_key = message_body.get("s3Key")
#             elif isinstance(message_body, str) and message_body.startswith("video/") and message_body.endswith("/process"):
#                 video_id = message_body.split('/')[1]
#                 s3_key = f"videos/{video_id}.mp4"

#             if video_id and s3_key:
#                 temp_path = None
#                 try:
#                     # Download video from S3 using the provided key
#                     fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(s3_key)[1] or '.mp4')
#                     os.close(fd)
#                     s3_client.download_file(S3_BUCKET_NAME, s3_key, temp_path)

#                     # Create OpenAI client and vector DB only when processing a video
#                     openai_client = get_openai_client()
#                     vector_db = get_vector_db()

#                     # Transcribe audio to text
#                     with open(temp_path, 'rb') as audio_file:
#                         transcript = openai_client.audio.transcriptions.create(
#                             model="whisper-1",
#                             file=audio_file
#                         ).text

#                     # Store transcript in vector DB as a document
#                     vector_db.add_texts(
#                         [transcript],
#                         metadatas=[{
#                             "source": f"video_{video_id}",
#                             "s3_key": s3_key,
#                             "page_label": "1"
#                         }]
#                     )

#                     processed_videos.append({
#                         "video_id": video_id,
#                         "s3_key": s3_key,
#                         "status": "processed",
#                         "transcript_length": len(transcript)
#                     })

#                     # Delete the message from queue
#                     sqs_client.delete_message(
#                         QueueUrl=SQS_QUEUE_URL,
#                         ReceiptHandle=message['ReceiptHandle']
#                     )
#                 except Exception as e:
#                     processed_videos.append({
#                         "video_id": video_id,
#                         "s3_key": s3_key,
#                         "status": "error",
#                         "error": str(e)
#                     })
#                 finally:
#                     if temp_path and os.path.exists(temp_path):
#                         try:
#                             os.remove(temp_path)
#                         except Exception:
#                             pass
#             else:
#                 # Regular message
#                 processed_messages.append({
#                     "messageId": message['MessageId'],
#                     "receiptHandle": message['ReceiptHandle'],
#                     "body": message_body,
#                     "attributes": message.get('Attributes', {}),
#                     "messageAttributes": message.get('MessageAttributes', {})
#                 })
        
#         return {
#             "message": "Messages processed",
#             "regular_messages": processed_messages,
#             "processed_videos": processed_videos,
#             "total_regular": len(processed_messages),
#             "total_videos": len(processed_videos)
#         }
#     except Exception as e:
#         return {"error": str(e)}, 500

# # DELETE /sqs/message - Delete message from queue after processing
# @app.delete('/sqs/message')
# def delete_sqs_message(receiptHandle: str = Body(..., description="Receipt handle from consumed message")):
#     """
#     Delete a message from the SQS queue after processing.
#     """
#     try:
#         sqs_client.delete_message(
#             QueueUrl=SQS_QUEUE_URL,
#             ReceiptHandle=receiptHandle
#         )
        
#         return {
#             "message": "Message deleted from queue",
#             "receiptHandle": receiptHandle
#         }
#     except Exception as e:
#         return {"error": str(e)}, 500

import os
import json
import tempfile
from fastapi import FastAPI, Query
import boto3

from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from openai import OpenAI

# ---------------- CONFIG ---------------- #

SQS_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/257293814825/video-ai-helper'
S3_BUCKET_NAME = 'ai-video-helper'

app = FastAPI()

sqs_client = boto3.client("sqs")
s3_client = boto3.client("s3")


# ---------------- OPENAI ---------------- #

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding_model():
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(model="text-embedding-3-small")


# ---------------- QDRANT ---------------- #

def get_vector_db():
    client = QdrantClient(url="http://localhost:6333")
    collection_name = "learning_rag"

    # Ensure collection exists
    existing = [c.name for c in client.get_collections().collections]

    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,  # for text-embedding-3-small
                distance=Distance.COSINE
            )
        )

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=get_embedding_model()
    )


# ---------------- HELPER ---------------- #

def process_video(video_id: str, s3_key: str):
    temp_path = None

    try:
        # Download video
        fd, temp_path = tempfile.mkstemp(
            suffix=os.path.splitext(s3_key)[1] or ".mp4"
        )
        os.close(fd)

        s3_client.download_file(S3_BUCKET_NAME, s3_key, temp_path)

        openai_client = get_openai_client()
        vector_db = get_vector_db()

        # Transcribe
        with open(temp_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            ).text

        # Chunking
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
        chunks = splitter.split_text(transcript)

        # Store in Qdrant
        vector_db.add_texts(
            texts=chunks,
            metadatas=[
                {
                    "video_id": video_id,
                    "s3_key": s3_key,
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
        )

        return {
            "video_id": video_id,
            "status": "processed",
            "chunks": len(chunks),
            "transcript_length": len(transcript)
        }

    except Exception as e:
        return {
            "video_id": video_id,
            "status": "error",
            "error": str(e)
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


# ---------------- API ---------------- #

@app.post("/sqs/consume")
def consume_sqs_messages(
    maxMessages: int = Query(1),
    waitTimeSeconds: int = Query(20)
):
    try:
        print('SQS_QUEUE_URl',SQS_QUEUE_URL)
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=maxMessages,
            WaitTimeSeconds=waitTimeSeconds,
            MessageAttributeNames=["All"],
            AttributeNames=["All"]
        )

        if "Messages" not in response:
            return {"message": "No messages", "videos": []}

        results = []

        for message in response["Messages"]:
            try:
                body = json.loads(message["Body"])
            except:
                body = message["Body"]

            video_id = None
            s3_key = None

            # Handle JSON message
            if isinstance(body, dict):
                video_id = body.get("videoId")
                s3_key = body.get("s3Key")

            # Handle string pattern: video/{id}/process
            elif isinstance(body, str) and body.startswith("video/"):
                video_id = body.split("/")[1]
                s3_key = f"videos/{video_id}.mp4"

            if video_id and s3_key:
                result = process_video(video_id, s3_key)
                results.append(result)

                # Delete message after processing
                sqs_client.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"]
                )
            else:
                results.append({
                    "status": "skipped",
                    "body": body
                })

        return {
            "message": "Processed",
            "results": results
        }

    except Exception as e:
        return {"error": str(e)}
