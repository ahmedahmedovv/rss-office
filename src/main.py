import os
from supabase import create_client
from dotenv import load_dotenv
import yaml
import logging
from logging.handlers import RotatingFileHandler
from rss_fetcher import RSSFetcher
from rss_translator import RSSTranslator
from rss_summarizer import RSSSummarizer

def load_config():
    """Load configuration from YAML file"""
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def setup_basic_logger(
    logger_name: str,
    log_file: str = "app.log",
    log_level: str = "INFO",
    log_dir: str = "logs"
):
    """
    Set up a basic logger with both console and file output
    
    Args:
        logger_name: Name of the logger
        log_file: Name of the log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, log_level))
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create and set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Create and set up file handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=1024*1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def read_urls(filename: str) -> list:
    """Read URLs from file"""
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def main():
    # Load environment variables and configuration
    load_dotenv()
    config = load_config()
    logger = setup_basic_logger(
        "RSSApp",
        config['logging']['filename'],
        config['logging']['level'],
        config['logging']['directory']
    )
    
    try:
        # Initialize Supabase client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        mistral_api_key = os.environ.get("MISTRAL_API_KEY")

        # Validate environment variables
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
        if not mistral_api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment variables")

        supabase = create_client(supabase_url, supabase_key)
        
        # Initialize components with validated credentials
        fetcher = RSSFetcher(supabase, logger)
        translator = RSSTranslator(supabase, logger)
        summarizer = RSSSummarizer(
            supabase=supabase,
            mistral_api_key=mistral_api_key,
            logger=logger,
            config=config
        )
        
        # Fetch new RSS entries
        urls = read_urls(config['rss']['urls_file'])
        for url in urls:
            fetcher.fetch_and_save(url, config['rss']['default_history_days'])
        
        # Translate pending entries
        translator.translate_entries(config['translation']['batch_size'])
        
        # Summarize translated entries
        summarizer.summarize_entries(config['summarization']['batch_size'])
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        logger.exception("Detailed error trace:")

if __name__ == "__main__":
    main() 