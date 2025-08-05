"""Initial database optimizations

Add indexes and constraints for better query performance

Revision ID: 001
Revises: 
Create Date: 2025-08-02 17:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create indexes for User model
    op.create_index('idx_user_email_lower', 'users', [sa.text('lower(email)')], unique=True)
    op.create_index('idx_user_phone_lower', 'users', [sa.text('lower(phone_number)')], unique=True)
    op.create_index('idx_user_customer_number_lower', 'users', [sa.text('lower(customer_number)')], unique=True)
    op.create_index('idx_user_name_search', 'users', 
                   [sa.text('lower(first_name)'), sa.text('lower(last_name)')], 
                   postgresql_using='gin', 
                   postgresql_ops={
                       'lower(first_name)': 'gin_trgm_ops',
                       'lower(last_name)': 'gin_trgm_ops'
                   })
    
    # Create indexes for Account model
    op.create_index('idx_account_user_status', 'accounts', ['user_id', 'status'])
    op.create_index('idx_account_balance_status', 'accounts', 
                   ['current_balance', 'available_balance', 'status'])
    op.create_index('idx_account_last_activity', 'accounts', ['last_activity'])
    
    # Create indexes for Card model
    op.create_index('idx_card_account_status', 'cards', ['account_id', 'status'])
    op.create_index('idx_card_expiry', 'cards', ['expiry_date'])
    op.create_index('idx_card_number_hash', 'cards', 
                   [sa.text('substring(card_number, -4)')], 
                   postgresql_using='hash')
    
    # Add check constraints
    op.create_check_constraint(
        'ck_user_email_format',
        'users',
        "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'"
    )
    
    op.create_check_constraint(
        'ck_phone_format',
        'users',
        "phone_number ~* '^\\+?[0-9\\s-]+$'"
    )
    
    # Add partial indexes for better performance on active records
    op.create_index(
        'idx_active_users',
        'users',
        ['status'],
        postgresql_where=sa.text("status IN ('active', 'pending_verification')")
    )
    
    op.create_index(
        'idx_active_accounts',
        'accounts',
        ['status'],
        postgresql_where=sa.text("status = 'active'")
    )
    
    # Add GIN index for JSONB fields
    op.execute("""
        CREATE INDEX idx_user_metadata ON users USING GIN (metadata_);
        CREATE INDEX idx_account_metadata ON accounts USING GIN (metadata_);
        CREATE INDEX idx_card_metadata ON cards USING GIN (metadata_);
    """)
    
    # Add foreign key with ON DELETE CASCADE for cards
    op.drop_constraint('cards_account_id_fkey', 'cards', type_='foreignkey')
    op.create_foreign_key(
        'cards_account_id_fkey',
        'cards', 'accounts',
        ['account_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop all created indexes and constraints
    op.drop_index('idx_user_email_lower', table_name='users')
    op.drop_index('idx_user_phone_lower', table_name='users')
    op.drop_index('idx_user_customer_number_lower', table_name='users')
    op.drop_index('idx_user_name_search', table_name='users')
    op.drop_index('idx_account_user_status', table_name='accounts')
    op.drop_index('idx_account_balance_status', table_name='accounts')
    op.drop_index('idx_account_last_activity', table_name='accounts')
    op.drop_index('idx_card_account_status', table_name='cards')
    op.drop_index('idx_card_expiry', table_name='cards')
    op.drop_index('idx_card_number_hash', table_name='cards')
    op.drop_index('idx_active_users', table_name='users')
    op.drop_index('idx_active_accounts', table_name='accounts')
    op.drop_constraint('ck_user_email_format', 'users', type_='check')
    op.drop_constraint('ck_phone_format', 'users', type_='check')
    op.drop_index('idx_user_metadata', table_name='users')
    op.drop_index('idx_account_metadata', table_name='accounts')
    op.drop_index('idx_card_metadata', table_name='cards')
