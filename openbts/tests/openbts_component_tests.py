"""openbts.tests.openbts_component_tests
tests for the OpenBTS component
"""

import json
import time
import unittest

import mock

from openbts.components import OpenBTS
from openbts.exceptions import InvalidRequestError
from openbts.codes import (SuccessCode, ErrorCode)


class OpenBTSNominalConfigTestCase(unittest.TestCase):
  """Testing the components.OpenBTS class.

  Applying nominal uses of the 'config' command and 'openbts' target.
  """

  def setUp(self):
    self.openbts_connection = OpenBTS()
    # mock a zmq socket with a simple recv return value
    self.openbts_connection.socket = mock.Mock()
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 204,
      'data': 'sample',
      'dirty': 0
    })

  def test_create_config_raises_error(self):
    """Creating a config key should is not yet supported via NodeManager."""
    with self.assertRaises(InvalidRequestError):
      self.openbts_connection.create_config('sample-key', 'sample-value')

  def test_read_config(self):
    """Reading a key should send a message over zmq and get a response."""
    response = self.openbts_connection.read_config('sample-key')
    # check that we touched the socket to send the message
    self.assertTrue(self.openbts_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'config',
      'action': 'read',
      'key': 'sample-key',
      'value': ''
    })
    # check that we've sent the expected message
    self.assertEqual(self.openbts_connection.socket.send.call_args[0],
                     (expected_message,))
    # we should have touched the socket again to receive the reply
    self.assertTrue(self.openbts_connection.socket.recv.called)
    # verify we received a valid response
    self.assertEqual(response.code, SuccessCode.NoContent)

  def test_update_config(self):
    """Updating a key should send a message over zmq and get a response."""
    response = self.openbts_connection.update_config('sample-key',
                                                     'sample-value')
    self.assertTrue(self.openbts_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'config',
      'action': 'update',
      'key': 'sample-key',
      'value': 'sample-value'
    })
    self.assertEqual(self.openbts_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.openbts_connection.socket.recv.called)
    self.assertEqual(response.code, 204)

  def test_delete_config_raises_error(self):
    """Deleting a config key should is not yet supported via NodeManager."""
    with self.assertRaises(InvalidRequestError):
      self.openbts_connection.delete_config('sample-key')

  def test_responses_with_no_dirty_param(self):
    """We should handle responses that don't have the 'dirty' attribute."""
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': 'sample'
    })
    response = self.openbts_connection.read_config('sample-key')
    self.assertEqual(response.code, SuccessCode.OK)

  def test_responses_with_no_data_param(self):
    """We should handle responses that don't have the 'data' attribute."""
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 200,
    })
    response = self.openbts_connection.read_config('sample-key')
    self.assertEqual(response.code, SuccessCode.OK)


class OpenBTSOffNominalConfigTestCase(unittest.TestCase):
  """Testing the components.OpenBTS class.

  Examining off-nominal behaviors of the 'config' command and 'openbts' target.
  """

  def setUp(self):
    self.openbts_connection = OpenBTS()
    # mock a zmq socket
    self.openbts_connection.socket = mock.Mock()

  def test_read_config_unknown_key(self):
    """Reading a nonexistent key raises an error."""
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 404,
    })
    with self.assertRaises(InvalidRequestError):
      self.openbts_connection.read_config('nonexistent-key')

  def test_update_config_invalid_value(self):
    """Updating a value outside the allowed range raises an error."""
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 406,
    })
    with self.assertRaises(InvalidRequestError):
      self.openbts_connection.update_config('sample-key', 'sample-value')

  def test_update_config_storing_value_fails(self):
    """If storing the new value fails, an error should be raised."""
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 500,
    })
    with self.assertRaises(InvalidRequestError):
      self.openbts_connection.update_config('sample-key', 'sample-value')


class OpenBTSNominalGetVersionTestCase(unittest.TestCase):
  """Testing the 'get_version' command on the components.OpenBTS class."""

  def setUp(self):
    self.openbts_connection = OpenBTS()
    # mock a zmq socket with a simple recv return value
    self.openbts_connection.socket = mock.Mock()
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': 'release 4.0.0.8025'
    })

  def test_get_version(self):
    """The 'get_version' command should return a response."""
    response = self.openbts_connection.get_version()
    self.assertTrue(self.openbts_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'version',
      'action': '',
      'key': '',
      'value': ''
    })
    self.assertEqual(self.openbts_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.openbts_connection.socket.recv.called)
    self.assertEqual(response.data, 'release 4.0.0.8025')

class OpenBTSNominalTMSIsTestCase(unittest.TestCase):
  """Testing the 'tmsis' command on the components.OpenBTS class."""

  def setUp(self):
    self.openbts_connection = OpenBTS()
    # mock a zmq socket with a simple recv return value
    self.openbts_connection.socket = mock.Mock()
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': [
        {
          'ACCESSED' : time.time() - 30,
          'IMSI' : '901550000000084',
        },
        {
          'ACCESSED' : time.time() - 180,
          'IMSI' : '901550000000082',
        }
      ]
    })

  def test_tmsis(self):
    """The 'tmsis' command should return a response."""
    response = self.openbts_connection.tmsis(access_period=90)
    self.assertTrue(self.openbts_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'tmsis',
      'action': 'read',
      'match': {'AUTH': '2'},
      'fields': ['IMSI', 'ACCESSED']
    })
    self.assertEqual(self.openbts_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.openbts_connection.socket.recv.called)
    self.assertEqual(len(response), 1)
    self.assertEqual(response[0]['IMSI'], '901550000000084')

class OpenBTSNominalMonitorTestCase(unittest.TestCase):
  """Testing the 'monitor' command on the components.OpenBTS class."""

  def setUp(self):
    self.openbts_connection = OpenBTS()
    # mock a zmq socket with a simple recv return value
    self.openbts_connection.socket = mock.Mock()
    self.openbts_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': {
        'noiseRSSI': -68
      }
    })

  def test_monitor(self):
    """The 'monitor' command should return a response."""
    response = self.openbts_connection.monitor()
    self.assertTrue(self.openbts_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'monitor',
      'action': '',
      'key': '',
      'value': ''
    })
    self.assertEqual(self.openbts_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.openbts_connection.socket.recv.called)
    self.assertEqual(response.data['noiseRSSI'], -68)
