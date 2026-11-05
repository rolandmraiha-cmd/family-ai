import asyncio
from datetime import datetime, timezone
import tempfile
import unittest

from family_backend.account import RunPodAccount
from family_backend.api import ControlAPI
from family_backend.control import Ledger, ControlError


class AccountTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.now = datetime(2026, 11, 5, 12, tzinfo=timezone.utc).timestamp()
        self.calls = []
        self.fail = set()
        self.data = {'balance': {'data': {'myself': {'clientBalance': 15.53, 'currentSpendPerHr': .001}}}}
        for part, start, end in [('day', '2026-11-05', '2026-11-06'), ('month', '2026-11-01', '2026-12-01')]:
            self.data[part] = {'metadata': {'query': {'bucketSize': part, 'startTime': start+'T00:00:00Z',
                'endTime': end+'T00:00:00Z'}, 'totals': {'totalAmount': .002 if part == 'day' else 10.39}}}
        async def fetch(part):
            self.calls.append(part)
            await asyncio.sleep(0)
            if part in self.fail:
                raise RuntimeError('sensitive-provider-error')
            return self.data[part]
        self.monitor = RunPodAccount(fetch=fetch, clock=lambda: self.now)

    async def test_readings_are_provider_figures_and_concurrent_refresh_is_cached(self):
        first, second = await asyncio.gather(self.monitor.get(), self.monitor.get())
        self.assertCountEqual(self.calls, ['balance', 'day', 'month'])
        self.assertEqual(first, second)
        self.assertEqual(first['balance']['amount_usd'], 15.53)
        self.assertEqual(first['day']['amount_usd'], .002)
        self.assertTrue(first['billing_may_lag'])
        first['balance']['amount_usd'] = 999
        self.assertEqual((await self.monitor.get())['balance']['amount_usd'], 15.53)

    async def test_partial_failure_keeps_last_good_value_and_never_leaks_errors(self):
        await self.monitor.get()
        self.now += 61
        self.fail = {'balance', 'day'}
        result = await self.monitor.get()
        self.assertEqual(result['balance']['amount_usd'], 15.53)
        self.assertEqual(result['balance']['status'], 'stale')
        self.assertEqual(result['month']['status'], 'fresh')
        self.assertNotIn('sensitive-provider-error', str(result))

    async def test_missing_null_negative_and_invalid_amounts_are_not_invented_zero(self):
        self.data['balance']['data']['myself']['clientBalance'] = None
        self.data['day']['metadata']['totals']['totalAmount'] = float('nan')
        self.data['month']['metadata']['totals']['totalAmount'] = True
        result = await self.monitor.get()
        for part in ('balance','day','month'):
            self.assertEqual(result[part], {'status':'unavailable'})
        self.now += 61
        self.data['balance']['data']['myself']['clientBalance'] = -1.25
        self.assertEqual((await self.monitor.get())['balance']['amount_usd'], -1.25)

    async def test_provider_errors_and_wrong_period_are_unavailable(self):
        self.data['balance']['errors'] = [{'message':'private'}]
        self.data['day']['metadata']['query']['endTime'] = '2026-11-05T00:00:00Z'
        result = await self.monitor.get()
        self.assertNotIn('amount_usd', result['balance'])
        self.assertNotIn('amount_usd', result['day'])

    async def test_rollover_does_not_present_previous_period_as_current(self):
        await self.monitor.get()
        self.now = datetime(2026, 12, 1, tzinfo=timezone.utc).timestamp()
        self.fail = {'day','month'}
        result = await self.monitor.get()
        self.assertEqual(result['day'], {'status':'unavailable'})
        self.assertEqual(result['month'], {'status':'unavailable'})

    async def test_account_is_admin_only_and_does_not_mutate_admission(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Ledger(folder+'/control.sqlite3')
            api = ControlAPI(ledger, account=self.monitor)
            before = ledger.usage()
            for user in [None, {'id':'member','role':'user'}]:
                with self.assertRaises(ControlError):
                    await api.dispatch('GET','/account', user)
            self.assertEqual(self.calls, [])
            result = await api.dispatch('GET','/account', {'id':'owner','role':'admin'})
            self.assertEqual(result['balance']['amount_usd'], 15.53)
            self.assertEqual(ledger.usage(), before)
            self.assertEqual(ledger.list_jobs('owner'), [])
