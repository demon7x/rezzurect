#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A set of general adapter classes which can be used to build Rez packages.'''

# IMPORT STANDARD LIBRARIES
import subprocess
import functools
import logging
import zipfile
import stat
import os

# IMPORT LOCAL LIBRARIES
from .. import base_builder
from ... import chooser
from . import helper


_DEFAULT_VALUE = object()
LOGGER = logging.getLogger('rezzurect.maya_installation_builder')


class BaseNukeAdapter(base_builder.BaseAdapter):

    '''An base-class which is meant share code across subclasses.

    This class is not meant to be used directly.

    Attributes:
        _install_file_name_template (str):
            The name of the actual file which can be used to install Nuke.
            The exact name should be whatever the third-party vendor prefers.
            Make sure to include any version information in the name, such as
            "Nuke{major}.{minor}v{patch}-win-x86-release-64.exe" or
            "Nuke{major}.{minor}v{patch}-linux-x86-release-64-installer".

    '''

    _install_archive_name_template = ''
    _install_file_name_template = ''

    @staticmethod
    def _extract_zip(zip_file_path, destination):
        '''Extract a ZIP file to some file location.

        Args:
            zip_file_path (str):
                The absolute path to some ZIP file.
            destination (str):
                An absolute path to a directory where `zip_file_path`
                will be extracted to.

        '''
        with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
            try:
                zip_file.extractall(destination)
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception('Zip file "%s" failed to unzip.', zip_file_path)
                raise

    @classmethod
    def get_archive_path_from_version(cls, source, version):
        '''str: Get the recommended folder for archive (installer) files to be.'''
        try:
            major, minor, patch = helper.get_version_parts(version)
        except TypeError:
            major, minor, patch = version

        file_name = cls._install_archive_name_template.format(
            major=major, minor=minor, patch=patch,
        )

        return cls.get_archive_path(source, file_name)

    @classmethod
    def get_install_file(cls, root, version):
        '''Get the absolute path to where the expected Nuke install file is.

        Args:
            root (str):
                The absolute path to the package folder where the Nuke executable
                would be found.
            version (str):
                The full, unparsed version information to get an executable of.
                Example: "11.2v3".

        Returns:
            str: The absolute path to the executable file of the given `version`.

        '''
        major, minor, patch = helper.get_version_parts(version)

        return cls.get_archive_path(
            root,
            cls._install_file_name_template.format(major=major, minor=minor, patch=patch),
        )

    def install_from_local(self, source, install):
        '''Search for a locally-installed Nuke file and install it, if it exists.

        Args:
            source (str):
                The absolute path to the package folder where the Nuke executable
                would be found.
            install (str):
                The absolute directory where `source` will be installed into.

        Raises:
            EnvironmentError: If the executable file could not be found.

        Returns:
            str: The absolute path to the executable file which is used for installation.

        '''
        executable = self.get_install_file(source, self.version)

        if not os.path.isfile(executable):
            raise EnvironmentError(
                'install_file "{executable}" does not exist. '
                'Check its spelling and try again.'.format(executable=executable))

        return executable


class LinuxAdapter(BaseNukeAdapter):

    '''An adapter for installing Nuke onto a Linux machine.'''

    name = 'nuke'
    _install_archive_name_template = 'Nuke{major}.{minor}v{patch}-linux-x86-release-64.tgz'
    _install_file_name_template = 'Nuke{major}.{minor}v{patch}-linux-x86-release-64-installer'

    def get_preinstalled_executables(self):
        '''Get a list of possible pre-installed executable Nuke files.

        Raises:
            RuntimeError:
                If we can't get version information from the stored version then
                this function will fail. Normally though, assuming this adapter
                was built correctly, this shouldn't occur.

        Returns:
            str: The absolute path to a Nuke executable.

        '''
        return helper.get_preinstalled_linux_executables(self.version)

    def install_from_local(self, source, install):
        '''Unzip the Nuke file to the given install folder.

        Args:
            source (str):
                The absolute path to the package folder where the Nuke executable
                would be found.
            install (str):
                The absolute directory where `source` will be installed into.

        Raises:
            EnvironmentError: If the Zip file failed to extract Nuke into `install`.

        '''
        try:
            zip_file_path = super(LinuxAdapter, self).install_from_local(source, install)
        except EnvironmentError:
            self._extract_tar(source, self.version)
            zip_file_path = super(LinuxAdapter, self).install_from_local(source, install)

        LOGGER.debug('Unzipping "%s".', zip_file_path)

        self._extract_zip(zip_file_path, install)

        major, minor, _ = helper.get_version_parts(self.version)
        executable = 'Nuke{major}.{minor}'.format(major=major, minor=minor)
        executable = os.path.join(install, executable)

        if not os.path.isfile(executable):
            raise EnvironmentError('Zip failed to extract to folder "{install}".'
                                   ''.format(install=install))

        # Reference: https://stackoverflow.com/questions/12791997
        executable_stats = os.stat(executable)
        os.chmod(executable, executable_stats.st_mode | stat.S_IEXEC)


def register(source_path, install_path, system, architecture):
    '''Add installation options to all of the Maya adapter classes.

    Each of the installation options take only one arg, which is the adapter
    which is used to handle the request. If the request is successful then the
    function should just complete. If it fails for whatever reason then
    have the function raise any exception.

    Args:
        source_path (str):
            The absolute path to where the Rez package is located, on-disk.
        install_path (str):
            The absolute path to where the package will be installed into.
        system (str):
            The name of the OS platform. Example: "Linux", "Windows", etc.
        architecture (str):
            The bits of the `system`. Example: "x86_64", "AMD64", etc.

    '''
    adapters = (
        ('Linux', LinuxAdapter),
    )

    for system_, adapter in adapters:
        adapter.strategies = []

        add_maya_from_internet_build = functools.partial(
            base_builder.add_from_internet_build,
            'maya', system, architecture, source_path, install_path)
        add_maya_local_filesystem_build = functools.partial(
            base_builder.add_local_filesystem_build, source_path, install_path)

        adapter.strategies.append(('local', add_maya_local_filesystem_build))
        adapter.strategies.append(('internet', add_maya_from_internet_build))
        adapter.strategies.append(('link', base_builder.add_link_build))

        chooser.register_build_adapter(adapter, 'maya_installation', system_)