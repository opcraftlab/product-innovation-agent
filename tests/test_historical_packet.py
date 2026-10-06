import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('historical_packet',Path(__file__).resolve().parents[1]/'scripts/check_historical_packet.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class HistoricalPacketTests(unittest.TestCase):
    def packet(self):
        return {'cutoff':'2015-12-31','items':[{'id':'S1','role':'input','basis':'contemporaneous',
          'statement':'A bounded prior observation','source':'local archive','source_available_at':'2015-12-30','event_date':'2015-12-20'}]}
    def test_contemporaneous_passes(self):
        self.assertTrue(module.audit(self.packet())['strict_asof_input'])
    def test_old_event_in_late_source_rejected(self):
        p=self.packet();p['items'][0]['source_available_at']='2016-01-01'
        self.assertFalse(module.audit(p)['passed'])
    def test_unknown_available_date_rejected(self):
        p=self.packet();p['items'][0]['source_available_at']=None
        self.assertFalse(module.audit(p)['passed'])
    def test_reconstruction_requires_opt_in_and_stays_non_strict(self):
        p=self.packet();p['items'][0].update(basis='retrospective_reconstruction',source_available_at=None)
        self.assertFalse(module.audit(p)['passed'])
        a=module.audit(p,True);self.assertTrue(a['passed']);self.assertFalse(a['strict_asof_input'])
    def test_future_event_stays_rejected_with_opt_in(self):
        p=self.packet();p['items'][0].update(basis='retrospective_reconstruction',event_date='2016-01-01')
        self.assertFalse(module.audit(p,True)['passed'])
    def test_future_heldout_does_not_poison_prior_input(self):
        p=self.packet();x=copy.deepcopy(p['items'][0]);x.update(id='S2',role='heldout',source_available_at='2025-01-01',event_date='2024-01-01');p['items'].append(x)
        self.assertTrue(module.audit(p)['strict_asof_input'])
    def test_no_input_rejected(self):
        p=self.packet();p['items'][0]['role']='heldout'
        self.assertFalse(module.audit(p)['passed'])
    def test_duplicate_ids_rejected(self):
        p=self.packet();p['items'].append(copy.deepcopy(p['items'][0]))
        with self.assertRaises(ValueError):module.audit(p)
    def test_invalid_calendar_day_rejected(self):
        p=self.packet();p['cutoff']='2015-02-30'
        with self.assertRaises(ValueError):module.audit(p)
    def test_invalid_role_rejected(self):
        p=self.packet();p['items'][0]['role']='guess'
        with self.assertRaises(ValueError):module.audit(p)

if __name__=='__main__':unittest.main()
