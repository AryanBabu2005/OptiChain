"""
SQLite Database and Persistence Layer for OptiChain.
Stores optimization models, scenarios, cost parameters, and experiment results.
Provides complete CRUD support: Save, Load, Duplicate, Rename, Delete.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_FILE_PATH = "data/optichain.db"

class OptiChainDatabase:
    def __init__(self, db_path: str = DB_FILE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize SQLite schema if not exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Models Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT UNIQUE NOT NULL,
                model_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                results_json TEXT NOT NULL,
                objective_value REAL,
                solver_status TEXT
            );
            """)

            # 2. Scenarios Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                config_json TEXT NOT NULL,
                results_json TEXT,
                service_ratio REAL,
                total_cost REAL
            );
            """)

            # 3. Experiments Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                runtime_seconds REAL,
                status TEXT NOT NULL,
                metrics_json TEXT NOT NULL
            );
            """)

            # 4. Cost Parameters Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                rates_json TEXT NOT NULL,
                is_active INTEGER DEFAULT 0
            );
            """)

            conn.commit()

    # --- MODEL CRUD ---
    def save_model(self, name: str, model_type: str, params: Dict[str, Any],
                   results: Dict[str, Any], obj_val: Optional[float] = None, status: str = "optimal") -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO optimization_models (model_name, model_type, created_at, parameters_json, results_json, objective_value, solver_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, model_type, now, json.dumps(params), json.dumps(results, default=str), obj_val, status))
            conn.commit()
            return cursor.lastrowid

    def list_models(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, model_name, model_type, created_at, objective_value, solver_status FROM optimization_models ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_model(self, name: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM optimization_models WHERE model_name = ?", (name,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["parameters"] = json.loads(res["parameters_json"])
            res["results"] = json.loads(res["results_json"])
            return res

    def rename_model(self, old_name: str, new_name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE optimization_models SET model_name = ? WHERE model_name = ?", (new_name, old_name))
            conn.commit()
            return cursor.rowcount > 0

    def delete_model(self, name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM optimization_models WHERE model_name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0

    # --- SCENARIO CRUD ---
    def save_scenario(self, name: str, description: str, config: Dict[str, Any],
                      results: Dict[str, Any], service_ratio: Optional[float] = None, total_cost: Optional[float] = None) -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO scenarios (scenario_name, description, created_at, config_json, results_json, service_ratio, total_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, description, now, json.dumps(config), json.dumps(results, default=str), service_ratio, total_cost))
            conn.commit()
            return cursor.lastrowid

    def list_scenarios(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, scenario_name, description, created_at, service_ratio, total_cost FROM scenarios ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_scenario(self, name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scenarios WHERE scenario_name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0

    # --- EXPERIMENT LOGGING ---
    def log_experiment(self, code: str, title: str, category: str,
                       runtime: float, status: str, metrics: Dict[str, Any]):
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO experiments (experiment_code, title, category, executed_at, runtime_seconds, status, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code, title, category, now, runtime, status, json.dumps(metrics, default=str)))
            conn.commit()

    def list_experiments(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, experiment_code, title, category, executed_at, runtime_seconds, status, metrics_json FROM experiments ORDER BY experiment_code ASC")
            rows = cursor.fetchall()
            output = []
            for r in rows:
                item = dict(r)
                item["metrics"] = json.loads(item["metrics_json"])
                output.append(item)
            return output
