"""
MapleRepair: Error Detection and Repair Framework for Text-to-SQL

Based on: "A Study of In-Context-Learning-Based Text-to-SQL Errors" (2025)
- 29 error types across 7 categories
- Rule-based + LLM-based repair
- 13.8% more queries repaired with 67.4% less overhead
"""

from .maple_repair_chain import create_maple_repair_chain, invoke_maple_repair_chain

__all__ = ["create_maple_repair_chain", "invoke_maple_repair_chain"]
