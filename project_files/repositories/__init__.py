from . import kasa_repository
from . import cari_repository
from . import stok_repository
from . import fatura_repository
from .db_core import get_db_connection

class KasaBankaService:
    hesap_repo = kasa_repository
    kasa_repo = kasa_repository

    def __init__(self, conn=None):
        self.conn = conn
        self.hesap_repo = kasa_repository
        self.kasa_repo = kasa_repository

    @classmethod
    def get_hesaplar(cls, tur=None):
        return kasa_repository.get_banka_hesaplari(tur)

    @classmethod
    def get_banka_hesaplari(cls, tur=None):
        return kasa_repository.get_banka_hesaplari(tur)

    @staticmethod
    def static_get_hesaplar(tur=None):
        return kasa_repository.get_banka_hesaplari(tur)