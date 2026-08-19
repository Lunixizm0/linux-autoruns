from dataclasses import dataclass, field


@dataclass
class AutostartEntry:
    category: str
    file_path: str
    name: str
    enabled: bool
    command: str | None = None
    exec_args: list[str] | None = None
    user: str | None = None
    scope: str = "system"
    description: str | None = None
    comment: str | None = None
    last_modified: str | None = None
    file_size: int | None = None
    file_permissions: str | None = None
    owner: str | None = None
    tags: list[str] = field(default_factory=list)
    details: dict[str, str | int | bool | list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "file_path": self.file_path,
            "name": self.name,
            "enabled": self.enabled,
            "command": self.command,
            "exec_args": self.exec_args,
            "user": self.user,
            "scope": self.scope,
            "description": self.description,
            "comment": self.comment,
            "last_modified": self.last_modified,
            "file_size": self.file_size,
            "file_permissions": self.file_permissions,
            "owner": self.owner,
            "tags": self.tags,
            "details": self.details,
        }
