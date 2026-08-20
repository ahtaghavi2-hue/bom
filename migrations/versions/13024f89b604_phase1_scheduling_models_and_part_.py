"""baseline + phase1: all tables, PERT fields, resources, scenarios

Revision ID: 13024f89b604
Revises:
Create Date: 2026-08-19 12:20:45.647041

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13024f89b604'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════════════
    # Base tables (pre-Phase 1)
    # ═══════════════════════════════════════════════════════════════════

    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(80), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('role', sa.String(20), server_default='viewer'),
        sa.Column('is_active_user', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('specs', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('order_count', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('assemblies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['assemblies.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('parts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assembly_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('part_code', sa.String(100), nullable=True),
        sa.Column('specs', sa.Text(), nullable=True),
        sa.Column('part_type', sa.String(20), server_default='make'),
        sa.Column('quantity', sa.Integer(), server_default='0'),
        sa.Column('required_quantity', sa.Integer(), server_default='1'),
        sa.Column('supplier', sa.String(200), nullable=True),
        sa.Column('supplier_email', sa.String(200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='not_started'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('vector_embedding', sa.Text(), nullable=True),
        # ── Phase 1: PERT / Uncertainty ──
        sa.Column('time_optimistic', sa.Float(), nullable=True),
        sa.Column('time_most_likely', sa.Float(), nullable=True),
        sa.Column('time_pessimistic', sa.Float(), nullable=True),
        # ── Phase 1: Cost breakdown ──
        sa.Column('cost_material', sa.Float(), nullable=True),
        sa.Column('cost_labor', sa.Float(), nullable=True),
        sa.Column('cost_overhead', sa.Float(), nullable=True),
        # ── Phase 1: Resource & storage ──
        sa.Column('required_resource_type', sa.String(50), nullable=True),
        sa.Column('storage_cost_per_day', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['assembly_id'], ['assemblies.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=True),
        sa.Column('assembly_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('label', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['assembly_id'], ['assemblies.id']),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('manufacturers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('quality_score', sa.Float(), server_default='70.0'),
        sa.Column('reliability_score', sa.Float(), server_default='70.0'),
        sa.Column('delivery_days', sa.Integer(), server_default='7'),
        sa.Column('rating_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('manufacturer_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manufacturer_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(['manufacturer_id'], ['manufacturers.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('manufacturer_phones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manufacturer_id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(['manufacturer_id'], ['manufacturers.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('manufacturer_socials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manufacturer_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(100), nullable=False),
        sa.Column('handle', sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(['manufacturer_id'], ['manufacturers.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('part_manufacturers',
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('manufacturer_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['manufacturer_id'], ['manufacturers.id']),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.PrimaryKeyConstraint('part_id', 'manufacturer_id'),
    )

    op.create_table('stages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), server_default='not_started'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('estimated_material_cost', sa.Float(), server_default='0.0'),
        sa.Column('actual_material_cost', sa.Float(), server_default='0.0'),
        sa.Column('estimated_labor_cost', sa.Float(), server_default='0.0'),
        sa.Column('actual_labor_cost', sa.Float(), server_default='0.0'),
        sa.Column('estimated_overhead', sa.Float(), server_default='0.0'),
        sa.Column('actual_overhead', sa.Float(), server_default='0.0'),
        sa.Column('estimated_hours', sa.Float(), server_default='0.0'),
        sa.Column('actual_hours', sa.Float(), server_default='0.0'),
        sa.Column('manufacturer_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['manufacturer_id'], ['manufacturers.id']),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('stage_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stage_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), server_default='0'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['stage_id'], ['stages.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('production_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), server_default='planned'),
        sa.Column('priority', sa.String(20), server_default='normal'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('work_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.ForeignKeyConstraint(['schedule_id'], ['production_schedules.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=True),
        sa.Column('assembly_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(200), nullable=False),
        sa.Column('original_name', sa.String(200), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('file_size', sa.Integer(), server_default='0'),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['assembly_id'], ['assemblies.id']),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.String(500), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_index('ix_settings_key', 'settings', ['key'])

    op.create_table('notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(20), server_default='email'),
        sa.Column('sent_to', sa.String(200), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('part_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('change_summary', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('part_id', 'version_number', name='uq_part_version'),
    )
    op.create_index('ix_part_versions_part_id', 'part_versions', ['part_id'])

    op.create_table('change_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_change_requests_part_id', 'change_requests', ['part_id'])

    op.create_table('change_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('change_request_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vote_type', sa.String(10), nullable=False),
        sa.Column('voted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['change_request_id'], ['change_requests.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('change_request_id', 'user_id', name='uq_change_vote'),
    )

    op.create_table('cost_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.Column('estimated_total', sa.Float(), server_default='0.0'),
        sa.Column('actual_total', sa.Float(), server_default='0.0'),
        sa.Column('material_cost', sa.Float(), server_default='0.0'),
        sa.Column('labor_cost', sa.Float(), server_default='0.0'),
        sa.Column('overhead', sa.Float(), server_default='0.0'),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cost_history_part_id', 'cost_history', ['part_id'])

    op.create_table('part_similarity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('similar_part_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), server_default='0.0'),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.ForeignKeyConstraint(['similar_part_id'], ['parts.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('part_id', 'similar_part_id', name='uq_part_similarity'),
    )
    op.create_index('ix_part_similarity_part_id', 'part_similarity', ['part_id'])

    op.create_table('artisans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('specialty', sa.String(200), nullable=True),
        sa.Column('labor_rate', sa.Float(), server_default='0.0'),
        sa.Column('quality_score', sa.Float(), server_default='70.0'),
        sa.Column('accuracy_score', sa.Float(), server_default='70.0'),
        sa.Column('rating_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('vendor_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_type', sa.String(20), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('quality_score', sa.Float(), server_default='0.0'),
        sa.Column('accuracy_score', sa.Float(), server_default='0.0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('rated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['rated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ═══════════════════════════════════════════════════════════════════
    # Phase 1 – New tables
    # ═══════════════════════════════════════════════════════════════════

    op.create_table('resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('capacity', sa.Integer(), server_default='1'),
        sa.Column('shift_hours', sa.Float(), server_default='8.0'),
        sa.Column('cost_per_hour', sa.Float(), server_default='0.0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_resources_resource_type', 'resources', ['resource_type'])

    op.create_table('project_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('target_delivery_date', sa.DateTime(), nullable=True),
        sa.Column('daily_penalty', sa.Float(), server_default='0.0'),
        sa.Column('total_budget', sa.Float(), server_default='0.0'),
        sa.Column('risk_reserve_pct', sa.Float(), server_default='10.0'),
        sa.Column('monte_carlo_runs', sa.Integer(), server_default='1000'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id'),
    )

    op.create_table('scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scenarios_product_id', 'scenarios', ['product_id'])

    op.create_table('scenario_overrides',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(50), nullable=False),
        sa.Column('field_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scenario_id', 'part_id', 'field_name', name='uq_scenario_override'),
    )

    op.create_table('schedule_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('result_type', sa.String(30), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('estimated_duration', sa.Float(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('probability_on_time', sa.Float(), nullable=True),
        sa.Column('critical_path_ids', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id']),
        sa.ForeignKeyConstraint(['schedule_id'], ['production_schedules.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_schedule_results_product_id', 'schedule_results', ['product_id'])

    op.create_table('resource_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('part_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.Float(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.ForeignKeyConstraint(['resource_id'], ['resources.id']),
        sa.ForeignKeyConstraint(['schedule_id'], ['production_schedules.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table('project_cost_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('cumulative_material', sa.Float(), server_default='0.0'),
        sa.Column('cumulative_labor', sa.Float(), server_default='0.0'),
        sa.Column('cumulative_overhead', sa.Float(), server_default='0.0'),
        sa.Column('cumulative_total', sa.Float(), server_default='0.0'),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_project_cost_snapshots_product_id', 'project_cost_snapshots', ['product_id'])


def downgrade():
    op.drop_table('project_cost_snapshots')
    op.drop_table('resource_assignments')
    op.drop_table('schedule_results')
    op.drop_table('scenario_overrides')
    op.drop_table('scenarios')
    op.drop_table('project_settings')
    op.drop_table('resources')
    op.drop_table('vendor_ratings')
    op.drop_table('artisans')
    op.drop_table('part_similarity')
    op.drop_table('cost_history')
    op.drop_table('change_votes')
    op.drop_table('change_requests')
    op.drop_table('part_versions')
    op.drop_table('notification_logs')
    op.drop_table('settings')
    op.drop_table('documents')
    op.drop_table('work_orders')
    op.drop_table('production_schedules')
    op.drop_table('stage_details')
    op.drop_table('stages')
    op.drop_table('part_manufacturers')
    op.drop_table('manufacturer_socials')
    op.drop_table('manufacturer_phones')
    op.drop_table('manufacturer_emails')
    op.drop_table('manufacturers')
    op.drop_table('images')
    op.drop_table('parts')
    op.drop_table('assemblies')
    op.drop_table('products')
    op.drop_table('users')
