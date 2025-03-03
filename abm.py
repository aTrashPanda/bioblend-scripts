#!/usr/bin/env python3

"""
The Automated Benchmarking Tool

Copyright 2021 The Galaxy Project. All rights reserved.

"""

import yaml
import sys
import os
import logging
import lib.common

# These imports are required because they need to be added to the symbol table
# so the parse_menu method can find them in globals()
from lib import job, dataset, workflow, history, library, folder, benchmark, helm, kubectl, config

log = logging.getLogger('abm')
log.setLevel(logging.INFO)

VERSION = '1.4.1'

BOLD = '\033[1m'
CLEAR = '\033[0m'

def bold(text: str):
    """
    Wraps the text in ANSI control sequences to generate bold text in the terminal.

    :param text: the text to be made bold
    :return: the original string wrapped in ANSI control sequences
    """
    return f"{BOLD}{text}{CLEAR}"


help_args = ['help', '-h', '--help']
version_args = ['-v', '--version', 'version']

def head(text):
    print(bold(text))


def command_list(commands:list):
    return '|'.join(bold(c) for c in commands)


def print_main_help(menu_data):
    print()
    head("SYNOPSIS")
    print("    Workflow and data management for remote Galaxy instances")
    print()
    head("USAGE")
    print(f"    {sys.argv[0]} COMMAND [SUBCOMMAND] [OPTIONS]")
    print()
    head("COMMANDS")
    for menu_item in menu_data:
        print(f"    {command_list(menu_item['name'])}")
        print(f"        {menu_item['help']}")
    print(f"    {command_list(['version', '-v', '--version'])}")
    print("        print the program version and exit")
    print(f"    {command_list(help_args)}")
    print("        print this help screen and exit")
    print()
    head("NOTES")
    print(f"    Available SUBCOMMANDS and OPTIONS depend on the command. Use the {bold('help')} subcommand")
    print(f"    to learn more about each of the commands. For example:\n")
    print(f"    $> abm workflow help\n")
    print("    Copyright 2021 The Galaxy Project\n")


def print_help(menu_data, command):
    submenu = None
    for menu_item in menu_data:
        if command in menu_item['name']:
            submenu = menu_item
            break
    if submenu is None:
        #print_main_help(menu_data)
        print(f"No help for {command} is available")
        return

    print()
    head("SYNOPSIS")
    print(f"    {submenu['help']}\n")
    head("SUBCOMMANDS")
    for menu_item in submenu['menu']:
        print(f"    {'|'.join(bold(x) for x in menu_item['name'])} {menu_item['params'] if 'params' in menu_item else ''}")
        print(f"        {menu_item['help']}")
    print(f"    {bold('help')}")
    print("        print this help screen and exit")
    print()
    print("    Copyright 2021 The Galaxy Project\n")


all_commands = {}


def get_menu(name: str):
    if name in all_commands:
        return all_commands[name]
    menu = dict()
    all_commands[name] = menu
    return menu


def register_handler(name: str, commands: list, handler):
    log.debug("Registering handler for menu: %s", name)
    menu = get_menu(name)
    for command in commands:
        menu[command] = handler


def alias(shortcut, fullname):
    all_commands[shortcut] = all_commands[fullname]


def parse_menu():
    log.debug('parse_menu')
    menu_config = f'{os.path.dirname(os.path.abspath(__file__))}/lib/menu.yml'
    if not os.path.exists(menu_config):
        print(f"ERROR: Unable to load the menu configuration from {menu_config}")
        sys.exit(1)
    with open(menu_config) as f:
        menu_data = yaml.safe_load(f)
    for main_menu_item in menu_data:
        # Use the first name in the list as the main name for the item. The
        # others will be aliased below.
        name = main_menu_item['name'][0]
        log.debug('Menu name: %s', name)
        for submenu_item in main_menu_item['menu']:
            handler = globals()
            handler_name = submenu_item['handler']
            log.debug('Submenu item: %s', handler_name)
            for part in handler_name.split('.'):
                log.debug("Part: %s", part)
                if type(handler) is not dict:
                    handler = handler.__dict__
                handler = handler[part]
            if isinstance(handler, dict):
                print(f"Handler not found {handler_name}")
                sys.exit(1)
            register_handler(name, submenu_item['name'], handler)
        for command_alias in main_menu_item['name'][1:]:
            alias(command_alias, name)
    return menu_data


def version():
    print()
    print(f"    Galaxy Automated Benchmarking v{VERSION}")
    print(f"    Copyright 2021 The Galaxy Project. All Rights Reserved.\n")


def entrypoint():
    menu_data = parse_menu()

    if len(sys.argv) < 2 or sys.argv[1] in help_args:
        print_main_help(menu_data)
        return

    if '--debug' in sys.argv:
        print("Enable debugging")
        log.setLevel(logging.DEBUG)
        sys.argv.remove('--debug')
    program = sys.argv[0]
    profile = sys.argv[1]
    if profile in version_args:
        version()
        return

    if profile == 'config':
        command = profile
        profile = None
        if len(sys.argv) < 3:
            print_help(menu_data, command)
            return
        subcommand = sys.argv[2]
        if len(sys.argv) > 3:
            params = sys.argv[3:]
        else:
            params = []
    else:
        command = sys.argv[2]
        if command in version_args:
            version()
            return
        subcommand = None
        if len(sys.argv) > 3:
            subcommand = sys.argv[3]
        if len(sys.argv) > 4:
            params = sys.argv[4:]
        else:
            params = []

    if command in help_args:
        print_help(menu_data, profile)
        return
    if subcommand and subcommand in help_args:
        print_help(menu_data, command)
        return

    if profile is not None:
        # common.GALAXY_SERVER, common.API_KEY, common.KUBECONFIG = parse_profile(profile)
        if not lib.common.set_active_profile(profile):
            print(f"ERROR: Unable to set the active profile. No GALAXY_SERVER defined.")
            return
        if lib.GALAXY_SERVER is None:
            print("ERROR: GALAXY_SERVER was not set in the profile.")
            return
    if command in all_commands:
        subcommands = all_commands[command]
        if subcommand not in subcommands:
            print(f'ERROR: unrecognized subcommand "{subcommand}"')
            print(f'Type "{program} {command} help" for more help.')
            return
        handler = subcommands[subcommand]
        handler(params)
    else:
        print(f'\n{bold("ERROR:")} Unknown command {bold({command})}')
        print_main_help(menu_data)


if __name__ == '__main__':
    entrypoint()
