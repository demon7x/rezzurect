#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''A set of adapters to bootstrap Rez packages.'''

# IMPORT STANDARD LIBRARIES
import abc

# IMPORT THIRD-PARTY LIBRARIES
from ..vendors import six


@six.add_metaclass(abc.ABCMeta)
class AbstractBaseAdapter(object):

    '''A basic class that creates system aliases for Rez packages.'''

    name = ''

    def __init__(self, version, alias=None):
        '''Create the adapter and add the session's alias class.

        Args:
            alias (callable[str, str]):
                The class which is used to add aliases to the OS.

        '''
        super(AbstractBaseAdapter, self).__init__()
        self.alias = alias
        self.version = version

    def __make_common_aliases(self, command):
        '''Create an alias which can be used to "run" the package.'''
        self.alias('main', command)

    @staticmethod
    @abc.abstractmethod
    def get_executable_command():
        '''str: The command that is run as the "main" alias, if it is enabled.'''
        return ''

    def execute(self):
        '''Add aliases and anything else that all packages should include.'''
        command = self.get_executable_command()

        if not command:
            return

        self.__make_common_aliases(command)


class BaseAdapter(AbstractBaseAdapter):

    '''An adapter that implements a DCC-specific command for the user to run.'''

    name = ''

    def execute(self):
        '''Add aliases and anything else that all packages should include.'''
        super(BaseAdapter, self).execute()

        if self.name:
            self.alias(self.name, self.get_executable_command())
