#!/usr/bin/env python
#

# IMPORT STANDARD LIBRARIES
import functools
import platform
import imp
import os

# IMPORT THIRD-PARTY LIBRARIES
from rez import config

# IMPORT LOCAL LIBRARIES
from .build_adapters import git_remote
from .build_adapters import internet
from .build_adapters import strategy
from . import common


def add_from_internet(package, system, distribution, architecture):
    download_from_package = functools.partial(
        internet.download,
        package,
        system,
        distribution,
        architecture,
    )
    strategy.register_strategy('download', download_from_package)


def add_git_remote_search(build_path, system, distribution, architecture):
    git_command = git_remote.get_git_command(
        git_remote.get_git_root_url(os.path.dirname(build_path)),
        system.lower(),
        distribution,
        architecture,
    )
    strategy.register_strategy('git', git_command)


def add_git_remote_ssh(install_path, system, distribution, architecture):
    git_command = git_remote.get_git_command(
        # TODO : This URL needs to be "resolved" properly
        'selecaotwo@192.168.0.11:/srv/git/rez-nuke.git',
        path=install_path,
        system=system,
        distribution=distribution,
        architecture=architecture,
    )
    strategy.register_strategy('git-ssh', git_command)


# TODO : This function, `get_package_name`, is probably not necessary.
#        Look into how to get the package name on-build and then remove this, later
#
def get_package_name(path):
    '''Get the name of the rez package that is being operated on.

    Args:
        path (str): The absolute path to the build path of some rez package.

    Returns:
        str: The found name, if any.

    '''
    for root in config.config.packages_path:
        package = os.path.relpath(path, root)

        found = not package.startswith('.')

        if found:
            # TODO : Make a better split function, later
            return package.split(os.sep)[0]

    return ''


def main(
        source_path,
        build_path,
        install_path,
        system=platform.system(),
        distribution='-'.join(platform.dist()),
        architecture=common.get_architecture(),
    ):
    '''Run the main execution of the current script.'''
    package_name = get_package_name(source_path)
    add_from_internet(package_name, system, distribution, architecture)

    add_git_remote_ssh(install_path, system, distribution, architecture)

    add_git_remote_search(build_path, system.lower(), distribution, architecture)