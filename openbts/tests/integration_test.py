"""integration testing
"""
import sys

import zmq

from openbts.components import OpenBTS, SMQueue, SIPAuthServe

if __name__ == '__main__':
  print ''
  print 'note: this script must be run against a live OpenBTS instance'
  print 'warning: during the test, this script will modify live config values'
  value = raw_input('\ncontinue? (y/n) ')
  if value.lower() != 'y':
    print 'exiting'
    sys.exit(1)
  print ''


  """ testing version querying
  """
  components = (OpenBTS, SIPAuthServe, SMQueue)
  print 'getting component versions:'
  for component in components:
    connection = component()
    response = connection.get_version()
    print '  %s: %s' % (connection, response.data)
  print ''


  """ testing nominal config reads and updates
  """
  component_tests = [
    (OpenBTS, 'Control.NumSQLTries', '6'),
    (SIPAuthServe, 'Log.Alarms.Max', '12'),
    (SMQueue, 'Bounce.Code', 555)
  ]
  for entry in component_tests:
    print 'testing the %s config operations:' % entry[0]()
    connection = entry[0]()
    response = connection.read_config(entry[1])
    original_value = response.data['value']
    print '  original value of %s: %s' % (entry[1], original_value)
    connection.update_config(entry[1], entry[2])
    response = connection.read_config(entry[1])
    print '  set %s to %s' % (entry[1], entry[2])
    connection.update_config(entry[1], original_value)
    response = connection.read_config(entry[1])
    print '  reverted %s to %s' % (entry[1], response.data['value'])
    print ''


  """ testing nominal OpenBTS monitoring
  """
  print 'getting OpenBTS monitoring data:'
  connection = OpenBTS()
  response = connection.monitor()
  print '  noise RSSI: %s' % response.data['noiseRSSI']
  print ''


  """ testing nominal SIPAuthServe subscriber operations
  """
  connection = SIPAuthServe()
  response = connection.get_subscribers()
  print 'testing SIPAuthServe subscriber operations:'
  print '  we currently have %s subscribers' % len(response.data)
  print 'creating two subscribers:'
  subscriber_a = ('jon', 0123, 4567, '127.0.0.1', '8888')
  subscriber_b = ('ada', 8901, 2345, '123.234.123.234', '4321', 6789)
  connection.create_subscriber(*subscriber_a)
  connection.create_subscriber(*subscriber_b)
  response = connection.get_subscribers()
  print '  we now have %s subscribers' % len(response.data)
  response = connection.get_subscribers(name='jon')
  print '  filtering for jon: %s, length: %d' % (response.data[0]['name'], len(response.data))
  response = connection.update_sip_buddies({'ipaddr': ''},
          {'name': 'non-existent'})
  print '  updating nonexistent: %s, code: %d' % (response.data, response.code)
  response = connection.update_sip_buddies({'name': 'bob'},
          {'name': 'ada'})
  print '  updating ada to bob: %s, code: %d' % (response.data, response.code)
  response = connection.read_sip_buddies(['name'], {})
  print '  getting the sip_buddies names  %s' % response.data
  response = connection.read_sip_buddies([], {'name': 'jon'})
  print '  getting the sip_buddies entries for jon len=%s, fields=%s' % (len(response.data), len(response.data[0]))
  print 'deleting those two subscribers:'
  connection.delete_subscriber(imsi=subscriber_a[1])
  connection.delete_subscriber(imsi=subscriber_b[1])
  response = connection.get_subscribers()
  print "  and we're back to %s subscribers" % len(response.data)


  print '\nintegration test complete.'
  print ''
