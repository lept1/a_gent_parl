import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


class NerdCuriositiesDB:
    """Database operations for the Weekly Nerd Curiosities module."""
    
    def __init__(self, db_name: str = 'nerd_curiosities.sqlite3'):
        """Initialize database connection and create schema if needed."""
        self.db_name = db_name
        # self.db_path = os.path.realpath(__file__).replace(os.path.basename(__file__), db_name)
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_schema()
    
    def _create_schema(self):
        """Create the ArticleHistory table and indexes if they don't exist."""
        # Create ArticleHistory table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ArticleHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_title TEXT NOT NULL UNIQUE,
            article_url TEXT NOT NULL,
            category TEXT,
            post_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            posted INTEGER DEFAULT 1
        )
        """
        
        # Create indexes for performance optimization
        create_title_index = """
        CREATE INDEX IF NOT EXISTS idx_article_title ON ArticleHistory(article_title)
        """
        
        create_date_index = """
        CREATE INDEX IF NOT EXISTS idx_post_date ON ArticleHistory(post_date)
        """
        
        try:
            self.cursor.execute(create_table_sql)
            self.cursor.execute(create_title_index)
            self.cursor.execute(create_date_index)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating database schema: {e}")
            raise
    
    def is_article_posted(self, article_title: str) -> bool:
        """
        Check if an article has already been posted.
        
        Args:
            article_title: The title of the article to check
            
        Returns:
            bool: True if article has been posted, False otherwise
        """
        try:
            query = "SELECT COUNT(*) FROM ArticleHistory WHERE article_title = ? AND posted = 1"
            result = self.cursor.execute(query, (article_title,)).fetchone()
            return result[0] > 0
        except sqlite3.Error as e:
            print(f"Error checking if article is posted: {e}")
            return True  # Assume posted to avoid duplicates on error
    
    def mark_article_posted(self, article_title: str, article_url: str, category: str = None) -> bool:
        """
        Mark an article as posted in the database.
        
        Args:
            article_title: The title of the article
            article_url: The URL of the article
            category: The Wikipedia category (optional)
            
        Returns:
            bool: True if successfully marked, False otherwise
        """
        try:
            insert_sql = """
            INSERT INTO ArticleHistory (article_title, article_url, category, post_date, posted)
            VALUES (?, ?, ?, ?, 1)
            """
            current_time = datetime.now().isoformat()
            self.cursor.execute(insert_sql, (article_title, article_url, category, current_time))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Article already exists (UNIQUE constraint)
            print(f"Article '{article_title}' already exists in database")
            return False
        except sqlite3.Error as e:
            print(f"Error marking article as posted: {e}")
            return False
    
    def get_recent_posts(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get articles posted in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of dictionaries containing article information
        """
        try:
            query = """
            SELECT article_title, article_url, category, post_date
            FROM ArticleHistory 
            WHERE posted = 1 
            AND datetime(post_date) >= datetime('now', '-{} days')
            ORDER BY post_date DESC
            """.format(days)
            
            results = self.cursor.execute(query).fetchall()
            
            return [
                {
                    'title': row[0],
                    'url': row[1],
                    'category': row[2],
                    'post_date': row[3]
                }
                for row in results
            ]
        except sqlite3.Error as e:
            print(f"Error getting recent posts: {e}")
            return []
    
    def get_category_stats(self) -> Dict[str, int]:
        """
        Get statistics on posted articles by category.
        
        Returns:
            Dictionary with category names as keys and post counts as values
        """
        try:
            query = """
            SELECT category, COUNT(*) as count
            FROM ArticleHistory 
            WHERE posted = 1 AND category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            """
            
            results = self.cursor.execute(query).fetchall()
            return {row[0]: row[1] for row in results}
        except sqlite3.Error as e:
            print(f"Error getting category stats: {e}")
            return {}
    
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