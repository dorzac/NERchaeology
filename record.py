"""
Record class for storing associations between a site and its era.
"""
from dataclasses import dataclass, field
from typing import List

@dataclass(unsafe_hash=True)
class Record:
	site_name: str = field(default="", hash=True)
	site_name_line: int = field(default=-1, hash=False)
	period_term: str = field(default="", hash=True)
	dates: List[str]  = field(default_factory=list, hash=False)
	artifacts: List[str]  = field(default_factory=list, hash=False)
	artifact: str = field(default="", hash=True)
	freq: float = field(default=0, hash=False)

	def __eq__(self, other):
		if other.__class__ is not self.__class__:
			return NotImplemented
		return (self.site_name, self.period_term, self.artifacts, self.artifact) \
				== (other.site_name, other.period_term, self.artifacts, self.artifact)
