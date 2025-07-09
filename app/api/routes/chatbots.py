from fastapi import APIRouter, HTTPException, Depends
from app.schema.chatbots import ChatbotCreate, ChatbotInfo, UserChatbotsResponse
from app.auth.auth import get_current_active_user
from app.db.postgres import get_db
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
import uuid
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/user/chatbots", response_model=UserChatbotsResponse)
async def get_user_chatbots(current_user=Depends(get_current_active_user), db=Depends(get_db)):
    try:
        cursor = db.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM chatbots 
            WHERE user_id = %s AND is_active = TRUE 
            ORDER BY created_at DESC
        """, (current_user['id'],))
        chatbots = cursor.fetchall()
        cursor.close()
        return {"chatbots": chatbots, "total_count": len(chatbots)}
    except Exception as e:
        logger.error(f"Error fetching user chatbots: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching chatbots")

@router.post("/", response_model=ChatbotInfo)
async def create_chatbot(chatbot_data: ChatbotCreate, current_user=Depends(get_current_active_user), db=Depends(get_db)):
    try:
        chatbot_id = str(uuid.uuid4())
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO chatbots (id, user_id, name, description, collection_name, source_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            chatbot_id,
            current_user['id'],
            chatbot_data.name,
            chatbot_data.description,
            chatbot_data.collection_name,
            chatbot_data.source_url
        ))
        db.commit()
        cursor.close()

        cursor = db.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM chatbots WHERE id = %s", (chatbot_id,))
        chatbot = cursor.fetchone()
        cursor.close()
        return chatbot
    except Exception as e:
        logger.error(f"Error creating chatbot: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating chatbot")

@router.delete("/{chatbot_id}")
async def delete_chatbot(chatbot_id: str, current_user=Depends(get_current_active_user), db=Depends(get_db)):
    try:
        logger.info(f"Delete request for chatbot {chatbot_id} by user {current_user['id']}")

        cursor = db.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM chatbots 
            WHERE id = %s AND user_id = %s AND is_active = TRUE
        """, (chatbot_id, current_user['id']))
        chatbot = cursor.fetchone()
        cursor.close()

        if not chatbot:
            logger.warning(f"Chatbot not found or access denied: {chatbot_id}")
            raise HTTPException(
                status_code=404,
                detail="Chatbot not found or you don't have permission to delete it"
            )

        cursor = db.cursor()
        cursor.execute("""
            UPDATE chatbots 
            SET is_active = FALSE, updated_at = %s
            WHERE id = %s AND user_id = %s
        """, (datetime.now(), chatbot_id, current_user['id']))
        db.commit()

        if cursor.rowcount == 0:
            cursor.close()
            logger.error(f"Failed to delete chatbot: {chatbot_id}")
            raise HTTPException(status_code=500, detail="Failed to delete chatbot")

        cursor.close()
        logger.info(f"Chatbot {chatbot_id} successfully deleted by user {current_user['id']}")
        return {
            "status": "success",
            "message": "Chatbot deleted successfully",
            "chatbot_id": chatbot_id,
            "chatbot_name": chatbot.get('name', 'Unknown')
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting chatbot {chatbot_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An error occurred while deleting the chatbot")
