#!/usr/bin/python3
# -*- coding: utf-8 -*-
# update_vgroups.py
#
# Copyright (C) 2017 the lanbilling-scripts authors and contributors
# <see AUTHORS file>
#
# This file is part of lanbilling-scripts.
#
# lanbilling-scripts is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lanbilling-scripts is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lanbilling-scripts.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import argparse

from wasp_general.config import WConfig
from wasp_general.csv import WCSVExporter

from lanbilling_stuff.rpc import WLanbillingRPC
from lanbilling_stuff.vgroup import fetch_vgroups
from lanbilling_stuff.scripts_args import lanbilling_scripts_args


if __name__ == '__main__':

	parser = argparse.ArgumentParser(
		description='VGroups bulk updater. By default, everything will be updated. But it can be limited by '
		'options'
	)
	parser.add_argument(
		'--update-ip-details', help='Set/unset ipdet option (1 - to set, 0 - to unset)', type=int,
		nargs='?', metavar='bool_flag', default=None
	)
	parser.add_argument(
		'--update-port-details', help='Set/unset portdet option (1 - to set, 0 - to unset)', type=int,
		nargs='?', metavar='bool_flag', default=None
	)
	parser.add_argument(
		'--from-tar-id', help='start tarid (tariff\'s id) number. '
		'Only those vgroups that are assigned to specified tariffs will be exported',
		**lanbilling_scripts_args['--from-tar-id']
	)
	parser.add_argument(
		'--to-tar-id', help='end tarid (tariff\'s id)  number. '
		'Only those vgroups that are assigned to specified tariffs will be exported',
		**lanbilling_scripts_args['--to-tar-id']
	)
	parser.add_argument(
		'--from-vg-id', help='start vg_id (vgroup\'s id) number. '
		'Only those vgroups whose id are inside the selection will be exported',
		**lanbilling_scripts_args['--from-vg-id']
	)
	parser.add_argument(
		'--to-vg-id', help='end vg_id (vgroup\'s id) number. '
		'Only those vgroups whose id are inside the selection will be exported',
		**lanbilling_scripts_args['--to-vg-id']
	)
	parser.add_argument(
		'--login',
		help='login pattern to search for. '
		'Only those vgroups whose login has the specified substring will be exported',
		**lanbilling_scripts_args['--login']
	)
	parser.add_argument(
		'--vgroup-agent-id', help='vgroup agent id. '
		'Only those vgroups that are belongs to the specified agent will be exported',
		**lanbilling_scripts_args['--vgroup-agent-id']
	)

	archive_group = parser.add_mutually_exclusive_group()
	archive_group.add_argument(
		'--archived-vgroups', help='Select and export archived vgroups only',
		**lanbilling_scripts_args['--archived-vgroups']
	)
	archive_group.add_argument(
		'--non-archived-vgroups', help='Select and export vgroups that are not archived',
		**lanbilling_scripts_args['--non-archived-vgroups']
	)

	args = parser.parse_args()

	archive_flag = None
	if args.archived_vgroups is True:
		archive_flag = True
	elif args.non_archived_vgroups is True:
		archive_flag = False

	if args.from_tar_id is not None and args.to_tar_id is not None:
		if args.from_tar_id > args.to_tar_id:
			raise ValueError('"from-tar-id" is greater then "to-tar-id"')

	if args.from_vg_id is not None and args.to_vg_id is not None:
		if args.from_vg_id > args.to_vg_id:
			raise ValueError('"from-vg-id" is greater then "to-vg-id"')

	if args.update_ip_details is None and args.update_port_details is None:
		raise ValueError('At least one update option must be specified')

	for arg_name in ['update_ip_details', 'update_port_details']:
		arg_value = getattr(args, arg_name)
		if arg_value is not None and arg_value not in [0, 1]:
			raise ValueError('Invalid value for "%s" option was specified' % arg_name)

	config = WConfig()
	config.merge(os.environ['LANBILLING_CONFIG'])
	rpc = WLanbillingRPC.from_configuration(config, 'lanbilling', password_prompt=True)

	try:
		exporter = WCSVExporter(sys.stdout)

		for vgroup in fetch_vgroups(
			rpc, from_vg_id=args.from_vg_id, to_vg_id=args.to_vg_id,
			from_tar_id=args.from_tar_id, to_tar_id=args.to_tar_id,
			login=args.login, vgroup_agent_id=args.vgroup_agent_id, archived_vgroups=archive_flag
		):
			vg_id = vgroup['vgid']
			update_report = {
				'vgid': vg_id,
				'ipdet': args.update_ip_details,
				'portdet': args.update_port_details
			}

			vgroup_details = rpc.getVgroup(vg_id)
			assert (len(vgroup_details) == 1)
			vgroup_details = vgroup_details[0]

			if args.update_ip_details is not None:
				vgroup_details['vgroup']['ipdet'] = args.update_ip_details

			if args.update_port_details is not None:
				vgroup_details['vgroup']['portdet'] = args.update_port_details

			rpc.insupdVgroup(0, vgroup_details)
			exporter.export(update_report)
	finally:
		rpc.rpc().Logout()
