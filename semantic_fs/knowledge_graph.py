import os
import re
import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple, Set

class AssociativeKnowledgeGraph:
    """
    Phase 2: Associative Knowledge Graph.
    Extracts entities (people, dates, tasks, topics, projects, files)
    and constructs an associative entity-relationship graph in embedded SQLite.
    Enables deep relational queries: "Who did I talk to about the physics exam last Tuesday?"
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "aos_knowledge_graph.db")
        else:
            self.db_path = db_path

        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE COLLATE NOCASE,
                    entity_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER,
                    target_id INTEGER,
                    relation_type TEXT,
                    context TEXT,
                    confidence REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE,
                    UNIQUE(source_id, target_id, relation_type)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities (name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations (source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations (target_id)")
            conn.commit()

    def add_entity(self, name: str, entity_type: str = "TOPIC") -> int:
        """Adds or retrieves an entity by name."""
        name = name.strip()
        if not name:
            return -1

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO entities (name, entity_type) VALUES (?, ?)", (name, entity_type.upper()))
            cursor.execute("SELECT id FROM entities WHERE name = ? COLLATE NOCASE", (name,))
            row = cursor.fetchone()
            conn.commit()
            return row["id"] if row else -1

    def add_relation(
        self,
        source_name: str,
        target_name: str,
        relation_type: str = "RELATE_TO",
        source_type: str = "TOPIC",
        target_type: str = "TOPIC",
        context: str = ""
    ) -> bool:
        """Creates an associative directed link between two entities."""
        src_id = self.add_entity(source_name, source_type)
        tgt_id = self.add_entity(target_name, target_type)

        if src_id == -1 or tgt_id == -1 or src_id == tgt_id:
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO relations (source_id, target_id, relation_type, context)
                VALUES (?, ?, ?, ?)
            """, (src_id, tgt_id, relation_type.upper(), context))
            conn.commit()
            return True

    def extract_and_ingest(self, text: str, source_context: str = "") -> List[Tuple[str, str, str]]:
        """
        Extracts entities and relational triplets from unstructured text
        (e.g., conversation logs, notes, documents).
        Returns list of extracted triplets (Subject, Relation, Object).
        """
        triplets = []

        # 1. Person names & interactions
        # e.g., "Send a message to Alice saying I will be late", "Had a meeting with Bob regarding Physics"
        talk_matches = re.finditer(
            r"(?:message|talk(?:ed)?\s+to|met\s+with|meet(?:ing)?\s+with|email(?:ed)?|spoke\s+to)\s+([A-Z][a-zA-Z]+)(?:\s+(?:about|regarding|saying|for)\s+([^\.,;\n]+))?",
            text, re.IGNORECASE
        )
        for m in talk_matches:
            person = m.group(1).capitalize()
            topic = m.group(2)
            if topic:
                topic = topic.strip()
                self.add_relation(person, topic, "DISCUSSED", source_type="PERSON", target_type="TOPIC", context=text)
                triplets.append((person, "DISCUSSED", topic))
            else:
                self.add_entity(person, "PERSON")

        # 2. File references
        file_matches = re.finditer(r"([/\\][a-zA-Z0-9_\-/\\]+\.[a-zA-Z0-9]+)", text)
        for m in file_matches:
            filepath = m.group(1)
            self.add_entity(filepath, "FILE")
            if source_context:
                self.add_relation(filepath, source_context, "ASSOCIATED_WITH", source_type="FILE", target_type="TOPIC")
                triplets.append((filepath, "ASSOCIATED_WITH", source_context))

        # 3. Dates & days
        date_matches = re.finditer(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|today|yesterday|tomorrow|\d{4}-\d{2}-\d{2})\b", text, re.IGNORECASE)
        for m in date_matches:
            date_str = m.group(1).capitalize()
            self.add_entity(date_str, "DATE")
            for sub, rel, obj in list(triplets):
                self.add_relation(sub, date_str, "OCCURRED_ON", source_type="PERSON", target_type="DATE")

        # 4. Exams / Projects / Tasks
        project_matches = re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Exam|Project|Assignment|Homework|Meeting))\b", text, re.IGNORECASE)
        for m in project_matches:
            proj = m.group(1).title()
            self.add_entity(proj, "PROJECT")

        return triplets

    def query_associations(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Retrieves all 1-hop and 2-hop associations connected to an entity.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e1.name AS source, e1.entity_type AS source_type,
                       r.relation_type, r.context,
                       e2.name AS target, e2.entity_type AS target_type
                FROM relations r
                JOIN entities e1 ON r.source_id = e1.id
                JOIN entities e2 ON r.target_id = e2.id
                WHERE e1.name = ? COLLATE NOCASE OR e2.name = ? COLLATE NOCASE
            """, (entity_name, entity_name))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "source": row["source"],
                    "source_type": row["source_type"],
                    "relation": row["relation_type"],
                    "target": row["target"],
                    "target_type": row["target_type"],
                    "context": row["context"]
                })
            return results

    def answer_associative_query(self, query: str) -> str:
        """
        Answers natural language queries like:
        'Who did I talk to about physics exam?'
        """
        q_lower = query.lower()

        # Identify mentioned entities
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, entity_type FROM entities")
            entities = cursor.fetchall()

        matched_entities = []
        for ent in entities:
            if ent["name"].lower() in q_lower:
                matched_entities.append(ent["name"])

        if not matched_entities:
            # Fallback search across relations
            tokens = [t for t in re.findall(r"\b\w{4,}\b", q_lower) if t not in ["about", "talk", "with", "what", "where", "last"]]
            for token in tokens:
                for ent in entities:
                    if token in ent["name"].lower():
                        matched_entities.append(ent["name"])

        matched_entities = list(set(matched_entities))
        if not matched_entities:
            return "No matching entities found in associative knowledge graph."

        answers = []
        for ent in matched_entities:
            associations = self.query_associations(ent)
            for assoc in associations:
                answers.append(f"• {assoc['source']} [{assoc['source_type']}] --({assoc['relation']})--> {assoc['target']} [{assoc['target_type']}]")

        if not answers:
            return f"Found entity '{', '.join(matched_entities)}' but no direct relations recorded yet."

        return "Knowledge Graph Associations:\n" + "\n".join(answers)

    def get_graph_snapshot(self, limit: int = 50) -> Dict[str, Any]:
        """Returns nodes and edges formatted for visualization."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, entity_type FROM entities LIMIT ?", (limit,))
            nodes = [{"id": row["id"], "name": row["name"], "type": row["entity_type"]} for row in cursor.fetchall()]

            cursor.execute("""
                SELECT r.id, e1.name as source, e2.name as target, r.relation_type, r.context
                FROM relations r
                JOIN entities e1 ON r.source_id = e1.id
                JOIN entities e2 ON r.target_id = e2.id
                LIMIT ?
            """, (limit,))
            edges = [{
                "id": row["id"],
                "source": row["source"],
                "target": row["target"],
                "relation": row["relation_type"],
                "context": row["context"]
            } for row in cursor.fetchall()]

        return {"nodes": nodes, "edges": edges}
