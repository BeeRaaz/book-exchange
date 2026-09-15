"""add_books_fts_gin_index

Revision ID: 21741dc3622c
Revises: 326b15e1b83d
Create Date: 2026-09-15 16:59:57.153584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21741dc3622c'
down_revision: Union[str, Sequence[str], None] = '326b15e1b83d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Standard column indexes for high-traffic queries and foreign keys
    op.create_index(op.f('ix_books_available'), 'books', ['available'], unique=False)
    op.create_index(op.f('ix_books_created_at'), 'books', ['created_at'], unique=False)
    op.create_index(op.f('ix_books_owner_id'), 'books', ['owner_id'], unique=False)

    op.create_index(op.f('ix_exchanges_requester_id'), 'exchanges', ['requester_id'], unique=False)
    op.create_index(op.f('ix_exchanges_receiver_id'), 'exchanges', ['receiver_id'], unique=False)
    op.create_index(op.f('ix_exchanges_requested_book_id'), 'exchanges', ['requested_book_id'], unique=False)
    op.create_index(op.f('ix_exchanges_offered_book_id'), 'exchanges', ['offered_book_id'], unique=False)
    op.create_index(op.f('ix_exchanges_status'), 'exchanges', ['status'], unique=False)
    op.create_index(op.f('ix_exchanges_created_at'), 'exchanges', ['created_at'], unique=False)

    op.create_index(op.f('ix_revoked_tokens_expires_at'), 'revoked_tokens', ['expires_at'], unique=False)

    # 2. Expression-based GIN index for PostgreSQL Full-Text Search
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_books_fts
        ON books
        USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(author, '')));
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_books_fts;")
    op.drop_index(op.f('ix_revoked_tokens_expires_at'), table_name='revoked_tokens')
    op.drop_index(op.f('ix_exchanges_created_at'), table_name='exchanges')
    op.drop_index(op.f('ix_exchanges_status'), table_name='exchanges')
    op.drop_index(op.f('ix_exchanges_offered_book_id'), table_name='exchanges')
    op.drop_index(op.f('ix_exchanges_requested_book_id'), table_name='exchanges')
    op.drop_index(op.f('ix_exchanges_receiver_id'), table_name='exchanges')
    op.drop_index(op.f('ix_exchanges_requester_id'), table_name='exchanges')
    op.drop_index(op.f('ix_books_owner_id'), table_name='books')
    op.drop_index(op.f('ix_books_created_at'), table_name='books')
    op.drop_index(op.f('ix_books_available'), table_name='books')
