"""
Project Alpha-Nexus - Agents Package
Modular multi-agent implementations for the LangGraph orchestration.
"""

from agents.scraper_agent import node_scraper
from agents.financial_agent import node_financial_analyst
from agents.career_agent import node_career_strategy
from agents.supervisor_agent import node_supervisor
from agents.learning_agent import node_learning_companion

__all__ = [
    "node_scraper",
    "node_financial_analyst",
    "node_career_strategy",
    "node_supervisor",
    "node_learning_companion",
]