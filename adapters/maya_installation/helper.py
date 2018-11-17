#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Any information that is used between one or more adapter modules.'''

# IMPORT STANDARD LIBRARIES
import os
import re


VERSION_PARSER = re.compile(r'(?P<major>\d+)')


def get_preinstalled_linux_executables(version):
    '''Get a list of possible pre-installed executable Nuke files.

    Args:
        version (str): A version of Nuke. Example: "11.2v3".

    Raises:
        RuntimeError:
            If we can't get version information from the stored version then
            this function will fail. Normally though, assuming this adapter
            was built correctly, this shouldn't occur.

    Returns:
        str: The absolute path to a Nuke executable.

    '''
    major = get_version_parts(version)

    if not major:
        raise RuntimeError(
            'Version "{version}" has no major component. This should not happen.'
            ''.format(version=version))

    return {
        '/usr/autodesk/maya{major}/bin/maya'.format(major=major),
        '/usr/autodesk/maya/bin/maya',
    }


def get_preinstalled_windows_executables(version):
    '''Get a list of possible pre-installed executable Nuke files.

    Args:
        version (str): A version of Nuke. Example: "11.2v3".

    Raises:
        RuntimeError:
            If we can't get version information from the stored version then
            this function will fail. Normally though, assuming this adapter
            was built correctly, this shouldn't occur.

    Returns:
        str: The absolute path to a Nuke executable.

    '''
    major = get_version_parts(version)

    if not major:
        raise RuntimeError(
            'Version "{version}" has no major component. This should not happen.'
            ''.format(version=version))

    # TODO : Find here
    return set()

#     return set([
#         r'C:\Program Files\Nuke{version}\Nuke{major}.{minor}.exe'.format(
#             version=version,
#             major=major,
#             minor=minor,
#         ),
#     ])


def get_version_parts(text):
    '''tuple[str, str, str]: Find the major, minor, and patch data of `text`.'''
    match = VERSION_PARSER.match(text)

    if not match:
        return ''

    return match.group('major')
