# PostgreSQL Database Documentation

## PostgreSQL Schema Definitions
The database schema is defined using SQLAlchemy ORM, stored within the `models.py` file. Key entities include:
- **Store**: Shopify store information (`stores` table)
- **Product**: Shopify products (`products` table)
- **ProductVariant**: Product variants like size and color (`product_variants` table)
- **InventoryItem**: Inventory levels per variant per location (`inventory_items` table)
- **Alert**: Alerts for inventory management (`alerts` table)

Additional schemas cover locations, suppliers, purchase orders, forecasts, custom fields, and more.

## Migration Instructions and History
Migrations are managed using Alembic. Key migration files:
- `001_add_performance_indexes.py`: Adds indexes for optimized query performance

To run migrations, use commands in the Alembic CLI:
```bash
alembic upgrade head
```
To create a new migration, use:
```bash
alembic revision --autogenerate -m "Migration description"
```

## Database Connection Configuration
Connection settings are provided in `.env` and `config.py`:
```plaintext
DATABASE_URL=postgresql://user:password@localhost:5432/inventorysync
```
Configuration in `database.py` manages both sync and async engines:
```python
db_engine = create_engine(DATABASE_URL)
async_db_engine = create_async_engine(ASYNC_DATABASE_URL)
```

## Backup and Restore Procedures
Backups can be automated with tools like `pg_dump`:
```bash
pg_dump -U user -h localhost inventorysync > backup.sql
```
Restore using:
```bash
psql -U user -d inventorysync < backup.sql
```

## Performance Optimization Tips
- Ensure indexes for frequently queried fields
- Use PostgreSQL extensions like "pg_trgm" for optimized text searches
- Leverage JSONB indexes for flexible queries

## Indexes and Constraints
Key indexes for performance include:
- **Stores Table**: `idx_stores_shop_domain`, `idx_stores_subscription_status`
- **Products Table**: `idx_products_store_status`, `idx_products_title_search`
- **Variants Table**: `idx_variants_sku`, `idx_variants_product_id`

Constraints are defined at the model level, such as unique keys and foreign key constraints.
