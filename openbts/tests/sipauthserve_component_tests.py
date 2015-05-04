"""openbts.tests.sipauthserve_component_tests
tests for the SIPAuthServe component
"""

import json
import unittest

import mock

from openbts.components import SIPAuthServe
from openbts.exceptions import InvalidRequestError
from openbts.codes import SuccessCode


class SIPAuthServeNominalConfigTestCase(unittest.TestCase):
  """Testing the components.SIPAuthServe class.

  Applying nominal uses of the 'config' command and 'sipauthserve' target.
  """

  def setUp(self):
    self.sipauthserve_connection = SIPAuthServe()
    # mock a zmq socket with a simple recv return value
    self.sipauthserve_connection.socket = mock.Mock()
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 204,
      'data': 'sample',
      'dirty': 0
    })

  def test_create_config_raises_error(self):
    """Creating a config key should is not yet supported via NodeManager."""
    with self.assertRaises(InvalidRequestError):
      self.sipauthserve_connection.create_config('sample-key', 'sample-value')

  def test_read_config(self):
    """Reading a key should send a message over zmq and get a response."""
    response = self.sipauthserve_connection.read_config('sample-key')
    # check that we touched the socket to send the message
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'config',
      'action': 'read',
      'key': 'sample-key',
      'value': ''
    })
    # check that we've sent the expected message
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    # we should have touched the socket again to receive the reply
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    # verify we received a valid response
    self.assertEqual(response.code, SuccessCode.NoContent)

  def test_update_config(self):
    """Updating a key should send a message over zmq and get a response."""
    response = self.sipauthserve_connection.update_config('sample-key',
                                                     'sample-value')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'config',
      'action': 'update',
      'key': 'sample-key',
      'value': 'sample-value'
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.NoContent)

  def test_delete_config_raises_error(self):
    """Deleting a config key should is not yet supported via NodeManager."""
    with self.assertRaises(InvalidRequestError):
      self.sipauthserve_connection.delete_config('sample-key')


class SIPAuthServeOffNominalConfigTestCase(unittest.TestCase):
  """Testing the components.SIPAuthServe class.

  Examining off-nominal behaviors of the 'config' command and 'sipauthserve'
  target.
  """

  def setUp(self):
    self.sipauthserve_connection = SIPAuthServe()
    # mock a zmq socket
    self.sipauthserve_connection.socket = mock.Mock()

  def test_read_config_unknown_key(self):
    """Reading a nonexistent key raises an error."""
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 404,
    })
    with self.assertRaises(InvalidRequestError):
      self.sipauthserve_connection.read_config('nonexistent-key')

  def test_update_config_invalid_value(self):
    """Updating a value outside the allowed range raises an error."""
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 406,
    })
    with self.assertRaises(InvalidRequestError):
      self.sipauthserve_connection.update_config('sample-key', 'sample-value')

  def test_update_config_storing_value_fails(self):
    """If storing the new value fails, an error should be raised."""
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 500,
    })
    with self.assertRaises(InvalidRequestError):
      self.sipauthserve_connection.update_config('sample-key', 'sample-value')


class SIPAuthServeNominalGetVersionTestCase(unittest.TestCase):
  """Testing the 'get_version' command on the components.SIPAuthServe class."""

  def setUp(self):
    self.sipauthserve_connection = SIPAuthServe()
    # mock a zmq socket with a simple recv return value
    self.sipauthserve_connection.socket = mock.Mock()
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': 'release 7'
    })

  def test_get_version(self):
    """The 'get_version' command should return a response."""
    response = self.sipauthserve_connection.get_version()
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'version',
      'action': '',
      'key': '',
      'value': ''
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.data, 'release 7')


class SIPAuthServeNominalSubscriberTestCase(unittest.TestCase):
  """Testing the components.SIPAuthServe class.

  Applying nominal uses of the 'subscribers' command and 'sipauthserve' target.
  """

  def setUp(self):
    self.sipauthserve_connection = SIPAuthServe()
    # mock a zmq socket with a simple recv return value
    self.sipauthserve_connection.socket = mock.Mock()
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 204,
      'data': [{'exten': '5551234', 'name': 'sample'}],
      'dirty': 0
    })

  def test_get_all_subscribers(self):
    """Requesting all subscribers should send a message over zmq and get a
    response.
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': [
        {'name': 'subscriber_a', 'exten': '5551234'},
        {'name': 'subscriber_b', 'exten': '5551456'}
      ]
    })
    self.sipauthserve_connection.get_subscribers()
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)

  def test_get_a_subscriber(self):
    """Requesting a subscriber using a filter should send a message over
    zmq and get a response.
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': [
        {'name': 'subscriber_filered', 'exten': '5551234'},
      ]
    })
    self.sipauthserve_connection.get_subscribers(imsi='IMSI000000')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)

  def test_create_subscriber_with_ki(self):
    """Creating a subscriber with a specficied ki should send a message over
    zmq and get a response.
    """
    response = self.sipauthserve_connection.create_subscriber(
        310150123456789, 123456789, '127.0.0.1', '1234', ki='abc')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    # TODO(matt): not the best test as the socket should be called twice..once
    #             for subscribers and once for dialdata..but this is also
    #             covered in the integration testing..
    expected_message = json.dumps({
      "action": "create",
      "fields": {
        "exten": "123456789",
        "dial": "310150123456789"
      },
      "command": "dialdata_table"
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.NoContent)

  def test_create_subscriber_sans_ki(self):
    """Creating a subscriber without a specficied ki should still send a
    message over zmq and get a response.
    """
    response = self.sipauthserve_connection.create_subscriber(
        310150123456789, 123456789, '127.0.0.1', '1234')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      "action": "create",
      "fields": {
        "exten": "123456789",
        "dial": "310150123456789"
      },
      "command": "dialdata_table"
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.NoContent)

  def test_delete_subscriber_by_imsi(self):
    """Deleting a subscriber by passing an IMSI should send a message over zmq
    and get a response.
    """
    response = self.sipauthserve_connection.delete_subscriber(310150123456789)
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'delete',
      'match': {
        'imsi': '310150123456789'
      }
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.NoContent)


class SIPAuthServeNonNominalSubscriberTestCase(unittest.TestCase):
  """Testing the components.SIPAuthServe class.

  Applying nonnominal uses of the 'subscribers' command and 'sipauthserve' target.
  """

  def setUp(self):
    self.sipauthserve_connection = SIPAuthServe()
    # mock a zmq socket with a simple recv return value
    self.sipauthserve_connection.socket = mock.Mock()
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': 'sample',
      'dirty': 0
    })

  def test_get_nonexistent_subscribers(self):
    """Requesting a nonexistent subscriber returns an empty array."""
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 404,
      'data': 'not found'
    })
    response = self.sipauthserve_connection.get_subscribers(
        imsi='non-existent')
    self.assertEqual([], response)

  def test_delete_subscriber_when_sqlite_unavailable(self):
    """Testing the subscriber deletion case when OpenBTS reports sqlite is unavailble"""
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 503,
      'data': {
          'sip_buddies': 'something bad',
          'dialdata_table': 'this could be ok'
        }
      })
    with self.assertRaises(InvalidRequestError):
        response = self.sipauthserve_connection.delete_subscriber(310150123456789)
