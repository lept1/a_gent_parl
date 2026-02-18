"""
Generic Database Manager for a_gent_parl modules.

This module provides a centralized database management system that can be
used across all modules in the project. It handles generic content operations,
duplicate checking, statistics, and specialized database operations.

This module is completely independent and requires database paths to be provided
as parameters. It does not perform any internal path resolution or configuration loading.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class ContentDatabase:
    """
    Generic database operations for content management across all modules.
    
    Provides centralized database operations including:
    - Generic content tracking (articles, quotes, images, etc.)
    - Configurable duplicate checking and posting status
    - Category and content type statistics
    - Time-based content tracking and filtering
    - Flexible database schema management
    """
    
    def __init__(self, db_path: str, table_name: str = 'ContentHistory'):
        """
        Initialize database connection and create schema if needed.
        
        Args:
            db_path: Full path to the database file
            table_name: Name of the table to use for content tracking
        """
        self.db_path = db_path
        self.table_name = table_name
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Enable foreign keys and set row factory for dict-like access
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Create default schema
        self.create_schema()
    
    def create_schema(self, additional_columns: Optional[Dict[str, str]] = None) -> None:
        """
        Create the content tracking table and indexes if they don't exist.
        
        Args:
            additional_columns: Optional dictionary of additional column definitions
                               Format: {'column_name': 'column_type_and_constraints'}
        """
        # Base schema for generic content tracking
        base_columns = [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "content_title TEXT NOT NULL",
            "content_url TEXT",
            "content_type TEXT",
            "category TEXT",
            "module_name TEXT",
            "post_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "posted INTEGER DEFAULT 1",
            "metadata TEXT"  # JSON for additional module-specific data
        ]
        
        # Add additional columns if provided
        if additional_columns:
            for col_name, col_definition in additional_columns.items():
                base_columns.append(f"{col_name} {col_definition}")
        
        # Create table SQL
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            {', '.join(base_columns)},
            UNIQUE(content_title, content_type, module_name)
        )
        """
        
        # Create indexes for performance optimization
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_title ON {self.table_name}(content_title)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_type ON {self.table_name}(content_type)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_date ON {self.table_name}(post_date)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_posted ON {self.table_name}(posted)",
            f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_module ON {self.table_name}(module_name)"
        ]
        
        try:
            self.cursor.execute(create_table_sql)
            for index_sql in indexes:
                self.cursor.execute(index_sql)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating database schema: {e}")
            raise
    
    def is_content_posted(self, content_title: str, content_type: Optional[str] = None) -> bool:
        """
        Check if content has already been posted.
        
        Args:
            content_title: The title of the content to check
            content_type: Optional content type filter
            
        Returns:
            bool: True if content has been posted, False otherwise
        """
        try:
            if content_type:
                query = f"SELECT COUNT(*) FROM {self.table_name} WHERE content_title = ? AND content_type = ? AND posted = 1"
                result = self.cursor.execute(query, (content_title, content_type)).fetchone()
            else:
                query = f"SELECT COUNT(*) FROM {self.table_name} WHERE content_title = ? AND posted = 1"
                result = self.cursor.execute(query, (content_title,)).fetchone()
            
            return result[0] > 0
        except sqlite3.Error as e:
            print(f"Error checking if content is posted: {e}")
            return True  # Assume posted to avoid duplicates on error
    
    def mark_content_posted(self, 
                          content_title: str, 
                          content_url: Optional[str] = None, 
                          category: Optional[str] = None, 
                          content_type: Optional[str] = None,
                          module_name: Optional[str] = None,
                          **kwargs) -> bool:
        """
        Mark content as posted in the database.
        
        Args:
            content_title: The title of the content
            content_url: The URL of the content (optional)
            category: The content category (optional)
            content_type: Type of content (e.g., 'article', 'quote', 'image')
            module_name: Name of the module posting the content
            **kwargs: Additional metadata to store as JSON
            
        Returns:
            bool: True if successfully marked, False otherwise
        """
        try:
            # Prepare metadata
            metadata = json.dumps(kwargs) if kwargs else None
            
            insert_sql = f"""
            INSERT INTO {self.table_name} 
            (content_title, content_url, content_type, category, module_name, post_date, posted, metadata)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """
            
            current_time = datetime.now().isoformat()
            self.cursor.execute(insert_sql, (
                content_title, content_url, content_type, category, 
                module_name, current_time, metadata
            ))
            self.conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            # Content already exists (UNIQUE constraint)
            print(f"Content '{content_title}' already exists in database")
            return False
        except sqlite3.Error as e:
            print(f"Error marking content as posted: {e}")
            return False
    
    def get_recent_posts(self, days: int = 30, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get content posted in the last N days.
        
        Args:
            days: Number of days to look back
            content_type: Optional filter by content type
            
        Returns:
            List of dictionaries containing content information
        """
        try:
            if content_type:
                query = f"""
                SELECT content_title, content_url, content_type, category, module_name, post_date, metadata
                FROM {self.table_name} 
                WHERE posted = 1 AND content_type = ?
                AND datetime(post_date) >= datetime('now', '-{days} days')
                ORDER BY post_date DESC
                """
                results = self.cursor.execute(query, (content_type,)).fetchall()
            else:
                query = f"""
                SELECT content_title, content_url, content_type, category, module_name, post_date, metadata
                FROM {self.table_name} 
                WHERE posted = 1 
                AND datetime(post_date) >= datetime('now', '-{days} days')
                ORDER BY post_date DESC
                """
                results = self.cursor.execute(query).fetchall()
            
            return [
                {
                    'title': row['content_title'],
                    'url': row['content_url'],
                    'type': row['content_type'],
                    'category': row['category'],
                    'module': row['module_name'],
                    'post_date': row['post_date'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                for row in results
            ]
        except sqlite3.Error as e:
            print(f"Error getting recent posts: {e}")
            return []
    
    def get_category_stats(self, content_type: Optional[str] = None) -> Dict[str, int]:
        """
        Get statistics on posted content by category.
        
        Args:
            content_type: Optional filter by content type
            
        Returns:
            Dictionary with category names as keys and post counts as values
        """
        try:
            if content_type:
                query = f"""
                SELECT category, COUNT(*) as count
                FROM {self.table_name} 
                WHERE posted = 1 AND content_type = ? AND category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
                """
                results = self.cursor.execute(query, (content_type,)).fetchall()
            else:
                query = f"""
                SELECT category, COUNT(*) as count
                FROM {self.table_name} 
                WHERE posted = 1 AND category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
                """
                results = self.cursor.execute(query).fetchall()
            
            return {row['category']: row['count'] for row in results}
        except sqlite3.Error as e:
            print(f"Error getting category stats: {e}")
            return {}
    
    def get_content_by_type(self, content_type: str) -> List[Dict[str, Any]]:
        """
        Get all content of a specific type.
        
        Args:
            content_type: The type of content to retrieve
            
        Returns:
            List of dictionaries containing content information
        """
        try:
            query = f"""
            SELECT content_title, content_url, content_type, category, module_name, post_date, posted, metadata
            FROM {self.table_name} 
            WHERE content_type = ?
            ORDER BY post_date DESC
            """
            
            results = self.cursor.execute(query, (content_type,)).fetchall()
            
            return [
                {
                    'title': row['content_title'],
                    'url': row['content_url'],
                    'type': row['content_type'],
                    'category': row['category'],
                    'module': row['module_name'],
                    'post_date': row['post_date'],
                    'posted': bool(row['posted']),
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                for row in results
            ]
        except sqlite3.Error as e:
            print(f"Error getting content by type: {e}")
            return []
    
    def get_unposted_content(self, 
                           content_type: Optional[str] = None, 
                           category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get content that hasn't been posted yet.
        
        Args:
            content_type: Optional filter by content type
            category: Optional filter by category
            
        Returns:
            List of dictionaries containing unposted content information
        """
        try:
            conditions = ["posted = 0"]
            params = []
            
            if content_type:
                conditions.append("content_type = ?")
                params.append(content_type)
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            query = f"""
            SELECT content_title, content_url, content_type, category, module_name, post_date, metadata
            FROM {self.table_name} 
            WHERE {' AND '.join(conditions)}
            ORDER BY post_date ASC
            """
            
            results = self.cursor.execute(query, params).fetchall()
            
            return [
                {
                    'title': row['content_title'],
                    'url': row['content_url'],
                    'type': row['content_type'],
                    'category': row['category'],
                    'module': row['module_name'],
                    'post_date': row['post_date'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                for row in results
            ]
        except sqlite3.Error as e:
            print(f"Error getting unposted content: {e}")
            return []
    
    def get_random_unposted_content(self, 
                                  content_type: Optional[str] = None,
                                  category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get a random piece of unposted content.
        
        Args:
            content_type: Optional filter by content type
            category: Optional filter by category
            
        Returns:
            Dictionary containing random unposted content information, or None if no content found
        """
        try:
            conditions = ["posted = 0"]
            params = []
            
            if content_type:
                conditions.append("content_type = ?")
                params.append(content_type)
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            query = f"""
            SELECT content_title, content_url, content_type, category, module_name, post_date, metadata
            FROM {self.table_name} 
            WHERE {' AND '.join(conditions)}
            ORDER BY RANDOM()
            LIMIT 1
            """
            
            result = self.cursor.execute(query, params).fetchone()
            
            if result:
                return {
                    'title': result['content_title'],
                    'url': result['content_url'],
                    'type': result['content_type'],
                    'category': result['category'],
                    'module': result['module_name'],
                    'post_date': result['post_date'],
                    'metadata': json.loads(result['metadata']) if result['metadata'] else {}
                }
            
            return None
        except sqlite3.Error as e:
            print(f"Error getting random unposted content: {e}")
            return None
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class QuoteDatabase(ContentDatabase):
    """
    Specialized database operations for quote management.
    
    Extends ContentDatabase to provide quote-specific functionality while
    maintaining compatibility with existing quote_db.sqlite3 schema.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize quote database with compatibility for existing schema.
        
        Args:
            db_path: Full path to the quote database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Enable foreign keys and set row factory for dict-like access
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Check if legacy Quote table exists, if not create it
        self._ensure_quote_schema()
    
    def _ensure_quote_schema(self) -> None:
        """
        Ensure the Quote table exists with the expected schema.
        Creates the table if it doesn't exist.
        """
        try:
            # Check if Quote table exists
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Quote';")
            table_exists = self.cursor.fetchone()
            
            if not table_exists:
                # Create Quote table with legacy schema
                create_quote_table = """
                CREATE TABLE Quote (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author TEXT,
                    category TEXT,
                    quote_text TEXT,
                    posted INTEGER DEFAULT 0
                )
                """
                
                # Create indexes
                create_indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_quote_posted ON Quote(posted)",
                    "CREATE INDEX IF NOT EXISTS idx_quote_category ON Quote(category)",
                    "CREATE INDEX IF NOT EXISTS idx_quote_author ON Quote(author)"
                ]
                
                self.cursor.execute(create_quote_table)
                for index_sql in create_indexes:
                    self.cursor.execute(index_sql)
                self.conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error ensuring quote schema: {e}")
            raise
    
    def get_random_unposted_quote(self, categories: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Get a random unposted quote, optionally excluding certain categories.
        
        Args:
            categories: List of categories to select
            
        Returns:
            Dictionary containing quote information, or None if no quotes found
        """
        try:
            conditions = ["posted = 0"]
            params=[]
            
            if categories:
                category_conditions = ' OR '.join(['category LIKE ?' for _ in categories])
                conditions.append(f"({category_conditions})")
                params.extend([f"%{category}%" for category in categories])
            
            query = f"""
            SELECT *
            FROM Quote 
            WHERE {' AND '.join(conditions)}
            ORDER BY RANDOM()
            LIMIT 1
            """
            
            result = self.cursor.execute(query,params).fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'author': result[1],
                    'category': result[2],
                    'quote_text': result[3],
                    'posted': bool(result[4])
                }
            
            return None
        except sqlite3.Error as e:
            print(f"Error getting random unposted quote: {e}")
            return None
    
    def mark_quote_posted(self, quote_id: int) -> bool:
        """
        Mark a quote as posted by its ID.
        
        Args:
            quote_id: The ID of the quote to mark as posted
            
        Returns:
            bool: True if successfully marked, False otherwise
        """
        try:
            update_sql = "UPDATE Quote SET posted = 1 WHERE id = ?"
            self.cursor.execute(update_sql, (quote_id,))
            self.conn.commit()
            
            # Check if any rows were affected
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error marking quote as posted: {e}")
            return False
    
    def get_quote_by_id(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific quote by its ID.
        
        Args:
            quote_id: The ID of the quote to retrieve
            
        Returns:
            Dictionary containing quote information, or None if not found
        """
        try:
            query = "SELECT id, author, category, quote_text, posted FROM Quote WHERE id = ?"
            result = self.cursor.execute(query, (quote_id,)).fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'author': result[1],
                    'category': result[2],
                    'quote_text': result[3],
                    'posted': bool(result[4])
                }
            
            return None
        except sqlite3.Error as e:
            print(f"Error getting quote by ID: {e}")
            return None
    
    def get_quotes_by_category(self, category: str, posted: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Get quotes by category, optionally filtered by posted status.
        
        Args:
            category: The category to filter by
            posted: Optional filter by posted status (True/False/None for all)
            
        Returns:
            List of dictionaries containing quote information
        """
        try:
            conditions = ["category = ?"]
            params = [category]
            
            if posted is not None:
                conditions.append("posted = ?")
                params.append(1 if posted else 0)
            
            query = f"""
            SELECT id, author, category, quote_text, posted
            FROM Quote 
            WHERE {' AND '.join(conditions)}
            ORDER BY id
            """
            
            results = self.cursor.execute(query, params).fetchall()
            
            return [
                {
                    'id': row[0],
                    'author': row[1],
                    'category': row[2],
                    'quote_text': row[3],
                    'posted': bool(row[4])
                }
                for row in results
            ]
        except sqlite3.Error as e:
            print(f"Error getting quotes by category: {e}")
            return []
    
    def get_quote_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the quote database.
        
        Returns:
            Dictionary containing various statistics about quotes
        """
        try:
            stats = {}
            
            # Total quotes
            result = self.cursor.execute("SELECT COUNT(*) FROM Quote").fetchone()
            stats['total_quotes'] = result[0]
            
            # Posted vs unposted
            result = self.cursor.execute("SELECT COUNT(*) FROM Quote WHERE posted = 1").fetchone()
            stats['posted_quotes'] = result[0]
            stats['unposted_quotes'] = stats['total_quotes'] - stats['posted_quotes']
            
            # Category breakdown
            results = self.cursor.execute("""
                SELECT category, COUNT(*) as count, 
                       SUM(posted) as posted_count,
                       COUNT(*) - SUM(posted) as unposted_count
                FROM Quote 
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """).fetchall()
            
            stats['categories'] = {
                row['category']: {
                    'total': row['count'],
                    'posted': row['posted_count'],
                    'unposted': row['unposted_count']
                }
                for row in results
            }
            
            # Author breakdown (top 10)
            results = self.cursor.execute("""
                SELECT author, COUNT(*) as count
                FROM Quote 
                WHERE author IS NOT NULL
                GROUP BY author
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            
            stats['top_authors'] = {
                row['author']: row['count']
                for row in results
            }
            
            return stats
        except sqlite3.Error as e:
            print(f"Error getting quote statistics: {e}")
            return {}
    
    def migrate_to_content_database(self, content_db: ContentDatabase, module_name: str = 'weekly_quote') -> bool:
        """
        Migrate quotes from the Quote table to a ContentDatabase instance.
        
        Args:
            content_db: ContentDatabase instance to migrate to
            module_name: Name of the module for the migration
            
        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            # Get all quotes
            results = self.cursor.execute("""
                SELECT id, author, category, quote_text, posted
                FROM Quote
            """).fetchall()
            
            migration_count = 0
            
            for row in results:
                # Create content title from quote text (truncated)
                quote_preview = row['quote_text'][:50] + "..." if len(row['quote_text']) > 50 else row['quote_text']
                content_title = f"Quote by {row['author']}: {quote_preview}"
                
                # Prepare metadata
                metadata = {
                    'original_quote_id': row['id'],
                    'author': row['author'],
                    'full_quote_text': row['quote_text']
                }
                
                # Mark as posted in ContentDatabase if it was posted in Quote table
                if row['posted']:
                    success = content_db.mark_content_posted(
                        content_title=content_title,
                        content_type='quote',
                        category=row['category'],
                        module_name=module_name,
                        **metadata
                    )
                    if success:
                        migration_count += 1
                else:
                    # Add as unposted content
                    # Note: ContentDatabase doesn't have a direct method for unposted content
                    # We'll need to insert directly with posted=0
                    insert_sql = f"""
                    INSERT INTO {content_db.table_name} 
                    (content_title, content_type, category, module_name, posted, metadata)
                    VALUES (?, ?, ?, ?, 0, ?)
                    """
                    
                    try:
                        content_db.cursor.execute(insert_sql, (
                            content_title, 'quote', row['category'], 
                            module_name, json.dumps(metadata)
                        ))
                        migration_count += 1
                    except sqlite3.IntegrityError:
                        # Skip duplicates
                        continue
            
            content_db.conn.commit()
            print(f"Successfully migrated {migration_count} quotes to ContentDatabase")
            return True
            
        except sqlite3.Error as e:
            print(f"Error during migration: {e}")
            return False

class NewsDatabase(ContentDatabase):
    """
    Specialized database operations for news management.
    
    Extends ContentDatabase to provide news-specific functionality while
    maintaining compatibility with existing news_db.sqlite3 schema.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize news database with compatibility for existing schema.
        
        Args:
            db_path: Full path to the news database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Enable foreign keys and set row factory for dict-like access
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Check if legacy News table exists, if not create it
        self._ensure_news_schema()

    def _ensure_news_schema(self) -> None:
        """
        Ensure the News table exists with the expected schema.
        Creates the table if it doesn't exist.
        """
        try:
            # Check if News table exists
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='News';")
            table_exists = self.cursor.fetchone()
            
            if not table_exists:
                # Create News table with legacy schema
                create_news_table = """
                CREATE TABLE News (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    url TEXT UNIQUE,
                    source TEXT,
                    published_date TIMESTAMP,
                    posted INTEGER DEFAULT 0
                )
                """
                
                # Create indexes
                create_indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_news_posted ON News(posted)",
                    "CREATE INDEX IF NOT EXISTS idx_news_category ON News(category)",
                    "CREATE INDEX IF NOT EXISTS idx_news_published_date ON News(published_date)"
                ]
                
                self.cursor.execute(create_news_table)
                for index_sql in create_indexes:
                    self.cursor.execute(index_sql)
                self.conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error ensuring news schema: {e}")
            raise

    def mark_news_posted(self, news_id: int) -> bool:
        """
        Mark a news item as posted by its ID.
        
        Args:
            news_id: The ID of the news item to mark as posted
        Returns:
            bool: True if successfully marked, False otherwise
        """
        try:
            update_sql = "UPDATE News SET posted = 1 WHERE id = ?"
            self.cursor.execute(update_sql, (news_id,))
            self.conn.commit()
            
            # Check if any rows were affected
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error marking news as posted: {e}")
            return False