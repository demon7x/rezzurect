#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module for rez-specific build instructions and sourcing external files.'''

# IMPORT STANDARD LIBRARIES
import logging
import json
import os

# IMPORT THIRD-PARTY LIBRARIES
from rez.utils.graph_utils import view_graph
from rez import build_process_
from rez import build_system
from rez import exceptions
from rez import packages_


LOGGER = logging.getLogger('rezzurect.multipurpose_helper')


def get_current_pipeline_configuration():
    '''Find the user's current Pipeline Configuration.

    Returns:
        `sgtk.pipelineconfig.PipelineConfiguration`:
            The found pipeline context.

    '''
    from sgtk import pipelineconfig_factory
    return pipelineconfig_factory.from_path(os.getenv('TANK_CURRENT_PC'))


def get_current_pipeline_configuration_safe():
    '''Find the user's current Pipeline Configuration, if any.

    Returns:
        `sgtk.pipelineconfig.PipelineConfiguration` or NoneType:
            The found Configuration.

    '''
    try:
        return get_current_pipeline_configuration()
    except ImportError:
        return None


def get_current_pipeline_configuration_root():
    '''str: The path on-disk to where the Configuration is located.'''
    return get_current_pipeline_configuration().get_config_location()


def get_current_pipeline_configuration_root_safe():
    '''str: The path on-disk to where the Configuration is located, if any.'''
    try:
        return get_current_pipeline_configuration_root()
    except ImportError:
        return ''


def _read_settings_from_shotgun_field():
    '''dict[str, str]: Get the user's Respawn keys using their Toolkit context.'''
    from tank_vendor.shotgun_api3 import shotgun
    from sgtk import authentication

    authenticator = authentication.ShotgunAuthenticator()
    user = authenticator.get_user()
    shotgun_connection = user.create_sg_connection()

    try:
        has_respawn_key_field = \
            bool(shotgun_connection.schema_field_read('PipelineConfiguration', 'sg_respawn_keys'))
    # except shotgun.Fault:
    except Exception:
        has_respawn_key_field = False

    if not has_respawn_key_field:
        return dict()

    configuration_id = get_current_pipeline_configuration().get_shotgun_id()
    configuration = shotgun_connection.find_one(
        'PipelineConfiguration',
        [['id', 'is', configuration_id]],
        ['sg_respawn_keys'],
    )

    return json.loads(configuration.get('sg_respawn_keys', ''))


def read_settings_from_shotgun_field_safe():
    '''dict[str, str]: Get the user's Respawn keys using their Toolkit context.'''
    try:
        return _read_settings_from_shotgun_field()
    except (ImportError, TypeError):
        LOGGER.exception('Respawn Shotgun Field was not found or has a syntax error.')

        configuration = get_current_pipeline_configuration_safe()

        if configuration:
            LOGGER.debug(
                'Configuration name "%s" and id "%s" has missing field.',
                configuration.get_project_disk_name(),
                configuration.get_shotgun_id(),
            )
        else:
            LOGGER.debug('No configuration was found.')

        return dict()


def build(path, install_path=''):
    '''Build the given Rez package directory into a Rez package.

    This command is basically a copy/paste of
    the `rez.cli.build.command` function and, essentially is the same as
    running

    ```bash
    cd path
    rez-build --install
    ```

    Args:
        path (str):
            The path to a package definition folder
            (which must contain a package.py file).
        install_path (str, optional):
            The absolute path to a directory on-disk which will be used to
            build `path`. If no path is given then the user's local_package_path
            is used instead (which is what Rez defaults to).
            Default: "".

    '''
    # import subprocess

    # command = 'cd "{path}" && rez-build --install'.format(path=path)

    # if install_path:
    #     command += ' --prefix {install_path}'.format(install_path=install_path)

    # process = subprocess.Popen(
    #     [command],
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     shell=True
    # )

    # (_, stderr) = process.communicate()

    # if stderr:
    #     raise ValueError(stderr)

    package = packages_.get_developer_package(path)

    build_system_ = build_system.create_build_system(
        path,
        package=package,
        buildsys_type=None,
        write_build_scripts=False,
        verbose=True,
        build_args=[],
        child_build_args=[],
    )

    # create and execute build process
    builder = build_process_.create_build_process(
        'local',
        path,
        package=package,
        build_system=build_system_,
        verbose=True,
    )

    try:
        builder.build(
            install_path=install_path or None,
            clean=False,
            install=True,
            variants=None,
        )
    except exceptions.BuildContextResolveError as err:
        LOGGER.exception('Path "%s" failed to build.', path)

        if err.context.graph:
            graph = err.context.graph(as_dot=True)
            view_graph(graph)
        else:
            LOGGER.error('the failed resolve context did not generate a graph.')

        raise
