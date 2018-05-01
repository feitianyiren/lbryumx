from binascii import unhexlify
from unittest.mock import MagicMock

from .data.regtest_chain import hex_blocks, expected_names
from lbryumx.coin import LBCRegTest


def test_simple_claim_backup(block_processor):
    daemon_mock = MagicMock()
    daemon_mock.cached_height.return_value = 0
    block_processor.coin = LBCRegTest
    block_processor.daemon = daemon_mock

    raw_blocks = list(map(unhexlify, hex_blocks))
    blocks = [LBCRegTest.block(raw_block, i) for (i, raw_block) in enumerate(raw_blocks)]
    empty_blocks = blocks[:101]
    first_claim_block = blocks[102]

    block_processor.advance_blocks(empty_blocks)
    assert not list(filter(None, map(block_processor.get_claims_for_name, expected_names)))

    block_processor.advance_blocks([first_claim_block])
    block_processor.flush(True)  # A full flush to disk means a sync is completed

    # check state with a single claim before backup
    assert len(block_processor.get_claims_for_name(expected_names[0])) == 1
    assert not block_processor.get_claims_for_name(expected_names[1])
    first_claim_id = list(block_processor.get_claims_for_name(expected_names[0]).keys())[0]
    parsed_claim_info = block_processor.get_claim_info(first_claim_id)
    assert parsed_claim_info

    block_processor.backup_blocks([raw_blocks[102]])

    assert not list(filter(None, map(block_processor.get_claims_for_name, expected_names)))
    parsed_claim_info = block_processor.get_claim_info(first_claim_id)
    assert not parsed_claim_info