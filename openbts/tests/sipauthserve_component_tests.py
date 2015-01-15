"""openbts.tests.sipauthserve_component_tests
tests for the SIPAuthServe component
"""

import json
import unittest

import mock

from openbts.components import SIPAuthServe
from openbts.exceptions import InvalidRequestError
from openbts.codes import (SuccessCode, ErrorCode)


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
      'data': 'sample',
      'dirty': 0
    })

  def test_get_all_subscribers(self):
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
      'match': {},
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.OK)

  def test_get_a_subscribers(self):
    """Requesting a subscriber using a filter should send a message over
    zmq and get a response.
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': ['subscriber_filtered']
    })
    response = self.sipauthserve_connection.get_subscribers(imsi='IMSI000000',
            msisdn='000000', name='TEST')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'read',
      'match': {
          'imsi': 'IMSI000000',
          'msisdn': '000000',
          'name': 'TEST'
          },
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.OK)

  def test_create_subscriber_with_ki(self):
    """Creating a subscriber with a specficied ki should send a message over
    zmq and get a response.
    """
    response = self.sipauthserve_connection.create_subscriber('sample-name',
        310150123456789, 123456789, '127.0.0.1', '1234', 'abc')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'create',
      'fields': {
        'name': 'sample-name',
        'imsi': '310150123456789',
        'msisdn': '123456789',
        'ipaddr': '127.0.0.1',
        'port': '1234',
        'ki': 'abc'
      }
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.NoContent)

  def test_create_subscriber_sans_ki(self):
    """Creating a subscriber without a specficied ki should still send a
    message over zmq and get a response.
    """
    response = self.sipauthserve_connection.create_subscriber('sample-name',
        310150123456789, 123456789, '127.0.0.1', '1234')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'create',
      'fields': {
        'name': 'sample-name',
        'imsi': '310150123456789',
        'msisdn': '123456789',
        'ipaddr': '127.0.0.1',
        'port': '1234',
        'ki': ''
      }
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

  def test_update_subscriber_by_imsi(self):
    """Updating a subscriber by passing an IMSI should send a message over zmq
    and get a response.
    """
    response = self.sipauthserve_connection.update_subscriber(new_name="NEW_NAME",
            new_msisdn='1234567890', new_ipaddr='127.0.0.1', new_port='1234', imsi='310150123456789')
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'update',
      'match': {
        'imsi': '310150123456789'
      },
      'fields': {
          'name' : 'NEW_NAME',
          'msisdn': '1234567890',
          'ipaddr': '127.0.0.1',
          'port': '1234'
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
    """Requesting a nonexistent subscriber using a filter should
       raise an exception
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 404,
      'data': 'not found'
      })

    with self.assertRaises(InvalidRequestError):
        response = self.sipauthserve_connection.get_subscribers(imsi='non-existent',
                msisdn='000000', name='TEST')

    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'read',
      'match': {
          'imsi': 'non-existent',
          'msisdn': '000000',
          'name': 'TEST'
          },
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)

  def test_update_nonexistent_subscriber_by_imsi(self):
    """Updating a nonexistent subscriber should not raise an exception
    """
    response = self.sipauthserve_connection.update_subscriber(new_name="NEW_NAME",
            new_msisdn='1234567890', new_ipaddr='127.0.0.1', new_port='1234', imsi='non-existent')

    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'subscribers',
      'action': 'update',
      'match': {
        'imsi': 'non-existent'
      },
      'fields': {
          'name' : 'NEW_NAME',
          'msisdn': '1234567890',
          'ipaddr': '127.0.0.1',
          'port': '1234'
      }
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.OK)

class SIPAuthServeNominalSubscriberRegistryTestCase(unittest.TestCase):
  """Testing the components.SIPAuthServe class.

  Applying nominal uses of the read/update commands of the subscriber registry
  table interface methods.
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

  def test_read_subscriber_registry(self):
    """Requesting a table from the subsciber registry should send a message 
    over zmq and get a response.
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': {'ipaddr': '0.0.0.0'}
    })
    response = self.sipauthserve_connection.read_sip_buddies(['ipaddr'],
            {'name': 'NAME'})
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'sip_buddies',
      'action': 'read',
      'match': {'name': 'NAME'},
      'fields': ['ipaddr']
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.OK)

  def test_update_subscriber_registry(self):
    """Requesting a table from the subsciber registry should send a message 
    over zmq and get a response.
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': 'SQLITE_DONE'
    })
    response = self.sipauthserve_connection.update_sip_buddies({'ipaddr': '0.0.0.0'},
            {'name': 'NAME'})
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'sip_buddies',
      'action': 'update',
      'match': {'name': 'NAME'},
      'fields': {'ipaddr': '0.0.0.0' }
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.OK)

class SIPAuthServeNonNominalSubscriberRegistryTestCase(unittest.TestCase):
  """Testing the components.SIPAuthServe class.

  Applying non-nominal uses of the read/update commands of the subscriber registry
  table interface methods.
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

  def test_read_nonexistent_subscriber_registry(self):
    """Requesting a non-existent table entry should raise an exception
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 404,
      'data': 'not found'
    })
    with self.assertRaises(InvalidRequestError):
        response = self.sipauthserve_connection.read_sip_buddies(['ipaddr'],
            {'name': 'non-existent'})
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'sip_buddies',
      'action': 'read',
      'match': {'name': 'non-existent'},
      'fields': ['ipaddr']
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)


  def test_update_nonexistent_subscriber_registry(self):
    """Updating a non-existent table entry should proceed without an exception
    """
    self.sipauthserve_connection.socket.recv.return_value = json.dumps({
      'code': 200,
      'data': 'SQL_DONE'
    })
    response = self.sipauthserve_connection.update_sip_buddies({'ipaddr': 'blah'},
        {'name': 'non-existent'})
    self.assertTrue(self.sipauthserve_connection.socket.send.called)
    expected_message = json.dumps({
      'command': 'sip_buddies',
      'action': 'update',
      'match': {'name': 'non-existent'},
      'fields': {'ipaddr': 'blah'}
    })
    self.assertEqual(self.sipauthserve_connection.socket.send.call_args[0],
                     (expected_message,))
    self.assertTrue(self.sipauthserve_connection.socket.recv.called)
    self.assertEqual(response.code, SuccessCode.OK)
