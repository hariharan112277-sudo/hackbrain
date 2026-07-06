"""
Enterprise Production Operations Asset Lifecycle Service.
"""
from typing import List, Dict, Any
from uuid import UUID
from integration.interfaces import IAssetIntegrationService, IAssetRepository
from integration.contracts import AssetDTO
from integration.exceptions import ResourceNotFoundError


class AssetIntegrationService(IAssetIntegrationService):
    def __init__(self, asset_repo: IAssetRepository):
        self._repo = asset_repo

    def get_asset(self, session: Any, asset_id: UUID) -> AssetDTO:
        record = self._repo.find_by_id(session, asset_id)
        if not record:
            raise ResourceNotFoundError(f"Asset node verification signature '{asset_id}' mismatch.")
        return AssetDTO.model_validate(record)

    def get_asset_hierarchy(self, session: Any, root_asset_id: UUID) -> Dict[str, Any]:
        root = self.get_asset(session, root_asset_id)
        return {
            "node_id": str(root.id),
            "label": root.name,
            "category": root.category,
            "sub_components_matrix": []
        }

    def get_assets_by_production_line(self, session: Any, line_id: UUID) -> List[AssetDTO]:
        records = self._repo.find_by_production_line(session, line_id)
        return [AssetDTO.model_validate(r) for r in records]
