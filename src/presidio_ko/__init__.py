"""Presidio용 한국어 개인정보 recognizer, 컨텍스트 강화기, 마스킹, 가명 치환."""

from .analyzer import create_korean_analyzer
from .korean_context_enhancer import KoreanContextAwareEnhancer
from .kr_address_recognizer import KrAddressRecognizer
from .kr_bank_account_recognizer import KrBankAccountRecognizer
from .kr_health_insurance_recognizer import KrHealthInsuranceRecognizer
from .kr_person_recognizer import KrPersonRecognizer
from .kr_phone_recognizer import KrPhoneRecognizer
from .kr_vehicle_plate_recognizer import KrVehiclePlateRecognizer
from .masking import korean_operators
from .pseudonym import Pseudonymizer

KOREAN_RECOGNIZERS = [
    KrPhoneRecognizer(),
    KrBankAccountRecognizer(),
    KrPersonRecognizer(),
    KrAddressRecognizer(),
    KrVehiclePlateRecognizer(),
    KrHealthInsuranceRecognizer(),
]

__all__ = [
    "KOREAN_RECOGNIZERS",
    "KoreanContextAwareEnhancer",
    "KrAddressRecognizer",
    "Pseudonymizer",
    "KrBankAccountRecognizer",
    "KrHealthInsuranceRecognizer",
    "KrPersonRecognizer",
    "KrPhoneRecognizer",
    "KrVehiclePlateRecognizer",
    "create_korean_analyzer",
    "korean_operators",
]
