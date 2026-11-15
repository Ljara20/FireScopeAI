from firescope.shared.exceptions import NotImplementedStageError
class PostgisRepository:
    def connect(self) -> None:
        raise NotImplementedStageError("PostGIS integration is planned for a later stage")
