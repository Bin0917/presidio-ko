"""Presidio용 한국형 PII recognizer (KR_PHONE, KR_BANK_ACCOUNT)."""

from .kr_bank_account_recognizer import KrBankAccountRecognizer
from .kr_phone_recognizer import KrPhoneRecognizer

KOREAN_RECOGNIZERS = [KrPhoneRecognizer(), KrBankAccountRecognizer()]

__all__ = ["KOREAN_RECOGNIZERS", "KrBankAccountRecognizer", "KrPhoneRecognizer"]
