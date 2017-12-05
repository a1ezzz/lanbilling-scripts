#!/usr/bin/python3
# -*- coding: utf-8 -*-
# migrate_vgroups.py
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
from datetime import datetime

from wasp_general.config import WConfig
from wasp_general.csv import WCSVExporter

from lanbilling_stuff.rpc import WLanbillingRPC
from lanbilling_stuff.tariff import fetch_tariffs, assign_tariff, TariffPrefixCloneGenerator
from lanbilling_stuff.vgroup import fetch_vgroups, disable_vgroup, unblock_vgroup
from lanbilling_stuff.scripts_args import lanbilling_scripts_args


def supported_vgroup(vgroup):
	for attr in ('services', 'addons', 'macstaff', 'telstaff', 'staff', 'blockrasp', 'tarrasp'):
		if vgroup[attr] != []:
			print('Vgroup attribute "%s" has invalid value - %s' % (attr, vgroup[attr]))
			return False
	if vgroup['vgroup']['parentvgid'] != 0:
		return False
	if vgroup['vgroup']['blocked'] != 0:
		return False
	elif vgroup['vgroup']['parentvglogin'] is not None:
		return False
	elif vgroup['vgroup']['dirty'] != 0:
		return False
	return True


if __name__ == '__main__':

	parser = argparse.ArgumentParser(
		description='Vgroups agent migration tool. This script migrates vgroups to other agent (vgroup must '
		'not be archived). If vgroup has been already assigned to the agent then nothing is done to that '
		'vgroup.'
	)
	parser.add_argument(
		'--destination-agent-id', help='Destination agent id to which vgroups must be migrated', type=int,
		metavar='agent_id', required=True
	)
	parser.add_argument(
		'--destination-tariff-type', help='Type of tariff that should be assigned to destination vgroups',
		type=int, metavar='tariff_type', required=True
	)
	parser.add_argument(
		'--destination-tariff-prefix', help='Prefix of tariff that should have tariff, that are assigned to '
		'destination vgroups', type=str, metavar='tariff_type', default=None
	)
	parser.add_argument(
		'--export-report', help='Whether to export verbose result to csv-file or not',
		type=str, nargs='?', metavar='filename', default=None
	)
	parser.add_argument(
		'--from-tar-id', help='start tarid (tariff\'s id) number. '
		'Only those vgroups that are assigned to specified tariffs will be migrated',
		**lanbilling_scripts_args['--from-tar-id']
	)
	parser.add_argument(
		'--to-tar-id', help='end tarid (tariff\'s id)  number. '
		'Only those vgroups that are assigned to specified tariffs will be migrated',
		**lanbilling_scripts_args['--to-tar-id']
	)
	parser.add_argument(
		'--from-vg-id', help='start vgid (vgroup\'s id) number. '
		'Only those vgroups whose id are inside the selection will be migrated',
		**lanbilling_scripts_args['--from-vg-id']
	)
	parser.add_argument(
		'--to-vg-id', help='end vgid (vgroup\'s id) number. '
		'Only those vgroups whose id are inside the selection will be migrated',
		**lanbilling_scripts_args['--to-vg-id']
	)
	parser.add_argument(
		'--login',
		help='login pattern to search for. '
		'Only those vgroups whose login has the specified substring will be migrated',
		**lanbilling_scripts_args['--login']
	)
	parser.add_argument(
		'--vgroup-agent-id', help='vgroup agent id. '
		'Only those vgroups that are belongs to the specified agent will be migrated',
		**lanbilling_scripts_args['--vgroup-agent-id']
	)

	args = parser.parse_args()

	if args.destination_agent_id == args.vgroup_agent_id:
		print('Target agent id and vgroup agent id has the same value - nothing more can be done here')
		sys.exit(0)

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
		report_filename = args.export_report
		if report_filename is None:
			report_filename = '/dev/null'

		exporter = WCSVExporter(open(report_filename, 'w'))

		print('Fetching agents')
		agents = rpc.getAgents()
		print('%i agents fetched' % len(agents))

		target_agent = None
		for agent in agents:
			if agent['id'] == args.destination_agent_id:
				target_agent = agent
				break
		if target_agent is None:
			raise ValueError('Unable to find the specified agent (id=%i)' % args.destination_agent_id)

		print('Fetching source vgroups')
		source_vgroups = list(fetch_vgroups(
			rpc, from_vg_id=args.from_vg_id, to_vg_id=args.to_vg_id,
			from_tar_id=args.from_tar_id, to_tar_id=args.to_tar_id,
			login=args.login, vgroup_agent_id=args.vgroup_agent_id, archived_vgroups=False
		))
		print('%i selected vgroups was fetched' % len(source_vgroups))

		destination_tariffs = TariffPrefixCloneGenerator(
			rpc, args.destination_tariff_type, prefix=args.destination_tariff_prefix
		)
		print('%i tariffs with destination type was fetched' % len(destination_tariffs.current_tariffs()))

		for source_v in source_vgroups:
			source_id = source_v['vgid']
			source_agent_id = source_v['id']
			tariff_id = source_v['tarid']
			print('Migrating vgroup with vgid=%i' % source_id)
			migration_report = {
				'source_vgid': source_id, 'source_id': source_agent_id, 'source_tarid': tariff_id
			}

			if source_agent_id == target_agent['id']:
				print('Vgroup is at the specified agent already')
				migration_report.update({
					'skipped': True,
					'supported': None,
					'equal_tarid': None,
					'result_vgid': source_id
				})
				exporter.export(migration_report)
				continue

			full_source_v = rpc.getVgroup(source_id)
			assert(len(full_source_v) == 1)
			full_source_v = full_source_v[0]
			if supported_vgroup(full_source_v) is False:
				print('Unsupported vgroup (vg_id=%i) spotted. Skipping' % source_id)
				migration_report.update({
					'skipped': True,
					'supported': False,
					'equal_tarid': None,
					'result_vgid': None
				})
				exporter.export(migration_report)
				continue
			migration_report['supported'] = True

			current_tariff = list(fetch_tariffs(rpc, from_tar_id=tariff_id, to_tar_id=tariff_id))
			assert(len(current_tariff) == 1)
			current_tariff = current_tariff[0]
			print('Current tariff (with tarid=%i) was found for vgroup (vgid=%i)' % (tariff_id, source_id))

			equal_tariff = destination_tariffs.find_equal(current_tariff)
			if equal_tariff is None:
				print(
					'Unable to migrate vgroup (vgid=%i). Tariff with tarid=%i does not have '
					'suitable analog' % (source_id, tariff_id)
				)
				migration_report.update({
					'skipped': True,
					'equal_tarid': None,
					'result_vgid': None
				})
				exporter.export(migration_report)
				continue

			equal_tariff_id = equal_tariff['tarif']['tarid']
			print(
				'Equal tariff found (tarid=%i) for vgroup with vgid=%i (original tarid=%i)' %
				(equal_tariff_id, source_id, tariff_id)
			)
			migration_report['skipped'] = False
			migration_report['equal_tarid'] = equal_tariff_id

			disable_vgroup(rpc, source_id, target_agent['id'])
			print('Vgroup (vgid=%i) was disabled' % source_id)

			original_login = full_source_v['vgroup']['login']
			disabled_login = original_login + '-disabled-' + datetime.now().isoformat()
			full_source_v['vgroup']['login'] = disabled_login
			rpc.insupdVgroup(0, full_source_v)
			print('Vgroup (vgid=%i) login was renamed to "%s"' % (source_id, disabled_login))

			full_source_v['vgroup']['login'] = original_login
			full_source_v['vgroup']['vgid'] = 0
			full_source_v['vgroup']['id'] = target_agent['id']
			full_source_v['vgroup']['tarid'] = 0
			del full_source_v['vgroup']['uid']
			full_source_v['agentname'] = target_agent['name']
			new_vgroup_id = rpc.insupdVgroup(0, full_source_v)
			print('New vgroup created with vgid=%i (previous value - %i)' % (new_vgroup_id, source_id))
			migration_report['result_vgid'] = new_vgroup_id
			exporter.export(migration_report)

			assign_tariff(rpc, new_vgroup_id, target_agent['id'], equal_tariff_id)
			print('Tariff (tarid=%i) was assigned to vgroup (vgid=%i)' % (equal_tariff_id, new_vgroup_id))

			unblock_vgroup(rpc, new_vgroup_id, target_agent['id'])
			print('New vgroup (vgid=%i) was unblocked' % new_vgroup_id)
			print('Vgroup (vg_id=%i) was migrated to other agent (new vg_id=%i)' % (source_id, new_vgroup_id))

	finally:
		rpc.rpc().Logout()
