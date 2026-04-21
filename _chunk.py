from typing import List
from _classes import LogicalDocument, NormalizedDocument


def build_chunks(self, normalized_docs: List[LogicalDocument]) -> NormalizedDocument:
  """
  Chunks the normalized content blocks into smaller pieces (e.g., by splitting long text blocks into paragraphs or sections) to create a set of chunks that can be used for downstream tasks such as entity extraction.
  
  The goal of this function is to take the normalized content blocks and further break them down into smaller chunks that are more manageable for downstream processing. This may include:
  - Splitting long text blocks into paragraphs or sections based on line breaks, font changes, or other layout cues.
  - Creating separate chunks for table captions and notes if they were previously merged with the table block during normalization.
  - Creating separate chunks for figure captions if they were previously merged with the figure block during normalization.
  - Ensuring that each chunk has the necessary properties (e.g., content, bounding box, page number) for downstream processing.
  """
  pass
  
  
