#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''An adapter (and its functions) for creating and running a Nuke Rez package.'''

# IMPORT LOCAL LIBRARIES
from .. import common_setting
from . import helper


class CommonNukeSettingAdapter(common_setting.BaseAdapter):

    '''An adapter which is used to set up common settings / aliases for Nuke.'''

    name = 'nuke'

    def __init__(self, version, alias):
        '''Create the adapter and add the session's alias class.

        Args:
            alias_manager (`rezzurect.adapters.common.BaseAdapter` or NoneType):
                The class which is used to add aliases to the OS.
            include_common_aliases (`bool`, optional):
                If True, add a "main" alias to the current session.
                If False, don't add it.
                Default is True.

        '''
        super(CommonNukeSettingAdapter, self).__init__(version, alias)

    def get_executable_command(self):
        '''Get the command that is run as the "main" alias.

        Raises:
            EnvironmentError: If the stored version is incorrect.

        Returns:
            str: The found command for Nuke's version.

        '''
        match = helper.VERSION_PARSER.match(self.version)

        if not match:
            raise EnvironmentError(
                'version "{obj.version}" did not match expected pattern, '
                '"{parser.pattern}"'.format(
                    obj=self.version,
                    parser=helper.VERSION_PARSER,
                )
            )

        # The Nuke command on linux is "Nuke11.2". Non-commercial is "Nuke11.2 -nc"
        version = '.'.join([match.group('major'), match.group('minor')])
        return 'Nuke{version} -nc'.format(version=version)

    def execute(self):
        super(CommonNukeSettingAdapter, self).execute()

        # Note: Aliases and environment variable settings added here will be
        #       added to all Nuke versions in all OSes.
        env.PYTHONPATH.append('~/my_modules')
