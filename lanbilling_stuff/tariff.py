# -*- coding: utf-8 -*-
# lanbilling_stuff/tariff.py
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

from wasp_general.verify import verify_type, verify_value
from wasp_general.csv import WCSVExporter

from lanbilling_stuff.rpc import WLanbillingRPC
from lanbilling_stuff.rpc import fetch_vgroups


@verify_type('paranoid', from_vg_id=(int, None), to_vg_id=(int, None), login=(str, None), vgroup_agent_id=(int, None))
@verify_type('paranoid', archived_vgroups=(bool, None))
@verify_type(rpc_obj=WLanbillingRPC, from_tar_id=(int, None), to_tar_id=(int, None), tariff_type=(int, None))
@verify_value('paranoid', from_vg_id=lambda x: x is None or x >= 0, to_vg_id=lambda x: x is None or x >= 0)
@verify_value('paranoid', login=lambda x: x is None or len(x) > 0, vgroup_agent_id=lambda x: x is None or x >= 0)
@verify_value(from_tar_id=lambda x: x is None or x >= 0, to_tar_id=lambda x: x is None or x >= 0)
def fetch_tariffs(
	rpc_obj, from_vg_id=None, to_vg_id=None, tariff_type=None, from_tar_id=None, to_tar_id=None, login=None,
	vgroup_agent_id=None, archived_vgroups=None
):

	tariff_ids = set()
	vgroups_fetched = False

	for attr in [from_vg_id, to_vg_id, login, vgroup_agent_id, archived_vgroups]:
		if attr is not None:
			vgroups_fetched = True
			vgroups = fetch_vgroups(
				rpc_obj, from_vg_id=from_vg_id, to_vg_id=to_vg_id, from_tar_id=from_tar_id,
				to_tar_id=to_tar_id, login=login, vgroup_agent_id=vgroup_agent_id,
				archived_vgroups=archived_vgroups
			)
			tariff_ids.update(map(lambda x: x['tarid'], vgroups))
			break

	if vgroups_fetched is False:
		if from_tar_id is not None and from_tar_id == to_tar_id:
			tariff_ids.add(from_tar_id)
		else:
			tariff_ids = map(lambda x: x['id'], rpc_obj.rpc().getTarifs())
			if from_tar_id is not None:
				tariff_ids = filter(lambda x: x >= from_tar_id, tariff_ids)
			if to_tar_id is not None:
				tariff_ids = filter(lambda x: x <= to_tar_id, tariff_ids)

	result = map(lambda x: rpc_obj.getTarif(x), tariff_ids)
	result = filter(lambda x: len(x) == 1, result)
	result = map(lambda x: x[0], result)
	if tariff_type is not None:
		result = filter(lambda x: x['tarif']['type'] == tariff_type, result)

	return result


class TariffCloneGenerator:

	@verify_type(rpc=WLanbillingRPC, tariff_type=int)
	@verify_value(tariff_type=lambda x: x > 0)
	def __init__(self, rpc, tariff_type):
		self.__rpc = rpc
		self.__tariff_type = tariff_type
		self.__current_tariffs = list(fetch_tariffs(rpc, tariff_type=self.__tariff_type))

	def rpc(self):
		return self.__rpc

	def tariff_type(self):
		return self.__tariff_type

	def current_tariffs(self):
		return self.__current_tariffs

	def supported_tariff(self, tariff):
		if tariff['sizeshapes'] != []:
			return False
		if tariff['timeshapes'] != []:
			return False
		if tariff['tarif']['trafflimit'] != 0:
			return False
		if tariff['tarif']['archive'] != 0:
			return False
		if tariff['tarif']['catnumbers'] != []:
			return False
		if tariff['tarif']['additional'] != 0:
			return False
		if tariff['tarif']['saledictionaryid'] != 0:
			return False
		return True

	def compare_tariffs(self, tariff_a, tariff_b):
		if tariff_a['sizeshapes'] != tariff_b['sizeshapes']:
			return False

		if tariff_a['timeshapes'] != tariff_b['timeshapes']:
			return False

		dict_a = {x: tariff_a['tarif'][x] for x in tariff_a['tarif']}
		dict_b = {x: tariff_b['tarif'][x] for x in tariff_b['tarif']}

		for key in ['tarid', 'type', 'descr', 'descrfull', 'used', 'uuid', 'saledictionaryid']:
			del dict_a[key]
			del dict_b[key]

		return dict_a == dict_b

	def clone_request(self, tariff):
		tariff_dict = {x: tariff['tarif'][x] for x in tariff['tarif']}
		tariff_dict['tarid'] = 0
		tariff_dict['type'] = self.tariff_type()
		del tariff_dict['uuid']
		del tariff_dict['saledictionaryid']

		return {'tarif': tariff_dict, 'sizeshapes': [], 'timeshapes': []}

	def clone_tariff(self, tariff):
		return self.rpc().insupdTarif(0, self.clone_request(tariff))

	@verify_type(report_filename=(str, None))
	@verify_value(report_filename=lambda x: x is None or len(x) > 0)
	def clone(self, original_tariffs, report_filename=None):
		tariff_type = self.tariff_type()
		current_tariffs = self.current_tariffs()

		if report_filename is None:
			report_filename = '/dev/null'

		exporter = WCSVExporter(open(report_filename, 'w'))

		for original_t in original_tariffs:
			original_id = original_t['tarif']['tarid']

			if original_t['tarif']['type'] == tariff_type:
				print('Skipping tariff with tar_id=%i. Tariff has destination type already' % original_id)
				exporter.export({
					'source_tar_id': original_id,
					'equal_tar_id': original_id,
					'cloned_tar_id': None
				})
				continue

			if self.supported_tariff(original_t) is False:
				raise ValueError('Unsupported tariff spotted (tar_id=%i)' % original_id)

			equal_tariff = None
			for check_t in current_tariffs:
				if self.compare_tariffs(original_t, check_t) is True:
					if self.supported_tariff(check_t) is True:
						equal_tariff = check_t
						break
					else:
						print(
							'Skipping unsupported tariff with tar_id=%i' %
							check_t['tarif']['tarid']
						)

			if equal_tariff is None:
				print('Tariff with tar_id=%i will be cloned' % original_id)
				clone_id = self.clone_tariff(original_t)
				print('Cloned tariff tar_id - %i' % clone_id)
				exporter.export({
					'source_tar_id': original_id,
					'equal_tar_id': None,
					'cloned_tar_id': clone_id
				})
			else:
				equal_id = equal_tariff['tarif']['tarid']
				print(
					'Skipping tariff with tar_id=%i. Equal tariff was found (tar_id=%i)' %
					(original_id, equal_id)
				)
				exporter.export({
					'source_tar_id': original_id,
					'equal_tar_id': equal_id,
					'cloned_tar_id': None
				})


class TariffPrefixCloneGenerator(TariffCloneGenerator):

	@verify_type('paranoid', rpc=WLanbillingRPC, tariff_type=int)
	@verify_value('paranoid', tariff_type=lambda x: x > 0)
	@verify_type(prefix=(str, None))
	def __init__(self, rpc, tariff_type, prefix=None):
		TariffCloneGenerator.__init__(self, rpc, tariff_type)
		self.__tariff_prefix = prefix

	def tariff_prefix(self):
		return self.__tariff_prefix

	def compare_tariffs(self, tariff_a, tariff_b):
		prefix = self.tariff_prefix()
		if prefix is not None:
			if tariff_b['tarif']['descr'] != (prefix + tariff_a['tarif']['descr']):
				return False
		return TariffCloneGenerator.compare_tariffs(self, tariff_a, tariff_b)

	def clone_request(self, tariff):
		request = TariffCloneGenerator.clone_request(self, tariff)
		prefix = self.tariff_prefix()
		if prefix is not None:
			request['tarif']['descr'] = prefix + request['tarif']['descr']
		return request
