# -*- coding: utf-8 -*-
# lanbilling_stuff/rpc.py
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

# TODO: document the code
# TODO: write tests for the code

# noinspection PyUnresolvedReferences
from lanbilling_stuff.version import __author__, __version__, __credits__, __license__, __copyright__, __email__
# noinspection PyUnresolvedReferences
from lanbilling_stuff.version import __status__

import zeep.exceptions
from zeep import Client as SOAPClient
from getpass import getpass

from wasp_general.verify import verify_type, verify_value
from wasp_general.config import WConfig


class WLanbillingRPC:

	class MethodProxy:

		def __init__(self, lanbilling_rpc, soap_service, method_name):
			self.lanbilling_rpc = lanbilling_rpc
			self.soap_service = soap_service
			self.method_name = method_name

		def __call__(self, *args, **kwargs):
			try:
				return getattr(self.soap_service, self.method_name)(*args, **kwargs)
			except zeep.exceptions.Fault as e:
				if e.message != 'error_auth' or self.method_name in ('Login', 'Logout'):
					raise

			self.lanbilling_rpc.connect()
			self.soap_service = self.lanbilling_rpc.rpc()
			return getattr(self.soap_service, self.method_name)(*args, **kwargs)

	@verify_type(hostname=(str, None), login=(str, None), password=(str, None), wsdl_url=(str, None))
	@verify_type(soap_proxy=bool, soap_proxy_service=(str, None), soap_proxy_address=(str, None))
	@verify_value(hostname=lambda x: x is None or len(x) > 0, login=lambda x: x is None or len(x) > 0)
	@verify_value(wsdl_url=lambda x: x is None or len(x) > 0, soap_proxy_service=lambda x: x is None or len(x) > 0)
	@verify_value(soap_proxy_address=lambda x: x is None or len(x) > 0)
	def __init__(
		self, hostname=None, login=None, password=None, wsdl_url=None, soap_proxy=False,
		soap_proxy_service=None, soap_proxy_address=None
	):
		default = lambda x, d: x if x is not None else d

		self.__hostname = default(hostname, 'localhost')
		self.__login = default(login, 'admin')
		self.__password = default(password, '')
		self.__wsdl_url = default(wsdl_url, ('http://%s/admin/soap/api3.wsdl' % hostname))

		self.__soap_proxy_address = None
		self.__soap_proxy_service = None
		if soap_proxy is True:
			self.__soap_proxy_address = default(soap_proxy_address, ('http://%s:34012' % hostname))
			self.__soap_proxy_service = default(soap_proxy_service, '{urn:api3}api3')

		self.__client = None
		self.__service = None

	def hostname(self):
		return self.__hostname

	def login(self):
		return self.__login

	def password(self):
		return self.__password

	def wsdl_url(self):
		return self.__wsdl_url

	def proxy_address(self):
		return self.__soap_proxy_address

	def proxy_service(self):
		return self.__soap_proxy_service

	def soap_client(self):
		return self.__client

	def soap_proxy(self):
		return self.__service

	def connect(self):
		self.close()
		self.__client = SOAPClient(self.__wsdl_url)
		proxy_address = self.proxy_address()
		proxy_service = self.proxy_service()

		if proxy_address is not None and proxy_service is not None:
			self.__service = self.__client.create_service(proxy_service, proxy_address)
		self._rpc().Login(self.__login, self.__password)

	def _rpc(self):
		if self.__service is not None:
			return self.__service
		if self.__client is not None:
			return self.__client.service
		raise RuntimeError('RPC call before connect')

	def close(self):
		if self.__client is not None:
			self._rpc().Logout()
		self.__client = None
		self.__service = None

	def rpc(self):
		if self.__client is None:
			self.connect()
		return self._rpc()

	def __getattr__(self, item):
		try:
			return object.__getattribute__(self, item)
		except AttributeError:
			pass
		return WLanbillingRPC.MethodProxy(self, self.rpc(), item)

	@classmethod
	@verify_type(config=WConfig, section_name=str, password_prompt=bool)
	@verify_value(section_name=lambda x: len(x) > 0)
	def from_configuration(cls, config, section_name, password_prompt=False):
		login = config[section_name]['login'].strip()
		if len(login) == 0:
			login = None

		password = None
		if config.has_option(section_name, 'password') is True:
			password = config[section_name]['password'].strip()
			if len(password) == 0:
				password = None
		elif password_prompt is True:
			password = getpass('Please, type in password for Lanbilling: ')

		hostname = config[section_name]['hostname'].strip()
		if len(hostname) == 0:
			hostname = None

		wsdl_url = config[section_name]['wsdl_url'].strip()
		if len(wsdl_url) == 0:
			wsdl_url = None

		soap_proxy_address = config[section_name]['soap_proxy_address'].strip()
		if len(soap_proxy_address) == 0:
			soap_proxy_address = None
			soap_proxy = False
		else:
			soap_proxy = True

		return WLanbillingRPC(
			hostname=hostname, login=login, password=password,
			wsdl_url=wsdl_url, soap_proxy_address=soap_proxy_address, soap_proxy=soap_proxy
		)


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
