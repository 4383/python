# python-varlink

A [varlink](http://varlink.org) implementation for Python.

## varlink tool installation

```bash
$ sudo dnf copr enable "@varlink/varlink"
$ sudo dnf install fedora-varlink
$ sudo setenforce 0 # needed until systemd is able to create sockets in /run
$ sudo systemctl enable --now org.varlink.resolver.socket
$ varlink help
```

## python client example usage

```python
from varlink import Client    
iface = Client(interface='io.systemd.journal')["io.systemd.journal"]

iface.Monitor(initial_lines=1)

for m in iface.Monitor(initial_lines=10, _more=True):
    for e in m.entries:
        print("%s: %s" % (e.time, e.message))
```

```python
from varlink import Client

resolver = Client(address="unix:/run/org.varlink.resolver")['org.varlink.resolver']
ret = resolver.GetInfo()
print(ret.interfaces, "\n\n")

ifaces = Client(interface='com.redhat.system.accounts')
print(ifaces['com.redhat.system.accounts'].description)
accounts = ifaces['com.redhat.system.accounts']
ret = accounts.GetByName("root")
print(ret)
print(ret.account.full_name)
print(ret.account.home)
print(ret.account.shell)
```
outputs:
```
['com.redhat.system.accounts', 'io.systemd.devices', 'io.systemd.journal', 'io.systemd.network', 'io.systemd.sysinfo', 'org.kernel.kmod', 'org.varlink.activator', 'org.varlink.resolver'] 


# Manage System Accounts
interface com.redhat.system.accounts

type Account (
  name: string,
  uid: int,
  gid: int,
  full_name: string,
  home: string,
  shell: string
)

# Retrieve a list of account information for all known accounts
method GetAll() -> (accounts: Account[])

# Retrieve the account information for a specific user ID
method GetByUid(uid: int) -> (account: Account)

# Retrieve the account information
method GetByName(name: string) -> (account: Account)

# Add new account
method Add(account: Account) -> (account: Account)

error NotFound ()

error CreationFailed (field: string)

namespace(account=namespace(full_name='root', gid=0, home='/root', name='root', shell='/bin/bash', uid=0))
root
/root
/bin/bash
```

## python server example
See https://github.com/varlink/com.redhat.system/blob/master/accounts/accounts.py
