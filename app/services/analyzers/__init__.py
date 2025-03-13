"""
Analyzer Package Initialization
This module initializes the analyzer package and provides utilities for importing all analyzers.
"""

from app.services.analyzers.content_analyzer import ContentQualityAnalyzer
from app.services.analyzers.mobile_analyzer import MobileAnalyzer
from app.services.analyzers.technical_analyzer import TechnicalSEOAnalyzer
from app.services.analyzers.meta_analyzer import MetaAnalyzer
from app.services.analyzers.keyword_analyzer import KeywordOptimizationAnalyzer
from app.services.analyzers.competitive_analyzer import CompetitiveAnalyzer

# Export all analyzer classes
__all__ = [
    'ContentQualityAnalyzer',
    'MobileAnalyzer',
    'TechnicalSEOAnalyzer',
    'MetaAnalyzer',
    'KeywordOptimizationAnalyzer',
    'CompetitiveAnalyzer'
]

def get_all_analyzers():
    """
    Get instances of all available analyzers
    
    Returns:
        list: List of analyzer instances
    """
    return [
        MetaAnalyzer(),
        ContentQualityAnalyzer(),
        KeywordOptimizationAnalyzer(),
        TechnicalSEOAnalyzer(),
        MobileAnalyzer(),
        CompetitiveAnalyzer()
    ]