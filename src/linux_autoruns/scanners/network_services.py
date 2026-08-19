from __future__ import annotations

import os
from pathlib import Path

from ..scanner import BaseScanner
from ..models import AutostartEntry


class NetworkServicesScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "Network Services"

    @property
    def description(self) -> str:
        return "NGINX, Apache, SSH auto-restart"

    def scan(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        entries.extend(self._scan_nginx())
        entries.extend(self._scan_apache())
        entries.extend(self._scan_ssh())
        return entries

    def _scan_nginx(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        sites = "/etc/nginx/sites-enabled"
        if self._safe_exists(sites):
            for f in sorted(Path(sites).iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    content = self._read_file(str(f))
                    if not content:
                        continue
                    info = self._get_file_info(str(f))
                    server_names = []
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("server_name"):
                            parts = line.split()
                            if len(parts) > 1:
                                server_names.extend(parts[1:])
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=f.name,
                        enabled=True,
                        scope="system",
                        description=f"NGINX site: {', '.join(server_names[:3])}" if server_names else "NGINX site config",
                        last_modified=self._get_mtime_iso(str(f)),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["network", "nginx"],
                        details={"server_names": server_names, "service_type": "nginx"},
                    ))
        nginx_conf = "/etc/nginx/nginx.conf"
        if self._safe_exists(nginx_conf):
            info = self._get_file_info(nginx_conf)
            entries.append(self._make_entry(
                file_path=nginx_conf,
                name="nginx.conf",
                enabled=True,
                scope="system",
                description="NGINX main config",
                last_modified=self._get_mtime_iso(nginx_conf),
                file_size=info["size"],
                file_permissions=info["permissions"],
                owner=info["owner"],
                tags=["network", "nginx"],
                details={"service_type": "nginx", "config_type": "main"},
            ))
        return entries

    def _scan_apache(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        for sites_dir in ["/etc/apache2/sites-enabled", "/etc/httpd/conf.d"]:
            if not self._safe_exists(sites_dir):
                continue
            for f in sorted(Path(sites_dir).iterdir()):
                if f.is_file() and not f.name.startswith("."):
                    content = self._read_file(str(f))
                    if not content:
                        continue
                    info = self._get_file_info(str(f))
                    server_names = []
                    for line in content.splitlines():
                        line = line.strip()
                        if "ServerName" in line:
                            parts = line.split()
                            if len(parts) > 1:
                                server_names.append(parts[1])
                    entries.append(self._make_entry(
                        file_path=str(f),
                        name=f.name,
                        enabled=True,
                        scope="system",
                        description=f"Apache site: {', '.join(server_names[:3])}" if server_names else "Apache site config",
                        last_modified=self._get_mtime_iso(str(f)),
                        file_size=info["size"],
                        file_permissions=info["permissions"],
                        owner=info["owner"],
                        tags=["network", "apache"],
                        details={"server_names": server_names, "service_type": "apache"},
                    ))
        return entries

    def _scan_ssh(self) -> list[AutostartEntry]:
        entries: list[AutostartEntry] = []
        sshd_config = "/etc/ssh/sshd_config"
        if not self._safe_exists(sshd_config):
            return entries
        content = self._read_file(sshd_config)
        if not content:
            return entries
        info = self._get_file_info(sshd_config)
        params = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("Include"):
                continue
            if " " in line:
                key, _, val = line.partition(" ")
                params[key.strip()] = val.strip()
        entries.append(self._make_entry(
            file_path=sshd_config,
            name="sshd_config",
            enabled=params.get("PermitRootLogin", "yes") != "no",
            scope="system",
            description="SSH daemon config",
            last_modified=self._get_mtime_iso(sshd_config),
            file_size=info["size"],
            file_permissions=info["permissions"],
            owner=info["owner"],
            tags=["network", "ssh"],
            details={"params": params, "port": params.get("Port", "22")},
        ))
        return entries
