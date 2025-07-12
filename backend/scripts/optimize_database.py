#!/usr/bin/env python3
"""
Database Optimization CLI Tool
Provides command-line interface for database performance analysis and optimization
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.database_optimizer import DatabaseOptimizer, QueryProfiler, run_performance_analysis
from utils.logging import logger


def analyze_performance(args):
    """Run comprehensive performance analysis"""
    logger.info("Starting database performance analysis...")
    
    try:
        report = run_performance_analysis()
        
        if args.output:
            # Save report to file
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Performance report saved to {args.output}")
        else:
            # Print summary to console
            summary = report["performance_summary"]
            print(f"\n🔍 Database Performance Analysis")
            print(f"{'='*50}")
            print(f"Health Score: {summary['health_score']}/100")
            print(f"Total Tables: {summary['total_tables']}")
            print(f"Slow Queries: {summary['slow_queries_count']}")
            print(f"Missing Indexes: {summary['missing_indexes_count']}")
            
            print(f"\n📊 Recommendations:")
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"  {i}. {rec}")
            
            # Show table statistics
            print(f"\n📈 Table Statistics:")
            for table, stats in report["table_statistics"].items():
                if "error" not in stats:
                    print(f"  {table}: {stats['row_count']:,} rows, {stats['index_count']} indexes")
        
        return True
        
    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        return False


def suggest_indexes(args):
    """Suggest missing database indexes"""
    logger.info("Analyzing database for missing indexes...")
    
    try:
        optimizer = DatabaseOptimizer()
        suggestions = optimizer.suggest_missing_indexes()
        
        if not suggestions:
            print("✅ No missing indexes detected. Database indexing looks good!")
            return True
        
        print(f"\n🔧 Missing Index Suggestions ({len(suggestions)} found)")
        print(f"{'='*60}")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['table']}.{', '.join(suggestion['columns'])}")
            print(f"   Reason: {suggestion['reason']}")
            print(f"   SQL: {suggestion['sql']}")
        
        if args.apply:
            print(f"\n🚀 Applying suggested indexes...")
            applied = 0
            for suggestion in suggestions:
                try:
                    optimizer.db_session.execute(text(suggestion['sql']))
                    optimizer.db_session.commit()
                    print(f"✅ Created: {suggestion['index_name']}")
                    applied += 1
                except Exception as e:
                    print(f"❌ Failed to create {suggestion['index_name']}: {e}")
            
            print(f"\n📊 Applied {applied}/{len(suggestions)} indexes successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Index analysis failed: {e}")
        return False


def profile_query(args):
    """Profile a specific query"""
    if not args.query:
        print("❌ Query is required for profiling")
        return False
    
    logger.info(f"Profiling query: {args.query[:50]}...")
    
    try:
        profiler = QueryProfiler()
        
        # Parse parameters if provided
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError:
                print("❌ Invalid JSON format for parameters")
                return False
        
        result = profiler.profile_query(
            args.query, 
            params, 
            iterations=args.iterations
        )
        
        if "error" in result:
            print(f"❌ Query failed: {result['error']}")
            return False
        
        print(f"\n⚡ Query Performance Profile")
        print(f"{'='*40}")
        print(f"Iterations: {result['iterations']}")
        print(f"Average Time: {result['average_time_ms']:.2f}ms")
        print(f"Min Time: {result['min_time_ms']:.2f}ms")
        print(f"Max Time: {result['max_time_ms']:.2f}ms")
        print(f"Variance: {result['variance_ms']:.2f}ms")
        
        if result['suggestions']:
            print(f"\n💡 Optimization Suggestions:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        else:
            print(f"\n✅ No optimization suggestions - query looks good!")
        
        return True
        
    except Exception as e:
        logger.error(f"Query profiling failed: {e}")
        return False


def check_index_usage(args):
    """Check database index usage statistics"""
    logger.info("Checking index usage statistics...")
    
    try:
        optimizer = DatabaseOptimizer()
        usage_stats = optimizer.check_index_usage()
        
        if "error" in usage_stats:
            print(f"⚠️  {usage_stats['error']}")
            return False
        
        unused_indexes = usage_stats.get("unused_indexes", [])
        index_sizes = usage_stats.get("index_sizes", {})
        
        print(f"\n📊 Index Usage Analysis")
        print(f"{'='*40}")
        print(f"Total Unused Indexes: {len(unused_indexes)}")
        
        if unused_indexes:
            print(f"\n🗑️  Unused Indexes (consider dropping):")
            for idx in unused_indexes:
                size = index_sizes.get(idx['indexname'], 'Unknown')
                print(f"  • {idx['indexname']} on {idx['tablename']} (Size: {size})")
        else:
            print(f"✅ All indexes are being used!")
        
        if args.show_sizes:
            print(f"\n💾 Index Sizes:")
            for idx_name, size in index_sizes.items():
                print(f"  {idx_name}: {size}")
        
        return True
        
    except Exception as e:
        logger.error(f"Index usage check failed: {e}")
        return False


def optimize_custom_fields(args):
    """Optimize custom field (JSONB) queries"""
    logger.info("Optimizing custom field queries...")
    
    try:
        optimizer = DatabaseOptimizer()
        optimizations = optimizer.optimize_custom_data_queries()
        
        print(f"\n🔧 Custom Field Optimization Results")
        print(f"{'='*45}")
        
        for optimization in optimizations:
            if "Failed" in optimization:
                print(f"❌ {optimization}")
            elif "requires PostgreSQL" in optimization:
                print(f"⚠️  {optimization}")
            else:
                print(f"✅ {optimization}")
        
        return True
        
    except Exception as e:
        logger.error(f"Custom field optimization failed: {e}")
        return False


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="InventorySync Database Optimization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full performance analysis
  python optimize_database.py analyze --output report.json
  
  # Check for missing indexes and apply them
  python optimize_database.py suggest-indexes --apply
  
  # Profile a specific query
  python optimize_database.py profile-query --query "SELECT * FROM products WHERE store_id = :store_id" --params '{"store_id": 1}'
  
  # Check index usage
  python optimize_database.py check-indexes --show-sizes
  
  # Optimize custom field queries
  python optimize_database.py optimize-custom-fields
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run comprehensive performance analysis')
    analyze_parser.add_argument('--output', '-o', help='Save report to JSON file')
    
    # Suggest indexes command
    suggest_parser = subparsers.add_parser('suggest-indexes', help='Suggest missing database indexes')
    suggest_parser.add_argument('--apply', action='store_true', help='Apply suggested indexes')
    
    # Profile query command
    profile_parser = subparsers.add_parser('profile-query', help='Profile a specific query')
    profile_parser.add_argument('--query', '-q', required=True, help='SQL query to profile')
    profile_parser.add_argument('--params', '-p', help='Query parameters as JSON')
    profile_parser.add_argument('--iterations', '-i', type=int, default=1, help='Number of iterations to run')
    
    # Check indexes command
    check_parser = subparsers.add_parser('check-indexes', help='Check index usage statistics')
    check_parser.add_argument('--show-sizes', action='store_true', help='Show index sizes')
    
    # Optimize custom fields command
    optimize_parser = subparsers.add_parser('optimize-custom-fields', help='Optimize custom field queries')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate function
    success = False
    if args.command == 'analyze':
        success = analyze_performance(args)
    elif args.command == 'suggest-indexes':
        success = suggest_indexes(args)
    elif args.command == 'profile-query':
        success = profile_query(args)
    elif args.command == 'check-indexes':
        success = check_index_usage(args)
    elif args.command == 'optimize-custom-fields':
        success = optimize_custom_fields(args)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())