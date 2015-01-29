"""openbts.components
manages components in the OpenBTS application suite
"""

from openbts.core import BaseComponent
from openbts.exceptions import InvalidRequestError

class OpenBTS(BaseComponent):
  """Manages communication to an OpenBTS instance.

  Args:
    address: tcp socket for the zmq connection
  """

  def __init__(self, address='tcp://127.0.0.1:45060'):
    super(OpenBTS, self).__init__()
    self.socket.connect(address)

  def __repr__(self):
    return 'OpenBTS component'

  def monitor(self):
    """Monitor channel loads, queue sizes and noise levels.

    See 3.4.4 of the OpenBTS 4.0 Manual for more info.

    Returns:
      Response instance
    """
    message = {
      'command': 'monitor',
      'action': '',
      'key': '',
      'value': ''
    }
    return self._send_and_receive(message)


class SIPAuthServe(BaseComponent):
  """Manages communication to the SIPAuthServe service.

  Args:
    address: tcp socket for the zmq connection
  """

  def __init__(self, address='tcp://127.0.0.1:45064'):
    super(SIPAuthServe, self).__init__()
    self.socket.connect(address)

  def __repr__(self):
    return 'SIPAuthServe component'

  def get_subscribers(self, imsi=None, msisdn=None, name=None):
    """Gets subscribers filtering by IMSI, MSISDN, and/or name

    Args:
      imsi: the IMSI to search by
      name: the Name to search by
      msisdn: the number to search by

    Returns:
      Response instance

    Raises:
      InvalidRequestError if no qualified entry exists

    """

    qualifiers = {'imsi': imsi, 'msisdn': msisdn, 'name': name}

    # remove empty qualifiers
    for key in qualifiers.keys():
      if not qualifiers[key]:
        del qualifiers[key]

    message = {
      'command': 'subscribers',
      'action': 'read',
      'match': qualifiers
    }
    response = self._send_and_receive(message)
    return response

  def create_subscriber(self, name, imsi, msisdn, ipaddr, port, ki=''):
    """Add a subscriber.

    If the 'ki' argument is given, OpenBTS will use full auth.  Otherwise the
    system will use cache auth.  The values of IMSI, MSISDN and ki will all
    be cast to strings before the message is sent.

    Args:
      name: name of the subscriber
      imsi: IMSI of the subscriber
      msisdn: MSISDN of the subscriber
      ip: IP of the subscriber
      port: port of the subscriber
      ki: authentication key of the subscriber

    Returns:
      Response instance
    """
    message = {
      'command': 'subscribers',
      'action': 'create',
      'fields': {
        'name': name,
        'imsi': str(imsi),
        'msisdn': str(msisdn),
        'ipaddr': str(ipaddr),
        'port': str(port),
        'ki': str(ki)
      }
    }
    response = self._send_and_receive(message)
    return response

  def delete_subscriber(self, imsi):
    """Delete a subscriber by IMSI.

    Args:
      imsi: the IMSI of the to-be-deleted subscriber

    Returns:
      Response instance
    """
    message = {
      'command': 'subscribers',
      'action': 'delete',
      'match': {
        'imsi': str(imsi)
      }
    }
    response = self._send_and_receive(message)
    return response

  def update_subscriber(self, new_name, new_msisdn, new_ipaddr, new_port, imsi):
    """Update a subscriber by IMSI.

    Args:
      imsi: the IMSI of the to-be-updated subscriber
      new_name: the new name value
      new_msisdn: the new number
      new_ipaddr: the new ipaddr
      new_port: the new port

    Returns:
      Response instance

    Raises:
      InvalidRequestError: if a field is missing or request failed
      InvalidResponseError: if the operation failed
    """

    message = {
      'command': 'subscribers',
      'action': 'update',
      'match': {
          'imsi': imsi
       },
      'fields': {
          'name': new_name,
          'msisdn': new_msisdn,
          'ipaddr': new_ipaddr,
          'port': new_port
       }
    }
    return self._send_and_receive(message)

  def read_dialdata(self, fields, qualifier):
    """Reads a dial_data row entry.

    Args:
      fields: A list of column names in dialdata_table, if None return all
      qualifier: A dictionary of qualifiers

    Returns:
      Response instance

    Raises:
      InvalidRequestError if no qualified entry exists
    """

    return self._read_subscriber_registry('dialdata_table', fields, qualifier)


  def read_sip_buddies(self, fields, qualifier):
    """Reads a sip_buddies row entry.

    Args:
      fields: A list of column names in sip_buddies, if None return all
      qualifier: A dictionary of qualifiers

    Returns:
      Response instance

    Raises:
      InvalidRequestError if no qualified entry exists
    """
    return self._read_subscriber_registry('sip_buddies', fields, qualifier)

  def update_dialdata(self, fields, qualifier):
    """Updates a dial_data row entry.

    Args:
      fields: A dict of values to update
      qualifier: A dictionary of qualifiers

    Returns:
      Response instance

    Raises:
      InvalidRequestError if no qualified entry exists
    """

    return self._update_subscriber_registry('dialdata_table', fields, qualifier)

  def update_sip_buddies(self, fields, qualifier):
    """Updates a sip_buddies row entry.

    Args:
      fields: A dict of values to update
      qualifier: A dictionary of qualifiers

    Returns:
      Response instance

    Raises:
      InvalidRequestError if no qualified entry exists
    """
    return self._update_subscriber_registry('sip_buddies', fields, qualifier)

  def _update_subscriber_registry(self, table_name, fields, qualifier):
    """Reads an entry from one of the subscriber registry tables.

    Args:
      table_name: the name of the subscriber registry table
      fields: A dictionary of values of update
      qualifier: A dictionary of qualifiers

    Returns:
      Response instance

    Raises:
      InvalidRequestError if no qualified entry exists
    """

    # this is the only check we really need to do on the client
    # node manager will handle the rest
    if table_name not in ('sip_buddies', 'dialdata_table', 'RRLP'):
        raise InvalidRequestError('Invalid SR table name')
    if not isinstance(fields, dict) or not isinstance(qualifier, dict):
        raise InvalidRequestError('Invalid argument passed')

    message = {
      'command': table_name,
      'action': 'update',
      'match': qualifier,
      'fields': fields
    }

    return self._send_and_receive(message)

  def _read_subscriber_registry(self, table_name, fields, qualifier):
    """Reads an entry from one of the subscriber registry tables.

    Args:
      table_name: the name of the subscriber registry table
      fields: A list of column names in the table, if None return all
      qualifier: A dictionary of qualifiers

    Returns:
      Response instance

    Raises:
      InvalidRequestError if no qualified entry exists
    """

    # this is the only check we really need to do on the client
    # node manager will handle the rest
    if table_name not in ('sip_buddies', 'dialdata_table'):
        raise InvalidRequestError('Invalid SR table name')
    if (fields is not None and not isinstance(fields, list)) \
            or not isinstance(qualifier, dict):
        raise InvalidRequestError('Invalid argument passed')

    message = {
      'command': table_name,
      'action': 'read',
      'match': qualifier,
      'fields': fields,
    }

    return self._send_and_receive(message)

class SMQueue(BaseComponent):
  """Manages communication to the SMQueue service.

  Args:
    address: tcp socket for the zmq connection
  """

  def __init__(self, address='tcp://127.0.0.1:45063'):
    super(SMQueue, self).__init__()
    self.socket.connect(address)

  def __repr__(self):
    return 'SMQueue component'
