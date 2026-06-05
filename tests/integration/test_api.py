"""API 集成测试

使用 FastAPI 的 TestClient 测试所有 API 端点.
"""

from starlette.testclient import TestClient
from novel2script.api.main import create_app

# 使用 follow_redirects=True 以处理尾部斜杠重定向
client = TestClient(create_app(), follow_redirects=True)


class TestProjectAPI:
    """测试项目管理 API"""

    def test_list_projects(self):
        resp = client.get("/api/v1/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0

    def test_create_and_get_project(self):
        # 创建
        resp = client.post("/api/v1/projects", json={"name": "集成测试项目"})
        assert resp.status_code == 200
        proj = resp.json()["data"]
        proj_id = proj["id"]

        # 获取
        resp2 = client.get(f"/api/v1/projects/{proj_id}")
        assert resp2.status_code == 200
        assert resp2.json()["data"]["name"] == "集成测试项目"

    def test_delete_project(self):
        resp = client.post("/api/v1/projects", json={"name": "待删除"})
        proj_id = resp.json()["data"]["id"]

        resp2 = client.delete(f"/api/v1/projects/{proj_id}")
        assert resp2.status_code == 200

        resp3 = client.get(f"/api/v1/projects/{proj_id}")
        assert resp3.status_code == 404


class TestHealthCheck:
    """测试健康检查"""

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
