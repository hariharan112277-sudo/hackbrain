"""Package bridge for the existing root-level ingestion implementation.

The repository's historical ingestion modules live at the project root and use
package-relative imports. Extending this package's search path lets those files
load as ``ingestion.<module>`` without duplicating source or changing their
public import contract.
"""

from pathlib import Path

_LEGACY_MODULE_ROOT = str(Path(__file__).resolve().parent.parent)
if _LEGACY_MODULE_ROOT not in __path__:
    __path__.append(_LEGACY_MODULE_ROOT)

__all__: list[str] = []
