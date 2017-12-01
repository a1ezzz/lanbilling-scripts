# -*- coding: utf-8 -*-
# lanbilling_stuff/scripts_args.py
#
# Copyright (C) 2017 the lanbilling-scripts authors and contributors
# <see AUTHORS file>
#
# This file is part of lanbilling-scripts.
#
# Lanbilling-scripts is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lanbilling-scripts is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lanbilling-scripts.  If not, see <http://www.gnu.org/licenses/>.

# TODO: document the code
# TODO: write tests for the code

# noinspection PyUnresolvedReferences
from lanbilling_stuff.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from lanbilling_stuff.version import __status__


lanbilling_scripts_args = {
	'--from-tar-id': {
		'type': int,
		'nargs': '?',
		'metavar': 'tarid',
		'default': None
	},
	'--to-tar-id': {
		'type': int,
		'nargs': '?',
		'metavar': 'tarid',
		'default': None
	},
	'--from-vg-id': {
		'type': int,
		'nargs': '?',
		'metavar': 'vgid',
		'default': None
	},
	'--to-vg-id': {
		'type': int,
		'nargs': '?',
		'metavar': 'vgid',
		'default': None
	},
	'--tariff-type': {
		'type': int,
		'nargs': '?',
		'metavar': 'tariff_type',
		'default': None
	},
	'--login': {
		'type': str,
		'nargs': '?',
		'metavar': 'login',
		'default': None
	},
	'--vgroup-agent-id': {
		'type': int,
		'nargs': '?',
		'metavar': 'agent_id',
		'default': None
	},
	'--archived-vgroups': {
		'action': 'store_true'
	},
	'--non-archived-vgroups': {
		'action': 'store_true'
	}
}
