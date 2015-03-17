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

  def count_subscribers(self):
    """Counts the total number of subscribers.

    Returns:
      integer number of subscribers
    """
    try:
      result = self.get_subscribers()
      result = len(result)
    except InvalidRequestError:
      # 404 -- no subscribers found.
      result = 0
    return result

  def get_subscribers(self, imsi=None):
    """Gets subscribers, optionally filtering by IMSI.

    Args:
      imsi: the IMSI to search by

    Returns:
      array of subscriber dicts

    Raises:
      InvalidRequestError if no qualified entry exists
    """
    qualifiers = {}
    if imsi:
      qualifiers['name'] = imsi
    fields = ['name', 'ipaddr', 'port']
    message = {
      'command': 'sip_buddies',
      'action': 'read',
      'match': qualifiers,
      'fields': fields,
    }
    response = self._send_and_receive(message)
    subscribers = response.data
    # Now query for the associated numbers.  And join on the IMSI to combine
    # data from sip_buddies and dialdata.
    numbers = self.get_numbers(imsi)
    for subscriber in subscribers:
      subscriber['numbers'] = []
      for number in numbers:
        if subscriber['name'] == number:
          subscriber['numbers'].append(number['exten'])
    return subscribers

  def get_ipaddr(self, imsi):
    """Get the IP address of a subscriber."""
    fields = ['ipaddr']
    qualifiers = {
      'name': imsi
    }
    response = self.read_sip_buddies(fields, qualifiers)
    return response.data[0]['ipaddr']

  def get_port(self, imsi):
    """Get the port of a subscriber."""
    fields = ['port']
    qualifiers = {
      'name': imsi
    }
    response = self.read_sip_buddies(fields, qualifiers)
    return response.data[0]['port']

  def get_numbers(self, imsi):
    """Get the numbers associated with a subscriber.
    
    If imsi is None, get all numbers."""
    fields = ['exten']
    qualifiers = {}
    if imsi:
      qualifiers['dial'] = imsi
    response = self.read_dialdata(fields, qualifiers)
    return [d['exten'] for d in response.data]

  def add_number(self, imsi, number):
    """Associate a new number with an IMSI."""
    message = {
      'command': 'dialdata_table',
      'action': 'create',
      'fields': {
        'dial': str(imsi),
        'exten': str(number),
      }
    }
    return self._send_and_receive(message)

  def delete_number(self, imsi, number):
    """De-associate a number with an IMSI."""
    # First see if the number is attached to the subscriber.
    if number not in self.get_numbers(imsi):
      raise ValueError('number %s not attached to IMSI %s' % (number, imsi))
    message = {
      'command': 'dialdata_table',
      'action': 'delete',
      'match': {
        'dial': str(imsi),
        'exten': str(number),
      }
    }
    result = self._send_and_receive(message)
    print result.code
    print result.data
    return result

  def create_subscriber(self, imsi, msisdn, ipaddr, port, ki=''):
    """Add a subscriber.

    Technically we don't need every subscriber to have a number, but we'll just
    enforce this by convention.  We will also set the convention that a
    subscriber's name === their imsi.  Some things in NM are keyed on 'name'
    however, so we have to use both when making queries and updates.

    If the 'ki' argument is given, OpenBTS will use full auth.  Otherwise the
    system will use cache auth.  The values of IMSI, MSISDN and ki will all
    be cast to strings before the message is sent.

    Args:
      imsi: IMSI of the subscriber
      msisdn: MSISDN of the subscriber (their phone number)
      ipaddr: IP of the subscriber's OpenBTS instance
      port: port of the subscriber's OpenBTS instance
      ki: authentication key of the subscriber

    Returns:
      Response instance
    """
    message = {
      'command': 'subscribers',
      'action': 'create',
      'fields': {
        'imsi': str(imsi),
        'msisdn': str(msisdn),
        'ipaddr': str(ipaddr),
        'port': str(port),
        'name': str(imsi),
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

  def update_ipaddr(self, imsi, new_ipaddr):
    """Updates a subscriber's IP address."""
    message = {
      'command': 'sip_buddies',
      'action': 'update',
      'match': {
        'name': imsi
      },
      'fields': {
        'ipaddr': new_ipaddr
      }
    }
    return self._send_and_receive(message)

  def update_port(self, imsi, new_port):
    """Updates a subscriber's port."""
    message = {
      'command': 'sip_buddies',
      'action': 'update',
      'match': {
        'name': imsi
       },
      'fields': {
        'port': new_port,
       }
    }
    return self._send_and_receive(message)

  def update_subscriber(self, imsi, new_msisdn, new_ipaddr, new_port):
    """Update a subscriber by IMSI.

    Args:
      imsi: the IMSI of the to-be-updated subscriber
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
          'msisdn': new_msisdn,
          'ipaddr': new_ipaddr,
          'port': new_port,
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
    # This is the only check we really need to do on the client -- NodeManager
    # will handle the rest.
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
    # This is the only check we really need to do on the client NodeManager
    # will handle the rest.
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
