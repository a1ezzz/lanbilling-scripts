#!/usr/bin/python3
# -*- coding: utf-8 -*-
# migrate_tariffs.py
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
import argparse

from wasp_general.config import WConfig

from lanbilling_stuff.rpc import WLanbillingRPC
from lanbilling_stuff.scripts_args import lanbilling_scripts_args
from lanbilling_stuff.tariff import fetch_tariffs, TariffPrefixCloneGenerator


if __name__ == '__main__':

	parser = argparse.ArgumentParser(
		description='Tariffs agent cloning tool. This script clones tariffs from one tariff type to other. '
		'If there is a tariff which is equal to the copying one nothing is done. Two tariffs are equal when '
		'theirs parameters (except "tarid", "type", "descr", "descrfull", "used" and "uuid") are equal. '
		'If --target-tariff-prefix is specified, then destination tariff must have it. Two tariff '
		'does not meant equal if destination tariff does not have the specified prefix. Current implementation '
		'is able to clone not-archived primary tariffs without time/size limitations, without assigned '
		'"catalogs" only.'
	)

	parser.add_argument(
		'--destination-tariff-type', help='Destination tariff type to which tariff must be cloned', type=int,
		metavar='tariff_type', required=True
	)

	parser.add_argument(
		'--destination-tariff-prefix', help='Prefix that should be added to newly created tariffs',
		type=str, nargs='?', metavar='prefix', default=None
	)

	parser.add_argument(
		'--export-report', help='Whether to export verbose result to csv-file or not',
		type=str, nargs='?', metavar='filename', default=None
	)

	parser.add_argument(
		'--from-tar-id', help='start tarid (tariff\'s id) number. '
		'Only those tariffs whose id are inside the selection will be cloned',
		**lanbilling_scripts_args['--from-tar-id']
	)
	parser.add_argument(
		'--to-tar-id', help='end tarid (tariff\'s id)  number. '
		'Only those tariffs whose id are inside the selection will be cloned',
		**lanbilling_scripts_args['--to-tar-id']
	)

	parser.add_argument(
		'--from-vg-id', help='start vg_id (vgroup\'s id) number. '
		'Only those tariffs that are assigned to specified vgroups will be cloned',
		**lanbilling_scripts_args['--from-vg-id']
	)
	parser.add_argument(
		'--to-vg-id', help='end vg_id (vgroup\'s id) number. '
		'Only those tariffs that are assigned to specified vgroups will be cloned',
		**lanbilling_scripts_args['--to-vg-id']
	)
	parser.add_argument(
		'--login',
		help='login pattern to search for. Only assigned tariffs will be selected. '
		'Vgroup to which tariff is assigned must have the specified substring inside login string',
		**lanbilling_scripts_args['--login']
	)
	parser.add_argument(
		'--vgroup-agent-id', help='vgroup agent id.  Only assigned tariffs will be selected. '
		'Vgroup to which tariff is assigned must belong to the specified agent',
		**lanbilling_scripts_args['--vgroup-agent-id']
	)

	archive_group = parser.add_mutually_exclusive_group()
	archive_group.add_argument(
		'--archived-vgroups', help='Select and export tariffs that are assigned to archived vgroups only',
		**lanbilling_scripts_args['--archived-vgroups']
	)
	archive_group.add_argument(
		'--non-archived-vgroups', help='Select and export tariffs that are assigned to vgroups '
		'which are not archived',
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

	config = WConfig()
	config.merge(os.environ['LANBILLING_CONFIG'])
	rpc = WLanbillingRPC.from_configuration(config, 'lanbilling', password_prompt=True)

	try:
		print('Fetching source tariffs')
		source_tariffs = list(fetch_tariffs(
			rpc, from_vg_id=args.from_vg_id, to_vg_id=args.to_vg_id,
			from_tar_id=args.from_tar_id, to_tar_id=args.to_tar_id,
			login=args.login, vgroup_agent_id=args.vgroup_agent_id, archived_vgroups=archive_flag
		))
		print('%i selected tariffs was fetched' % len(source_tariffs))
		c_generator = TariffPrefixCloneGenerator(
			rpc, args.destination_tariff_type, prefix=args.destination_tariff_prefix
		)
		print('%i tariffs with destination type was fetched' % len(c_generator.current_tariffs()))
		c_generator.clone(source_tariffs, report_filename=args.export_report)

	finally:
		rpc.rpc().Logout()
