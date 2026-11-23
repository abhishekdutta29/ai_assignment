"""
KnowledgeLens - Module 1: Knowledge Base (TripleStore, KnowledgeGraph, EntityIndex)
Pure Symbolic representation and explainable graph algorithms without third-party graph/NLP libraries.
"""

import json
from typing import List, Dict, Set, Tuple, Any, Optional
from collections import deque
from src.extractor import Triple

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes the edit distance (Levenshtein distance) between two strings.
    Pure standard library implementation using dynamic programming.
    Time Complexity: O(len(s1) * len(s2))
    Space Complexity: O(min(len(s1), len(s2)))
    """
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    # Use single row optimization
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_

    return distances[-1]


def string_similarity(s1: str, s2: str) -> float:
    """Calculates normalized similarity score between 0.0 and 1.0 based on Levenshtein distance."""
    s1_clean = s1.lower().strip()
    s2_clean = s2.lower().strip()
    if s1_clean == s2_clean:
        return 1.0
    max_len = max(len(s1_clean), len(s2_clean))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1_clean, s2_clean)
    return max(0.0, 1.0 - (dist / max_len))


class EntityIndex:
    """
    Symbolic Entity Index maintaining canonical names, category annotations, 
    and alias dictionaries for deterministic entity linking.
    """
    def __init__(self):
        self.canonical_entities: Set[str] = set()
        self.entity_categories: Dict[str, str] = {}
        # Alias map: lowercase alias -> canonical entity name
        self.alias_map: Dict[str, str] = {}
        self._init_default_aliases()

    def _init_default_aliases(self):
        """Pre-seeds domain aliases and acronyms for the university handbook."""
        defaults = {
            # Acronyms & Short forms
            "ai": "AI201",
            "artificial intelligence": "AI201",
            "ml": "AI301",
            "machine learning": "AI301",
            "dl": "AI401",
            "deep learning": "AI401",
            "nlp": "AI305",
            "natural language processing": "AI305",
            "cv": "AI410",
            "computer vision": "AI410",
            "dsa": "CS102",
            "data structures": "CS102",
            "data structures and algorithms": "CS102",
            "oop": "CS205",
            "object oriented programming": "CS205",
            "dbms": "CS210",
            "databases": "CS210",
            "database management systems": "CS210",
            "os": "CS301",
            "operating systems": "CS301",
            "algo": "CS320",
            "algorithms": "CS320",
            "design and analysis of algorithms": "CS320",
            "se": "SE201",
            "software engineering": "SE201",
            "intro to programming": "CS101",
            "capstone": "AI499",
            "capstone project": "AI499",
            "linear algebra": "MAT101",
            "calculus": "MAT101",
            "probability": "MAT202",
            "statistics": "MAT202",
            "probability and statistics": "MAT202",
            
            # Instructors
            "turing": "Prof. Alan Turing",
            "alan turing": "Prof. Alan Turing",
            "lovelace": "Dr. Ada Lovelace",
            "ada lovelace": "Dr. Ada Lovelace",
            "hinton": "Prof. Geoffrey Hinton",
            "geoffrey hinton": "Prof. Geoffrey Hinton",
            "lecun": "Dr. Yann LeCun",
            "yann lecun": "Dr. Yann LeCun",
            "von neumann": "Prof. John von Neumann",
            "john von neumann": "Prof. John von Neumann",
            "shannon": "Dr. Claude Shannon",
            "claude shannon": "Dr. Claude Shannon",
            "gauss": "Prof. Carl Gauss",
            "carl gauss": "Prof. Carl Gauss",
            "knuth": "Dr. Donald Knuth",
            "donald knuth": "Dr. Donald Knuth",
            "chomsky": "Dr. Noam Chomsky",
            "noam chomsky": "Dr. Noam Chomsky",
            "hamilton": "Prof. Margaret Hamilton",
            "margaret hamilton": "Prof. Margaret Hamilton",
            "hopper": "Dr. Grace Hopper",
            "grace hopper": "Dr. Grace Hopper",
            "torvalds": "Prof. Linus Torvalds",
            "linus torvalds": "Prof. Linus Torvalds",
            "codd": "Dr. Edgar Codd",
            "edgar codd": "Dr. Edgar Codd",
            "fei-fei li": "Dr. Fei-Fei Li",
            "feifei li": "Dr. Fei-Fei Li",
            
            # Departments
            "cs department": "Department of Computer Science",
            "cs dept": "Department of Computer Science",
            "ai department": "Department of Artificial Intelligence",
            "ai dept": "Department of Artificial Intelligence",
            "math department": "Department of Mathematics",
            "math dept": "Department of Mathematics",
            "se department": "Department of Software Engineering",
            "se dept": "Department of Software Engineering",

            # Degrees
            "bsc ai": "Bachelor of Science in Artificial Intelligence",
            "bsc cs": "Bachelor of Science in Computer Science",
            "bs ai": "Bachelor of Science in Artificial Intelligence",
            "bs cs": "Bachelor of Science in Computer Science",
            "bsc in artificial intelligence": "Bachelor of Science in Artificial Intelligence",
            "bsc in computer science": "Bachelor of Science in Computer Science",

            # Policies
            "attendance": "attendance requirement",
            "pass mark": "pass mark",
            "probation": "Academic probation",
            "dean's list": "Dean's Honour List",
            "deans list": "Dean's Honour List",
            "course load": "course load",
            "max load": "maximum course load",
            "min load": "minimum course load"
        }
        for alias, canonical in defaults.items():
            self.alias_map[alias.lower()] = canonical

    def register_entity(self, name: str, category: str = "General"):
        """Registers a canonical entity name and attempts category classification."""
        clean_name = name.strip()
        if not clean_name:
            return
        self.canonical_entities.add(clean_name)
        if clean_name not in self.entity_categories or self.entity_categories[clean_name] == "General":
            self.entity_categories[clean_name] = category

        # Register self-identity lowercase alias (do not overwrite if already a Course code)
        if clean_name.lower() not in self.alias_map or self.entity_categories.get(self.alias_map[clean_name.lower()]) != "Course":
            self.alias_map[clean_name.lower()] = clean_name

        # For instructors with prefix like Dr. or Prof., register name without prefix
        for prefix in ["Prof. ", "Dr. ", "Mr. ", "Ms. "]:
            if clean_name.startswith(prefix):
                bare = clean_name[len(prefix):].strip()
                self.alias_map[bare.lower()] = clean_name

    def register_course(self, code: str, title: str):
        """Cross-registers course code and course title as mutual aliases."""
        clean_code = code.strip()
        clean_title = title.strip()
        self.register_entity(clean_code, "Course")
        self.register_entity(clean_title, "CourseTitle")
        self.alias_map[clean_code.lower()] = clean_code
        self.alias_map[clean_title.lower()] = clean_code
        self.alias_map[clean_title.lower() + " course"] = clean_code

    def resolve_entity(self, query_phrase: str, fuzzy: bool = True, threshold: float = 0.65) -> Optional[Tuple[str, float, str]]:
        """
        Symbolic Entity Linking:
        1. Exact match against canonical entities
        2. Exact match against alias map
        3. Fuzzy match using Levenshtein distance if enabled
        Returns (canonical_name, confidence, method) or None.
        """
        phrase = query_phrase.strip().lower()
        if not phrase:
            return None

        # 1. Exact match in alias dictionary (resolves titles to codes, e.g. "deep learning" -> "AI401")
        if phrase in self.alias_map:
            canonical = self.alias_map[phrase]
            return (canonical, 1.0, "EXACT_ALIAS")

        # 2. Exact match in canonical entities
        for entity in self.canonical_entities:
            if phrase == entity.lower():
                # If this entity has a course code mapping in alias_map, use it
                target = self.alias_map.get(phrase, entity)
                return (target, 1.0, "EXACT_CANONICAL")

        # 3. Check significant substring containment (avoiding generic stop words)
        generic_words = {"school", "department", "course", "degree", "university", "program", "programme", "law school"}
        if phrase not in generic_words:
            for entity in self.canonical_entities:
                e_lower = entity.lower()
                if phrase in e_lower and len(phrase) >= 5 and (len(phrase) / max(1, len(e_lower))) >= 0.55:
                    return (entity, 0.9, "SUBSTRING_MATCH")

        if not fuzzy:
            return None

        # 3. Fuzzy Levenshtein matching across canonical entities and aliases
        best_candidate = None
        best_score = 0.0
        best_method = "FUZZY_LEVENSHTEIN"

        # Check against canonical entities
        for entity in self.canonical_entities:
            score = string_similarity(phrase, entity)
            if score > best_score:
                best_score = score
                best_candidate = entity

        # Check against alias keys
        for alias_key, target in self.alias_map.items():
            score = string_similarity(phrase, alias_key)
            if score > best_score:
                best_score = score
                best_candidate = target

        if best_candidate and best_score >= threshold:
            return (best_candidate, round(best_score, 3), best_method)

        return None


class TripleStore:
    """
    In-memory symbolic triple store indexed by subject, predicate, object, and (subject, predicate).
    Offers O(1) indexed lookups for fact queries.
    """
    def __init__(self):
        self.triples: List[Triple] = []
        self._by_subj: Dict[str, List[Triple]] = {}
        self._by_pred: Dict[str, List[Triple]] = {}
        self._by_obj: Dict[str, List[Triple]] = {}
        self._by_subj_pred: Dict[Tuple[str, str], List[Triple]] = {}

    def add(self, triple: Triple):
        self.triples.append(triple)
        s_k = triple.subject.lower()
        p_k = triple.predicate.lower()
        o_k = triple.object.lower()

        self._by_subj.setdefault(s_k, []).append(triple)
        self._by_pred.setdefault(p_k, []).append(triple)
        self._by_obj.setdefault(o_k, []).append(triple)
        self._by_subj_pred.setdefault((s_k, p_k), []).append(triple)

    def find(self, subject: Optional[str] = None, predicate: Optional[str] = None, obj: Optional[str] = None) -> List[Triple]:
        """Queries triples with any combination of subject, predicate, and object constraints."""
        s_k = subject.lower() if subject else None
        p_k = predicate.lower() if predicate else None
        o_k = obj.lower() if obj else None

        results = []
        if s_k and p_k and o_k:
            candidates = self._by_subj_pred.get((s_k, p_k), [])
            results = [t for t in candidates if t.object.lower() == o_k]
        elif s_k and p_k:
            results = list(self._by_subj_pred.get((s_k, p_k), []))
        elif s_k:
            res = self._by_subj.get(s_k, [])
            if o_k:
                res = [t for t in res if t.object.lower() == o_k]
            results = list(res)
        elif p_k:
            res = self._by_pred.get(p_k, [])
            if o_k:
                res = [t for t in res if t.object.lower() == o_k]
            results = list(res)
        elif o_k:
            results = list(self._by_obj.get(o_k, []))
        else:
            results = list(self.triples)

        # If no results found with subject, check if subject is a Course Title mapped via has_title
        if not results and s_k and p_k:
            title_matches = [t for t in self._by_pred.get("has_title", []) if t.object.lower() == s_k]
            if title_matches:
                code_subj = title_matches[0].subject.lower()
                results = list(self._by_subj_pred.get((code_subj, p_k), []))

        return results

    def all_predicates(self) -> List[str]:
        return sorted(list({t.predicate for t in self.triples}))

    def all_subjects(self) -> List[str]:
        return sorted(list({t.subject for t in self.triples}))

    def count(self) -> int:
        return len(self.triples)


class KnowledgeGraph:
    """
    Explicit Symbolic Knowledge Graph with nodes and directed labelled edges.
    Implements explainable graph algorithms: BFS/DFS traversal, path reconstruction, 
    and transitive prerequisite chain resolution with Big-O complexity tracking.
    """
    def __init__(self):
        # node_id -> node_info dict
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # node_id -> list of (neighbor_id, relation_label, triple)
        self.adj: Dict[str, List[Tuple[str, str, Triple]]] = {}
        # reverse adjacency for reachability/predecessor traversal
        self.rev_adj: Dict[str, List[Tuple[str, str, Triple]]] = {}

        # title_to_code map for seamless course title -> code resolution
        self.title_to_code: Dict[str, str] = {}

    def add_node(self, node_id: str, label: str, category: str = "General"):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "label": label,
                "category": category
            }
            self.adj[node_id] = []
            self.rev_adj[node_id] = []

    def add_edge(self, source: str, target: str, label: str, triple: Triple):
        self.add_node(source, source)
        self.add_node(target, target)
        self.adj[source].append((target, label, triple))
        self.rev_adj[target].append((source, label, triple))
        if label.lower() == "has_title":
            self.title_to_code[target.lower()] = source

    def get_neighbors(self, node: str, relation: Optional[str] = None) -> List[Tuple[str, str, Triple]]:
        if node not in self.adj:
            return []
        if relation:
            return [edge for edge in self.adj[node] if edge[1].lower() == relation.lower()]
        return self.adj[node]

    def get_predecessors(self, node: str, relation: Optional[str] = None) -> List[Tuple[str, str, Triple]]:
        if node not in self.rev_adj:
            return []
        if relation:
            return [edge for edge in self.rev_adj[node] if edge[1].lower() == relation.lower()]
        return self.rev_adj[node]

    def bfs_shortest_path(self, start_node: str, end_node: str, allowed_relations: Optional[Set[str]] = None) -> Optional[List[Tuple[str, str, str, Triple]]]:
        """
        Finds the shortest directed path from start_node to end_node using BFS.
        Time Complexity: O(V + E)
        Space Complexity: O(V)
        Returns: list of (u, relation, v, triple) or None.
        """
        if start_node not in self.nodes or end_node not in self.nodes:
            return None
        if start_node == end_node:
            return []

        visited: Set[str] = {start_node}
        # queue elements: (current_node, path_of_edges)
        queue: deque = deque([(start_node, [])])

        while queue:
            curr, path = queue.popleft()
            if curr == end_node:
                return path

            for neighbor, rel, triple in self.adj.get(curr, []):
                if allowed_relations and rel.lower() not in allowed_relations:
                    continue
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_edge = (curr, rel, neighbor, triple)
                    queue.append((neighbor, path + [new_edge]))

        return None

    def find_transitive_dependencies(self, start_node: str, relation: str = "prerequisite") -> Tuple[List[str], List[Tuple[str, str, str, Triple]], List[str]]:
        """
        Traverses all transitive outgoing dependencies using DFS/BFS.
        e.g., Course -> prerequisite -> Course2 -> prerequisite -> Course3.
        Returns: (ordered_nodes, traversed_edges, traversal_steps_explanation)
        Time Complexity: O(V + E)
        """
        ordered_deps: List[str] = []
        traversed_edges: List[Tuple[str, str, str, Triple]] = []
        explanation_steps: List[str] = []

        # If node is a course title, resolve to course code
        root = self.title_to_code.get(start_node.lower(), start_node)
        if root not in self.nodes:
            for nid in self.nodes:
                if root.lower() == nid.lower():
                    root = nid
                    break

        visited: Set[str] = set()
        queue: deque = deque([root])

        explanation_steps.append(f"Initiated dependency traversal from root node '{root}' along relation '{relation}'.")

        while queue:
            curr = queue.popleft()
            # Find all outgoing edges with given relation
            edges = self.get_neighbors(curr, relation)
            if not edges:
                continue

            for target, rel, triple in edges:
                edge_tuple = (curr, rel, target, triple)
                if target not in visited:
                    visited.add(target)
                    ordered_deps.append(target)
                    traversed_edges.append(edge_tuple)
                    explanation_steps.append(f"Traversed {curr} --[{rel}]--> {target} (Source line {triple.source_line}: '{triple.raw_text}')")
                    queue.append(target)

        return ordered_deps, traversed_edges, explanation_steps

    def check_reachability(self, start_node: str, end_node: str, relation: str = "prerequisite") -> Tuple[bool, Optional[List[Tuple[str, str, str, Triple]]], str]:
        """
        Determines whether one node depends on another via transitive relation edges.
        Answers: 'Is Course A required before Course B?' or 'Is Course B reachable from A?'
        Checks both forward path (A requires ... requires B) and reverse path (B requires ... requires A).
        """
        # Resolve titles to codes if applicable
        s_node = self.title_to_code.get(start_node.lower(), start_node)
        e_node = self.title_to_code.get(end_node.lower(), end_node)

        if s_node not in self.nodes or e_node not in self.nodes:
            return False, None, f"One or both entities ('{start_node}', '{end_node}') do not exist in the graph."

        # Forward path: s_node -> ... -> e_node
        path_fwd = self.bfs_shortest_path(s_node, e_node, allowed_relations={relation.lower()})
        if path_fwd is not None:
            hops = len(path_fwd)
            reason = f"Yes, '{start_node}' transitively requires '{end_node}' in {hops} dependency hop(s)."
            return True, path_fwd, reason

        # Reverse path: e_node -> ... -> s_node (meaning e_node requires s_node)
        path_rev = self.bfs_shortest_path(e_node, s_node, allowed_relations={relation.lower()})
        if path_rev is not None:
            hops = len(path_rev)
            reason = f"Yes, '{start_node}' is a required prerequisite before '{end_node}' (chain length: {hops} hop(s))."
            return True, path_rev, reason

        return False, None, f"No prerequisite or dependency path exists between '{start_node}' and '{end_node}'."

    def to_visjs_graph(self) -> Dict[str, Any]:
        """Converts graph into Vis.js / D3 compatible JSON data structure."""
        color_map = {
            "Course": "#3b82f6",       # Blue
            "Instructor": "#10b981",   # Green
            "Department": "#8b5cf6",   # Purple
            "Semester": "#f59e0b",     # Amber
            "School": "#ec4899",       # Pink
            "Assessment": "#ef4444",   # Red
            "General": "#64748b"       # Gray
        }

        vis_nodes = []
        for nid, info in self.nodes.items():
            cat = info.get("category", "General")
            vis_nodes.append({
                "id": nid,
                "label": info.get("label", nid),
                "title": f"{nid} ({cat})",
                "color": color_map.get(cat, "#64748b"),
                "shape": "box" if cat == "Course" else "ellipse"
            })

        vis_edges = []
        edge_id = 0
        for src, edges in self.adj.items():
            for target, label, _ in edges:
                edge_id += 1
                vis_edges.append({
                    "id": f"e{edge_id}",
                    "from": src,
                    "to": target,
                    "label": label,
                    "arrows": "to",
                    "font": {"align": "middle", "size": 10}
                })

        return {"nodes": vis_nodes, "edges": vis_edges}


class KnowledgeBase:
    """
    Integrated Symbolic Knowledge Base combining TripleStore, KnowledgeGraph, 
    and EntityIndex. Supports JSON serialization/deserialization.
    """
    def __init__(self):
        self.triple_store = TripleStore()
        self.graph = KnowledgeGraph()
        self.entity_index = EntityIndex()
        self.metadata: Dict[str, Any] = {}

    def populate(self, extraction_result: Dict[str, Any]):
        """Populates TripleStore, KnowledgeGraph, and EntityIndex from extraction output."""
        self.triple_store = TripleStore()
        self.graph = KnowledgeGraph()
        self.entity_index = EntityIndex()
        self.metadata = {
            "total_sentences": extraction_result.get("total_sentences", 0),
            "parsed_sentences_count": extraction_result.get("parsed_sentences_count", 0),
            "coverage_percentage": extraction_result.get("coverage_percentage", 0),
            "rule_fire_counts": extraction_result.get("rule_fire_counts", {}),
            "unparsed_sentences": extraction_result.get("unparsed_sentences", [])
        }

        for triple in extraction_result.get("triples", []):
            self.triple_store.add(triple)

            # Register entities and categorize
            subj_cat = self._infer_category(triple.subject, triple.predicate, is_subject=True)
            obj_cat = self._infer_category(triple.object, triple.predicate, is_subject=False)

            self.entity_index.register_entity(triple.subject, subj_cat)
            self.entity_index.register_entity(triple.object, obj_cat)

            if triple.predicate == "has_title":
                self.entity_index.register_course(triple.subject, triple.object)

            # Build Knowledge Graph edge
            self.graph.add_node(triple.subject, triple.subject, subj_cat)
            self.graph.add_node(triple.object, triple.object, obj_cat)
            self.graph.add_edge(triple.subject, triple.object, triple.predicate, triple)

    def _infer_category(self, entity_str: str, predicate: str, is_subject: bool) -> str:
        """Assigns symbolic category labels for graph visualization."""
        if any(prefix in entity_str for prefix in ["Prof.", "Dr.", "Mr.", "Ms."]) or predicate in ["teaches", "taught_by"]:
            return "Instructor" if not (is_subject and predicate == "taught_by") else "Course"
        if predicate == "prerequisite" or predicate in ["credits", "has_title", "offered_in"]:
            return "Course"
        if "Semester" in entity_str:
            return "Semester"
        if "Department" in entity_str:
            return "Department"
        if "School" in entity_str:
            return "School"
        if "Exam" in entity_str or "Quiz" in entity_str or "Project" in entity_str or predicate == "assessment_weight":
            return "Assessment"
        return "General"

    def to_json(self) -> str:
        """Serializes the entire Knowledge Base to JSON."""
        data = {
            "metadata": self.metadata,
            "triples": [t.to_dict() for t in self.triple_store.triples],
            "entities": list(self.entity_index.canonical_entities),
            "categories": self.entity_index.entity_categories,
            "aliases": self.entity_index.alias_map
        }
        return json.dumps(data, indent=2)

    def load_from_json(self, json_str: str):
        """Deserializes Knowledge Base from JSON."""
        data = json.loads(json_str)
        self.triple_store = TripleStore()
        self.graph = KnowledgeGraph()
        self.entity_index = EntityIndex()
        self.metadata = data.get("metadata", {})

        for t_dict in data.get("triples", []):
            t = Triple(
                subject=t_dict["subject"],
                predicate=t_dict["predicate"],
                obj=t_dict["object"],
                source_line=t_dict["source_line"],
                rule_id=t_dict["rule_id"],
                raw_text=t_dict["raw_text"]
            )
            self.triple_store.add(t)
            subj_cat = data.get("categories", {}).get(t.subject, "General")
            obj_cat = data.get("categories", {}).get(t.object, "General")

            self.entity_index.register_entity(t.subject, subj_cat)
            self.entity_index.register_entity(t.object, obj_cat)
            self.graph.add_edge(t.subject, t.object, t.predicate, t)

        for alias, canonical in data.get("aliases", {}).items():
            self.entity_index.alias_map[alias.lower()] = canonical
