# AI Video Helper

AI Video Helper is a scalable serverless video processing platform that allows users to upload videos, process them asynchronously, generate transcripts using Speech-to-Text, and build a Retrieval-Augmented Generation (RAG) pipeline for AI-powered search and chat.

The project is built using AWS serverless services, Node.js, Python workers, SQS queues, and AI-based transcript processing.

---

# Features

- Video upload using AWS S3
- Serverless backend using AWS Lambda
- Asynchronous video processing using AWS SQS
- Python worker for Speech-to-Text
- Transcript chunking and embedding generation
- RAG-based AI querying
- Scalable event-driven architecture
- Retry mechanism and Dead Letter Queue support
- AI-powered search and summarization

---

# Architecture

```text
                        +------------------+
                        |      Client      |
                        +------------------+
                                  |
                                  v
                        +------------------+
                        |   API Gateway    |
                        +------------------+
                                  |
                                  v
                        +------------------+
                        | AWS Lambda APIs  |
                        +------------------+
                                  |
                                  v
                        +------------------+
                        |      AWS S3      |
                        |  Video Storage   |
                        +------------------+
                                  |
                                  v
                        +------------------+
                        |  S3 Event Trigger|
                        +------------------+
                                  |
                                  v
                        +------------------+
                        |   AWS SQS Queue  |
                        | Video Processing |
                        +------------------+
                                  |
                                  v
                    +--------------------------------+
                    |     Python Worker Service      |
                    +--------------------------------+
                    | 1. Download Video              |
                    | 2. Extract Audio (FFmpeg)      |
                    | 3. Speech-to-Text              |
                    | 4. Transcript Generation       |
                    | 5. Chunking                    |
                    | 6. Embedding Generation        |
                    | 7. Store in Vector Database    |
                    +--------------------------------+
                                  |
                                  v
                        +------------------+
                        |   RAG Pipeline   |
                        +------------------+
                                  |
                                  v
                        +------------------+
                        |   AI Responses   |
                        +------------------+
```

---

# Tech Stack

## Backend

- Node.js
- TypeScript
- Express.js
- Serverless Framework

## AWS Services

- AWS Lambda
- API Gateway
- AWS S3
- AWS SQS
- CloudWatch
- IAM

## Python Worker

- Python 3
- FastAPI / Flask
- FFmpeg
- Whisper / Faster-Whisper

## AI / RAG

- OpenAI Embeddings
- LangChain
- Pinecone / Qdrant / Weaviate

---

# Project Structure

```bash
ai-video-helper/
│
├── backend/
│   ├── src/
│   │   ├── handlers/
│   │   ├── services/
│   │   ├── queues/
│   │   ├── utils/
│   │   └── config/
│   │
│   ├── serverless.yml
│   ├── package.json
│   └── tsconfig.json
│
├── python-worker/
│   ├── app/
│   │   ├── speech_to_text/
│   │   ├── rag/
│   │   ├── embeddings/
│   │   ├── queues/
│   │   └── utils/
│   │
│   ├── requirements.txt
│   └── main.py
│
├── infrastructure/
│   ├── iam/
│   ├── s3/
│   ├── sqs/
│   └── cloudformation/
│
└── README.md
```

---

# Workflow

## 1. Upload Video

The client uploads a video to AWS S3 using a pre-signed URL.

```text
Client -> API Gateway -> Lambda -> S3
```

---

## 2. Trigger Video Processing

After upload:

- S3 triggers a Lambda event
- Lambda pushes a message into SQS queue

Example queue payload:

```json
{
  "videoId": "video-123",
  "s3Key": "uploads/video.mp4",
  "userId": "user-1",
  "uploadedAt": "2026-05-08T10:00:00Z"
}
```

---

## 3. Python Worker Processing

The Python worker continuously polls the SQS queue.

Processing steps:

1. Download video from S3
2. Extract audio using FFmpeg
3. Convert speech to text
4. Generate transcript
5. Split transcript into chunks
6. Generate embeddings
7. Store embeddings into vector database
8. Push result into RAG pipeline

---

## 4. AI Query Flow

Users can ask questions related to uploaded videos.

Example:

```text
"Summarize the video"
```

System flow:

1. Retrieve relevant transcript chunks
2. Search vector database
3. Send context to LLM
4. Return AI-generated response

---

# Installation

## Clone Repository

```bash
git clone <repository-url>

cd ai-video-helper
```

---

# Backend Setup

## Install Dependencies

```bash
cd backend

npm install
```

---

## Configure Environment Variables

Create `.env` file:

```env
AWS_REGION=ap-south-1

VIDEO_BUCKET=video-upload-bucket

VIDEO_PROCESSING_QUEUE_URL=https://sqs.amazonaws.com/xxxx/video-processing-queue

OPENAI_API_KEY=your_openai_key
```

---

## Deploy Serverless Backend

```bash
serverless deploy
```

Deploy for specific stage:

```bash
serverless deploy --stage dev
```

---

# Python Worker Setup

## Install Dependencies

```bash
cd python-worker

pip install -r requirements.txt
```

---

## Configure Environment Variables

Create `.env` file:

```env
AWS_ACCESS_KEY_ID=xxxx

AWS_SECRET_ACCESS_KEY=xxxx

AWS_REGION=ap-south-1

S3_BUCKET=video-upload-bucket

SQS_QUEUE_URL=https://sqs.amazonaws.com/xxxx/video-processing-queue

OPENAI_API_KEY=your_openai_key

VECTOR_DB_URL=your_vector_db_url
```

---

## Start Worker

```bash
python main.py
```

---

# Example Serverless Configuration

```yml
service: ai-video-helper

provider:
  name: aws
  runtime: nodejs18.x
  region: ap-south-1

functions:
  uploadVideo:
    handler: src/handlers/upload.handler
    events:
      - http:
          path: upload
          method: post

  processVideoTrigger:
    handler: src/handlers/process.handler
    events:
      - s3:
          bucket: video-upload-bucket
          event: s3:ObjectCreated:*
```

---

# API Endpoints

# Upload Video

## Request

```http
POST /upload
```

## Response

```json
{
  "videoId": "video-123",
  "uploadUrl": "signed-url"
}
```

---

# Get Video Status

## Request

```http
GET /video/:id/status
```

## Response

```json
{
  "videoId": "video-123",
  "status": "PROCESSING"
}
```

Possible statuses:

- UPLOADED
- PROCESSING
- COMPLETED
- FAILED

---

# Ask AI

## Request

```http
POST /ai/query
```

## Body

```json
{
  "videoId": "video-123",
  "question": "Summarize the video"
}
```

## Response

```json
{
  "answer": "This video explains serverless architecture..."
}
```

---

# AWS Resources

# S3 Buckets

| Bucket | Purpose |
|---|---|
| video-upload-bucket | Store uploaded videos |
| transcript-bucket | Store generated transcripts |
| processed-assets-bucket | Store subtitles and outputs |

---

# SQS Queues

| Queue | Purpose |
|---|---|
| video-processing-queue | Main processing queue |
| rag-processing-queue | Embedding pipeline queue |
| dead-letter-queue | Failed job handling |

---

# Scaling Strategy

## Lambda Scaling

AWS Lambda automatically scales based on traffic.

## Queue-Based Processing

Multiple Python workers can process SQS messages concurrently.

## Fault Tolerance

- Retry mechanism
- Dead Letter Queue support
- Idempotent processing
- Distributed asynchronous architecture

---

# Security

- IAM-based permissions
- Signed upload URLs
- Private S3 buckets
- Queue access restrictions
- Environment secret management

---

# Monitoring

- AWS CloudWatch Logs
- Queue monitoring
- Lambda metrics
- Worker health monitoring
- Error alerting

---

# Future Improvements

- Real-time subtitle generation
- Multi-language transcription
- Speaker diarization
- Video summarization
- OCR from video frames
- Timestamp-based semantic search
- Live stream processing

---

# Challenges Solved

- Large video handling
- Asynchronous distributed processing
- AI-ready transcript pipeline
- Queue-based scalability
- Event-driven architecture
- Fault-tolerant processing

---

# License

MIT License

---

# Author

Himanshu Ajwani

Software Engineer | Node.js | Serverless | AI | RAG Systems