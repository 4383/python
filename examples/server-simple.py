#!/usr/bin/python3

import os
import stat
import sys
import varlink
import time

service = varlink.Service(
    vendor='Varlink',
    product='Varlink Examples',
    version='1',
    interface_dir=os.path.dirname(__file__)
)

class ActionFailed(varlink.VarlinkError):
    def __init__(self, reason):
        varlink.VarlinkError.__init__(self,
            {'error': 'org.varlink.example.more.ActionFailed',
              'parameters': {'field': reason }})

@service.interface('org.varlink.example.more')
class Example:
    def TestMore(self, n, _more=True):
        try:
            if not _more:
                yield varlink.InvalidParameter('more')

            yield { 'state' : { 'start' : True } , '_continues' : True }

            for i in range(0, n):
                yield { 'state' : { 'progress' : int(i * 100 / n) } , '_continues' : True }
                time.sleep(1)

            yield { 'state' : { 'progress' : 100 } , '_continues' : True }

            yield { 'state' : { 'end' : True }, '_continues' : False }
        except Exception as error:
            print("ERROR", error,  file=sys.stderr)
            self.close()

    def Ping(self, ping):
        return { 'pong' : ping }

if len(sys.argv) < 2:
    print('missing address parameter')
    sys.exit(1)

try:
    if stat.S_ISSOCK(os.fstat(3).st_mode):
        listen_fd = 3
except OSError:
    listen_fd = None

with varlink.SimpleServer(service) as s:
    s.serve(sys.argv[1], listen_fd=listen_fd)
