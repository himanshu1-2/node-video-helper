// filepath: server.js
const serverless = require('serverless-http');
const express = require('express');
const multer = require('multer');
const multerS3 = require('multer-s3');
const { S3Client, GetObjectCommand } = require('@aws-sdk/client-s3');
const { SQSClient, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand } = require('@aws-sdk/client-sqs');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');

const app = express();

// Configure S3 client
const s3Client = new S3Client({
  region: process.env.AWS_REGION || 'us-east-1',
  credentials: process.env.AWS_ACCESS_KEY_ID ? {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  } : undefined
});

const BUCKET_NAME = process.env.S3_BUCKET_NAME || 'your-bucket-name';
const SQS_QUEUE_URL = process.env.SQS_QUEUE_URL 

// Configure SQS client
const sqsClient = new SQSClient({
  region: process.env.AWS_REGION || 'us-east-1',
  credentials: process.env.AWS_ACCESS_KEY_ID ? {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  } : undefined
});

// Configure multer with S3 storage
const upload = multer({
  storage: multerS3({
    s3: s3Client,
    bucket: BUCKET_NAME,
    metadata: (req, file, cb) => {
      cb(null, { 
        fieldName: file.fieldname,
        originalName: file.originalname,
        mimeType: file.mimetype
      });
    },
    key: (req, file, cb) => {
      const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
      cb(null, `videos/${uniqueSuffix}-${file.originalname}`);
    }
  }),
  limits: { 
    fileSize: 2 * 1024 * 1024 * 1024 // 2GB limit
  }
});

// Enable CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// JSON body parser
app.use(express.json());

// GET /items
app.get('/items', (req, res) => {
  res.json({ message: 'GET request successful' });
});

// POST /items
app.post('/items', (req, res) => {
  const newItem = {
    id: Math.floor(Math.random() * 1000),
    name: req.body.name || 'Unnamed Item',
    createdAt: new Date().toISOString()
  };
  res.status(201).json({ message: 'POST request successful', item: newItem });
});

// POST /videos/upload - Get pre-signed URL
app.post('/videos/upload', async (req, res) => {
  try {
    const { fileName, contentType } = req.body;
    
    if (!fileName) {
      return res.status(400).json({ error: 'fileName is required' });
    }

    const key = `videos/${Date.now()}-${fileName}`;
    const { PutObjectCommand } = require('@aws-sdk/client-s3');
    const command = new PutObjectCommand({
      Bucket: BUCKET_NAME,
      Key: key,
      ContentType: contentType || 'video/mp4'
    });

    const signedUrl = await getSignedUrl(s3Client, command, { expiresIn: 3600 });

    // Extract videoId from key
    const videoId = key.replace('videos/', '');

    res.json({
      message: 'Pre-signed URL generated',
      uploadUrl: signedUrl,
      videoId: videoId,  // Use this ID to get the video later
      key: key,
      expiresIn: 3600,
      note: 'Use uploadUrl to upload directly to S3, then use videoId to get the video'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /videos/upload-multipart - Direct upload through Lambda (multipart form data)
app.post('/videos/upload-multipart', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }
  
  // Extract just the filename from the full key
  const videoId = req.file.key.replace('videos/', '');
  
  res.json({
    message: 'File uploaded successfully',
    file: {
      videoId: videoId,  // Use this ID to get the video later
      key: req.file.key,
      bucket: req.file.bucket,
      location: req.file.location,
      size: req.file.size,
      mimetype: req.file.mimetype
    },
    getVideoUrl: `/videos/${videoId}`
  });
});

// GET /videos/:videoId - Get video URL
app.get('/videos/:videoId', async (req, res) => {
  try {
    const videoId = req.params.videoId;
    
    if (!videoId) {
      return res.status(400).json({ error: 'videoId is required' });
    }

    // If videoId doesn't start with videos/, add the prefix
    const key = videoId.startsWith('videos/') ? videoId : `videos/${videoId}`;

    const command = new GetObjectCommand({
      Bucket: BUCKET_NAME,
      Key: key
    });

    const signedUrl = await getSignedUrl(s3Client, command, { expiresIn: 3600 });

    res.json({
      message: 'Video URL generated',
      videoUrl: signedUrl,
      videoId: videoId,
      key: key,
      expiresIn: 3600
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /videos/:videoId/process - Send video to worker via SQS
app.post('/videos/:videoId/process', async (req, res) => {
  try {
    const videoId = req.params.videoId;
    
    if (!videoId) {
      return res.status(400).json({ error: 'videoId is required' });
    }

    // Construct the S3 key
    const key = videoId.startsWith('videos/') ? videoId : `videos/${videoId}`;

    // Prepare message for SQS
    const message = {
      videoId: videoId,
      s3Key: key,
      bucket: BUCKET_NAME,
      timestamp: new Date().toISOString(),
      action: 'process_video'
    };

    // Send message to SQS queue
    console.log('SQS_QUEUE_URL,',`${JSON.stringify(process.env)}`);
    const command = new SendMessageCommand({
      QueueUrl: `${process.env.SQS_QUEUE_URL}`,
      MessageBody: JSON.stringify(message),
      MessageAttributes: {
        videoId: {
          DataType: 'String',
          StringValue: videoId
        },
        action: {
          DataType: 'String',
          StringValue: 'process_video'
        }
      }
    });

    const result = await sqsClient.send(command);

    res.json({
      message: 'Video sent to worker queue',
      videoId: videoId,
      s3Key: key,
      sqsMessageId: result.MessageId,
      queueUrl: SQS_QUEUE_URL
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Export as serverless handler
module.exports.handler = serverless(app);