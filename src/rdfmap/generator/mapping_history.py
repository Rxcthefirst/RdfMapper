"""Mapping history database for learning from past mappings.

This module provides persistent storage of mapping decisions and enables
the system to learn from historical successes to improve future mappings.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class MappingRecord:
    """A single mapping decision record."""
    column_name: str
    property_uri: str
    property_label: Optional[str]
    match_type: str
    confidence: float
    user_accepted: bool  # True if user kept it, False if corrected
    correction_to: Optional[str]  # If user changed it, what property?
    ontology_file: str
    data_file: str
    timestamp: str
    matcher_name: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class MappingHistory:
    """Persistent storage and retrieval of mapping decisions."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the mapping history database.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to ~/.rdfmap/mapping_history.db
        """
        if db_path is None:
            # Default location
            home = Path.home()
            rdfmap_dir = home / ".rdfmap"
            rdfmap_dir.mkdir(exist_ok=True)
            db_path = str(rdfmap_dir / "mapping_history.db")

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Mapping decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mapping_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                column_name TEXT NOT NULL,
                property_uri TEXT NOT NULL,
                property_label TEXT,
                match_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                user_accepted INTEGER NOT NULL,
                correction_to TEXT,
                ontology_file TEXT NOT NULL,
                data_file TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                matcher_name TEXT NOT NULL
            )
        """)

        # Create indexes for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_column_name 
            ON mapping_decisions(column_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_uri 
            ON mapping_decisions(property_uri)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_accepted 
            ON mapping_decisions(user_accepted)
        """)

        # Matcher performance stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matcher_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matcher_name TEXT NOT NULL,
                total_matches INTEGER DEFAULT 0,
                accepted_matches INTEGER DEFAULT 0,
                rejected_matches INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0.0,
                last_updated TEXT NOT NULL
            )
        """)

        self.conn.commit()

    def record_mapping(self, record: MappingRecord):
        """Record a mapping decision.

        Args:
            record: MappingRecord to store
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO mapping_decisions 
            (column_name, property_uri, property_label, match_type, confidence,
             user_accepted, correction_to, ontology_file, data_file, timestamp, matcher_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.column_name,
            record.property_uri,
            record.property_label,
            record.match_type,
            record.confidence,
            1 if record.user_accepted else 0,
            record.correction_to,
            record.ontology_file,
            record.data_file,
            record.timestamp,
            record.matcher_name
        ))
        self.conn.commit()

        # Update matcher stats
        self._update_matcher_stats(record.matcher_name, record.user_accepted, record.confidence)

    def _update_matcher_stats(self, matcher_name: str, accepted: bool, confidence: float):
        """Update statistics for a matcher.

        Args:
            matcher_name: Name of the matcher
            accepted: Whether the match was accepted
            confidence: Confidence score of the match
        """
        cursor = self.conn.cursor()

        # Check if matcher exists
        cursor.execute("SELECT * FROM matcher_stats WHERE matcher_name = ?", (matcher_name,))
        existing = cursor.fetchone()

        if existing:
            # Update existing
            total = existing['total_matches'] + 1
            accepted_count = existing['accepted_matches'] + (1 if accepted else 0)
            rejected_count = existing['rejected_matches'] + (0 if accepted else 1)

            # Calculate new average confidence
            old_avg = existing['avg_confidence']
            new_avg = ((old_avg * existing['total_matches']) + confidence) / total

            cursor.execute("""
                UPDATE matcher_stats 
                SET total_matches = ?,
                    accepted_matches = ?,
                    rejected_matches = ?,
                    avg_confidence = ?,
                    last_updated = ?
                WHERE matcher_name = ?
            """, (total, accepted_count, rejected_count, new_avg,
                  datetime.now().isoformat(), matcher_name))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO matcher_stats 
                (matcher_name, total_matches, accepted_matches, rejected_matches, 
                 avg_confidence, last_updated)
                VALUES (?, 1, ?, ?, ?, ?)
            """, (matcher_name, 1 if accepted else 0, 0 if accepted else 1,
                  confidence, datetime.now().isoformat()))

        self.conn.commit()

    def find_similar_mappings(
        self,
        column_name: str,
        limit: int = 5,
        accepted_only: bool = True
    ) -> List[Dict]:
        """Find similar column mappings from history.

        Args:
            column_name: Column name to search for
            limit: Maximum number of results
            accepted_only: Only return user-accepted mappings

        Returns:
            List of similar mapping records
        """
        cursor = self.conn.cursor()

        # Clean column name for matching
        clean_name = column_name.lower().replace('_', '').replace(' ', '')

        # Build query
        query = """
            SELECT * FROM mapping_decisions 
            WHERE LOWER(REPLACE(REPLACE(column_name, '_', ''), ' ', '')) = ?
        """
        params = [clean_name]

        if accepted_only:
            query += " AND user_accepted = 1"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_property_success_rate(self, property_uri: str) -> float:
        """Get the success rate for a specific property.

        Args:
            property_uri: URI of the property

        Returns:
            Success rate (0-1)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(user_accepted) as accepted
            FROM mapping_decisions
            WHERE property_uri = ?
        """, (property_uri,))

        row = cursor.fetchone()
        if row['total'] == 0:
            return 0.5  # No history, neutral

        return row['accepted'] / row['total']

    def get_matcher_performance(self, matcher_name: str) -> Optional[Dict]:
        """Get performance statistics for a matcher.

        Args:
            matcher_name: Name of the matcher

        Returns:
            Dictionary with performance stats or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM matcher_stats WHERE matcher_name = ?", (matcher_name,))
        row = cursor.fetchone()

        if row:
            stats = dict(row)
            stats['success_rate'] = (
                stats['accepted_matches'] / stats['total_matches']
                if stats['total_matches'] > 0 else 0
            )
            return stats
        return None

    def get_all_matcher_stats(self) -> List[Dict]:
        """Get performance statistics for all matchers.

        Returns:
            List of matcher performance dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM matcher_stats 
            ORDER BY total_matches DESC
        """)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            stats = dict(row)
            stats['success_rate'] = (
                stats['accepted_matches'] / stats['total_matches']
                if stats['total_matches'] > 0 else 0
            )
            results.append(stats)

        return results

    def get_total_mappings(self) -> int:
        """Get total number of mappings recorded.

        Returns:
            Total count of mapping records
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM mapping_decisions")
        return cursor.fetchone()['count']

    def get_success_rate(self) -> float:
        """Get overall mapping success rate.

        Returns:
            Success rate (0-1)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(user_accepted) as accepted
            FROM mapping_decisions
        """)
        row = cursor.fetchone()

        if row['total'] == 0:
            return 0.0

        return row['accepted'] / row['total']

    def get_recent_mappings(self, limit: int = 10) -> List[Dict]:
        """Get most recent mapping decisions.

        Args:
            limit: Maximum number of results

        Returns:
            List of recent mapping records
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM mapping_decisions 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def export_to_json(self, output_file: str):
        """Export mapping history to JSON file.

        Args:
            output_file: Path to output JSON file
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM mapping_decisions")
        mappings = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM matcher_stats")
        stats = [dict(row) for row in cursor.fetchall()]

        data = {
            'mappings': mappings,
            'matcher_stats': stats,
            'exported_at': datetime.now().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

    def clear_history(self):
        """Clear all mapping history (use with caution!)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM mapping_decisions")
        cursor.execute("DELETE FROM matcher_stats")
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

