from typing import List
from _classes import RawDataBlock


def normalize_page_headers(blocks: List[RawDataBlock], page_headers: list = None) -> List[RawDataBlock]:
  return blocks