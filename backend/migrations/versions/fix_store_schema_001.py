"""
Fix Store model schema - add missing columns
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = 'fix_store_schema_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to stores table"""
    
    # Check if columns exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('stores')]
    
    # Add shopify_domain if it doesn't exist
    if 'shopify_domain' not in existing_columns:
        # If shop_domain exists, rename it to shopify_domain
        if 'shop_domain' in existing_columns:
            op.alter_column('stores', 'shop_domain', new_column_name='shopify_domain')
        else:
            op.add_column('stores', sa.Column('shopify_domain', sa.String(), nullable=True))
            # Update from shopify_store_id if it exists
            if 'shopify_store_id' in existing_columns:
                op.execute("UPDATE stores SET shopify_domain = shopify_store_id || '.myshopify.com' WHERE shopify_domain IS NULL")
    
    # Add email if it doesn't exist
    if 'email' not in existing_columns:
        op.add_column('stores', sa.Column('email', sa.String(), nullable=True))
    
    # Add shop_name if it doesn't exist
    if 'shop_name' not in existing_columns:
        # If store_name exists, rename it to shop_name
        if 'store_name' in existing_columns:
            op.alter_column('stores', 'store_name', new_column_name='shop_name')
        else:
            op.add_column('stores', sa.Column('shop_name', sa.String(), nullable=True))
    
    # Make shopify_domain unique and not null after data migration
    if 'shopify_domain' in existing_columns or 'shop_domain' in existing_columns:
        # Ensure no null values
        op.execute("UPDATE stores SET shopify_domain = 'temp-' || id || '.myshopify.com' WHERE shopify_domain IS NULL")
        op.alter_column('stores', 'shopify_domain', nullable=False)
        
        # Create unique index if not exists
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('stores')]
        if 'ix_stores_shopify_domain' not in existing_indexes:
            op.create_index('ix_stores_shopify_domain', 'stores', ['shopify_domain'], unique=True)


def downgrade():
    """Revert schema changes"""
    op.drop_index('ix_stores_shopify_domain', 'stores')
    
    # Rename columns back
    op.alter_column('stores', 'shopify_domain', new_column_name='shop_domain')
    op.alter_column('stores', 'shop_name', new_column_name='store_name')
    
    # Drop email column
    op.drop_column('stores', 'email')
