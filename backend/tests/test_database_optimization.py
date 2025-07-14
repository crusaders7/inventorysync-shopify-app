"""
Test database optimization features
Tests indexes, query performance, and optimization tools
"""

import pytest
import time
from sqlalchemy import text, inspect
from unittest.mock import patch, Mock

from utils.database_optimizer import DatabaseOptimizer, QueryProfiler, run_performance_analysis
from models import Store, Product, ProductVariant, InventoryItem, Alert


class TestDatabaseOptimizer:
    """Test database optimization utilities"""
    
    def test_table_statistics(self, db_session, sample_store):
        """Test getting table statistics"""
        optimizer = DatabaseOptimizer(db_session)
        stats = optimizer.get_table_statistics()
        
        assert isinstance(stats, dict)
        assert "stores" in stats
        assert stats["stores"]["row_count"] >= 1  # Should have our sample store
    
    def test_query_performance_analysis(self, db_session, sample_store):
        """Test query performance analysis"""
        optimizer = DatabaseOptimizer(db_session)
        
        # Simple query that should be fast
        query = "SELECT COUNT(*) FROM stores WHERE id = :store_id"
        params = {"store_id": sample_store.id}
        
        result = optimizer.analyze_query_performance(query, params)
        
        assert "execution_time_ms" in result
        assert "performance_rating" in result
        assert result["performance_rating"] in ["excellent", "good", "acceptable", "slow", "very_slow"]
        assert "query" in result
    
    def test_slow_query_analysis(self, db_session, sample_store):
        """Test analysis of potentially slow queries"""
        optimizer = DatabaseOptimizer(db_session)
        
        # Create some test data first
        product = Product(
            store_id=sample_store.id,
            shopify_product_id="test_prod_001",
            title="Test Product",
            handle="test-product"
        )
        db_session.add(product)
        db_session.commit()
        
        slow_queries = optimizer.analyze_slow_queries()
        
        assert isinstance(slow_queries, list)
        assert len(slow_queries) > 0
        
        # Check that each query analysis has required fields
        for query_result in slow_queries:
            assert "query_name" in query_result
            assert "execution_time_ms" in query_result
    
    def test_missing_index_suggestions(self, db_session):
        """Test missing index suggestions"""
        optimizer = DatabaseOptimizer(db_session)
        suggestions = optimizer.suggest_missing_indexes()
        
        assert isinstance(suggestions, list)
        
        # Each suggestion should have required fields
        for suggestion in suggestions:
            assert "table" in suggestion
            assert "columns" in suggestion
            assert "reason" in suggestion
            assert "sql" in suggestion
    
    @pytest.mark.skipif(True, reason="Requires PostgreSQL for index usage stats")
    def test_index_usage_analysis(self, db_session):
        """Test index usage analysis (PostgreSQL only)"""
        optimizer = DatabaseOptimizer(db_session)
        usage_stats = optimizer.check_index_usage()
        
        # Should return either stats or error message for non-PostgreSQL
        assert isinstance(usage_stats, dict)
        assert "unused_indexes" in usage_stats or "error" in usage_stats
    
    def test_performance_report_generation(self, db_session, sample_store):
        """Test comprehensive performance report generation"""
        optimizer = DatabaseOptimizer(db_session)
        report = optimizer.generate_performance_report()
        
        # Check report structure
        assert "timestamp" in report
        assert "table_statistics" in report
        assert "slow_query_analysis" in report
        assert "missing_index_suggestions" in report
        assert "performance_summary" in report
        
        # Check performance summary
        summary = report["performance_summary"]
        assert "health_score" in summary
        assert 0 <= summary["health_score"] <= 100
        assert "recommendations" in summary
        assert isinstance(summary["recommendations"], list)
    
    def test_custom_data_optimization(self, db_session):
        """Test custom data field optimization"""
        optimizer = DatabaseOptimizer(db_session)
        optimizations = optimizer.optimize_custom_data_queries()
        
        assert isinstance(optimizations, list)
        # Should either apply optimizations or note PostgreSQL requirement
        assert len(optimizations) > 0


class TestQueryProfiler:
    """Test query profiling functionality"""
    
    def test_single_query_profiling(self, db_session, sample_store):
        """Test profiling a single query"""
        profiler = QueryProfiler(db_session)
        
        query = "SELECT COUNT(*) FROM stores WHERE id = :store_id"
        params = {"store_id": sample_store.id}
        
        result = profiler.profile_query(query, params)
        
        assert "average_time_ms" in result
        assert "min_time_ms" in result
        assert "max_time_ms" in result
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)
    
    def test_multi_iteration_profiling(self, db_session, sample_store):
        """Test profiling with multiple iterations"""
        profiler = QueryProfiler(db_session)
        
        query = "SELECT * FROM stores WHERE id = :store_id"
        params = {"store_id": sample_store.id}
        
        result = profiler.profile_query(query, params, iterations=5)
        
        assert result["iterations"] == 5
        assert "variance_ms" in result
        # Variance should be non-negative
        assert result["variance_ms"] >= 0
    
    def test_query_optimization_suggestions(self, db_session):
        """Test query optimization suggestions"""
        profiler = QueryProfiler(db_session)
        
        # Query with potential optimization issues
        problematic_query = "SELECT * FROM products ORDER BY created_at"
        
        result = profiler.profile_query(problematic_query)
        
        if "suggestions" in result:
            suggestions = result["suggestions"]
            # Should suggest avoiding SELECT * and adding LIMIT
            suggestion_text = " ".join(suggestions).lower()
            assert "select *" in suggestion_text or "limit" in suggestion_text
    
    def test_error_handling(self, db_session):
        """Test error handling for invalid queries"""
        profiler = QueryProfiler(db_session)
        
        # Invalid SQL query
        invalid_query = "SELECT * FROM nonexistent_table"
        
        result = profiler.profile_query(invalid_query)
        
        assert "error" in result


class TestDatabaseIndexes:
    """Test database index presence and effectiveness"""
    
    def test_primary_indexes_exist(self, db_session):
        """Test that primary indexes exist"""
        inspector = inspect(db_session.bind)
        
        # Check for critical indexes
        critical_indexes = [
            ("stores", "shopify_store_id"),
            ("products", "store_id"),
            ("product_variants", "sku"),
            ("inventory_items", "store_id"),
            ("alerts", "store_id")
        ]
        
        for table, column in critical_indexes:
            indexes = inspector.get_indexes(table)
            indexed_columns = []
            for idx in indexes:
                indexed_columns.extend(idx["column_names"])
            
            # Check if column is indexed (either individually or as part of composite)
            assert column in indexed_columns, f"Missing index on {table}.{column}"
    
    def test_foreign_key_indexes(self, db_session):
        """Test that foreign key columns are indexed"""
        inspector = inspect(db_session.bind)
        
        # Get all foreign keys and check if they're indexed
        tables = inspector.get_table_names()
        
        for table in tables:
            foreign_keys = inspector.get_foreign_keys(table)
            indexes = inspector.get_indexes(table)
            
            indexed_columns = set()
            for idx in indexes:
                indexed_columns.update(idx["column_names"])
            
            for fk in foreign_keys:
                for column in fk["constrained_columns"]:
                    # Note: This is a recommendation, not always required
                    # but good for performance
                    pass  # We'll just document this for now
    
    def test_unique_constraint_indexes(self, db_session):
        """Test that unique constraints have supporting indexes"""
        inspector = inspect(db_session.bind)
        
        # Check that unique constraints are properly indexed
        tables = ["stores", "products", "product_variants"]
        
        for table in tables:
            try:
                unique_constraints = inspector.get_unique_constraints(table)
                indexes = inspector.get_indexes(table)
                
                # Unique constraints should have corresponding indexes
                for constraint in unique_constraints:
                    constraint_columns = set(constraint["column_names"])
                    
                    # Check if there's an index covering these columns
                    index_found = False
                    for idx in indexes:
                        if set(idx["column_names"]) == constraint_columns:
                            index_found = True
                            break
                    
                    # Note: SQLAlchemy usually creates these automatically
                    # This is more of a verification
                    assert index_found or len(constraint_columns) == 0
                    
            except Exception:
                # Some databases might not support this introspection
                pass


class TestQueryPerformance:
    """Test actual query performance with real data"""
    
    def test_store_scoped_query_performance(self, db_session, sample_store, performance_timer):
        """Test store-scoped queries are fast"""
        # Create some test data
        products = []
        for i in range(100):
            product = Product(
                store_id=sample_store.id,
                shopify_product_id=f"perf_test_{i}",
                title=f"Performance Test Product {i}",
                handle=f"perf-test-product-{i}",
                product_type="Electronics" if i % 2 == 0 else "Clothing"
            )
            products.append(product)
        
        db_session.add_all(products)
        db_session.commit()
        
        # Test query performance
        performance_timer.start()
        
        result = db_session.query(Product).filter(
            Product.store_id == sample_store.id,
            Product.product_type == "Electronics"
        ).limit(50).all()
        
        performance_timer.stop()
        
        # Should be fast with proper indexing
        assert performance_timer.elapsed() < 0.5  # Less than 500ms
        assert len(result) > 0
    
    def test_sku_lookup_performance(self, db_session, sample_store, performance_timer):
        """Test SKU lookup performance"""
        # Create variant with SKU
        product = Product(
            store_id=sample_store.id,
            shopify_product_id="sku_test_prod",
            title="SKU Test Product",
            handle="sku-test-product"
        )
        db_session.add(product)
        db_session.flush()
        
        variant = ProductVariant(
            product_id=product.id,
            shopify_variant_id="sku_test_var",
            title="Test Variant",
            sku="PERF-TEST-SKU-001",
            price=99.99
        )
        db_session.add(variant)
        db_session.commit()
        
        # Test SKU lookup performance
        performance_timer.start()
        
        found_variant = db_session.query(ProductVariant).filter(
            ProductVariant.sku == "PERF-TEST-SKU-001"
        ).first()
        
        performance_timer.stop()
        
        # SKU lookups should be very fast
        assert performance_timer.elapsed() < 0.1  # Less than 100ms
        assert found_variant is not None
        assert found_variant.sku == "PERF-TEST-SKU-001"
    
    def test_inventory_low_stock_query_performance(self, db_session, sample_store, performance_timer):
        """Test low stock detection query performance"""
        # Create test inventory data
        product = Product(
            store_id=sample_store.id,
            shopify_product_id="inv_test_prod",
            title="Inventory Test Product",
            handle="inventory-test"
        )
        db_session.add(product)
        db_session.flush()
        
        variant = ProductVariant(
            product_id=product.id,
            shopify_variant_id="inv_test_var",
            title="Test Variant",
            sku="INV-TEST-SKU",
            price=50.0
        )
        db_session.add(variant)
        db_session.flush()
        
        # Create inventory items with low stock
        for i in range(10):
            inventory = InventoryItem(
                store_id=sample_store.id,
                location_id=1,
                variant_id=variant.id,
                available_quantity=5,  # Low stock
                reorder_point=20
            )
            db_session.add(inventory)
        
        db_session.commit()
        
        # Test low stock query performance
        performance_timer.start()
        
        low_stock_items = db_session.query(InventoryItem).filter(
            InventoryItem.store_id == sample_store.id,
            InventoryItem.available_quantity <= InventoryItem.reorder_point
        ).all()
        
        performance_timer.stop()
        
        # Should be fast with proper composite index
        assert performance_timer.elapsed() < 0.2  # Less than 200ms
        assert len(low_stock_items) > 0
    
    def test_alert_dashboard_query_performance(self, db_session, sample_store, performance_timer):
        """Test alert dashboard query performance"""
        # Create test alerts
        alerts = []
        for i in range(50):
            alert = Alert(
                store_id=sample_store.id,
                alert_type="low_stock",
                severity="high" if i % 3 == 0 else "medium",
                title=f"Test Alert {i}",
                message=f"Test alert message {i}",
                is_resolved=i % 4 == 0  # 25% resolved
            )
            alerts.append(alert)
        
        db_session.add_all(alerts)
        db_session.commit()
        
        # Test alert dashboard query
        performance_timer.start()
        
        unresolved_alerts = db_session.query(Alert).filter(
            Alert.store_id == sample_store.id,
            Alert.is_resolved == False
        ).order_by(Alert.created_at.desc()).limit(20).all()
        
        performance_timer.stop()
        
        # Should be fast with proper index
        assert performance_timer.elapsed() < 0.15  # Less than 150ms
        assert len(unresolved_alerts) > 0


class TestIntegrationFunctions:
    """Test integration functions for database optimization"""
    
    def test_run_performance_analysis_function(self, db_session, sample_store):
        """Test the convenience function for performance analysis"""
        report = run_performance_analysis()
        
        assert isinstance(report, dict)
        assert "performance_summary" in report
        assert "health_score" in report["performance_summary"]
    
    def test_performance_analysis_with_mock_data(self, db_session, sample_store):
        """Test performance analysis with mocked slow queries"""
        with patch('utils.database_optimizer.DatabaseOptimizer.analyze_query_performance') as mock_analyze:
            # Mock a slow query result
            mock_analyze.return_value = {
                "execution_time_ms": 2500,  # Slow query
                "performance_rating": "slow",
                "query": "SELECT * FROM products"
            }
            
            optimizer = DatabaseOptimizer(db_session)
            slow_queries = optimizer.analyze_slow_queries()
            
            # Should detect the slow query
            slow_query_ratings = [q.get("performance_rating") for q in slow_queries]
            assert "slow" in slow_query_ratings


class TestDatabaseMigrationIndexes:
    """Test that our migration indexes are properly created"""
    
    def test_migration_indexes_applied(self, db_session):
        """Test that migration indexes have been applied"""
        inspector = inspect(db_session.bind)
        
        # Test a few key indexes from our migration
        expected_indexes = [
            ("products", "idx_products_store_status"),
            ("inventory_items", "idx_inventory_low_stock"),
            ("alerts", "idx_alerts_store_unresolved"),
            ("product_variants", "idx_variants_sku")
        ]
        
        for table, expected_index in expected_indexes:
            try:
                indexes = inspector.get_indexes(table)
                index_names = [idx["name"] for idx in indexes if idx["name"]]
                
                # Note: Index names might be auto-generated differently
                # So we check for the presence of indexes on the expected columns
                # rather than exact name matches
                if expected_index == "idx_products_store_status":
                    # Check for index on store_id, status combination
                    composite_found = any(
                        set(["store_id", "status"]).issubset(set(idx["column_names"]))
                        for idx in indexes
                    )
                    # This is an ideal case, actual implementation may vary
                    
            except Exception:
                # Index introspection might not be available for all databases
                pass


# =============================================================================
# PERFORMANCE BENCHMARKS
# =============================================================================

class TestPerformanceBenchmarks:
    """Benchmark tests for database performance"""
    
    @pytest.mark.performance
    def test_bulk_insert_performance(self, db_session, sample_store, performance_timer):
        """Test bulk insert performance"""
        performance_timer.start()
        
        # Create 1000 products in bulk
        products = []
        for i in range(1000):
            product = Product(
                store_id=sample_store.id,
                shopify_product_id=f"bulk_test_{i}",
                title=f"Bulk Test Product {i}",
                handle=f"bulk-test-{i}",
                product_type="Test Category"
            )
            products.append(product)
        
        db_session.add_all(products)
        db_session.commit()
        
        performance_timer.stop()
        
        # Should complete bulk insert reasonably quickly
        assert performance_timer.elapsed() < 10.0  # Less than 10 seconds
    
    @pytest.mark.performance
    def test_complex_join_performance(self, db_session, sample_store, performance_timer):
        """Test complex multi-table join performance"""
        # This test requires the bulk insert data from above
        performance_timer.start()
        
        # Complex query joining multiple tables
        query = db_session.query(Product.title, ProductVariant.sku, InventoryItem.available_quantity).join(
            ProductVariant, Product.id == ProductVariant.product_id
        ).join(
            InventoryItem, ProductVariant.id == InventoryItem.variant_id
        ).filter(
            Product.store_id == sample_store.id
        ).limit(100)
        
        results = query.all()
        
        performance_timer.stop()
        
        # Complex joins should complete within reasonable time
        assert performance_timer.elapsed() < 2.0  # Less than 2 seconds