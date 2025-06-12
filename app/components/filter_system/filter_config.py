"""
Filter Configuration System

Defines which filters are available on each page and their configuration.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


class FilterType(Enum):
    """Available filter types"""
    DATE_RANGE = "date_range"
    MAILBOX_SELECTION = "mailbox_selection"
    DIRECTION = "direction"
    SENDER = "sender"
    RECIPIENT = "recipient"
    HAS_ATTACHMENTS = "has_attachments"
    MAILING_LIST = "mailing_list"
    ADVANCED_SEARCH = "advanced_search"
    CONTACT_FILTER = "contact_filter"


@dataclass
class FilterConfig:
    """Configuration for a single filter"""
    filter_type: FilterType
    enabled: bool = True
    required: bool = False
    default_value: Any = None
    options: Optional[Dict[str, Any]] = None


@dataclass
class PageFilterConfig:
    """Configuration for filters on a specific page"""
    page_name: str
    show_filter_bar: bool = True
    filters: List[FilterConfig] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = []


class FilterConfigManager:
    """Manages filter configurations for all pages"""
    
    def __init__(self):
        self.page_configs = {}
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Set up default filter configurations for each page"""
        
        # Dashboard - full filters
        self.page_configs["Dashboard"] = PageFilterConfig(
            page_name="Dashboard",
            show_filter_bar=True,
            filters=[
                FilterConfig(FilterType.DATE_RANGE, enabled=True, required=True),
                FilterConfig(FilterType.MAILBOX_SELECTION, enabled=True, required=True),
                FilterConfig(FilterType.DIRECTION, enabled=True),
                FilterConfig(FilterType.HAS_ATTACHMENTS, enabled=True),
                FilterConfig(FilterType.MAILING_LIST, enabled=True),
                FilterConfig(FilterType.CONTACT_FILTER, enabled=True),
            ]
        )
        
        # Email Explorer - search focused
        self.page_configs["Email Explorer"] = PageFilterConfig(
            page_name="Email Explorer",
            show_filter_bar=True,
            filters=[
                FilterConfig(FilterType.DATE_RANGE, enabled=True, required=True),
                FilterConfig(FilterType.MAILBOX_SELECTION, enabled=True, required=True),
                FilterConfig(FilterType.DIRECTION, enabled=True),
                FilterConfig(FilterType.SENDER, enabled=True),
                FilterConfig(FilterType.RECIPIENT, enabled=True),
                FilterConfig(FilterType.HAS_ATTACHMENTS, enabled=True),
                FilterConfig(FilterType.ADVANCED_SEARCH, enabled=True),
            ]
        )
        
        # Graph - minimal filters (graphs work best with full datasets)
        self.page_configs["Graph"] = PageFilterConfig(
            page_name="Graph",
            show_filter_bar=False,  # No filters for graph by default
            filters=[]
        )
        
        # Search pages - full search capabilities
        self.page_configs["Recherche Sémantique"] = PageFilterConfig(
            page_name="Recherche Sémantique",
            show_filter_bar=True,
            filters=[
                FilterConfig(FilterType.DATE_RANGE, enabled=True),
                FilterConfig(FilterType.MAILBOX_SELECTION, enabled=True, required=True),
                FilterConfig(FilterType.DIRECTION, enabled=True),
                FilterConfig(FilterType.SENDER, enabled=True),
                FilterConfig(FilterType.RECIPIENT, enabled=True),
                FilterConfig(FilterType.HAS_ATTACHMENTS, enabled=True),
                FilterConfig(FilterType.ADVANCED_SEARCH, enabled=True),
            ]
        )
        
        # Recherche ElasticSearch - has its own internal filters
        self.page_configs["Recherche ElasticSearch"] = PageFilterConfig(
            page_name="Recherche ElasticSearch",
            show_filter_bar=False,  # Has its own internal filter system
            filters=[]
        )
        
        # RAG/Chat pages - basic filters
        self.page_configs["Chat + RAG"] = PageFilterConfig(
            page_name="Chat + RAG",
            show_filter_bar=True,
            filters=[
                FilterConfig(FilterType.DATE_RANGE, enabled=True),
                FilterConfig(FilterType.MAILBOX_SELECTION, enabled=True, required=True),
            ]
        )
        
        self.page_configs["Colbert RAG"] = PageFilterConfig(
            page_name="Colbert RAG",
            show_filter_bar=True,
            filters=[
                FilterConfig(FilterType.DATE_RANGE, enabled=True),
                FilterConfig(FilterType.MAILBOX_SELECTION, enabled=True, required=True),
            ]
        )
        
        # Structure de la boîte mail - no filters needed
        self.page_configs["Structure de la boîte mail"] = PageFilterConfig(
            page_name="Structure de la boîte mail",
            show_filter_bar=False,
            filters=[]
        )
        
    def get_page_config(self, page_name: str) -> PageFilterConfig:
        """Get the filter configuration for a specific page"""
        return self.page_configs.get(page_name, PageFilterConfig(page_name, show_filter_bar=False, filters=[]))
    
    def update_page_config(self, page_name: str, config: PageFilterConfig):
        """Update the configuration for a specific page"""
        self.page_configs[page_name] = config
        
    def get_enabled_filters(self, page_name: str) -> List[FilterConfig]:
        """Get all enabled filters for a specific page"""
        config = self.get_page_config(page_name)
        return [filter_config for filter_config in config.filters if filter_config.enabled]
        
    def is_filter_enabled(self, page_name: str, filter_type: FilterType) -> bool:
        """Check if a specific filter is enabled for a page"""
        enabled_filters = self.get_enabled_filters(page_name)
        return any(f.filter_type == filter_type for f in enabled_filters)
        
    def should_show_filter_bar(self, page_name: str) -> bool:
        """Check if the filter bar should be shown for a page"""
        config = self.get_page_config(page_name)
        return config.show_filter_bar


# Global instance
filter_config_manager = FilterConfigManager()
