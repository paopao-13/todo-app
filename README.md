# 个人待办事项小程序

基于 Flask + SQLite 的待办事项管理系统，提供 RESTful API 接口。

## 功能特性

- 待办事项 CRUD（增删改查）
- 分类管理（工作、学习、生活等）
- 优先级设置（高/中/低）
- 关键词搜索筛选
- 统计数据接口
- 完整的单元测试覆盖

## 技术栈

- Python 3.10+
- Flask 3.x
- SQLite
- pytest

## 快速开始

```bash
pip install flask pytest
python app.py
```

服务启动在 http://localhost:5000

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/todos | 获取全部待办（支持分类/状态/关键词筛选） |
| POST | /api/todos | 创建待办 |
| GET | /api/todos/{id} | 获取单个待办 |
| PUT | /api/todos/{id} | 更新待办 |
| DELETE | /api/todos/{id} | 删除待办 |
| GET | /api/categories | 获取全部分类 |
| POST | /api/categories | 创建分类 |
| DELETE | /api/categories/{id} | 删除分类 |
| GET | /api/stats | 获取统计数据 |

## 运行测试

```bash
pytest -v
```

## 项目结构

```
todo-app/
├── app.py           # 主程序（Flask应用 + RESTful API）
├── test_app.py      # 单元测试
├── requirements.txt # 依赖
└── README.md        # 说明文档
```
