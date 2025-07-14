"""
Database Query Optimization and Analysis Tools
Provides utilities for analyzing query performance and suggesting optimizations
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from database import get_db, engine
from models import (
    Store, Product, ProductVariant, InventoryItem, Alert, 
    CustomFieldDefinition, WorkflowRule, Location, InventoryMovement
)

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database performance analysis and optimization utilities"""
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session or next(get_db())
        self.engine = engine
    
    def analyze_query_performance(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Analyze the performance of a specific query"""
        start_time = time.time()
        
        try:
            # Execute query with timing
            result = self.db_session.execute(text(query), params or {})
            rows = result.fetchall()
            execution_time = time.time() - start_time
            
            # Get query plan (PostgreSQL specific)
            explain_query = f"EXPLAIN ANALYZE {query}"
            try:
                explain_result = self.db_session.execute(text(explain_query), params or {})
                query_plan = [row[0] for row in explain_result.fetchall()]
            except Exception:
                query_plan = ["Query plan not available (requires PostgreSQL)"]
            
            return {
                "query": query,
                "execution_time_ms": execution_time * 1000,
                "row_count": len(rows),
                "query_plan": query_plan,
                "performance_rating": self._rate_performance(execution_time, len(rows))
            }
            
        except Exception as e:
            return {
                "query": query,
                "error": str(e),
                "execution_time_ms": (time.time() - start_time) * 1000
            }
    
    def _rate_performance(self, execution_time: float, row_count: int) -> str:
        """Rate query performance based on execution time and row count"""
        if execution_time < 0.01:  # < 10ms
            return "excellent"
        elif execution_time < 0.1:  # < 100ms
            return "good"
        elif execution_time < 0.5:  # < 500ms
            return "acceptable"
        elif execution_time < 2.0:  # < 2s
            return "slow"
        else:
            return "very_slow"
    
    def get_table_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tables"""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        
        stats = {}
        for table in tables:
            try:
                # Get row count
                count_query = f"SELECT COUNT(*) FROM {table}"
                result = self.db_session.execute(text(count_query))
                row_count = result.scalar()
                
                # Get table size (PostgreSQL specific)
                try:
                    size_query = f"SELECT pg_size_pretty(pg_total_relation_size('{table}'))"
                    size_result = self.db_session.execute(text(size_query))
                    table_size = size_result.scalar()
                except Exception:
                    table_size = "Unknown"
                
                # Get indexes
                indexes = inspector.get_indexes(table)
                
                stats[table] = {
                    "row_count": row_count,
                    "table_size": table_size,
                    "index_count": len(indexes),
                    "indexes": [idx["name"] for idx in indexes]
                }
                
            except Exception as e:
                stats[table] = {"error": str(e)}
        
        return stats
    
    def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analyze common slow queries and suggest optimizations"""
        slow_queries = []
        
        # Common query patterns that might be slow
        test_queries = [
            {
                "name": "Get all products for store with status filter",
                "query": """
                    SELECT p.id, p.title, p.status, p.product_type
                    FROM products p 
                    WHERE p.store_id = :store_id AND p.status = 'active'
                    ORDER BY p.created_at DESC
                    LIMIT 50
                """,
                "params": {"store_id": 1}
            },
            {
                "name": "Get low stock items",
                "query": """
                    SELECT i.id, v.sku, i.available_quantity, i.reorder_point
                    FROM inventory_items i
                    JOIN product_variants v ON i.variant_id = v.id
                    WHERE i.store_id = :store_id 
                    AND i.available_quantity <= i.reorder_point
                    ORDER BY i.available_quantity ASC
                """,
                "params": {"store_id": 1}
            },
            {
                "name": "Get unresolved alerts",
                "query": """
                    SELECT a.id, a.alert_type, a.severity, a.title, a.created_at
                    FROM alerts a
                    WHERE a.store_id = :store_id 
                    AND a.is_resolved = false
                    ORDER BY a.created_at DESC, a.severity DESC
                    LIMIT 100
                """,
                "params": {"store_id": 1}
            },
            {
                "name": "Search products by title",
                "query": """
                    SELECT p.id, p.title, p.product_type, p.vendor
                    FROM products p
                    WHERE p.store_id = :store_id 
                    AND p.title ILIKE '%' || :search_term || '%'
                    ORDER BY p.title
                    LIMIT 20
                """,
                "params": {"store_id": 1, "search_term": "test"}
            },
            {
                "name": "Get variant inventory across locations",
                "query": """
                    SELECT v.sku, l.name, i.available_quantity, i.reorder_point
                    FROM inventory_items i
                    JOIN product_variants v ON i.variant_id = v.id
                    JOIN locations l ON i.location_id = l.id
                    WHERE i.store_id = :store_id AND v.sku = :sku
                """,
                "params": {"store_id": 1, "sku": "TEST-SKU"}
            },
            {
                "name": "Get product with variants and inventory",
                "query": """
                    SELECT p.title, v.title as variant_title, v.sku, 
                           SUM(i.available_quantity) as total_stock
                    FROM products p
                    JOIN product_variants v ON p.id = v.product_id
                    LEFT JOIN inventory_items i ON v.id = i.variant_id
                    WHERE p.store_id = :store_id AND p.id = :product_id
                    GROUP BY p.id, p.title, v.id, v.title, v.sku
                """,
                "params": {"store_id": 1, "product_id": 1}
            },
            {
                "name": "Get workflow rules for event",
                "query": """
                    SELECT w.id, w.rule_name, w.trigger_conditions, w.actions
                    FROM workflow_rules w
                    WHERE w.store_id = :store_id 
                    AND w.is_active = true 
                    AND w.trigger_event = :event_type
                    ORDER BY w.priority ASC
                """,
                "params": {"store_id": 1, "event_type": "inventory_low"}
            }
        ]
        
        for query_info in test_queries:
            result = self.analyze_query_performance(
                query_info["query"], 
                query_info["params"]
            )
            result["query_name"] = query_info["name"]
            slow_queries.append(result)
        
        return slow_queries
    
    def suggest_missing_indexes(self) -> List[Dict[str, Any]]:
        """Suggest missing indexes based on common query patterns"""
        suggestions = []
        
        # Analyze query patterns and suggest indexes
        query_patterns = [
            {
                "table": "products",
                "columns": ["store_id", "status", "created_at"],
                "reason": "Common dashboard queries filtering by store and status with date ordering"
            },
            {
                "table": "inventory_items", 
                "columns": ["store_id", "available_quantity"],
                "reason": "Stock level reports and low stock detection"
            },
            {
                "table": "alerts",
                "columns": ["store_id", "is_resolved", "severity"],
                "reason": "Alert dashboard filtering by resolution status and severity"
            },
            {
                "table": "product_variants",
                "columns": ["sku"],
                "reason": "SKU lookups are extremely common in inventory operations"
            },
            {
                "table": "workflow_rules",
                "columns": ["store_id", "is_active", "trigger_event"],
                "reason": "Workflow execution queries filtering by store, active status, and event type"
            }
        ]
        
        inspector = inspect(self.engine)
        
        for pattern in query_patterns:
            table_name = pattern["table"]
            columns = pattern["columns"]
            
            # Check if index already exists
            existing_indexes = inspector.get_indexes(table_name)
            index_exists = any(
                set(columns).issubset(set(idx["column_names"])) 
                for idx in existing_indexes
            )
            
            if not index_exists:
                suggestions.append({
                    "table": table_name,
                    "columns": columns,
                    "index_name": f"idx_{table_name}_{'_'.join(columns)}",
                    "reason": pattern["reason"],
                    "sql": f"CREATE INDEX idx_{table_name}_{'_'.join(columns)} ON {table_name} ({', '.join(columns)})"
                })
        
        return suggestions
    
    def check_index_usage(self) -> Dict[str, Any]:
        """Check index usage statistics (PostgreSQL specific)"""
        try:
            usage_query = """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                ORDER BY schemaname, tablename, indexname
            """
            result = self.db_session.execute(text(usage_query))
            unused_indexes = [dict(row._mapping) for row in result.fetchall()]
            
            # Get index sizes
            size_query = """
                SELECT 
                    indexname,
                    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
                FROM pg_indexes 
                WHERE schemaname = 'public'
            """
            size_result = self.db_session.execute(text(size_query))
            index_sizes = {row[0]: row[1] for row in size_result.fetchall()}
            
            return {
                "unused_indexes": unused_indexes,
                "index_sizes": index_sizes,
                "total_unused": len(unused_indexes)
            }
            
        except Exception as e:
            return {
                "error": "Index usage statistics not available (requires PostgreSQL)",
                "details": str(e)
            }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive database performance report"""
        logger.info("Generating database performance report...")
        
        report = {
            "timestamp": time.time(),
            "table_statistics": self.get_table_statistics(),
            "slow_query_analysis": self.analyze_slow_queries(),
            "missing_index_suggestions": self.suggest_missing_indexes(),
            "index_usage": self.check_index_usage()
        }
        
        # Calculate overall health score
        slow_queries = [q for q in report["slow_query_analysis"] 
                       if q.get("performance_rating") in ["slow", "very_slow"]]
        
        health_score = max(0, 100 - (len(slow_queries) * 10) - 
                          (len(report["missing_index_suggestions"]) * 5))
        
        report["performance_summary"] = {
            "health_score": health_score,
            "slow_queries_count": len(slow_queries),
            "missing_indexes_count": len(report["missing_index_suggestions"]),
            "total_tables": len(report["table_statistics"]),
            "recommendations": self._generate_recommendations(report)
        }
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []
        
        # Check for slow queries
        slow_queries = [q for q in report["slow_query_analysis"] 
                       if q.get("performance_rating") in ["slow", "very_slow"]]
        if slow_queries:
            recommendations.append(
                f"Found {len(slow_queries)} slow queries that need optimization"
            )
        
        # Check for missing indexes
        missing_indexes = report["missing_index_suggestions"]
        if missing_indexes:
            recommendations.append(
                f"Consider adding {len(missing_indexes)} suggested indexes for better performance"
            )
        
        # Check table sizes
        large_tables = [name for name, stats in report["table_statistics"].items() 
                       if stats.get("row_count", 0) > 100000]
        if large_tables:
            recommendations.append(
                f"Large tables ({', '.join(large_tables)}) may benefit from partitioning"
            )
        
        # Check for unused indexes
        unused_indexes = report["index_usage"].get("unused_indexes", [])
        if unused_indexes:
            recommendations.append(
                f"Consider dropping {len(unused_indexes)} unused indexes to save space"
            )
        
        if not recommendations:
            recommendations.append("Database performance looks good! No immediate optimizations needed.")
        
        return recommendations
    
    def optimize_custom_data_queries(self) -> List[str]:
        """Optimize queries on JSONB custom_data fields"""
        optimizations = []
        
        # Check if we're using PostgreSQL
        try:
            self.db_session.execute(text("SELECT version()"))
            
            # Add GIN indexes for custom_data fields
            tables_with_custom_data = ['products', 'product_variants', 'inventory_items', 'alerts']
            
            for table in tables_with_custom_data:
                try:
                    # Check if GIN index exists
                    check_query = """
                        SELECT 1 FROM pg_indexes 
                        WHERE tablename = :table 
                        AND indexdef LIKE '%gin%custom_data%'
                    """
                    result = self.db_session.execute(text(check_query), {"table": table})
                    
                    if not result.fetchone():
                        # Create GIN index
                        create_query = f"""
                            CREATE INDEX CONCURRENTLY idx_{table}_custom_data_gin 
                            ON {table} USING GIN (custom_data)
                        """
                        self.db_session.execute(text(create_query))
                        optimizations.append(f"Created GIN index for {table}.custom_data")
                
                except Exception as e:
                    optimizations.append(f"Failed to optimize {table}: {str(e)}")
            
        except Exception:
            optimizations.append("Custom data optimization requires PostgreSQL")
        
        return optimizations


class QueryProfiler:
    """Profile individual queries and provide optimization suggestions"""
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session or next(get_db_session())
    
    def profile_query(self, query: str, params: Dict = None, iterations: int = 1) -> Dict[str, Any]:
        """Profile a query over multiple iterations"""
        execution_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                result = self.db_session.execute(text(query), params or {})
                result.fetchall()  # Ensure all rows are fetched
                execution_times.append(time.time() - start_time)
            except Exception as e:
                return {"error": str(e)}
        
        avg_time = sum(execution_times) / len(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        return {
            "query": query,
            "iterations": iterations,
            "average_time_ms": avg_time * 1000,
            "min_time_ms": min_time * 1000,
            "max_time_ms": max_time * 1000,
            "variance_ms": (max_time - min_time) * 1000,
            "suggestions": self._analyze_query_for_optimization(query)
        }
    
    def _analyze_query_for_optimization(self, query: str) -> List[str]:
        """Analyze query and suggest optimizations"""
        suggestions = []
        query_lower = query.lower()
        
        # Check for common performance issues
        if "select *" in query_lower:
            suggestions.append("Avoid SELECT *, specify only needed columns")
        
        if "order by" in query_lower and "limit" not in query_lower:
            suggestions.append("Consider adding LIMIT to ORDER BY queries")
        
        if "like" in query_lower and query.count("%") >= 2:
            suggestions.append("Full text search might be more efficient than LIKE with wildcards")
        
        if "in (" in query_lower and query.count(",") > 100:
            suggestions.append("Large IN clauses can be slow, consider using EXISTS or JOIN")
        
        if query_lower.count("join") > 5:
            suggestions.append("Complex multi-table joins may benefit from query restructuring")
        
        if "group by" in query_lower and "having" not in query_lower:
            suggestions.append("Consider adding appropriate indexes for GROUP BY operations")
        
        return suggestions


# Convenience functions for common operations
def run_performance_analysis() -> Dict[str, Any]:
    """Run complete database performance analysis"""
    optimizer = DatabaseOptimizer()
    return optimizer.generate_performance_report()


def check_query_performance(query: str, params: Dict = None) -> Dict[str, Any]:
    """Quick query performance check"""
    optimizer = DatabaseOptimizer()
    return optimizer.analyze_query_performance(query, params)


def suggest_optimizations() -> List[Dict[str, Any]]:
    """Get optimization suggestions"""
    optimizer = DatabaseOptimizer()
    return optimizer.suggest_missing_indexes()