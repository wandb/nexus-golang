"""nexus setup."""

import distutils
from distutils.command.install import install
# from distutils.command.bdist import bdist
from wheel.bdist_wheel import bdist_wheel
import os
from pathlib import Path
import platform
import subprocess
from setuptools import setup
from setuptools.command.develop import develop

PACKAGE: str = "wandb_nexus"
ALL_PLATFORMS = (("darwin", "arm64"),
                 ("darwin", "amd64"),
                 ("linux", "amd64"),
                 ("windows", "amd64"),
                 )


class nexus_base:
    def _get_package_path(self):
        base = Path(self.install_platlib) / PACKAGE
        return base

    def _get_wheel_nexus_path(self, path=None, goos=None, goarch=None):
        path = path or self._get_package_path()
        goos = goos or platform.system().lower()
        goarch = goarch or platform.machine().lower()
        path = (path / f"bin-{goos}-{goarch}" / "wandb-nexus").resolve()
        return path

    def _build_nexus(self, path=None, goos=None, goarch=None):
        nexus_path = self._get_wheel_nexus_path(path=path, goos=goos, goarch=goarch)
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


class wrap_install(install, nexus_base):

    user_options = [
        ('nexus-build=', None, "nexus binaries to build comma separated (eg darwin-arm64,linux-amd64)"),
    ] + install.user_options

    def initialize_options(self):
        super().initialize_options()
        self.nexus_build = None

    def finalize_options(self):
        super().finalize_options()
        self.set_undefined_options('bdist_wheel', ('nexus_build', 'nexus_build'))

    def run(self):
        install.run(self)

        nexus_wheel_path = self._get_wheel_nexus_path()
        if self.nexus_build:
            if self.nexus_build == "all":
                for goos, goarch in ALL_PLATFORMS:
                    self._build_nexus(goos=goos, goarch=goarch)
        elif not nexus_wheel_path.exists():
            self._build_nexus()


class wrap_develop(develop, nexus_base):

    def run(self):
        develop.run(self)
        self._build_nexus(path=Path("wandb_nexus"))


class post_bdist(bdist_wheel, nexus_base):

    user_options = [
        ('nexus-build=', None, "nexus binaries to build comma separated (eg darwin-arm64,linux-amd64)"),
    ] + bdist_wheel.user_options

    def initialize_options(self):
        super().initialize_options()
        self.nexus_build = "all"

    def finalize_options(self):
        super().finalize_options()

    def run(self):
        bdist_wheel.run(self)


setup(
    name="wandb-nexus",
    version="0.0.1.dev1",
    description="Wandb core",
    packages=[PACKAGE],
    zip_safe=False,
    include_package_data=True,
    license="MIT license",
    python_requires=">=3.6",
    cmdclass={
        "install": wrap_install,
        "develop": wrap_develop,
        "bdist_wheel": post_bdist,
        },
)
