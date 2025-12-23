"""
Prometheus Metrics Module for the Items API
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time

# ℹ️ INFO : Informations statiques sur l'application
app_info = Info("fastapi_app_info", "Information about the FastAPI application")

# 📊 COUNTER : Compteurs pour les opérations CRUD
items_created_total = Counter(
    "items_created_total", "Number of items created since startup"
)

items_read_total = Counter("items_read_total", "Number of items read since startup")

target_item_read_total = Counter(
    "target_item_read_total", "Number of target items read since startup"
)

items_updated_total = Counter(
    "items_updated_total", "Number of items updated since startup"
)

items_deleted_total = Counter(
    "items_deleted_total", "Number of items deleted since startup"
)

# 📈 GAUGE : Instantaneous value
db_connection_pool_size = Gauge(
    "db_connection_pool_size", "Current size of the DB connection pool"
)

# ⏱️ HISTOGRAM : Distribution de valeurs avec buckets
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Duration of database queries (seconds)",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


# 🎯 Context Manager to automatically measure durations
class DatabaseQueryTimer:
    """Context manager to measure the execution time of a DB query."""

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        db_query_duration_seconds.observe(duration)
