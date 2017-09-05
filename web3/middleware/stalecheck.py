from collections import defaultdict
import datetime
import time

from web3.exceptions import StaleBlockchain

SKIP_STALECHECK_FOR_METHODS = set([
    'eth_getBlockByHash',
    'eth_getBlockByNumber',
    'eth_getBlockTransactionCountByHash',
    'eth_getBlockTransactionCountByNumber',
    'eth_getTransactionByBlockHashAndIndex',
    'eth_getTransactionByBlockNumberAndIndex',
    'eth_getUncleCountByBlockHash',
    'eth_getUncleCountByBlockNumber',
])


def _isfresh(block, allowable_delay):
    return block and time.time() - block['timestamp'] <= allowable_delay


def assert_fresh(web3, cached_blocks, allowable_delay):
    last_cached = cached_blocks[web3.providers]
    if _isfresh(last_cached, allowable_delay):
        return True
    else:
        last_block = web3.eth.getBlock('latest')
        if _isfresh(last_block, allowable_delay):
            cached_blocks[web3.providers] = last_block
            return True
        else:
            raise StaleBlockchain(last_block, allowable_delay)


def make_stalecheck_middleware(seconds=0, minutes=0, hours=0, days=0):
    '''
    Use to require that a function will run only of the blockchain is recently updated.

    This middleware takes an argument, so unlike other middleware, you must make the middleware
    with a method call.
    For example: `make_stalecheck_middleware(hours=6, days=1)`

    If the latest block in the chain is older than 30 hours ago in this example, then the
    middleware will raise a StaleBlockchain exception.
    '''
    allowable_delta = datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
    allowable_delay = allowable_delta.total_seconds()
    cached_blocks = defaultdict(lambda: None)

    def stalecheck_middleware(make_request, web3):
        def middleware(method, params):
            if method not in SKIP_STALECHECK_FOR_METHODS:
                assert_fresh(web3, cached_blocks, allowable_delay)

            return make_request(method, params)
        return middleware
    return stalecheck_middleware
