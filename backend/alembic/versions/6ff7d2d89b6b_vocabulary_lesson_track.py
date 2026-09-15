"""vocabulary lesson track

Revision ID: 6ff7d2d89b6b
Revises: 8912ac352320
Create Date: 2026-09-15 12:19:55.925638

Adds a second, independently-unlocking lesson track (vocabulary, alongside
the existing alphabet track) to the lessons table:
  - lesson_type: discriminates alphabet vs vocabulary lessons
  - concept_key: vocabulary category slug (letter stays the alphabet-track key)
  - order_index uniqueness becomes scoped to (lesson_type, order_index)
    instead of globally unique, so each track can independently number its
    own lessons starting at 1

Written with SQLite's batch-recreate mode (op.batch_alter_table) rather than
plain ALTER TABLE / autogenerate's raw output, since SQLite cannot drop or
change an unnamed UNIQUE constraint in place — batch mode rebuilds the table
under the hood and preserves existing rows.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ff7d2d89b6b'
down_revision: Union[str, Sequence[str], None] = '8912ac352320'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Explicit copy_from, WITHOUT a unique constraint on order_index: the
    # original table declared order_index globally unique (via mapped_column
    # unique=True), which recreate mode would otherwise silently preserve
    # (SQLite's anonymous UNIQUE(order_index) constraint isn't addressable
    # by drop_constraint()). Describing the pre-migration table explicitly
    # here — minus that constraint — is what actually removes it, since
    # batch mode rebuilds the table from this definition rather than a
    # reflection of the live schema.
    old_lessons = sa.Table(
        'lessons',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('letter', sa.String(length=1), unique=True, nullable=False),
        sa.Column('order_index', sa.Integer, nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
    )

    with op.batch_alter_table('lessons', recreate='always', copy_from=old_lessons) as batch_op:
        batch_op.add_column(
            sa.Column(
                'lesson_type',
                sa.Enum('ALPHABET', 'VOCABULARY', name='lessontype'),
                nullable=False,
                server_default='ALPHABET',
            )
        )
        batch_op.add_column(sa.Column('concept_key', sa.String(length=50), nullable=True))
        batch_op.alter_column('letter', existing_type=sa.VARCHAR(length=1), nullable=True)
        batch_op.create_unique_constraint('uq_lesson_type_order', ['lesson_type', 'order_index'])
        batch_op.create_unique_constraint('uq_lessons_concept_key', ['concept_key'])

    # server_default only needed to backfill existing rows during the batch
    # rebuild above; drop it so future inserts must specify lesson_type
    # explicitly via the ORM (matches the model, which has no DB-level default).
    with op.batch_alter_table('lessons') as batch_op:
        batch_op.alter_column('lesson_type', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('lessons', recreate='always') as batch_op:
        batch_op.drop_constraint('uq_lessons_concept_key', type_='unique')
        batch_op.drop_constraint('uq_lesson_type_order', type_='unique')
        batch_op.alter_column('letter', existing_type=sa.VARCHAR(length=1), nullable=False)
        batch_op.drop_column('concept_key')
        batch_op.drop_column('lesson_type')
        batch_op.create_unique_constraint('uq_lessons_order_index', ['order_index'])
