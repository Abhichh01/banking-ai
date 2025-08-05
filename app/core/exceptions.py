"""
Enhanced exceptions for the Banking AI system.
"""
from typing import Any, Dict, Optional


class BankingAIException(Exception):
    """Base exception for Banking AI system."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AIAnalysisError(BankingAIException):
    """Exception raised when AI analysis fails."""
    
    def __init__(self, message: str, model_used: Optional[str] = None, analysis_type: Optional[str] = None):
        super().__init__(message, "AI_ANALYSIS_ERROR", {
            "model_used": model_used,
            "analysis_type": analysis_type
        })


class CacheError(BankingAIException):
    """Exception raised when cache operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, key: Optional[str] = None):
        super().__init__(message, "CACHE_ERROR", {
            "operation": operation,
            "key": key
        })


class RepositoryError(BankingAIException):
    """Exception raised when repository operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, entity: Optional[str] = None):
        super().__init__(message, "REPOSITORY_ERROR", {
            "operation": operation,
            "entity": entity
        })


class DatabaseError(BankingAIException):
    """Exception raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None):
        super().__init__(message, "DATABASE_ERROR", {
            "operation": operation,
            "table": table
        })


class ValidationError(BankingAIException):
    """Exception raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", {
            "field": field,
            "value": value
        })


class AuthenticationError(BankingAIException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str, user_id: Optional[str] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", {
            "user_id": user_id
        })


class AuthorizationError(BankingAIException):
    """Exception raised when authorization fails."""
    
    def __init__(self, message: str, required_permission: Optional[str] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", {
            "required_permission": required_permission
        })


class RateLimitError(BankingAIException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str, limit: Optional[int] = None, window: Optional[str] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", {
            "limit": limit,
            "window": window
        })


class ServiceUnavailableError(BankingAIException):
    """Exception raised when a service is unavailable."""
    
    def __init__(self, message: str, service: Optional[str] = None, retry_after: Optional[int] = None):
        super().__init__(message, "SERVICE_UNAVAILABLE_ERROR", {
            "service": service,
            "retry_after": retry_after
        })


# Transaction-specific exceptions
class InsufficientFundsError(BankingAIException):
    """Exception raised when there are insufficient funds for a transaction."""
    
    def __init__(self, message: str, account_id: Optional[str] = None, required_amount: Optional[float] = None):
        super().__init__(message, "INSUFFICIENT_FUNDS_ERROR", {
            "account_id": account_id,
            "required_amount": required_amount
        })


class TransactionLimitExceeded(BankingAIException):
    """Exception raised when transaction limits are exceeded."""
    
    def __init__(self, message: str, limit_type: Optional[str] = None, limit_value: Optional[float] = None):
        super().__init__(message, "TRANSACTION_LIMIT_EXCEEDED", {
            "limit_type": limit_type,
            "limit_value": limit_value
        })


class TransactionValidationError(BankingAIException):
    """Exception raised when transaction validation fails."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, validation_errors: Optional[list] = None):
        super().__init__(message, "TRANSACTION_VALIDATION_ERROR", {
            "transaction_id": transaction_id,
            "validation_errors": validation_errors
        })


# Behavioral analysis exceptions
class BehavioralPatternError(BankingAIException):
    """Exception raised when behavioral pattern analysis fails."""
    
    def __init__(self, message: str, pattern_type: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__(message, "BEHAVIORAL_PATTERN_ERROR", {
            "pattern_type": pattern_type,
            "user_id": user_id
        })


class PatternNotFoundError(BankingAIException):
    """Exception raised when a behavioral pattern is not found."""
    
    def __init__(self, message: str, pattern_id: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__(message, "PATTERN_NOT_FOUND_ERROR", {
            "pattern_id": pattern_id,
            "user_id": user_id
        })


class DuplicatePatternError(BankingAIException):
    """Exception raised when a duplicate behavioral pattern is detected."""
    
    def __init__(self, message: str, pattern_type: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__(message, "DUPLICATE_PATTERN_ERROR", {
            "pattern_type": pattern_type,
            "user_id": user_id
        })


class InvalidPatternDataError(BankingAIException):
    """Exception raised when behavioral pattern data is invalid."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, "INVALID_PATTERN_DATA_ERROR", {
            "field": field,
            "value": value
        })


# AI recommendation exceptions
class RecommendationError(BankingAIException):
    """Exception raised when recommendation generation fails."""
    
    def __init__(self, message: str, recommendation_type: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__(message, "RECOMMENDATION_ERROR", {
            "recommendation_type": recommendation_type,
            "user_id": user_id
        })


class InsufficientDataError(BankingAIException):
    """Exception raised when there is insufficient data for analysis."""
    
    def __init__(self, message: str, data_type: Optional[str] = None, required_amount: Optional[int] = None):
        super().__init__(message, "INSUFFICIENT_DATA_ERROR", {
            "data_type": data_type,
            "required_amount": required_amount
        })


# Fraud detection exceptions
class FraudDetectionError(BankingAIException):
    """Exception raised when fraud detection fails."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, risk_score: Optional[float] = None):
        super().__init__(message, "FRAUD_DETECTION_ERROR", {
            "transaction_id": transaction_id,
            "risk_score": risk_score
        })


class RiskAssessmentError(BankingAIException):
    """Exception raised when risk assessment fails."""
    
    def __init__(self, message: str, assessment_type: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__(message, "RISK_ASSESSMENT_ERROR", {
            "assessment_type": assessment_type,
            "user_id": user_id
        })


# LLM orchestrator exceptions
class LLMServiceError(BankingAIException):
    """Exception raised when LLM service fails."""
    
    def __init__(self, message: str, model: Optional[str] = None, provider: Optional[str] = None):
        super().__init__(message, "LLM_SERVICE_ERROR", {
            "model": model,
            "provider": provider
        })


class ModelSelectionError(BankingAIException):
    """Exception raised when model selection fails."""
    
    def __init__(self, message: str, task_type: Optional[str] = None, complexity: Optional[str] = None):
        super().__init__(message, "MODEL_SELECTION_ERROR", {
            "task_type": task_type,
            "complexity": complexity
        })


class PromptGenerationError(BankingAIException):
    """Exception raised when prompt generation fails."""
    
    def __init__(self, message: str, prompt_type: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "PROMPT_GENERATION_ERROR", {
            "prompt_type": prompt_type,
            "context": context
        })


# Memory management exceptions
class MemoryError(BankingAIException):
    """Exception raised when memory operations fail."""
    
    def __init__(self, message: str, memory_type: Optional[str] = None, operation: Optional[str] = None):
        super().__init__(message, "MEMORY_ERROR", {
            "memory_type": memory_type,
            "operation": operation
        })


class ConversationNotFoundError(BankingAIException):
    """Exception raised when a conversation is not found."""
    
    def __init__(self, message: str, conversation_id: Optional[str] = None, user_id: Optional[str] = None):
        super().__init__(message, "CONVERSATION_NOT_FOUND_ERROR", {
            "conversation_id": conversation_id,
            "user_id": user_id
        })


# Configuration exceptions
class ConfigurationError(BankingAIException):
    """Exception raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None):
        super().__init__(message, "CONFIGURATION_ERROR", {
            "config_key": config_key,
            "config_value": config_value
        })


class EnvironmentError(BankingAIException):
    """Exception raised when environment variables are missing or invalid."""
    
    def __init__(self, message: str, env_var: Optional[str] = None):
        super().__init__(message, "ENVIRONMENT_ERROR", {
            "env_var": env_var
        })


# Utility function to create standardized error responses
def create_error_response(
    exception: BankingAIException,
    include_details: bool = False
) -> Dict[str, Any]:
    """Create a standardized error response from an exception."""
    response = {
        "error": True,
        "message": exception.message,
        "error_code": exception.error_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if include_details and exception.details:
        response["details"] = exception.details
    
    return response


# Import datetime for the utility function
from datetime import datetime


class BehavioralAnalysisError(BankingAIException):
    """Exception raised for errors during behavioral analysis."""
    
    def __init__(self, message: str, user_id: Optional[int] = None):
        self.user_id = user_id
        super().__init__(message, error_code="BEHAVIORAL_ANALYSIS_ERROR", details={"user_id": user_id})


class PatternDetectionError(BankingAIException):
    """Exception raised for errors during pattern detection."""
    
    def __init__(self, message: str, user_id: Optional[int] = None):
        self.user_id = user_id
        super().__init__(message, error_code="PATTERN_DETECTION_ERROR", details={"user_id": user_id})