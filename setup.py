"""nexus setup."""

from distutils.command.install import install
import os
from pathlib import Path
import platform
import subprocess
from setuptools import setup

PACKAGE: str = "wandb_nexus"


class post_install(install):
    def _get_package_path(self):
        base = Path(self.install_platlib) / PACKAGE
        return base

    def _get_wheel_nexus_path(self, goos=None, goarch=None):
        goos = goos or platform.system().lower()
        goarch = goarch or platform.machine().lower()
        base = self._get_package_path()
        path = (base / f"bin-{goos}-{goarch}" / "wandb-nexus").resolve()
        return path

    def _get_native_nexus_path(self):
        base = self._get_package_path()
        path = (base / f"bin" / "wandb-nexus").resolve()
        return path

    def _build_nexus(self, nexus_path=None, goos=None, goarch=None):
        nexus_path = nexus_path or self._get_wheel_nexus_path(goos=goos, goarch=goarch)
        src_dir = Path(__file__).parent / "nexus"
        env = {}
        if goos:
            env["GOOS"] = goos
        if goarch:
            env["GOARCH"] = goarch
        os.makedirs(nexus_path.parent, exist_ok=True)
        ldflags = "-s -w"
        cmd = ("go", "build", f"-ldflags={ldflags}", "-o", str(nexus_path), "cmd/nexus_server/main.go")
        subprocess.check_call(cmd, cwd=src_dir, env=dict(os.environ, **env))

    def run(self):
        install.run(self)

        nexus_wheel_path = self._get_wheel_nexus_path()
        if not nexus_wheel_path.exists():
            nexus_native_path = self._get_native_nexus_path()
            self._build_nexus(nexus_native_path)


setup(
    name="wandb-nexus",
    version="0.0.1.dev1",
    description="Wandb core",
    packages=[PACKAGE],
    zip_safe=False,
    include_package_data=True,
    license="MIT license",
    python_requires=">=3.6",
    cmdclass={"install": post_install},
)
