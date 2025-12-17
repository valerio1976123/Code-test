"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-12-17

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_app_settings_key", "app_settings", ["key"], unique=True)

    op.create_table(
        "network_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("vendor", sa.String(length=50), nullable=False, server_default="generic"),
        sa.Column("username", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("password_enc", sa.Text(), nullable=True),
        sa.Column("enable_secret_enc", sa.Text(), nullable=True),
        sa.Column("passphrase_enc", sa.Text(), nullable=True),
        sa.Column("command_profile_json", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_network_devices_host", "network_devices", ["host"], unique=False)
    op.create_index("ix_network_devices_name", "network_devices", ["name"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "backup_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("schedule_type", sa.String(length=50), nullable=False),
        sa.Column("run_once_at", sa.DateTime(), nullable=True),
        sa.Column("time_of_day", sa.Time(), nullable=True),
        sa.Column("weekdays", sa.String(length=50), nullable=True),
        sa.Column("every_n_hours", sa.Integer(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["network_devices.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_backup_schedules_device_id", "backup_schedules", ["device_id"], unique=False)
    op.create_index("ix_backup_schedules_next_run_at", "backup_schedules", ["next_run_at"], unique=False)

    op.create_table(
        "backup_executions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("output_path", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["device_id"], ["network_devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["schedule_id"], ["backup_schedules.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_backup_executions_created_at", "backup_executions", ["created_at"], unique=False)
    op.create_index("ix_backup_executions_device_id", "backup_executions", ["device_id"], unique=False)
    op.create_index("ix_backup_executions_schedule_id", "backup_executions", ["schedule_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_backup_executions_schedule_id", table_name="backup_executions")
    op.drop_index("ix_backup_executions_device_id", table_name="backup_executions")
    op.drop_index("ix_backup_executions_created_at", table_name="backup_executions")
    op.drop_table("backup_executions")

    op.drop_index("ix_backup_schedules_next_run_at", table_name="backup_schedules")
    op.drop_index("ix_backup_schedules_device_id", table_name="backup_schedules")
    op.drop_table("backup_schedules")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_network_devices_name", table_name="network_devices")
    op.drop_index("ix_network_devices_host", table_name="network_devices")
    op.drop_table("network_devices")

    op.drop_index("ix_app_settings_key", table_name="app_settings")
    op.drop_table("app_settings")
