import json
from typing import Iterable, Any, Optional
from langgraph.store.base import BaseStore, Op, Result, GetOp, PutOp, SearchOp, ListNamespacesOp


class JSONFileStore(BaseStore):
    """A custom store backed by a JSON file for persistent key-value storage."""

    def __init__(self, file_path: str = "store.json"):
        self.file_path = file_path
        self._load_data()

    def _load_data(self):
        """Load data from the JSON file."""
        try:
            with open(self.file_path, "r") as file:
                self.data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {}  # Initialize with empty data if file doesn't exist or is invalid

    def _save_data(self):
        """Save data to the JSON file."""
        with open(self.file_path, "w") as file:
            json.dump(self.data, file, indent=4)

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        """Execute multiple operations synchronously."""
        results = []
        for op in ops:
            if isinstance(op, GetOp):
                results.append(self._get(op.namespace, op.key))
            elif isinstance(op, PutOp):
                results.append(self._put(op.namespace, op.key, op.value))
            # elif isinstance(op, DeleteOp):
            #     results.append(self._delete(op.namespace, op.key))
            elif isinstance(op, SearchOp):
                results.append(self._search(op.namespace_prefix, op.filter, op.limit, op.offset))
            elif isinstance(op, ListNamespacesOp):
                results.append(self._list_namespaces(op.match_conditions, op.max_depth, op.limit, op.offset))
            else:
                raise ValueError(f"Unsupported operation type: {type(op)}")
        self._save_data()
        return results

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        """Execute multiple operations asynchronously."""
        return self.batch(ops)

    def _get(self, namespace: tuple[str, ...], key: str) -> Optional[dict]:
        """Retrieve a single item."""
        ns = self._get_namespace(namespace)
        return ns.get(key)

    # def _put(self, namespace: tuple[str, ...], key: str, value: dict[str, Any]) -> None:
    #     """Store or update an item."""
    #     ns = self._get_or_create_namespace(namespace)
    #     ns[key] = value
    #     return {"status": "success", "key": key}

    def _put(self, namespace: tuple[str, ...], key: str, value: dict[str, Any]) -> None:
        """Store or update an item without overwriting other items."""
        ns = self._get_or_create_namespace(namespace)

        # Add or update the key-value pair
        ns[key] = value

        # Save the updated data to persist the change
        self._save_data()
        return {"status": "success", "key": key}

    def _delete(self, namespace: tuple[str, ...], key: str) -> None:
        """Delete an item."""
        ns = self._get_namespace(namespace)
        if key in ns:
            del ns[key]
        return {"status": "deleted", "key": key}

    def _search(self, namespace_prefix: tuple[str, ...], filter: Optional[dict] = None, limit: int = 10,
                offset: int = 0) -> list[dict]:
        """Search for items within a namespace prefix."""
        # Navigate to the namespace
        ns = self.data
        for part in namespace_prefix:
            if part in ns:
                ns = ns[part]
            else:
                return []  # Return empty if namespace doesn't exist

        # Collect items in the namespace
        results = []
        for key, item in ns.items():
            if isinstance(item, dict):  # Ensure the item is a dictionary
                if not filter or all(item.get(k) == v for k, v in filter.items()):
                    results.append({"key": key, "value": item})

        # Apply limit and offset
        return results[offset: offset + limit]

    def _list_namespaces(self, match_conditions, max_depth: Optional[int], limit: int, offset: int) -> list[tuple[str, ...]]:
        """List namespaces matching conditions."""
        namespaces = list(self.data.keys())
        if max_depth:
            namespaces = [ns[:max_depth] for ns in namespaces]
        return namespaces[offset : offset + limit]

    def _get_namespace(self, namespace: tuple[str, ...]) -> dict:
        """Retrieve a namespace."""
        ns = self.data
        for part in namespace:
            ns = ns.get(part, {})
        return ns

    def _get_or_create_namespace(self, namespace: tuple[str, ...]) -> dict:
        """Retrieve or create a namespace."""
        ns = self.data
        for part in namespace:
            if part not in ns:
                ns[part] = {}
            ns = ns[part]
        return ns
