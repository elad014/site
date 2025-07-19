import psycopg2
from utils import Logger
from contextlib import contextmanager

logger = Logger.setup_logger(__name__)

class DB_Config:
    @staticmethod
    def get_db_connection():
        conn = psycopg2.connect(
        "postgresql://neondb_owner:npg_MYw2ejoqv3BX@ep-green-wind-a2yx94w5-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"
        )
        return conn

    @staticmethod
    def get_cursor():
        """Create and return a database cursor"""
        conn = DB_Config.get_db_connection()
        return conn.cursor()
        
    @staticmethod
    def print_table_content(table_name):
        cursor = DB_Config.get_cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        logger.info(f"Content of {table_name} table:")
        logger.info("\t".join(colnames))
        logger.info("-" * 40)
        
        for row in rows:
            logger.info("\t".join(map(str, row)))
        logger.info("\n")
        
    @staticmethod
    def delete_table(cursor, conn, table_name):
        drop_table_query = f"DROP TABLE IF EXISTS {table_name};"

        try:
            cursor.execute(drop_table_query)
            conn.commit()
            logger.info(f"Table '{table_name}' deleted successfully.")
        except Exception as e:
            logger.error(f"Error occurred: {e}")
        finally:
            cursor.close()
            conn.close() 

class DB_Manager:
    """Handle database operations and connection management"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def insert_record(self, table_name: str, data: dict) -> None:
        """Insert a record into specified table
        Args:
            table_name: Name of table to insert into
            data: Dictionary of column names and values
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f'%({k})s' for k in data.keys()])
        query = f'''
            INSERT INTO {table_name} ({columns})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING;
        '''
        self.cursor.execute(query, data)

    def delete_record(self, table_name: str, condition: dict) -> None:
        """Delete records from specified table matching condition
        Args:
            table_name: Name of table to delete from  
            condition: Dictionary of column names and values for WHERE clause
        """
        where_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        self.cursor.execute(query, list(condition.values()))

    def update_record(self, table_name: str, data: dict, condition: dict) -> None:
        """Update records in specified table matching condition
        Args:
            table_name: Name of table to update
            data: Dictionary of column names and values to update
            condition: Dictionary of column names and values for WHERE clause
        """
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        query = f'''
            UPDATE {table_name}
            SET {set_clause}
            WHERE {where_clause}
        '''
        self.cursor.execute(query, list(data.values()) + list(condition.values()))

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        try:
            yield
            self.cursor.connection.commit()
        except Exception as e:
            self.cursor.connection.rollback()
            raise e 