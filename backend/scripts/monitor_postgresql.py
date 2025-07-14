#!/usr/bin/env python3
"""
PostgreSQL Performance Monitoring Script
Monitors database health, performance metrics, and alerts on issues
"""

import psycopg2
import os
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse
import time
from decimal import Decimal

load_dotenv()

# Configuration
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://inventorysync:devpassword123@localhost:5432/inventorysync_dev")
MONITORING_DIR = Path("/home/brend/inventorysync-shopify-app/monitoring")
ALERT_THRESHOLDS = {
    "connection_usage_percent": 80,  # Alert if > 80% connections used
    "cache_hit_ratio": 90,  # Alert if < 90% cache hit ratio
    "database_size_gb": 10,  # Alert if database > 10GB
    "long_running_queries_seconds": 300,  # Alert if query runs > 5 minutes
    "table_bloat_percent": 30,  # Alert if table bloat > 30%
}

# Parse PostgreSQL URL
url = urllib.parse.urlparse(POSTGRES_URL)


def ensure_monitoring_dir():
    """Create monitoring directory"""
    MONITORING_DIR.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:],
        user=url.username,
        password=url.password
    )


def check_connection_stats(conn):
    """Check database connection statistics"""
    with conn.cursor() as cur:
        # Get max connections
        cur.execute("SHOW max_connections;")
        max_connections = int(cur.fetchone()[0])
        
        # Get current connections
        cur.execute("""
            SELECT count(*) 
            FROM pg_stat_activity 
            WHERE state != 'idle'
        """)
        active_connections = cur.fetchone()[0]
        
        # Get total connections
        cur.execute("SELECT count(*) FROM pg_stat_activity")
        total_connections = cur.fetchone()[0]
        
        usage_percent = (total_connections / max_connections) * 100
        
        return {
            "max_connections": max_connections,
            "total_connections": total_connections,
            "active_connections": active_connections,
            "usage_percent": round(usage_percent, 2),
            "alert": usage_percent > ALERT_THRESHOLDS["connection_usage_percent"]
        }


def check_cache_performance(conn):
    """Check cache hit ratios"""
    with conn.cursor() as cur:
        # Database-wide cache hit ratio
        cur.execute("""
            SELECT 
                sum(heap_blks_read) as heap_read,
                sum(heap_blks_hit) as heap_hit,
                sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
            FROM pg_statio_user_tables
            WHERE heap_blks_hit + heap_blks_read > 0
        """)
        result = cur.fetchone()
        
        cache_hit_ratio = float(result[2]) if result[2] else 0
        
        return {
            "heap_blocks_read": result[0],
            "heap_blocks_hit": result[1],
            "cache_hit_ratio": round(cache_hit_ratio, 2),
            "alert": cache_hit_ratio < ALERT_THRESHOLDS["cache_hit_ratio"]
        }


def check_database_size(conn):
    """Check database and table sizes"""
    with conn.cursor() as cur:
        # Get database size
        cur.execute("""
            SELECT 
                pg_database_size(current_database()) as db_size,
                pg_size_pretty(pg_database_size(current_database())) as db_size_pretty
        """)
        db_result = cur.fetchone()
        db_size_bytes = db_result[0]
        db_size_gb = db_size_bytes / (1024**3)
        
        # Get largest tables
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10
        """)
        
        largest_tables = []
        for row in cur.fetchall():
            largest_tables.append({
                "schema": row[0],
                "table": row[1],
                "size_pretty": row[2],
                "size_bytes": row[3]
            })
        
        return {
            "database_size_bytes": db_size_bytes,
            "database_size_pretty": db_result[1],
            "database_size_gb": round(db_size_gb, 2),
            "largest_tables": largest_tables,
            "alert": db_size_gb > ALERT_THRESHOLDS["database_size_gb"]
        }


def check_long_running_queries(conn):
    """Check for long-running queries"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                pid,
                now() - pg_stat_activity.query_start AS duration,
                query,
                state
            FROM pg_stat_activity
            WHERE (now() - pg_stat_activity.query_start) > interval '1 minute'
                AND state != 'idle'
                AND query NOT LIKE '%pg_stat_activity%'
            ORDER BY duration DESC
        """)
        
        long_queries = []
        has_alert = False
        
        for row in cur.fetchall():
            duration_seconds = row[1].total_seconds() if row[1] else 0
            if duration_seconds > ALERT_THRESHOLDS["long_running_queries_seconds"]:
                has_alert = True
                
            long_queries.append({
                "pid": row[0],
                "duration_seconds": round(duration_seconds, 2),
                "duration_pretty": str(row[1]).split('.')[0] if row[1] else "0:00:00",
                "query": row[2][:100] + "..." if len(row[2]) > 100 else row[2],
                "state": row[3]
            })
        
        return {
            "count": len(long_queries),
            "queries": long_queries[:5],  # Top 5 longest
            "alert": has_alert
        }


def check_table_bloat(conn):
    """Check for table bloat"""
    with conn.cursor() as cur:
        # Simplified bloat check
        cur.execute("""
            SELECT
                schemaname,
                relname as tablename,
                pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) as table_size,
                n_live_tup,
                n_dead_tup,
                CASE WHEN n_live_tup > 0 
                    THEN round(100.0 * n_dead_tup / n_live_tup, 2)
                    ELSE 0 
                END as bloat_percent
            FROM pg_stat_user_tables
            WHERE n_dead_tup > 1000
            ORDER BY n_dead_tup DESC
            LIMIT 10
        """)
        
        bloated_tables = []
        has_alert = False
        
        for row in cur.fetchall():
            bloat_percent = float(row[5])
            if bloat_percent > ALERT_THRESHOLDS["table_bloat_percent"]:
                has_alert = True
                
            bloated_tables.append({
                "schema": row[0],
                "table": row[1],
                "table_size": row[2],
                "live_tuples": row[3],
                "dead_tuples": row[4],
                "bloat_percent": bloat_percent
            })
        
        return {
            "bloated_tables": bloated_tables,
            "alert": has_alert
        }


def check_index_usage(conn):
    """Check index usage statistics"""
    with conn.cursor() as cur:
        # Find unused indexes
        cur.execute("""
            SELECT
                schemaname,
                relname as tablename,
                indexrelname as indexname,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                idx_scan
            FROM pg_stat_user_indexes
            WHERE idx_scan < 50
            ORDER BY pg_relation_size(indexrelid) DESC
            LIMIT 10
        """)
        
        unused_indexes = []
        for row in cur.fetchall():
            unused_indexes.append({
                "schema": row[0],
                "table": row[1],
                "index": row[2],
                "size": row[3],
                "scans": row[4]
            })
        
        return {
            "unused_indexes": unused_indexes,
            "recommendation": "Consider dropping unused indexes to save space and improve write performance"
        }


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def generate_performance_report(metrics):
    """Generate a performance report"""
    timestamp = datetime.datetime.now()
    
    report = {
        "timestamp": timestamp.isoformat(),
        "metrics": metrics,
        "alerts": [],
        "recommendations": []
    }
    
    # Check for alerts
    for metric_name, metric_data in metrics.items():
        if isinstance(metric_data, dict) and metric_data.get("alert"):
            report["alerts"].append({
                "metric": metric_name,
                "message": f"Alert: {metric_name} threshold exceeded",
                "data": metric_data
            })
    
    # Add recommendations
    if metrics["cache_performance"]["cache_hit_ratio"] < 95:
        report["recommendations"].append(
            "Consider increasing shared_buffers to improve cache performance"
        )
    
    if metrics["connection_stats"]["usage_percent"] > 70:
        report["recommendations"].append(
            "Connection pool usage is high. Consider increasing max_connections or optimizing connection usage"
        )
    
    if len(metrics["table_bloat"]["bloated_tables"]) > 0:
        report["recommendations"].append(
            "Run VACUUM on bloated tables to reclaim space"
        )
    
    # Save report
    report_path = MONITORING_DIR / f"performance_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=json_serializer)
    
    # Also save latest report
    latest_path = MONITORING_DIR / "latest_performance_report.json"
    with open(latest_path, 'w') as f:
        json.dump(report, f, indent=2, default=json_serializer)
    
    return report


def print_summary(report):
    """Print a summary of the performance report"""
    print("=== PostgreSQL Performance Report ===")
    print(f"Timestamp: {report['timestamp']}")
    print()
    
    # Connection stats
    conn_stats = report["metrics"]["connection_stats"]
    print(f"Connections: {conn_stats['active_connections']}/{conn_stats['total_connections']} active " +
          f"({conn_stats['usage_percent']}% of {conn_stats['max_connections']} max)")
    
    # Cache performance
    cache = report["metrics"]["cache_performance"]
    print(f"Cache Hit Ratio: {cache['cache_hit_ratio']}%")
    
    # Database size
    db_size = report["metrics"]["database_size"]
    print(f"Database Size: {db_size['database_size_pretty']}")
    
    # Long queries
    long_queries = report["metrics"]["long_running_queries"]
    print(f"Long Running Queries: {long_queries['count']}")
    
    # Alerts
    if report["alerts"]:
        print("\n⚠️  ALERTS:")
        for alert in report["alerts"]:
            print(f"  - {alert['message']}")
    else:
        print("\n✅ No alerts")
    
    # Recommendations
    if report["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")
    
    print(f"\nFull report saved to: {MONITORING_DIR}/latest_performance_report.json")


def monitor_continuously(interval_seconds=300):
    """Monitor continuously at specified interval"""
    print(f"Starting continuous monitoring (interval: {interval_seconds}s)")
    print("Press Ctrl+C to stop")
    
    while True:
        try:
            conn = get_db_connection()
            metrics = {
                "connection_stats": check_connection_stats(conn),
                "cache_performance": check_cache_performance(conn),
                "database_size": check_database_size(conn),
                "long_running_queries": check_long_running_queries(conn),
                "table_bloat": check_table_bloat(conn),
                "index_usage": check_index_usage(conn)
            }
            conn.close()
            
            report = generate_performance_report(metrics)
            print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
            print_summary(report)
            
            time.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            time.sleep(interval_seconds)


def main():
    """Main monitoring function"""
    ensure_monitoring_dir()
    
    # Get metrics
    conn = get_db_connection()
    
    print("Collecting performance metrics...")
    metrics = {
        "connection_stats": check_connection_stats(conn),
        "cache_performance": check_cache_performance(conn),
        "database_size": check_database_size(conn),
        "long_running_queries": check_long_running_queries(conn),
        "table_bloat": check_table_bloat(conn),
        "index_usage": check_index_usage(conn)
    }
    
    conn.close()
    
    # Generate report
    report = generate_performance_report(metrics)
    
    # Print summary
    print_summary(report)
    
    # Ask if user wants continuous monitoring
    response = input("\nStart continuous monitoring? (y/n): ")
    if response.lower() == 'y':
        monitor_continuously()


if __name__ == "__main__":
    main()
