"""merge all heads branches"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '999999'
down_revision = ('028', '156ed976eba1')  # 两个head版本
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
