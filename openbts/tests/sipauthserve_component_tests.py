"""openbts.tests.sipauthserve_component_tests
tests for the SIPAuthServe component
"""

import json
import unittest

import mock

from openbts.components import SIPAuthServe
from openbts.exceptions import InvalidRequestError


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

  def test_read_config_sends_message_and_receives_response(self):
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
    self.assertEqual(response.code, 204)

  def test_update_config_sends_message_and_receives_response(self):
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
    self.assertEqual(response.code, 204)

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
      'data': 'sample',
      'dirty': 0
    })

  def test_get_subscribers(self):
    """Requesting all subscribers should send a message over zmq and get a
    response.
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': ['subscriber_a', 'subscriber_b']
    })
    response = self.sipauthserve_connection.get_subscribers()
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'read',
      'key': '',
      'value': ''
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, 200)

  def test_create_subscriber_with_ki_sends_message_and_receives_response(self):
    """Creating a subscriber with a specficied ki should send a message over
    zmq and get a response.
    """
    response = self.sipauthserve_connection.create_subscriber('sample-name',
        310150123456789, 123456789, 'abc')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'create',
      'fields': {
        'name': 'sample-name',
        'imsi': '310150123456789',
        'msisdn': '123456789',
        'ki': 'abc'
      }
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, 204)

  def test_create_subscriber_sans_ki_sends_message_and_receives_response(self):
    """Creating a subscriber without a specficied ki should still send a
    message over zmq and get a response.
    """
    response = self.sipauthserve_connection.create_subscriber('sample-name',
        310150123456789, 123456789)
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'create',
      'fields': {
        'name': 'sample-name',
        'imsi': '310150123456789',
        'msisdn': '123456789',
        'ki': ''
      }
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, 204)

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
    self.assertEqual(response.code, 204)
