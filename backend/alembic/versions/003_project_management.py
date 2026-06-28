"""Project management schema

Revision ID: 003
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sprints",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("goal", sa.Text()),
        sa.Column("status", sa.String(50), server_default="planned"),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sprints_project_id", "sprints", ["project_id"])

    op.create_table(
        "milestones",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("due_date", sa.Date()),
        sa.Column("order_index", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_milestones_project_id", "milestones", ["project_id"])

    op.add_column("tasks", sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True))
    op.add_column("tasks", sa.Column("sprint_id", sa.UUID(), sa.ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True))
    op.add_column("tasks", sa.Column("milestone_id", sa.UUID(), sa.ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True))
    op.add_column("tasks", sa.Column("kanban_column", sa.String(50), server_default="backlog"))
    op.add_column("tasks", sa.Column("order_index", sa.Integer(), server_default="0"))
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])
    op.create_index("ix_tasks_kanban", "tasks", ["project_id", "kanban_column"])


def downgrade() -> None:
    op.drop_index("ix_tasks_kanban", "tasks")
    op.drop_index("ix_tasks_project_id", "tasks")
    op.drop_index("ix_tasks_user_id", "tasks")
    op.drop_column("tasks", "order_index")
    op.drop_column("tasks", "kanban_column")
    op.drop_column("tasks", "milestone_id")
    op.drop_column("tasks", "sprint_id")
    op.drop_column("tasks", "user_id")
    op.drop_table("milestones")
    op.drop_table("sprints")
