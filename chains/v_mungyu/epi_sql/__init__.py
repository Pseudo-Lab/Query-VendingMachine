"""
EPI-SQL: Error-Prevention Instructions for Text-to-SQL

Based on: "EPI-SQL: Enhancing Text-to-SQL Translation with Error-Prevention Instructions" (2024)
- Proactive error prevention through contextualized instructions
- 85.1% execution accuracy on Spider benchmark
- Zero-shot approach with task-specific guidance
"""

from .epi_sql_chain import create_epi_sql_chain, invoke_epi_sql_chain

__all__ = ["create_epi_sql_chain", "invoke_epi_sql_chain"]
