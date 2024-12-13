import redis
import os
import logging

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        logger.info("Initializing Redis Service")
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        
        logger.debug(f"Connecting to Redis at {redis_host}:{redis_port}")
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=0,
            decode_responses=True
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info("Successfully connected to Redis")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def toggle_article_read(self, user_id, article_link):
        """Toggle the read status of an article for a user."""
        try:
            key = f"user:{user_id}:read_articles"
            logger.debug(f"Toggling article status. Key: {key}, Article: {article_link}")
            
            # Check current status
            current_status = self.redis_client.sismember(key, article_link)
            logger.debug(f"Current read status: {current_status}")
            
            if current_status:
                logger.debug("Removing article from read set")
                self.redis_client.srem(key, article_link)
                return False
            else:
                logger.debug("Adding article to read set")
                self.redis_client.sadd(key, article_link)
                return True
                
        except redis.RedisError as e:
            logger.exception(f"Redis error in toggle_article_read: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in toggle_article_read: {str(e)}")
            raise

    def get_all_read_articles(self, user_id):
        """Get all read articles for a user"""
        try:
            key = f"user:{user_id}:read_articles"
            logger.debug(f"Fetching all read articles for key: {key}")
            articles = list(self.redis_client.smembers(key))
            logger.debug(f"Found {len(articles)} read articles")
            return articles
        except redis.RedisError as e:
            logger.exception(f"Redis error in get_all_read_articles: {str(e)}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected error in get_all_read_articles: {str(e)}")
            return []

    def clear_read_history(self, user_id):
        """Clear all read articles for a user"""
        try:
            key = f"user:{user_id}:read_articles"
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Redis error in clear_read_history: {str(e)}")  # Add logging
            raise