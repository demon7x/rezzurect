#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A module which is used to communicate with paths outside of Rezzurect.

Reference:
    https://github.com/ColinKennedy/tk-config-default2-respawn/wiki/Referring-To-Custom-Code

'''

# IMPORT STANDARD LIBRARIES
import logging
import json
import os
import re

# IMPORT THIRD-PARTY LIBRARIES
from yaml import parser
import yaml
import six

# IMPORT LOCAL LIBRARIES
from . import multipurpose_helper


LOGGER = logging.getLogger('rezzurect.config')
_ENVIRONMENT_EXPRESSION = re.compile(r'REZZURECT_CUSTOM_KEY_(?P<key>\w+)')
_PIPELINE_CONFIGURATION_ROOT = multipurpose_helper.get_current_pipeline_configuration_root_safe()


def _read_setting_file(path):
    '''dict[str, str]: Try to read the given file as a JSON or YAML file.'''
    def _as_json(path):
        with open(path, 'r') as file_:
            return json.load(file_)

    def _as_yaml(path):
        with open(path, 'r') as file_:
            return yaml.safe_load(file_)

    known_exceptions = (
        # If the file does not exist
        IOError,

        # If the JSON has syntax issues
        ValueError,

        # If the YAML has syntax issues
        parser.ParserError,
    )

    for loader in (_as_yaml, _as_json):
        try:
            return loader(path) or dict()
        except known_exceptions:
            pass

    return dict()


def get_custom_keys_from_environment():
    '''dict[str, str]: Get every user-defined custom key and its value.'''
    keys = dict()

    for key, value in six.iteritems(os.environ):
        match = _ENVIRONMENT_EXPRESSION.match(key)

        if match:
            keys[match.group('key')] = value

    return keys


def get_custom_keys():
    return get_settings().get('keys', dict())


def get_settings():
    '''dict[str, str]: All of the user-defined Respawn custom keys.'''
    def update(data, output):
        for key, value in data.items():
            if key == 'keys':
                output[key].update(value)
            else:
                output[key] = value

    output = {
        'keys': dict(),
    }

    update(read_configuration_setting_file(), output)
    update(multipurpose_helper.read_settings_from_shotgun_field_safe(), output)
    update(read_user_settings_file(), output)
    update(get_custom_keys_from_environment(), output)

    return output


def read_configuration_setting_file():
    '''dict[str, str]: Get the custom keys for this Configuration.'''
    if not os.path.isdir(_PIPELINE_CONFIGURATION_ROOT):
        return dict()

    settings_file = os.path.join(_PIPELINE_CONFIGURATION_ROOT, '.respawnrc')

    if not os.path.isfile(settings_file):
        return dict()

    return _read_setting_file(settings_file)


def read_user_settings_file():
    '''dict[str, str]: Get every user-defined custom key.'''
    settings_file = os.path.expanduser('~/.respawnrc')

    if not os.path.isfile(settings_file):
        return dict()

    return _read_setting_file(settings_file)


def expand(text):
    '''Replace the given format text with an absolute path.

    Important:
        The keys which are used to expand `text` come from
        the user's environment settings. The only "reserved" key that the user
        may not modify is "respawn_root", which signifies the current path to
        the user's current Pipeline Configuration.

    Args:
        text (str): Some Python string to expand such as "{foo}/bar".

    Returns:
        str: The expanded text result.

    '''
    settings = get_custom_keys()
    settings['respawn_root'] = _PIPELINE_CONFIGURATION_ROOT

    try:
        return text.format(**settings)
    except KeyError:
        LOGGER.exception(
            'Text "%s" is missing one or more keys. Keys found, "%s".', text, settings)
        raise


def expand_first(options, default=''):
    '''str: Try a number of different string options until one succeeds.'''
    for option in options:
        try:
            return expand(option)
        except KeyError:
            pass

    return default
