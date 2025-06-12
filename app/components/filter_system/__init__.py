"""
Filter System Module

This module provides a configurable filter system that can be displayed as a dropdown
menu on hover instead of in the sidebar, with per-page configuration options.
"""

from .filter_manager import FilterManager, create_hover_filter_menu
from .filter_config import PageFilterConfig, FilterType

__all__ = ['FilterManager', 'create_hover_filter_menu', 'PageFilterConfig', 'FilterType']
