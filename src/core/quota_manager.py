"""API Quota Management and Rate Limiting"""
import json
import time
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ProviderQuota:
    """Quota limits for a provider"""
    provider: str
    max_tokens_per_hour: int = 100000
    max_tokens_per_day: int = 1000000
    max_requests_per_minute: int = 60
    max_vision_calls_per_hour: int = 100
    
    # Current usage
    tokens_used_hour: int = 0
    tokens_used_day: int = 0
    requests_this_minute: int = 0
    vision_calls_hour: int = 0
    
    # Timestamps
    hour_reset: float = field(default_factory=time.time)
    day_reset: float = field(default_factory=time.time)
    minute_reset: float = field(default_factory=time.time)

class QuotaManager:
    """Manage API quotas and rate limits"""
    
    def __init__(self, storage_path: str = ".quota_usage.json"):
        self.storage_path = Path(storage_path)
        self.quotas: Dict[str, ProviderQuota] = {}
        self._load()
    
    def set_limits(self, provider: str, 
                   max_tokens_per_hour: int = 100000,
                   max_tokens_per_day: int = 1000000,
                   max_requests_per_minute: int = 60,
                   max_vision_calls_per_hour: int = 100):
        """Set quota limits for a provider"""
        if provider not in self.quotas:
            self.quotas[provider] = ProviderQuota(provider=provider)
        
        quota = self.quotas[provider]
        quota.max_tokens_per_hour = max_tokens_per_hour
        quota.max_tokens_per_day = max_tokens_per_day
        quota.max_requests_per_minute = max_requests_per_minute
        quota.max_vision_calls_per_hour = max_vision_calls_per_hour
        
        self._save()
        logger.info(f"Set quota limits for {provider}")
    
    def check_quota(self, provider: str, tokens: int, 
                    is_vision: bool = False) -> bool:
        """Check if request is within quota
        
        Args:
            provider: Provider name
            tokens: Tokens to be used
            is_vision: Whether this is a vision API call
        
        Returns:
            True if within quota, False otherwise
        """
        if provider not in self.quotas:
            self.quotas[provider] = ProviderQuota(provider=provider)
        
        quota = self.quotas[provider]
        self._reset_if_needed(quota)
        
        # Check rate limits
        if quota.requests_this_minute >= quota.max_requests_per_minute:
            logger.warning(f"Rate limit exceeded for {provider} (requests/min)")
            return False
        
        # Check token limits
        if quota.tokens_used_hour + tokens > quota.max_tokens_per_hour:
            logger.warning(f"Hourly token limit exceeded for {provider}")
            return False
        
        if quota.tokens_used_day + tokens > quota.max_tokens_per_day:
            logger.warning(f"Daily token limit exceeded for {provider}")
            return False
        
        # Check vision calls
        if is_vision and quota.vision_calls_hour >= quota.max_vision_calls_per_hour:
            logger.warning(f"Vision call limit exceeded for {provider}")
            return False
        
        return True
    
    def record_usage(self, provider: str, tokens: int, is_vision: bool = False):
        """Record API usage
        
        Args:
            provider: Provider name
            tokens: Tokens used
            is_vision: Whether this was a vision call
        """
        if provider not in self.quotas:
            self.quotas[provider] = ProviderQuota(provider=provider)
        
        quota = self.quotas[provider]
        self._reset_if_needed(quota)
        
        quota.tokens_used_hour += tokens
        quota.tokens_used_day += tokens
        quota.requests_this_minute += 1
        
        if is_vision:
            quota.vision_calls_hour += 1
        
        self._save()
        
        logger.debug(f"{provider}: +{tokens} tokens, "
                    f"hour={quota.tokens_used_hour}/{quota.max_tokens_per_hour}, "
                    f"day={quota.tokens_used_day}/{quota.max_tokens_per_day}")
    
    def get_usage(self, provider: str) -> Dict:
        """Get current usage stats for provider"""
        if provider not in self.quotas:
            return {}
        
        quota = self.quotas[provider]
        self._reset_if_needed(quota)
        
        return {
            'tokens_hour': quota.tokens_used_hour,
            'tokens_day': quota.tokens_used_day,
            'requests_minute': quota.requests_this_minute,
            'vision_calls_hour': quota.vision_calls_hour,
            'limits': {
                'max_tokens_hour': quota.max_tokens_per_hour,
                'max_tokens_day': quota.max_tokens_per_day,
                'max_requests_minute': quota.max_requests_per_minute,
                'max_vision_calls_hour': quota.max_vision_calls_per_hour
            }
        }
    
    def reset_usage(self, provider: Optional[str] = None):
        """Reset usage counters
        
        Args:
            provider: Provider to reset, or None for all
        """
        if provider:
            if provider in self.quotas:
                quota = self.quotas[provider]
                quota.tokens_used_hour = 0
                quota.tokens_used_day = 0
                quota.requests_this_minute = 0
                quota.vision_calls_hour = 0
                quota.hour_reset = time.time()
                quota.day_reset = time.time()
                quota.minute_reset = time.time()
                logger.info(f"Reset usage for {provider}")
        else:
            for quota in self.quotas.values():
                quota.tokens_used_hour = 0
                quota.tokens_used_day = 0
                quota.requests_this_minute = 0
                quota.vision_calls_hour = 0
                quota.hour_reset = time.time()
                quota.day_reset = time.time()
                quota.minute_reset = time.time()
            logger.info("Reset usage for all providers")
        
        self._save()
    
    def _reset_if_needed(self, quota: ProviderQuota):
        """Check and reset counters if time windows have passed"""
        now = time.time()
        
        # Reset minute counter
        if now - quota.minute_reset >= 60:
            quota.requests_this_minute = 0
            quota.minute_reset = now
        
        # Reset hourly counters
        if now - quota.hour_reset >= 3600:
            quota.tokens_used_hour = 0
            quota.vision_calls_hour = 0
            quota.hour_reset = now
        
        # Reset daily counter
        if now - quota.day_reset >= 86400:
            quota.tokens_used_day = 0
            quota.day_reset = now
    
    def _save(self):
        """Save quota data to disk"""
        try:
            data = {
                provider: asdict(quota)
                for provider, quota in self.quotas.items()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save quota data: {e}")
    
    def _load(self):
        """Load quota data from disk"""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for provider, quota_data in data.items():
                self.quotas[provider] = ProviderQuota(**quota_data)
        except Exception as e:
            logger.warning(f"Failed to load quota data: {e}")
