import os
import json

class ProjectRegistry:
    def __init__(self, registry_file="E:\\F.R.I.D.A.Y\\project_registry.json"):
        self.registry_file = registry_file
        self.registry = self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r") as f:
                    return json.load(f)
            except: pass
        return {}

    def _save_registry(self):
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=4)

    def resolve_path(self, project_name: str) -> str:
        """Looks up the absolute path for a project anywhere on the PC."""
        name_lower = project_name.lower()
        if name_lower in self.registry:
            return self.registry[name_lower]
        return None

    def register_project(self, project_name: str, absolute_path: str) -> str:
        """Links a project name to a specific folder on the hard drive."""
        if not os.path.exists(absolute_path):
            return f"Error: The path {absolute_path} does not exist on this PC."
        
        self.registry[project_name.lower()] = absolute_path
        self._save_registry()
        return f"Successfully registered '{project_name}' to {absolute_path}."

# Global instance
global_registry = ProjectRegistry()