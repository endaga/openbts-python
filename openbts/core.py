"""openbts.core
defines the base component and responses
"""

import json

import zmq

from openbts.exceptions import (InvalidRequestError, InvalidResponseError,
                                TimeoutError)
from openbts.codes import (SuccessCode, ErrorCode)

class BaseComponent(object):
  """Manages a zeromq connection.

  The intent is to create other components that inherit from this base class.

  Kwargs:
    socket_timeout: time in seconds to wait on self.socket.recv before raising
        a TimeoutError
  """

  def __init__(self, **kwargs):
    context = zmq.Context()
    # the component inheriting from BaseComponent should call connect on this
    # socket with the appropriate address
    self.socket = context.socket(zmq.REQ)
    self.socket.setsockopt(zmq.LINGER, 0) # zmq.LINGER sets a timeout for socket.send
    self.socket_timeout = kwargs.pop('socket_timeout', 10)

  def create_config(self, key, value):
    """Create a config parameter and initialize it.

    This functionality is not yet available via Node Manager.  The method will
    be left for completeness but will always raise an InvalidRequestError.

    Args:
      key: the config parameter to create
      value: the initial value of the new parameter

    Always raises:
      InvalidRequestError as this functionality is not yet available via the
          Node Manager
    """
    raise InvalidRequestError('create config not implemented')

  def read_config(self, key):
    """Reads a config value.

    Args:
      key: the config parameter to inspect

    Returns:
      Response instance

    Raises:
      InvalidRequestError if the key does not exist
    """
    message = {
      'command': 'config',
      'action': 'read',
      'key': key,
      'value': ''
    }
    return self._send_and_receive(message)

  def update_config(self, key, value):
    """Updates a config value.

    Args:
      key: the config parameter to update
      value: set the config parameter to this value

    Returns:
      Response instance

    Raises:
      InvalidRequestError if the key does not exist
    """
    message = {
      'command': 'config',
      'action': 'update',
      'key': key,
      'value': str(value)
    }
    response = self._send_and_receive(message)
    return response

  def delete_config(self, key):
    """Deletes a config value.

    This functionality is not yet available via Node Manager.  The method will
    be left for completeness but will always raise an InvalidRequestError.

    Args:
      key: the config parameter to delete

    Always raises:
      InvalidRequestError as this functionality is not yet available via the
          Node Manager
    """
    raise InvalidRequestError('delete config not implemented')

  def get_version(self):
    """Query the version of a component.

    Returns:
      Response instance
    """
    message = {
      'command': 'version',
      'action': '',
      'key': '',
      'value': ''
    }
    response = self._send_and_receive(message)
    return response

  def _send_and_receive(self, message):
    """Sending payloads to NM and returning Response instances.

    Or, if the action failed, an error will be raised during the instantiation
    of the Response.  Can also timeout if the socket receives no data for some
    period.

    Args:
      message: dict of a message to send to NM

    Returns:
      Response instance if the request succeeded

    Raises:
      TimeoutError: if nothing is received for the timeout
    """
    # send the message and poll for responses
    self.socket.send(json.dumps(message))
    responses = self.socket.poll(timeout=self.socket_timeout * 1000)
    if responses:
      raw_response_data = self.socket.recv()
      return Response(raw_response_data)
    else:
      raise TimeoutError('did not receive a response')


class Response(object):
  """Provides access to the response data.

  Raises an exception if the request was not successful (e.g. key not found).
  Note that we are explicitly ignoring NodeManager error code 501 (unknown
  action).  We are tightly controlling the specified action, so we do not
  expect to encounter this error.

  Args:
    raw_response_data: json-encoded text received by zmq

  Attributes:
    code: the response code (matches HTTP response code spec)
    data: text or dict of response data
    dirty: boolean that, if True, indicates that the command will take effect
        only when the component is restarted
  """
  def __init__(self, raw_response_data):
    data = json.loads(raw_response_data)
    if 'code' not in data.keys():
      raise InvalidResponseError('key "code" not in raw response: "%s"' %
                                 raw_response_data)
    # if the request was successful, create a response object and exit
    if data['code'] in list(SuccessCode):
      self.code = SuccessCode(data['code'])
      self.data = data.get('data', None)
      self.dirty = data.get('dirty', None)
      return

    # if the request failed for some reason, raise an error
    if data['code'] in list(ErrorCode):
      if data['code'] == ErrorCode.NotFound:
        raise InvalidRequestError('not found')
      elif data['code'] == ErrorCode.InvalidRequest:
        msg = data['data'] if 'data' in data else 'invalid value'
        raise InvalidRequestError(msg)
      elif data['code'] == ErrorCode.ConflictingValue:
        # TODO(matt): if creating config values isn't possible, will we ever
        #             see the 409 code?
        raise InvalidRequestError('conflicting value')
      elif data['code'] == ErrorCode.StoreFailed:
        raise InvalidRequestError('storing new value failed')
      elif data['code'] == ErrorCode.ServiceUnavailable:
        raise InvalidRequestError('service unavailable')
      elif data['code'] == ErrorCode.UnknownAction:
        raise InvalidRequestError('unknown action')
    # handle unknown response codes
    else:
      raise InvalidResponseError('code "%s" not known' % data['code'])
