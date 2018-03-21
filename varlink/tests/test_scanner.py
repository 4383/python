# /usr/bin/env python3

import varlink


def test_scanner_1():
    interface = varlink.Interface("""# Example Varlink service
interface org.varlink.example.more

# Enum, returning either start, progress or end
# progress: [0-100]
type State (
     start: bool,
     progress: int,
     end: bool
)

# Returns the same string
method Ping(ping : string) -> (pong: string)

# Dummy progress method
# n: number of progress steps
method TestMore(n : int) -> (state: State)

# Stop serving
method StopServing() -> ()

# Something failed
error ActionFailed (reason: string)
""")
    assert interface.name == "org.varlink.example.more"
    assert interface.get_method("Ping") != None
    assert interface.get_method("TestMore") != None
    assert interface.get_method("StopServing") != None
    assert isinstance(interface.members.get("ActionFailed"), varlink._Error)
    assert isinstance(interface.members.get("State"), varlink._Alias)


def test_complex():
    interface = varlink.Interface("""
interface org.example.complex

type TypeEnum ( a, b, c )

type TypeFoo (
    bool: bool,
    int: int,
    float: float,
    string: string,
    enum: ( foo, bar, baz )[],
    type: TypeEnum,
    anon: ( foo: bool, bar: int, baz: (a: int, b: int)[] )
)

method Foo(a: (b: bool, c: int), foo: TypeFoo) -> (a: (b: bool, c: int)[], foo: TypeFoo)

error ErrorFoo (a: (b: bool, c: int), foo: TypeFoo)
""")
    assert interface.name == "org.example.complex"
    assert interface.get_method("Foo") != None
    assert isinstance(interface.members.get("ErrorFoo"), varlink._Error)
    assert isinstance(interface.members.get("TypeEnum"), varlink._Alias)
