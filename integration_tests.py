"""Integration testing -- requires OpenBTS components to be running.

Usage (from the repo's root):
  $ nosetests
  $ nosetests openbts.tests.integration_tests:SIPAuthServeTest
  $ nosetests openbts.tests.integration_tests:SIPAuthServeTest.test_one_thing

Warning: this will change live values in OpenBTS.
"""
import unittest

import openbts


class VersionTest(unittest.TestCase):
  """We can read version data without throwing errors."""

  def test_query_openbts_version(self):
    connection = openbts.components.OpenBTS()
    response = connection.get_version()
    self.assertTrue(str, isinstance(response.data))

  def test_query_sipauthserve_version(self):
    connection = openbts.components.SIPAuthServe()
    response = connection.get_version()
    self.assertTrue(str, isinstance(response.data))

  def test_query_smqueue_version(self):
    connection = openbts.components.SMQueue()
    response = connection.get_version()
    self.assertTrue(str, isinstance(response.data))


class ConfigReadTest(unittest.TestCase):
  """We can read config vars without throwing errors."""

  def test_read_openbts_config(self):
    connection = openbts.components.OpenBTS()
    connection.read_config('Control.NumSQLTries')

  def test_read_sipauthserve_config(self):
    connection = openbts.components.SIPAuthServe()
    connection.read_config('Log.Alarms.Max')

  def test_read_smqueue_config(self):
    connection = openbts.components.SMQueue()
    connection.read_config('Bounce.Code')


class ConfigUpdateTest(unittest.TestCase):
  """We can update config vars without throwing errors."""

  def test_update_openbts_config(self):
    connection = openbts.components.OpenBTS()
    key = 'Control.NumSQLTries'
    response = connection.read_config(key)
    original_value = response.data['value']
    connection.update_config(key, 6)
    connection.update_config(key, original_value)

  def test_update_sipauthserve_config(self):
    connection = openbts.components.SIPAuthServe()
    key = 'Log.Alarms.Max'
    response = connection.read_config(key)
    original_value = response.data['value']
    connection.update_config(key, 12)
    connection.update_config(key, original_value)

  def test_update_smqueue_config(self):
    connection = openbts.components.SMQueue()
    key = 'Bounce.Code'
    response = connection.read_config(key)
    original_value = response.data['value']
    connection.update_config(key, 555)
    connection.update_config(key, original_value)


class OpenBTSMonitoringTest(unittest.TestCase):

  def test_monitor_openbts(self):
    connection = openbts.components.OpenBTS()
    response = connection.monitor()
    self.assertIn(response.data, 'noiseRSSI')


class SIPAuthServeTest(unittest.TestCase):
  """Testing SIPAuthServe subscriber and number operations."""

  def setUp(self):
    self.conn = openbts.components.SIPAuthServe(socket_timeout=0.1)
    self.sub_a_imsi = 'IMSI000123'
    self.sub_b_imsi = 'IMSI000789'
    self.tearDown()
    self.conn.create_subscriber(self.sub_a_imsi, '5551234', '127.0.0.1',
                                '8888')
    self.conn.create_subscriber(self.sub_b_imsi, '5556789', '123.234.123.234',
                                '8000', ki=6789)

  def tearDown(self):
    self.conn.delete_subscriber(imsi=self.sub_a_imsi)
    self.conn.delete_subscriber(imsi=self.sub_b_imsi)

  def test_subscriber_count(self):
    self.assertEqual(2, self.conn.count_subscribers())

  def test_get_all_subscribers(self):
    result = self.conn.get_subscribers()
    expected_data = [{
      'name': self.sub_a_imsi,
      'ipaddr': '127.0.0.1',
      'port': '8888',
      'numbers': ['5551234'],
      'account_balance': '0',
    }, {
      'name': self.sub_b_imsi,
      'ipaddr': '123.234.123.234',
      'port': '8000',
      'numbers': ['5556789'],
      'account_balance': '0',
    }]
    self.assertItemsEqual(expected_data, result)

  def test_subscriber_filter(self):
    result = self.conn.get_subscribers(imsi=self.sub_a_imsi)
    expected_data = [{
      'name': self.sub_a_imsi,
      'ipaddr': '127.0.0.1',
      'port': '8888',
      'numbers': ['5551234'],
      'account_balance': '0',
    }]
    self.assertEqual(expected_data, result)

  def test_subscriber_filter_nonexistent_imsi(self):
    result = self.conn.get_subscribers(imsi='IMSI00993322')
    expected_data = []
    self.assertEqual(expected_data, result)

  def test_create_duplicate_subscriber(self):
    """If the IMSI already exists, this should fail."""
    with self.assertRaises(ValueError):
      self.conn.create_subscriber(self.sub_a_imsi, '5554321', '127.123.2.3',
                                  '4499')

  def test_get_ipaddr(self):
    self.assertEqual('123.234.123.234', self.conn.get_ipaddr(self.sub_b_imsi))

  def test_get_port(self):
    self.assertEqual('8000', self.conn.get_port(self.sub_b_imsi))

  def test_get_single_number(self):
    self.assertEqual(['5556789'], self.conn.get_numbers(self.sub_b_imsi))

  def test_set_ipaddr(self):
    self.conn.update_ipaddr(self.sub_a_imsi, '244.255.200.201')
    self.assertEqual('244.255.200.201', self.conn.get_ipaddr(self.sub_a_imsi))

  def test_set_port(self):
    self.conn.update_port(self.sub_a_imsi, '9999')
    self.assertEqual('9999', self.conn.get_port(self.sub_a_imsi))

  def test_associate_more_numbers(self):
    """A subscriber can have multiple associated numbers."""
    self.conn.add_number(self.sub_a_imsi, '5557744')
    expected_numbers = ['5551234', '5557744']
    self.assertItemsEqual(expected_numbers,
                          self.conn.get_numbers(self.sub_a_imsi))

  def test_add_preexisting_number(self):
    """If we try to add a pre-existing number, do nothing."""
    self.conn.add_number(self.sub_a_imsi, '5551234')
    expected_numbers = ['5551234']
    self.assertItemsEqual(expected_numbers,
                          self.conn.get_numbers(self.sub_a_imsi))

  def test_delete_last_number(self):
    with self.assertRaises(ValueError):
      self.conn.delete_number(self.sub_a_imsi, '5556789')

  def test_delete_single_number(self):
    self.conn.add_number(self.sub_a_imsi, '5557744')
    self.conn.delete_number(self.sub_a_imsi, '5551234')
    expected_numbers = ['5557744']
    self.assertItemsEqual(expected_numbers,
                          self.conn.get_numbers(self.sub_a_imsi))

  def test_delete_subscribers(self):
    self.conn.delete_subscriber(imsi=self.sub_a_imsi)
    self.conn.delete_subscriber(imsi=self.sub_b_imsi)
    self.assertEqual(0, self.conn.count_subscribers())

  def test_get_imsi_from_number(self):
    result = self.conn.get_imsi_from_number('5551234')
    self.assertEqual(self.sub_a_imsi, result)

  def test_get_imsi_from_nonexistent_number(self):
    with self.assertRaises(openbts.exceptions.InvalidRequestError):
      self.conn.get_imsi_from_number('5558876')

  def test_get_account_balance(self):
    result = self.conn.get_account_balance(self.sub_a_imsi)
    self.assertEqual('0', result)

  def test_get_account_balance_from_nonexistent_imsi(self):
    with self.assertRaises(openbts.exceptions.InvalidRequestError):
      self.conn.get_account_balance('IMSI000443322')

  def test_update_account_balance(self):
    self.conn.update_account_balance(self.sub_a_imsi, '1000')
    result = self.conn.get_account_balance(self.sub_a_imsi)
    self.assertEqual('1000', result)

  def test_update_account_balance_invalid_type(self):
    """Account balances must be integer values."""
    with self.assertRaises(TypeError):
      self.conn.update_account_balance(self.sub_a_imsi, 999)
    with self.assertRaises(TypeError):
      self.conn.update_account_balance(self.sub_a_imsi, 9.99)
