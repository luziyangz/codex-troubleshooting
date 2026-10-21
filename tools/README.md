# Codex Doctor 只读诊断工具

工具只收集结构和计数，用来判断下一步应该排查什么。不会修改 Codex 文件、请求网络或生成自动修复清单。不会尝试读取 `auth.json`、聊天正文、原始日志、项目名称、工作目录或真实标识。

## 运行

从仓库根目录使用 Python 3.10+：

```sh
python tools/codex_doctor.py
python tools/codex_doctor.py --codex-home /path/to/.codex
python tools/codex_doctor.py --output ./doctor-report.json
```

Windows PowerShell 例子：

```powershell
python tools/codex_doctor.py --codex-home "$env:USERPROFILE\.codex"
```

如果设置过 `CODEX_HOME`，优先使用默认检测或传入其真实值。不要照抄默认目录，去检查另一份闲置状态。保存报告时父目录需已存在；工具不会覆盖已有文件。

## 读懂结果

| 代码 | 含义 | 下一步 |
| --- | --- | --- |
| STATE_PARSE_FAILED | 当前主状态无法按预期解析 | 备份现场并结合启动错误核对 |
| STATE_MISSING | 指定目录没有主状态文件 | 确认实际状态目录 |
| PROJECT_DEFINITIONS_WITHOUT_CACHE | 某份数据库有项目，配置缓存为空或不可解析 | 确认活动数据源，按恢复 SOP 评估 |
| LOCAL_ASSIGNMENT_CACHE_MISMATCH | 本地关联和缓存项目不匹配 | 核对结构与应用接口，不自动覆盖 |
| MULTIPLE_DATABASE_CANDIDATES | 找到多份状态数据库 | 不根据文件新旧自动决定哪份正确 |
| STATE_CHECK_INCOMPLETE | 结构不支持、文件过大或读取失败 | 单独排查该条件 |
| NO_STRUCTURAL_FAILURE_FOUND | 没发现工具能识别的问题 | 继续检查界面、账号、主机、过滤和归档 |

`readable` 不表示数据库是活动库；配置中有关联也不表示侧栏已恢复。`threads` 计数可能包含内部会话。工具不是完整性检查或备份工具。

首版按已观察到的 JSON 字段和 SQLite 表进行检查。支持结构变化时需新增脱敏合成测试。实际跨平台适用性以测试记录为准，不把标准库可运行等同于已在所有平台验证。

## 测试

```sh
python -m unittest discover -s tests -v
python tools/check_docs.py
```

测试使用临时目录和合成数据，覆盖非法 JSON、空字符、缺失目录、不同表结构、重复数据库候选、报告脱敏及检查前后输入不变。
