"""add edge runtime tables"""

from alembic import op
import sqlalchemy as sa


revision = "20260701_000003"
down_revision = "20260701_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "edge_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("node_key", sa.String(length=128), nullable=False),
        sa.Column("hostname", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("software_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_edge_nodes_id", "edge_nodes", ["id"])
    op.create_index("ix_edge_nodes_name", "edge_nodes", ["name"], unique=True)
    op.create_index("ix_edge_nodes_node_key", "edge_nodes", ["node_key"], unique=True)
    op.create_index("ix_edge_nodes_status", "edge_nodes", ["status"])
    op.create_index("ix_edge_nodes_last_seen_at", "edge_nodes", ["last_seen_at"])
    op.create_index("ix_edge_nodes_created_at", "edge_nodes", ["created_at"])

    op.create_table(
        "edge_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("edge_node_id", sa.Integer(), sa.ForeignKey("edge_nodes.id"), nullable=False),
        sa.Column("job_kind", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_edge_jobs_id", "edge_jobs", ["id"])
    op.create_index("ix_edge_jobs_edge_node_id", "edge_jobs", ["edge_node_id"])
    op.create_index("ix_edge_jobs_job_kind", "edge_jobs", ["job_kind"])
    op.create_index("ix_edge_jobs_status", "edge_jobs", ["status"])
    op.create_index("ix_edge_jobs_created_at", "edge_jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_edge_jobs_created_at", table_name="edge_jobs")
    op.drop_index("ix_edge_jobs_status", table_name="edge_jobs")
    op.drop_index("ix_edge_jobs_job_kind", table_name="edge_jobs")
    op.drop_index("ix_edge_jobs_edge_node_id", table_name="edge_jobs")
    op.drop_index("ix_edge_jobs_id", table_name="edge_jobs")
    op.drop_table("edge_jobs")

    op.drop_index("ix_edge_nodes_created_at", table_name="edge_nodes")
    op.drop_index("ix_edge_nodes_last_seen_at", table_name="edge_nodes")
    op.drop_index("ix_edge_nodes_status", table_name="edge_nodes")
    op.drop_index("ix_edge_nodes_node_key", table_name="edge_nodes")
    op.drop_index("ix_edge_nodes_name", table_name="edge_nodes")
    op.drop_index("ix_edge_nodes_id", table_name="edge_nodes")
    op.drop_table("edge_nodes")
