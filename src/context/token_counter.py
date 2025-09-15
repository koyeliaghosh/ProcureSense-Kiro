"""
Token counting utilities for accurate budget tracking
"""
import re
from typing import List, Dict, Any


class TokenCounter:
    """
    Utility class for counting tokens in text content.
    Uses a simple approximation based on word count and character patterns.
    """
    
    # Approximate tokens per word for different content types
    TOKENS_PER_WORD = {
        'text': 1.3,  # Regular text
        'code': 1.5,  # Code content
        'json': 1.2,  # JSON data
        'technical': 1.4  # Technical documentation
    }
    
    @classmethod
    def count_tokens(cls, text: str, content_type: str = 'text') -> int:
        """
        Count approximate tokens in text content.
        
        Args:
            text: The text content to count
            content_type: Type of content ('text', 'code', 'json', 'technical')
            
        Returns:
            Estimated token count
        """
        if not text or not text.strip():
            return 0
            
        # Basic word count
        words = len(text.split())
        
        # Adjust for punctuation and special characters
        special_chars = len(re.findall(r'[^\w\s]', text))
        
        # Get multiplier for content type
        multiplier = cls.TOKENS_PER_WORD.get(content_type, 1.3)
        
        # Calculate estimated tokens
        estimated_tokens = int((words + special_chars * 0.5) * multiplier)
        
        return max(1, estimated_tokens)  # Minimum 1 token
    
    @classmethod
    def count_list_tokens(cls, items: List[str], content_type: str = 'text') -> int:
        """Count tokens in a list of strings."""
        return sum(cls.count_tokens(item, content_type) for item in items)
    
    @classmethod
    def count_dict_tokens(cls, data: Dict[str, Any], content_type: str = 'json') -> int:
        """Count tokens in dictionary data."""
        if not data:
            return 0
            
        # Convert dict to string representation for counting
        text_repr = str(data)
        return cls.count_tokens(text_repr, content_type)
    
    @classmethod
    def validate_budget(cls, actual_tokens: int, budget_tokens: int, tolerance: float = 0.05) -> bool:
        """
        Validate if actual token count is within budget.
        
        Args:
            actual_tokens: Actual token count
            budget_tokens: Allocated budget
            tolerance: Allowed tolerance (5% by default)
            
        Returns:
            True if within budget (including tolerance)
        """
        max_allowed = budget_tokens * (1 + tolerance)
        return actual_tokens <= max_allowed