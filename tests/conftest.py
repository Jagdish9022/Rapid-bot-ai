# Pytest fixtures and global mocks so tests run without Qdrant/network
import unittest.mock

# Avoid real Qdrant connection when app.db.qdrant is imported (patch client constructor)
_mock_client = unittest.mock.MagicMock()
_qdrant_patcher = unittest.mock.patch(
    "qdrant_client.QdrantClient",
    return_value=_mock_client,
)
_qdrant_patcher.start()


def pytest_sessionfinish(session, exitstatus):
    _qdrant_patcher.stop()
