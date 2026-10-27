import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from helpers import CONTRACT, Env  # noqa: E402


@pytest.fixture
def env(direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie):
    contract = direct_deploy(CONTRACT)
    from genlayer import Address  # importable once the SDK is loaded by the deploy

    accounts = tuple(Address(bytes(a)) for a in (direct_alice, direct_bob, direct_charlie))
    direct_vm.sender = accounts[0]
    return Env(direct_vm, contract, accounts)
