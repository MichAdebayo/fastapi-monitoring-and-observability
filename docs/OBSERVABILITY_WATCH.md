# OBSERVABILITY WATCH
022
## Mission 1: Understanding PromQL

### 1. What is the difference between `rate()` and `increase()`?

- `rate(v range-vector)`: Calculates the per-second average rate of increase of the time series over the given range. It automatically adjusts for breaks in monotonicity (such as target restarts). Example: `rate(http_requests_total{job="api-server"}[5m])` gives the average number of requests per second over 5 minutes.

- `increase(v range-vector)`: Calculates the total increase in the time series over the given range. It also adjusts for breaks in monotonicity. Example: `increase(http_requests_total{job="api-server"}[5m])` gives the total number of requests over 5 minutes.

The main difference is that `rate()` gives a per-second rate, while `increase()` gives the absolute total value. `increase()` is actually syntactic sugar for `rate()` multiplied by the number of seconds in the range.

### 2. How to filter metrics by label?

Metrics can be filtered using label matchers in curly braces `{}`:

- `=`: Selects labels that exactly match the provided string.
- `!=`: Selects labels that do not match the provided string.
- `=~`: Selects labels that regex-match the provided string.
- `!~`: Selects labels that do not regex-match the provided string.

Examples:
- `http_requests_total{job="prometheus", method="GET"}`
- `http_requests_total{environment=~"staging|testing|development"}`
- `http_requests_total{method!="POST"}`

### 3. What does the `histogram_quantile()` function do?

`histogram_quantile(φ scalar, b instant-vector)` calculates the φ-quantile (0 ≤ φ ≤ 1) from a classic or native histogram. The φ-quantile represents the value below which φ * 100% of observations fall.

For a classic histogram:
- `histogram_quantile(0.9, rate(http_request_duration_seconds_bucket[10m]))` calculates the 90th percentile of request durations over 10 minutes.

For a native histogram:
- `histogram_quantile(0.9, rate(http_request_duration_seconds[10m]))`

The function interpolates values if necessary and handles special cases (missing values, etc.).

## Quiz Answers

### 1. What is the difference between Monitoring and Observability?

Monitoring focuses on knowing WHEN something breaks (reactive alerts), while Observability focuses on understanding WHY something breaks (investigation). Monitoring is a subset of observability - you can have monitoring without full observability, but not vice versa.

### 2. Name the 3 pillars of observability

1. **Metrics**: Numeric aggregated data over time (CPU usage, request counts, latencies)
2. **Logs**: Textual events with timestamps (error messages, user actions)
3. **Traces**: End-to-end request tracking across services (distributed tracing)

### 3. What type of metric to count HTTP requests?

**Counter** - A monotonically increasing value that can only go up (or stay the same). Example: `http_requests_total` counting total requests since startup.

### 4. What type of metric for current RAM usage?

**Gauge** - A value that can go up and down, measuring an instantaneous value. Example: `memory_usage_bytes` showing current RAM consumption.

### 5. What does P95 mean?

P95 (95th percentile) means that 95% of observations are below this value. For example, if P95 latency is 200ms, 95% of requests took less than 200ms, and 5% took 200ms or more. It's commonly used to understand the worst-case performance while ignoring outliers.

## Overview of Prometheus and Grafana Roles

### Prometheus
Prometheus is an open-source time-series database and monitoring system that specializes in collecting and storing metrics. Its key roles include:

- **Metrics Collection**: Uses a pull-based model to scrape metrics from application endpoints (like `/metrics`) every 15 seconds by default.
- **Time-Series Storage**: Stores metric data with timestamps, allowing for historical analysis and trend monitoring.
- **Query Language (PromQL)**: Provides a powerful query language for aggregating, filtering, and analyzing metric data in real-time.
- **Alerting Rules**: Supports defining alerting rules based on metric thresholds and conditions.
- **Service Discovery**: Can automatically discover and monitor new services in dynamic environments.

Prometheus follows a pull architecture where it actively fetches metrics from targets, making it reliable for detecting when services are down.

### Grafana
Grafana is an open-source visualization and dashboarding platform that transforms metrics into interactive, real-time dashboards. Its key roles include:

- **Data Visualization**: Creates rich, customizable dashboards with various chart types (time series, gauges, heatmaps, etc.) to display metrics.
- **Multi-Source Integration**: Connects to multiple data sources including Prometheus, InfluxDB, and others.
- **Real-Time Monitoring**: Provides live updates and alerting capabilities directly in dashboards.
- **User Collaboration**: Allows sharing dashboards and setting up role-based access control.
- **Alerting Integration**: Can integrate with Prometheus alerts and send notifications via Slack, email, etc.

Together, Prometheus handles the data collection and storage, while Grafana provides the user interface for visualization and monitoring.

## Mission 2: Prometheus Best Practices

### 1. How to name a metric correctly?

- Use a relevant application prefix (namespace), such as the application name.
- Include the unit in the suffix (seconds, bytes, total for counters).
- Use base units (seconds, bytes, meters).
- For counters, add `_total` at the end.
- Order components for convenient lexicographic grouping.
- Examples:
  - `http_request_duration_seconds`
  - `node_memory_usage_bytes`
  - `http_requests_total`
  - `process_cpu_seconds_total`

### 2. When to use labels vs. create multiple metrics?

Use labels to differentiate the characteristics of what is being measured:
- `api_http_requests_total{operation="create|update|delete"}`

Do not use labels to store high-cardinality dimensions (such as user IDs), as this creates too many time series.

Create multiple metrics if the sum or average over all dimensions is not meaningful. For example, mixing the capacity of a queue with the current number of elements is not ideal.

### 3. What are the dashboard anti-patterns to avoid?

- **Dashboard sprawl**: Uncontrolled growth of dashboards, unnecessary duplication.
- Copying dashboards without significant changes (missing updates).
- Temporary dashboards not deleted.
- No version control for dashboard JSON.
- Difficult navigation (lots of searching to find the right dashboard).
- No alerts to direct to the right dashboard.
- Inefficient use of template variables.
- Dashboards not hierarchical or organized according to an observability strategy.
- Aggregated metrics that drown out important information.
- Non-normalized axes (compare CPU by percentage rather than absolute values).
- Undirected browsing (too much random browsing).