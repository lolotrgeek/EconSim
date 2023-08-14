import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.ExchangeRequests import ExchangeRequests
from source.company.PublicCompanyRequests import PublicCompanyRequests

class TraderRequests(ExchangeRequests, PublicCompanyRequests):
    def __init__(self, exchange_requester, public_company_requester):
        ExchangeRequests.__init__(self=self, requester=exchange_requester)
        PublicCompanyRequests.__init__(self=self, requester=public_company_requester)