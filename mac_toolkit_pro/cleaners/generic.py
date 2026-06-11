from typing import Any, Dict, List
from mac_toolkit_pro.cleaners.base import BaseCleaner
from mac_toolkit_pro.core.models import CleanableItem


class GenericCleaner(BaseCleaner):
    def clean(self, items: List[CleanableItem]) -> List[Dict[str, Any]]:
        return [self._delete(item.path) for item in items]
