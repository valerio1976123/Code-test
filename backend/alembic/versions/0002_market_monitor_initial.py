"""market monitor initial tables

Revision ID: 0002_market_monitor_initial
Revises: 0001_initial
Create Date: 2025-12-18

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_market_monitor_initial"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("exchange", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("country", sa.String(length=2), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_stocks_symbol", "stocks", ["symbol"], unique=True)
    op.create_index("ix_stocks_country", "stocks", ["country"], unique=False)

    op.create_table(
        "market_indexes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("country", sa.String(length=2), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_market_indexes_symbol", "market_indexes", ["symbol"], unique=True)
    op.create_index("ix_market_indexes_country", "market_indexes", ["country"], unique=False)

    op.create_table(
        "country_macro_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("gdp_growth", sa.Float(), nullable=True),
        sa.Column("inflation", sa.Float(), nullable=True),
        sa.Column("interest_rate", sa.Float(), nullable=True),
        sa.Column("unemployment", sa.Float(), nullable=True),
        sa.Column("sentiment_index", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("country", "as_of_date", name="uq_country_macro_country_date"),
    )
    op.create_index("ix_country_macro_data_country", "country_macro_data", ["country"], unique=False)
    op.create_index("ix_country_macro_data_as_of_date", "country_macro_data", ["as_of_date"], unique=False)

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("instrument_type", sa.String(length=10), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("instrument_type", "symbol", "timestamp", name="uq_price_instr_symbol_ts"),
    )
    op.create_index("ix_price_history_instrument_type", "price_history", ["instrument_type"], unique=False)
    op.create_index("ix_price_history_symbol", "price_history", ["symbol"], unique=False)
    op.create_index("ix_price_history_timestamp", "price_history", ["timestamp"], unique=False)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("target_type", sa.String(length=10), nullable=False),
        sa.Column("target_identifier", sa.String(length=32), nullable=False),
        sa.Column("timestamp_generated", sa.DateTime(), nullable=False),
        sa.Column("forecast_horizon", sa.String(length=10), nullable=False, server_default="1d"),
        sa.Column("predicted_direction", sa.String(length=10), nullable=False),
        sa.Column("predicted_return", sa.Float(), nullable=False, server_default="0"),
        sa.Column("model_used", sa.String(length=100), nullable=False, server_default="rf_v1"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.UniqueConstraint(
            "target_type",
            "target_identifier",
            "timestamp_generated",
            "forecast_horizon",
            name="uq_pred_target_ts_horizon",
        ),
    )
    op.create_index("ix_predictions_target_type", "predictions", ["target_type"], unique=False)
    op.create_index("ix_predictions_target_identifier", "predictions", ["target_identifier"], unique=False)
    op.create_index("ix_predictions_timestamp_generated", "predictions", ["timestamp_generated"], unique=False)

    op.create_table(
        "watchlist_stocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "stock_id", name="uq_watchlist_user_stock"),
    )
    op.create_index("ix_watchlist_stocks_user_id", "watchlist_stocks", ["user_id"], unique=False)
    op.create_index("ix_watchlist_stocks_stock_id", "watchlist_stocks", ["stock_id"], unique=False)

    op.create_table(
        "watchlist_indexes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("index_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["index_id"], ["market_indexes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "index_id", name="uq_watchlist_user_index"),
    )
    op.create_index("ix_watchlist_indexes_user_id", "watchlist_indexes", ["user_id"], unique=False)
    op.create_index("ix_watchlist_indexes_index_id", "watchlist_indexes", ["index_id"], unique=False)

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(length=10), nullable=False),
        sa.Column("target_identifier", sa.String(length=32), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("comparator", sa.String(length=5), nullable=False, server_default="gt"),
        sa.Column("threshold", sa.Float(), nullable=False, server_default="0"),
        sa.Column("direction", sa.String(length=10), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_alert_rules_user_id", "alert_rules", ["user_id"], unique=False)
    op.create_index("ix_alert_rules_target_type", "alert_rules", ["target_type"], unique=False)
    op.create_index("ix_alert_rules_target_identifier", "alert_rules", ["target_identifier"], unique=False)
    op.create_index("ix_alert_rules_rule_type", "alert_rules", ["rule_type"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(length=10), nullable=False),
        sa.Column("target_identifier", sa.String(length=32), nullable=False),
        sa.Column("triggered_at", sa.DateTime(), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False, server_default="info"),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id",
            "triggered_at",
            "target_type",
            "target_identifier",
            "message",
            name="uq_alert_dedupe",
        ),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"], unique=False)
    op.create_index("ix_alerts_target_type", "alerts", ["target_type"], unique=False)
    op.create_index("ix_alerts_target_identifier", "alerts", ["target_identifier"], unique=False)
    op.create_index("ix_alerts_triggered_at", "alerts", ["triggered_at"], unique=False)
    op.create_index("ix_alerts_is_read", "alerts", ["is_read"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_alerts_is_read", table_name="alerts")
    op.drop_index("ix_alerts_triggered_at", table_name="alerts")
    op.drop_index("ix_alerts_target_identifier", table_name="alerts")
    op.drop_index("ix_alerts_target_type", table_name="alerts")
    op.drop_index("ix_alerts_user_id", table_name="alerts")
    op.drop_table("alerts")

    op.drop_index("ix_alert_rules_rule_type", table_name="alert_rules")
    op.drop_index("ix_alert_rules_target_identifier", table_name="alert_rules")
    op.drop_index("ix_alert_rules_target_type", table_name="alert_rules")
    op.drop_index("ix_alert_rules_user_id", table_name="alert_rules")
    op.drop_table("alert_rules")

    op.drop_index("ix_watchlist_indexes_index_id", table_name="watchlist_indexes")
    op.drop_index("ix_watchlist_indexes_user_id", table_name="watchlist_indexes")
    op.drop_table("watchlist_indexes")

    op.drop_index("ix_watchlist_stocks_stock_id", table_name="watchlist_stocks")
    op.drop_index("ix_watchlist_stocks_user_id", table_name="watchlist_stocks")
    op.drop_table("watchlist_stocks")

    op.drop_index("ix_predictions_timestamp_generated", table_name="predictions")
    op.drop_index("ix_predictions_target_identifier", table_name="predictions")
    op.drop_index("ix_predictions_target_type", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("ix_price_history_timestamp", table_name="price_history")
    op.drop_index("ix_price_history_symbol", table_name="price_history")
    op.drop_index("ix_price_history_instrument_type", table_name="price_history")
    op.drop_table("price_history")

    op.drop_index("ix_country_macro_data_as_of_date", table_name="country_macro_data")
    op.drop_index("ix_country_macro_data_country", table_name="country_macro_data")
    op.drop_table("country_macro_data")

    op.drop_index("ix_market_indexes_country", table_name="market_indexes")
    op.drop_index("ix_market_indexes_symbol", table_name="market_indexes")
    op.drop_table("market_indexes")

    op.drop_index("ix_stocks_country", table_name="stocks")
    op.drop_index("ix_stocks_symbol", table_name="stocks")
    op.drop_table("stocks")

