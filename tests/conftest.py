import json
import pytest
from electrumx.server.controller import Controller
from xprocess import ProcessStarter
from os import environ
from lbryumx.coin import LBC, LBCRegTest
from electrumx.server.storage import Storage
from electrumx.server.env import Env
from urllib.request import urlopen
import os
import stat


def download_lbrycrdd(path):
    # TODO: get from lbrycrd repo when the changes are there
    print("Downloading lbrycrdd into {}".format(path))
    with open(path, "wb") as lbrycrdd_file:
        req = urlopen("http://victor.lbry.tech:5000/lbrycrdd")
        lbrycrdd_file.write(req.read())


def ensure_lbrycrdd():
    path = "/tmp/lbrycrdd"
    if not os.path.isfile(path):
        download_lbrycrdd(path)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)
    return path


@pytest.fixture()
def block_processor(tmpdir_factory):
    environ.clear()
    environ['DB_DIRECTORY'] = tmpdir_factory.mktemp('db', numbered=True).strpath
    environ['DAEMON_URL'] = ''
    env = Env(LBC)
    bp = LBC.BLOCK_PROCESSOR(env, None, None)
    yield bp
    for attr in dir(bp):  # hack to close dbs on tear down
        obj = getattr(bp, attr)
        if isinstance(obj, Storage):
            obj.close()


@pytest.fixture('module')
def block_infos():
    block_data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
    blocks = {}
    for block_file_name in os.listdir(block_data_path):
        if not block_file_name.startswith('block'): continue
        number = block_file_name.split('_')[1].replace('.json', '')
        block_file_path = os.path.join(block_data_path, block_file_name)
        with open(block_file_path, 'r') as block_file:
            blocks[number] = json.loads(block_file.read())
    return blocks


def setup_session(data_dir, rpc_port):
    conf = {'DB_DIRECTORY': data_dir,
            'DAEMON_URL': 'http://lbry:lbry@localhost:{}/'.format(rpc_port)}
    os.environ.update(conf)
    controller = Controller(Env(LBCRegTest))
    session = LBC.SESSIONCLS(controller, 'TCP')
    return session


@pytest.fixture(scope="module")
def regtest_session(xprocess, tmpdir_factory):
    rpc_port = 1337
    class RegtestLbryStarter(ProcessStarter):
        pattern = ".*Done\ loading.*"
        lbrycrdd_path = ensure_lbrycrdd()
        data_path = "/tmp/regtest"
        args = ['{}'.format(lbrycrdd_path), "-server", "-txindex", "-rpcuser=lbry", "-rpcpassword=lbry",
                "-rpcport={}".format(rpc_port), "-datadir={}".format(data_path), "-printtoconsole", "-regtest"]

    xprocess.ensure("lbrycrdd", RegtestLbryStarter)
    xprocess.getinfo("lbrycrdd")
    data_dir = tmpdir_factory.mktemp('db', numbered=True).strpath
    return setup_session(data_dir, 1337)
