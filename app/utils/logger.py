"""
Structured logging configuration for BISG Labels service
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(app_name="bisg-labels", log_level=None):
    """
    Configure structured logging with file rotation and console output

    Args:
        app_name: Name of the application
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Get log level from environment or use default
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler (rotating, only in development)
    # Railway uses ephemeral filesystem, so file logging is not recommended
    if os.getenv('FLASK_ENV') == 'development':
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            os.path.join(log_dir, f'{app_name}.log'),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


def log_request(logger, request, extra_data=None):
    """
    Log incoming HTTP request with sanitized data

    Args:
        logger: Logger instance
        request: Flask request object
        extra_data: Optional dictionary of additional data to log
    """
    data = {
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')[:100],
    }

    if extra_data:
        data.update(extra_data)

    # Don't log sensitive data (API keys, passwords, etc.)
    logger.info(f"Request: {data}")


def log_response(logger, request, response, duration_ms=None):
    """
    Log HTTP response

    Args:
        logger: Logger instance
        request: Flask request object
        response: Flask response object
        duration_ms: Request duration in milliseconds
    """
    data = {
        'method': request.method,
        'path': request.path,
        'status': response.status_code,
    }

    if duration_ms is not None:
        data['duration_ms'] = round(duration_ms, 2)

    logger.info(f"Response: {data}")


def log_error(logger, error, request=None, extra_data=None):
    """
    Log error with context

    Args:
        logger: Logger instance
        error: Exception object
        request: Optional Flask request object
        extra_data: Optional dictionary of additional data
    """
    data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
    }

    if request:
        data.update({
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
        })

    if extra_data:
        data.update(extra_data)

    logger.error(f"Error: {data}", exc_info=True)


def sanitize_log_data(data):
    """
    Remove sensitive information from log data

    Args:
        data: Dictionary of data to sanitize

    Returns:
        dict: Sanitized data
    """
    sensitive_keys = [
        'password', 'token', 'api_key', 'secret', 'credit_card',
        'cvv', 'ssn', 'stripe_key', 'client_secret'
    ]

    sanitized = data.copy()

    for key in sanitized.keys():
        # Check if key contains sensitive terms
        if any(sensitive_term in key.lower() for sensitive_term in sensitive_keys):
            sanitized[key] = '***REDACTED***'

    return sanitized
