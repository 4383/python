#!/usr/bin/env python

"""Server and Client example of varlink for python

From the main git repository directory run::

    $ PYTHONPATH=$(pwd) python3 ./varlink/tests/test_orgexamplemore.py

or::

    $ PYTHONPATH=$(pwd) python3 ./varlink/tests/test_orgexamplemore.py --varlink="unix:@test" &
    Listening on @test
    [1] 6434
    $ PYTHONPATH=$(pwd) python3 ./varlink/tests/test_orgexamplemore.py --client --varlink="unix:@test"
    [...]

"""

from __future__ import print_function
from __future__ import unicode_literals

from builtins import int
from builtins import next
from builtins import object
from builtins import range

import os
import sys
import threading
import time
import unittest
import getopt

import varlink
from sys import platform


######## CLIENT #############

def run_client(address):
    print('Connecting to %s\n' % address)
    try:
        with varlink.Client(address) as client, \
                client.open('org.example.more', namespaced=True) as con1, \
                client.open('org.example.more', namespaced=True) as con2:

            for m in con1.TestMore(10, _more=True):
                if hasattr(m.state, 'start') and m.state.start != None:
                    if m.state.start:
                        print("--- Start ---", file=sys.stderr)

                if hasattr(m.state, 'end') and m.state.end != None:
                    if m.state.end:
                        print("--- End ---", file=sys.stderr)

                if hasattr(m.state, 'progress') and m.state.progress != None:
                    print("Progress:", m.state.progress, file=sys.stderr)
                    if m.state.progress > 50:
                        ret = con2.Ping("Test")
                        print("Ping: ", ret.pong)

    except varlink.ConnectionError as e:
        print("ConnectionError:", e)
        raise e
    except varlink.VarlinkError as e:
        print(e)
        print(e.error())
        print(e.parameters())
        raise e


######## SERVER #############

service = varlink.Service(
    vendor='Varlink',
    product='Varlink Examples',
    version='1',
    url='http://varlink.org',
    interface_dir=os.path.dirname(__file__)
)


class ServiceRequestHandler(varlink.RequestHandler):
    service = service


class ActionFailed(varlink.VarlinkError):

    def __init__(self, reason):
        varlink.VarlinkError.__init__(self,
                                      {'error': 'org.example.more.ActionFailed',
                                       'parameters': {'field': reason}})


@service.interface('org.example.more')
class Example(object):
    sleep_duration = 1

    def TestMore(self, n, _more=True, _server=None):
        try:
            if not _more:
                yield varlink.InvalidParameter('more')

            yield {'state': {'start': True}, '_continues': True}

            for i in range(0, n):
                yield {'state': {'progress': int(i * 100 / n)}, '_continues': True}
                time.sleep(self.sleep_duration)

            yield {'state': {'progress': 100}, '_continues': True}

            yield {'state': {'end': True}, '_continues': False}
        except Exception as error:
            print("ERROR", error, file=sys.stderr)
            if _server:
                _server.shutdown()

    def Ping(self, ping):
        return {'pong': ping}

    def StopServing(self, _request=None, _server=None):
        print("Server ends.")

        if _request:
            print("Shutting down client connection")
            _server.shutdown_request(_request)

        if _server:
            print("Shutting down server")
            _server.shutdown()

    def TestMap(self, map):
        i = 1
        ret = {}
        for (key, val) in map.items():
            ret[key] = {"i": i, "val": val}
            i += 1
        return {'map': ret}

    def TestObject(self, object):
        import json
        return {"object": json.loads(json.dumps(object))}


def run_server(address):
    with varlink.ThreadingServer(address, ServiceRequestHandler) as server:
        print("Listening on", server.server_address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


######## MAIN #############

def usage():
    print('Usage: %s [[--client] --varlink=<varlink address>]' % sys.argv[0], file=sys.stderr)
    print('\tSelf Exec: $ %s' % sys.argv[0], file=sys.stderr)
    print('\tServer   : $ %s --varlink=<varlink address>' % sys.argv[0], file=sys.stderr)
    print('\tClient   : $ %s --client --varlink=<varlink address>' % sys.argv[0], file=sys.stderr)


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["help", "client", "varlink="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    address = None
    client_mode = False

    for opt, arg in opts:
        if opt == "--help":
            usage()
            sys.exit(0)
        elif opt == "--varlink":
            address = arg
        elif opt == "--client":
            client_mode = True

    if not address and not client_mode:
        client_mode = True
        address = 'exec:' + __file__

        if platform != "linux":
            print("varlink exec: not supported on platform %s" % platform, file=sys.stderr)
            usage()
            sys.exit(2)

    if client_mode:
        try:
            run_client(address)
        except Exception as e:
            print("Exception: ", type(e), e)
            sys.exit(1)
    else:
        run_server(address)

    sys.exit(0)


######## UNITTEST #############

class TestService(unittest.TestCase):
    def test_service(self):
        address = "tcp:127.0.0.1:23451"
        Example.sleep_duration = 0.1

        server = varlink.ThreadingServer(address, ServiceRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            run_client(address)

            with varlink.Client(address=address) as client, \
                    client.open('org.example.more', namespaced=True) as con1, \
                    client.open('org.example.more', namespaced=True) as con2:

                self.assertEqual(con1.Ping("Test").pong, "Test")

                it = con1.TestMore(10, _more=True)

                m = next(it)
                self.assertTrue(hasattr(m.state, 'start'))
                self.assertFalse(hasattr(m.state, 'end'))
                self.assertFalse(hasattr(m.state, 'progress'))
                self.assertIsNotNone(m.state.start)

                for i in range(0, 110, 10):
                    m = next(it)
                    self.assertTrue(hasattr(m.state, 'progress'))
                    self.assertFalse(hasattr(m.state, 'start'))
                    self.assertFalse(hasattr(m.state, 'end'))
                    self.assertIsNotNone(m.state.progress)
                    self.assertEqual(i, m.state.progress)

                    if i > 50:
                        ret = con2.Ping("Test")
                        self.assertEqual("Test", ret.pong)

                m = next(it)
                self.assertTrue(hasattr(m.state, 'end'))
                self.assertFalse(hasattr(m.state, 'start'))
                self.assertFalse(hasattr(m.state, 'progress'))
                self.assertIsNotNone(m.state.end)

                self.assertRaises(StopIteration, next, it)

                con1.StopServing(_oneway=True)
                time.sleep(0.5)
                self.assertRaises(varlink.ConnectionError, con1.Ping, "Test")
        finally:
            server.shutdown()
            server.server_close()
