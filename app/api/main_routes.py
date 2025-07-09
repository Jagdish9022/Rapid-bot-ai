from fastapi import APIRouter
from app.api.routes import auth, scraping, files, chatbots, ask_quation
 
api_router = APIRouter(prefix="/api")
 
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(scraping.router, prefix="/scraping", tags=["Scraping"])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(chatbots.router, prefix="/chatbots", tags=["Chatbots"])
api_router.include_router(ask_quation.router, prefix="/questions", tags=["Question Answering"])
 