"""initial platform"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_workspaces_id", "workspaces", ["id"])
    op.create_index("ix_workspaces_name", "workspaces", ["name"], unique=True)
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)

    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sites_id", "sites", ["id"])
    op.create_index("ix_sites_name", "sites", ["name"])
    op.create_index("ix_sites_code", "sites", ["code"], unique=True)

    op.create_table(
        "network_segments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("cidr", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("scan_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_network_segments_id", "network_segments", ["id"])
    op.create_index("ix_network_segments_cidr", "network_segments", ["cidr"])

    op.create_table(
        "integration_endpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("target_ref", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_integration_endpoints_id", "integration_endpoints", ["id"])
    op.create_index("ix_integration_endpoints_name", "integration_endpoints", ["name"])
    op.create_index("ix_integration_endpoints_kind", "integration_endpoints", ["kind"])

    op.create_table(
        "api_clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("client_key", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_api_clients_id", "api_clients", ["id"])
    op.create_index("ix_api_clients_name", "api_clients", ["name"])
    op.create_index("ix_api_clients_client_key", "api_clients", ["client_key"], unique=True)

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("hostname", sa.String(length=128), nullable=True),
        sa.Column("vendor", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_devices_id", "devices", ["id"])
    op.create_index("ix_devices_ip_address", "devices", ["ip_address"], unique=True)

    op.create_table(
        "protocol_fingerprints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("protocol_name", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_protocol_fingerprints_id", "protocol_fingerprints", ["id"])

    op.create_table(
        "telemetry_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("quality", sa.String(length=32), nullable=False),
        sa.Column("source_protocol", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_telemetry_records_id", "telemetry_records", ["id"])
    op.create_index("ix_telemetry_records_metric_key", "telemetry_records", ["metric_key"])
    op.create_index("ix_telemetry_records_observed_at", "telemetry_records", ["observed_at"])

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=False),
        sa.Column("operator", sa.String(length=16), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("notification_channel", sa.String(length=32), nullable=False),
    )
    op.create_index("ix_alert_rules_id", "alert_rules", ["id"])
    op.create_index("ix_alert_rules_name", "alert_rules", ["name"], unique=True)
    op.create_index("ix_alert_rules_metric_key", "alert_rules", ["metric_key"])

    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("alert_rules.id"), nullable=False),
        sa.Column("telemetry_id", sa.Integer(), sa.ForeignKey("telemetry_records.id"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("delivered", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_alert_events_id", "alert_events", ["id"])

    op.create_table(
        "semantic_hypotheses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("raw_metric_key", sa.String(length=128), nullable=False),
        sa.Column("predicted_metric_key", sa.String(length=128), nullable=False),
        sa.Column("predicted_unit", sa.String(length=32), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("learning_state", sa.String(length=32), nullable=False),
        sa.Column("last_observed_value", sa.Float(), nullable=True),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_semantic_hypotheses_id", "semantic_hypotheses", ["id"])
    op.create_index("ix_semantic_hypotheses_raw_metric_key", "semantic_hypotheses", ["raw_metric_key"])

    op.create_table(
        "traffic_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("source_ip", sa.String(length=64), nullable=False),
        sa.Column("source_port", sa.Integer(), nullable=False),
        sa.Column("destination_ip", sa.String(length=64), nullable=False),
        sa.Column("destination_port", sa.Integer(), nullable=False),
        sa.Column("transport", sa.String(length=16), nullable=False),
        sa.Column("protocol_hint", sa.String(length=64), nullable=False),
        sa.Column("payload_sample", sa.Text(), nullable=True),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_traffic_observations_id", "traffic_observations", ["id"])
    op.create_index("ix_traffic_observations_source_ip", "traffic_observations", ["source_ip"])
    op.create_index("ix_traffic_observations_destination_ip", "traffic_observations", ["destination_ip"])
    op.create_index("ix_traffic_observations_observed_at", "traffic_observations", ["observed_at"])

    op.create_table(
        "flow_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_key", sa.String(length=255), nullable=False),
        sa.Column("protocol_hint", sa.String(length=64), nullable=False),
        sa.Column("source_ip", sa.String(length=64), nullable=False),
        sa.Column("destination_ip", sa.String(length=64), nullable=False),
        sa.Column("destination_port", sa.Integer(), nullable=False),
        sa.Column("transport", sa.String(length=16), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("last_payload_sample", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_flow_clusters_id", "flow_clusters", ["id"])
    op.create_index("ix_flow_clusters_cluster_key", "flow_clusters", ["cluster_key"], unique=True)
    op.create_index("ix_flow_clusters_source_ip", "flow_clusters", ["source_ip"])
    op.create_index("ix_flow_clusters_destination_ip", "flow_clusters", ["destination_ip"])
    op.create_index("ix_flow_clusters_updated_at", "flow_clusters", ["updated_at"])

    op.create_table(
        "unknown_protocol_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("flow_cluster_id", sa.Integer(), sa.ForeignKey("flow_clusters.id"), nullable=False),
        sa.Column("candidate_label", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("payload_fingerprint", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_unknown_protocol_candidates_id", "unknown_protocol_candidates", ["id"])
    op.create_index(
        "ix_unknown_protocol_candidates_candidate_label",
        "unknown_protocol_candidates",
        ["candidate_label"],
    )
    op.create_index("ix_unknown_protocol_candidates_updated_at", "unknown_protocol_candidates", ["updated_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
    op.create_index("ix_audit_logs_actor", "audit_logs", ["actor"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "semantic_maps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("vendor", sa.String(length=128), nullable=True),
        sa.Column("protocol_name", sa.String(length=64), nullable=False),
        sa.Column("source_key", sa.String(length=128), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_semantic_maps_id", "semantic_maps", ["id"])
    op.create_index("ix_semantic_maps_vendor", "semantic_maps", ["vendor"])
    op.create_index("ix_semantic_maps_protocol_name", "semantic_maps", ["protocol_name"])
    op.create_index("ix_semantic_maps_source_key", "semantic_maps", ["source_key"])
    op.create_index("ix_semantic_maps_metric_key", "semantic_maps", ["metric_key"])
    op.create_index("ix_semantic_maps_created_at", "semantic_maps", ["created_at"])
    op.create_index("ix_semantic_maps_updated_at", "semantic_maps", ["updated_at"])


def downgrade() -> None:
    for index, table in [
        ("ix_semantic_maps_updated_at", "semantic_maps"),
        ("ix_semantic_maps_created_at", "semantic_maps"),
        ("ix_semantic_maps_metric_key", "semantic_maps"),
        ("ix_semantic_maps_source_key", "semantic_maps"),
        ("ix_semantic_maps_protocol_name", "semantic_maps"),
        ("ix_semantic_maps_vendor", "semantic_maps"),
        ("ix_semantic_maps_id", "semantic_maps"),
    ]:
        op.drop_index(index, table_name=table)
    op.drop_table("semantic_maps")
    for index, table in [
        ("ix_audit_logs_created_at", "audit_logs"),
        ("ix_audit_logs_action", "audit_logs"),
        ("ix_audit_logs_actor", "audit_logs"),
        ("ix_audit_logs_id", "audit_logs"),
    ]:
        op.drop_index(index, table_name=table)
    op.drop_table("audit_logs")
    for index, table in [
        ("ix_unknown_protocol_candidates_updated_at", "unknown_protocol_candidates"),
        ("ix_unknown_protocol_candidates_candidate_label", "unknown_protocol_candidates"),
        ("ix_unknown_protocol_candidates_id", "unknown_protocol_candidates"),
    ]:
        op.drop_index(index, table_name=table)
    op.drop_table("unknown_protocol_candidates")
    for index, table in [
        ("ix_flow_clusters_updated_at", "flow_clusters"),
        ("ix_flow_clusters_destination_ip", "flow_clusters"),
        ("ix_flow_clusters_source_ip", "flow_clusters"),
        ("ix_flow_clusters_cluster_key", "flow_clusters"),
        ("ix_flow_clusters_id", "flow_clusters"),
    ]:
        op.drop_index(index, table_name=table)
    op.drop_table("flow_clusters")
    for index, table in [
        ("ix_traffic_observations_observed_at", "traffic_observations"),
        ("ix_traffic_observations_destination_ip", "traffic_observations"),
        ("ix_traffic_observations_source_ip", "traffic_observations"),
        ("ix_traffic_observations_id", "traffic_observations"),
    ]:
        op.drop_index(index, table_name=table)
    op.drop_table("traffic_observations")
    for index, table in [
        ("ix_semantic_hypotheses_raw_metric_key", "semantic_hypotheses"),
        ("ix_semantic_hypotheses_id", "semantic_hypotheses"),
    ]:
        op.drop_index(index, table_name=table)
    op.drop_table("semantic_hypotheses")
    op.drop_index("ix_alert_events_id", table_name="alert_events")
    op.drop_table("alert_events")
    op.drop_index("ix_alert_rules_metric_key", table_name="alert_rules")
    op.drop_index("ix_alert_rules_name", table_name="alert_rules")
    op.drop_index("ix_alert_rules_id", table_name="alert_rules")
    op.drop_table("alert_rules")
    op.drop_index("ix_telemetry_records_observed_at", table_name="telemetry_records")
    op.drop_index("ix_telemetry_records_metric_key", table_name="telemetry_records")
    op.drop_index("ix_telemetry_records_id", table_name="telemetry_records")
    op.drop_table("telemetry_records")
    op.drop_index("ix_protocol_fingerprints_id", table_name="protocol_fingerprints")
    op.drop_table("protocol_fingerprints")
    op.drop_index("ix_devices_ip_address", table_name="devices")
    op.drop_index("ix_devices_id", table_name="devices")
    op.drop_table("devices")
    op.drop_index("ix_api_clients_client_key", table_name="api_clients")
    op.drop_index("ix_api_clients_name", table_name="api_clients")
    op.drop_index("ix_api_clients_id", table_name="api_clients")
    op.drop_table("api_clients")
    op.drop_index("ix_integration_endpoints_kind", table_name="integration_endpoints")
    op.drop_index("ix_integration_endpoints_name", table_name="integration_endpoints")
    op.drop_index("ix_integration_endpoints_id", table_name="integration_endpoints")
    op.drop_table("integration_endpoints")
    op.drop_index("ix_network_segments_cidr", table_name="network_segments")
    op.drop_index("ix_network_segments_id", table_name="network_segments")
    op.drop_table("network_segments")
    op.drop_index("ix_sites_code", table_name="sites")
    op.drop_index("ix_sites_name", table_name="sites")
    op.drop_index("ix_sites_id", table_name="sites")
    op.drop_table("sites")
    op.drop_index("ix_workspaces_slug", table_name="workspaces")
    op.drop_index("ix_workspaces_name", table_name="workspaces")
    op.drop_index("ix_workspaces_id", table_name="workspaces")
    op.drop_table("workspaces")
