# Baap AI WebChat API

A comprehensive FastAPI-based backend for an AI-powered web chat widget system with multi-chatbot support, document processing, web scraping, and intelligent question answering capabilities.

## 🚀 Features

- **Multi-Chatbot Management**: Create and manage multiple chatbots with different knowledge bases
- **Document Processing**: Upload and process PDF, SVG, TXT, DOC, and DOCX files
- **Web Scraping**: Automatically scrape websites and ingest content into vector databases
- **AI-Powered Q&A**: Intelligent question answering using Gemini AI and vector similarity search
- **User Authentication**: JWT-based authentication with user management
- **Vector Database Integration**: Qdrant vector database for semantic search
- **Conversation Memory**: Maintain conversation history for context-aware responses
- **Real-time Progress Tracking**: Monitor scraping and processing tasks in real-time
- **Comprehensive Logging**: Structured logging throughout the application

## 📁 Project Structure

```
baap_builder/
├── app/
│   ├── api/
│   │   ├── main_routes.py         # Main API router configuration
│   │   ├── routes/               # API route modules
│   │   │   ├── ask_quation.py    # Ask question endpoints
│   │   │   ├── auth.py           # Auth endpoints
│   │   │   ├── chatbots.py       # Chatbot management endpoints
│   │   │   ├── files.py          # File upload and processing
│   │   │   ├── scraping.py       # Web scraping endpoints
│   │   │   └── __init__.py       # Init file
│   │   └── __init__.py           # Init file
│   ├── auth/
│   │   └── auth.py               # Authentication logic
│   ├── db/
│   │   ├── postgres.py           # PostgreSQL database operations
│   │   └── qdrant.py             # Qdrant vector database operations
│   ├── schema/                   # Pydantic schemas
│   │   ├── ask_question.py       # Schema for Q&A
│   │   ├── auth_schema.py        # Schema for authentication
│   │   ├── chatbots.py           # Schema for chatbots
│   │   └── scrap_schema.py       # Schema for scraping
│   ├── services/
│   │   ├── embeddings.py         # Embedding generation
│   │   └── gemini.py             # Gemini AI integration
│   ├── utils/
│   │   ├── common.py             # Common utility functions
│   │   ├── conversation.py       # Conversation management
│   │   ├── langChain.py          # LangChain integration
│   │   ├── logger.py             # Logger setup
│   │   ├── process_files.py      # File processing utilities
│   │   ├── scraping_utils.py     # Web scraping utilities
│   │   └── task_management.py    # Background task management
│   ├── config.py                 # Centralized application settings
│   └── main.py                   # FastAPI application entry point
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
└── venv/                         # Virtual environment (not versioned)
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Qdrant Vector Database (optional, stubs provided)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd baap_builder
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# Or
source venv/bin/activate  # On Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=baap_ai_chatbot_v5

# JWT Configuration
SECRET_KEY=your_secret_key_here

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Qdrant Configuration (optional)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 5. Database Setup

The application will automatically create required tables on startup:
- `users` - User accounts and authentication
- `chatbots` - Chatbot configurations and metadata
- `conversations` - Conversation history storage

### 6. Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api
```

### Authentication Endpoints

| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| POST   | `/auth/signup`     | Register a new user      |
| POST   | `/auth/login`      | Login with credentials   |

### Chatbot Management

| Method | Endpoint                         | Description                |
|--------|----------------------------------|----------------------------|
| GET    | `/chatbots/user/chatbots`        | Get user's chatbots        |
| POST   | `/chatbots`                      | Create a new chatbot       |
| DELETE | `/chatbots/{chatbot_id}`         | Delete a chatbot           |

### File Processing

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| POST   | `/files/upload-and-process`     | Upload and process documents       |

### Question Answering

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| POST   | `/questions/ask-question`       | Ask questions to AI chatbot        |

### Web Scraping

| Method | Endpoint                                          | Description                                 |
|--------|---------------------------------------------------|---------------------------------------------|
| POST   | `/scraping/scrape-and-ingest`                     | Start web scraping task                     |
| GET    | `/scraping/scraping-progress/{task_id}`           | Get scraping progress                       |
| POST   | `/scraping/stop-scraping/{task_id}`               | Stop scraping task                          |
| POST   | `/scraping/stop-and-store-scraping/{task_id}`     | Stop and store partial results              |

> **Note:** Some endpoints for listing or deleting scraping tasks are commented out in the code and not currently available.

## 🔧 Key Components

- **Authentication System**: JWT-based token authentication, password hashing, user registration and login endpoints, protected route middleware
- **Database Layer**: MySQL for user/chatbot/conversation data, Qdrant for vector storage
- **AI Integration**: Google Gemini AI for Q&A, Sentence Transformers for embeddings, LangChain for conversation memory
- **File Processing**: PDF, SVG, TXT, DOC, DOCX support, text extraction, chunking, vector embedding, ingestion
- **Web Scraping**: Automated crawling, content extraction, incremental storage, real-time progress, cancellation

## 🚀 Usage Examples

### 1. User Registration
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword"
  }'
```

### 2. User Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

### 3. Create Chatbot
```bash
curl -X POST "http://localhost:8000/api/chatbots" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Chatbot",
    "description": "A helpful AI assistant",
    "collection_name": "my_knowledge_base",
    "source_url": "https://example.com"
  }'
```

### 4. Upload and Process File
```bash
curl -X POST "http://localhost:8000/api/files/upload-and-process" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "collection_name=my_knowledge_base"
```

### 5. Ask Question
```bash
curl -X POST "http://localhost:8000/api/questions/ask-question" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What services do you offer?",
    "collection_name": "my_knowledge_base"
  }'
```

### 6. Start Web Scraping
```bash
curl -X POST "http://localhost:8000/api/scraping/scrape-and-ingest" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "collection_name": "scraped_content"
  }'
```

### 7. Get Scraping Progress
```bash
curl -X GET "http://localhost:8000/api/scraping/scraping-progress/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 8. Stop Scraping
```bash
curl -X POST "http://localhost:8000/api/scraping/stop-scraping/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 9. Stop and Store Scraping
```bash
curl -X POST "http://localhost:8000/api/scraping/stop-and-store-scraping/{task_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔍 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Development

### Running Tests
```bash
# Add test commands when implemented
pytest
```

### Code Formatting
```bash
# Add formatting commands when implemented
black .
isort .
```

### Linting
```bash
# Add linting commands when implemented
flake8 .
mypy .
```

## 📝 Logging

The application uses structured logging throughout:
- Log level: INFO
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Output: Console (stdout)
- All major operations are logged with START/END markers

## 🔒 Security Features

- JWT token authentication
- Password hashing with bcrypt
- CORS middleware configuration
- Input validation with Pydantic models
- SQL injection prevention with parameterized queries

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Use proper secret management
2. **Database**: Configure production MySQL instance
3. **Vector Database**: Set up Qdrant in production
4. **Logging**: Configure production logging (file, syslog, etc.)
5. **CORS**: Restrict allowed origins in production
6. **Rate Limiting**: Implement API rate limiting
7. **Monitoring**: Add health checks and monitoring

### Docker Deployment (Future Enhancement)

```dockerfile
# Add Dockerfile when implemented
FROM python:3.10-slim
# ... Docker configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


# Production 

1. Environment Variables: Use proper secret management
2. Database: Configure production MySQL instance
3. Vector Database: Set up Qdrant in production
4. Logging: Configure production logging (file, syslog, etc.)
5. CORS: Restrict allowed origins in production
6. Rate Limiting: Implement API rate limiting
7. Monitoring: Add health checks and monitoring

# 🐳 Docker Deployment
1. Build the Docker Image
  - Make sure you're in the root directory (where the Dockerfile is located):
  ```
    docker build -t baap-builder .
  ```
    This builds the Docker image using the configuration defined in your Dockerfile.

2. 🚀 Run the Docker Container
   ```
    docker run -d \
  --name baap-builder-container \
  --env-file .env \
  -p 8000:8000 \
  baap-builder
   ```
  - --env-file .env: Loads environment variables (DB credentials, API keys, etc.)
  - -p 8000:8000: Maps container port to local host
  - The app will be available at: http://localhost:8000

3. 🧼 Stop & Clean Up
   ```
   docker stop baap-builder-container
   docker rm baap-builder-container
   ```

# 🔁 Optional: Rebuild on Code Changes
    - If you update your code and want to apply changes:
    ```
    docker build -t baap-builder .
    docker stop baap-builder-container
    docker rm baap-builder-container
    docker run -d \
      --name baap-builder-container \
      --env-file .env \
      -p 8000:8000 \
      baap-builder
    ```


**Note**: This is a production-ready FastAPI application with comprehensive features for AI-powered web chat functionality. The modular architecture makes it easy to extend and maintain.