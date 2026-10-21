# 项目与聊天异常的快速分诊

依次确认账号、工作区或主机、侧栏分组、过滤条件、归档状态，再判断是否需要检查本地存储。不要仅因侧栏为空就替换配置。

| 现象 | 下一步 | 对应问题 |
| --- | --- | --- |
| 项目仍在，但聊天平铺 | 查看分组设置 | [CT-003](../issues/CT-003-sidebar-grouping.md) |
| 少数聊天不显示 | 调整过滤条件、查看归档 | [CT-004](../issues/CT-004-hidden-or-archived-chats.md) |
| 少数项目入口不显示 | 重新添加原目录，并检查归属 | [CT-001](../issues/CT-001-projects-disappear.md) |
| 多数本地项目同时消失，旧聊天仍存在 | 检查状态文件及日志，先备份 | [CT-001](../issues/CT-001-projects-disappear.md) |
| 提示修复就绪，但重启无变化 | 确认修复程序是否真正完成写入 | [CT-002](../issues/CT-002-repair-stops-on-exit.md) |
| 读写文件或联网被拒绝 | 核对操作目标与权限边界 | [CT-005](../issues/CT-005-permission-denied.md) |
| 原文件夹或聊天本体也无法找到 | 单独处理数据恢复，保留现场 | 不直接套用配置恢复 |

当账号、主机或实际 `CODEX_HOME` 与以前不同，也可能看见不同的本地历史。先确认正在读取哪个目录，不要将它直接归因于第三方服务商、模型或升级。

只读辅助检查：

```sh
python tools/codex_doctor.py --codex-home /path/to/.codex
```

从仓库根目录执行。路径必须指向实际使用的状态目录。输出 `unknown`、`unavailable` 或 `schema_not_supported` 表示检查范围有限，不能解释为数据丢失。
