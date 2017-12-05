# -*- coding: utf-8 -*-
# lanbilling_stuff/vgroup.py
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
from lanbilling_stuff.rpc import WLanbillingRPC


@verify_type(rpc_obj=WLanbillingRPC, from_vg_id=(int, None), to_vg_id=(int, None), from_tar_id=(int, None))
@verify_type(to_tar_id=(int, None), login=(str, None), vgroup_agent_id=(int, None), archived_vgroups=(bool, None))
@verify_value(from_vg_id=lambda x: x is None or x >= 0, to_vg_id=lambda x: x is None or x >= 0)
@verify_value(from_tar_id=lambda x: x is None or x >= 0, to_tar_id=lambda x: x is None or x >= 0)
@verify_value(login=lambda x: x is None or len(x) > 0, vgroup_agent_id=lambda x: x is None or x >= 0)
def fetch_vgroups(
	rpc_obj, from_vg_id=None, to_vg_id=None, from_tar_id=None, to_tar_id=None, login=None, vgroup_agent_id=None,
	archived_vgroups=None
):

	request_param = {}
	single_vg_id = False
	single_tar_id = False

	if from_vg_id is not None and from_vg_id == to_vg_id:
		single_vg_id = True
		request_param['vgid'] = from_vg_id
	if login is not None:
		request_param['login'] = login
	if vgroup_agent_id is not None:
		request_param['agentid'] = vgroup_agent_id
	if archived_vgroups is not None:
		request_param['archive'] = int(archived_vgroups)
	if from_tar_id is not None and from_tar_id == to_tar_id:
		single_tar_id = True
		request_param['tarid'] = from_tar_id

	records = rpc_obj.rpc().getVgroups(request_param)

	if single_vg_id is False:
		if from_vg_id is not None:
			records = filter(lambda x: x['vgid'] >= from_vg_id, records)
		if to_vg_id is not None:
			records = filter(lambda x: x['vgid'] <= to_vg_id, records)

	if single_tar_id is False:
		if from_tar_id is not None:
			records = filter(lambda x: x['tarid'] >= from_tar_id, records)
		if to_tar_id is not None:
			records = filter(lambda x: x['tarid'] <= to_tar_id, records)

	return records


@verify_type(rpc_obj=WLanbillingRPC, vg_id=int, agent_id=int)
@verify_value(vg_id=lambda x: x >= 0, agent_id=lambda x: x >= 0)
def disable_vgroup(rpc_obj, vg_id, agent_id):
	rpc_obj.insBlkRasp({'recordid': 0, 'vgid': vg_id, 'id': agent_id, 'blkreq': 10})


@verify_type(rpc_obj=WLanbillingRPC, vg_id=int, agent_id=int)
@verify_value(vg_id=lambda x: x >= 0, agent_id=lambda x: x >= 0)
def unblock_vgroup(rpc_obj, vg_id, agent_id):
	rpc_obj.insBlkRasp({'recordid': 0, 'vgid': vg_id, 'id': agent_id, 'blkreq': 0})
