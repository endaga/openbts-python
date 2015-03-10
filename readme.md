a Python client for the OpenBTS NodeManager,
providing access to several components in the OpenBTS application suite:
SMQueue, SIPAuthServe, and OpenBTS itself.


### requirements
* OpenBTS 5.0 public alpha (tested on `11465a2`)
* Python 2.7


### installation

```shell
$ pip install openbts
```


### usage

```python
import openbts

# read a config value from SMQueue
smqueue_connection = openbts.components.SMQueue()
response = smqueue_connection.read_config('Bounce.Code')
print response.data['value']
# 101

# update an SIPAuthServe config value
sipauthserve_connection = openbts.components.SIPAuthServe()
response = sipauthserve_connection.update_config('Log.Alarms.Max', 12)
print response.code
# 204

# get realtime OpenBTS monitoring data
openbts_connection = openbts.components.OpenBTS()
response = openbts_connection.monitor()
print response.data['noiseRSSI']
# -67

# view all subscriber data
response = sipauthserve_connection.get_subscribers()
print len(response.data)
# 78

# create a new subscriber by name, IMSI, MSIDSN and optional ki
subscriber = ('ada', 0123, 4567, 8901)
response = sipauthserve_connection.create_subscriber(*subscriber)
print response.code
# 200
```

see additional examples in `integration_test.py`


### license
MIT


### releases
* 0.0.6 - fixes distribution manifest
* 0.0.5 - pypi points to Endaga fork
* 0.0.4 - expands SIPAuthServe and SR tables
* 0.0.3 - SMQueue config operations, OpenBTS monitoring, SIPAuthServe config and subscriber operations, version command for all components
* 0.0.2 - config reading and updating for the OpenBTS component
* 0.0.1 - barebones setup for pypi


### resources
* see the [OpenBTS 4.0 manual](http://openbts.org/site/wp-content/uploads/2014/07/OpenBTS-4.0-Manual.pdf)
* and the [NodeManager source](https://github.com/RangeNetworks/NodeManager) from Range


### testing
run unit tests with `nose`:

```shell
$ nosetests --with-coverage --cover-package=openbts
```

We have quite a few similar unit tests between components.
Many could be written against `openbts.core.BaseComponent`, as the components
all inherit from this single class.  But it seems better to individually
inspect the functionality of each class in `openbts.components`. Anyway,
onward..

To run the integration tests, you'll need an OpenBTS instance running on the
same machine as the testing script.  The test will modify real system
parameters, so run it with caution.  Or, better yet, run it against a system
not in production.

```shell
$ python integration_test.py
```


### release process
you need a `~/.pypirc` like this:

```
[distutils]
index-servers =
  pypi

[pypi]
repository: https://pypi.python.org/pypi
username: yosemitebandit
password: mhm
```

bump the versions in `setup.py` and in the readme, then run:

```shell
$ git tag 0.0.1 -m 'openbts-python v0.0.1'
$ git push origin master --tags
$ python setup.py sdist upload -r pypi
```
