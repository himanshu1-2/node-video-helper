// filepath: upload.js
const multer = require('multer');
const multerS3 = require('multer-s3');
const { S3Client } = require('@aws-sdk/client-s3');

// Configure S3 client
const s3Client = new S3Client({
  region: process.env.AWS_REGION || 'us-east-1',
  credentials: process.env.AWS_ACCESS_KEY_ID ? {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  } : undefined
});

const BUCKET_NAME = process.env.S3_BUCKET_NAME || 'your-bucket-name';

// Configure multer with S3 storage for large file uploads
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

// Export the upload middleware
module.exports = upload;
module.exports.s3Client = s3Client;
module.exports.BUCKET_NAME = BUCKET_NAME;