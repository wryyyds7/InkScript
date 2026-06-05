"""测试 ProjectStore"""

import tempfile
from pathlib import Path

from novel2script.core.project_store import FileSystemProjectStore


class TestFileSystemProjectStore:
    """测试 FileSystemProjectStore"""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.store = FileSystemProjectStore(base_dir=Path(self.tmp))

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_create_and_get(self):
        meta = self.store.create_project("测试项目", "这是小说内容")
        assert "id" in meta
        assert meta["name"] == "测试项目"

        got = self.store.get_project(meta["id"])
        assert got is not None
        assert got["name"] == "测试项目"

    def test_list_projects(self):
        self.store.create_project("项目1", "内容1")
        self.store.create_project("项目2", "内容2")
        projects = self.store.list_projects()
        assert len(projects) == 2

    def test_delete_project(self):
        meta = self.store.create_project("待删除", "")
        self.store.delete_project(meta["id"])
        assert self.store.get_project(meta["id"]) is None

    def test_save_and_load_novel(self):
        meta = self.store.create_project("测试", "初始内容")
        self.store.save_novel(meta["id"], "新内容")
        assert self.store.load_novel(meta["id"]) == "新内容"
