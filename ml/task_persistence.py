#!/usr/bin/env python3
"""
Task Persistence Layer
Integrates API tasks with Phase 1 PostgreSQL database
Provides persistent storage for task execution and results
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ml.clients import DevForgeClient


class TaskPersistenceManager:
    """Manages task persistence with Phase 1 infrastructure"""

    def __init__(self):
        """Initialize persistence manager"""
        self.client = DevForgeClient()
        self.postgres_client = self.client.postgres_client

    def create_task_record(
        self,
        task_id: str,
        task_type: str,
        description: str,
        params: Dict,
        priority: str = "medium",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create new task record in database"""

        record = {
            "task_id": task_id,
            "task_type": task_type,
            "description": description,
            "status": "pending",
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "params": json.dumps(params),
            "metadata": json.dumps(metadata or {}),
            "result": None,
            "error": None,
            "execution_time_ms": 0
        }

        # Store in PostgreSQL
        try:
            # Insert into custom task_executions table (would need to be created)
            query = """
            INSERT INTO task_executions
            (task_id, task_type, description, status, priority,
             created_at, params, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            params_list = [
                record["task_id"],
                record["task_type"],
                record["description"],
                record["status"],
                record["priority"],
                record["created_at"],
                record["params"],
                record["metadata"]
            ]

            self.postgres_client.execute_query(query, params_list)
            return record

        except Exception as e:
            print(f"Error creating task record: {e}")
            return {"error": str(e)}

    def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: int = 0
    ) -> bool:
        """Update task status in database"""

        try:
            query = """
            UPDATE task_executions
            SET status = %s, updated_at = %s
            WHERE task_id = %s
            """

            params_list = [
                status,
                datetime.utcnow().isoformat(),
                task_id
            ]

            self.postgres_client.execute_query(query, params_list)
            return True

        except Exception as e:
            print(f"Error updating task status: {e}")
            return False

    def store_task_result(
        self,
        task_id: str,
        result: Dict,
        execution_time_ms: int
    ) -> bool:
        """Store task result in database"""

        try:
            query = """
            UPDATE task_executions
            SET status = %s, result = %s, completed_at = %s,
                execution_time_ms = %s
            WHERE task_id = %s
            """

            params_list = [
                "completed",
                json.dumps(result),
                datetime.utcnow().isoformat(),
                execution_time_ms,
                task_id
            ]

            self.postgres_client.execute_query(query, params_list)
            return True

        except Exception as e:
            print(f"Error storing task result: {e}")
            return False

    def store_task_error(
        self,
        task_id: str,
        error: str,
        execution_time_ms: int
    ) -> bool:
        """Store task error in database"""

        try:
            query = """
            UPDATE task_executions
            SET status = %s, error = %s, completed_at = %s,
                execution_time_ms = %s
            WHERE task_id = %s
            """

            params_list = [
                "failed",
                error,
                datetime.utcnow().isoformat(),
                execution_time_ms,
                task_id
            ]

            self.postgres_client.execute_query(query, params_list)
            return True

        except Exception as e:
            print(f"Error storing task error: {e}")
            return False

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Retrieve task from database"""

        try:
            query = "SELECT * FROM task_executions WHERE task_id = %s"
            result = self.postgres_client.execute_query(query, [task_id])

            if result:
                task = result[0]
                # Parse JSON fields
                task["params"] = json.loads(task["params"])
                task["metadata"] = json.loads(task["metadata"])
                if task["result"]:
                    task["result"] = json.loads(task["result"])
                return task

            return None

        except Exception as e:
            print(f"Error retrieving task: {e}")
            return None

    def list_tasks(
        self,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """List tasks with filtering"""

        try:
            query = "SELECT * FROM task_executions WHERE 1=1"
            params_list = []

            if task_type:
                query += " AND task_type = %s"
                params_list.append(task_type)

            if status:
                query += " AND status = %s"
                params_list.append(status)

            if priority:
                query += " AND priority = %s"
                params_list.append(priority)

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params_list.extend([limit, offset])

            results = self.postgres_client.execute_query(query, params_list)

            tasks = []
            for task in results:
                task["params"] = json.loads(task["params"])
                task["metadata"] = json.loads(task["metadata"])
                if task.get("result"):
                    task["result"] = json.loads(task["result"])
                tasks.append(task)

            return tasks

        except Exception as e:
            print(f"Error listing tasks: {e}")
            return []

    def get_task_statistics(self) -> Dict:
        """Get task execution statistics"""

        try:
            stats = {}

            # Total tasks
            query = "SELECT COUNT(*) as count FROM task_executions"
            result = self.postgres_client.execute_query(query, [])
            stats["total_tasks"] = result[0]["count"] if result else 0

            # Status breakdown
            query = "SELECT status, COUNT(*) as count FROM task_executions GROUP BY status"
            result = self.postgres_client.execute_query(query, [])
            stats["by_status"] = {r["status"]: r["count"] for r in result}

            # Type breakdown
            query = "SELECT task_type, COUNT(*) as count FROM task_executions GROUP BY task_type"
            result = self.postgres_client.execute_query(query, [])
            stats["by_type"] = {r["task_type"]: r["count"] for r in result}

            # Average execution time
            query = "SELECT AVG(execution_time_ms) as avg_time FROM task_executions WHERE status = 'completed'"
            result = self.postgres_client.execute_query(query, [])
            stats["avg_execution_time"] = result[0]["avg_time"] if result else 0

            # Success rate
            query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM task_executions
            """
            result = self.postgres_client.execute_query(query, [])
            if result and result[0]["total"] > 0:
                stats["success_rate"] = (
                    result[0]["completed"] / result[0]["total"] * 100
                )
            else:
                stats["success_rate"] = 0

            return stats

        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}

    def delete_task(self, task_id: str) -> bool:
        """Delete task from database"""

        try:
            query = "DELETE FROM task_executions WHERE task_id = %s"
            self.postgres_client.execute_query(query, [task_id])
            return True

        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    def store_test_result(
        self,
        task_id: str,
        test_result: Dict
    ) -> bool:
        """Store generated test in test_cases table"""

        try:
            query = """
            INSERT INTO test_cases
            (test_id, title, description, code, framework, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            params_list = [
                str(uuid.uuid4()),
                test_result.get("test_name", "Generated Test"),
                f"Generated from task {task_id}",
                test_result.get("code", ""),
                test_result.get("framework", "pytest"),
                datetime.utcnow().isoformat()
            ]

            self.postgres_client.execute_query(query, params_list)
            return True

        except Exception as e:
            print(f"Error storing test result: {e}")
            return False

    def store_bug_report(
        self,
        task_id: str,
        bug_report: Dict
    ) -> bool:
        """Store detected bugs in bugs table"""

        try:
            for bug in bug_report.get("bugs", []):
                query = """
                INSERT INTO bugs
                (bug_id, title, description, severity, category,
                 steps_to_reproduce, expected, actual, task_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                params_list = [
                    bug.get("id", str(uuid.uuid4())),
                    f"{bug.get('severity', 'unknown').upper()}: {bug.get('description', '')[:50]}",
                    bug.get("description", ""),
                    bug.get("severity", "medium"),
                    bug.get("category", "other"),
                    json.dumps(bug.get("steps", [])),
                    bug.get("expected", ""),
                    bug.get("actual", ""),
                    task_id,
                    datetime.utcnow().isoformat()
                ]

                self.postgres_client.execute_query(query, params_list)

            return True

        except Exception as e:
            print(f"Error storing bug report: {e}")
            return False

    def get_agent_performance(self) -> Dict:
        """Get performance metrics for each agent type"""

        try:
            performance = {}

            agent_types = ["browser_automation", "test_generation", "bug_detection", "web_task"]

            for agent_type in agent_types:
                query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    AVG(execution_time_ms) as avg_time
                FROM task_executions
                WHERE task_type = %s
                """

                result = self.postgres_client.execute_query(query, [agent_type])

                if result:
                    r = result[0]
                    total = r.get("total", 0)
                    completed = r.get("completed", 0)

                    performance[agent_type] = {
                        "total_tasks": total,
                        "completed": completed,
                        "success_rate": (completed / total * 100) if total > 0 else 0,
                        "avg_execution_time_ms": r.get("avg_time", 0)
                    }

            return performance

        except Exception as e:
            print(f"Error getting agent performance: {e}")
            return {}


# Convenience function
def get_persistence_manager() -> TaskPersistenceManager:
    """Get a task persistence manager instance"""
    return TaskPersistenceManager()
