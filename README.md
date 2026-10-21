# Codex 问题与解决方案集合

非官方的中文 Codex 排障知识库。每个问题都记录**现象、原因与证据、解决方案、验收方法及适用范围**，帮助你把一次故障变成可以复用的处理流程。

本项目与 OpenAI 没有隶属关系。内容可能涉及版本相关的内部文件结构，先按问题页面确认条件。仓库不收集用户配置、聊天正文或登录凭据。

## 从这里开始

1. 项目或聊天突然不见：先看 [快速分诊](docs/triage.md)。
2. 确认是项目状态异常：按 [通用恢复 SOP](docs/recovery-sop.md) 操作。
3. 想检查本地状态：运行 [只读诊断工具](tools/README.md)。
4. 提交新问题：使用 [问题反馈表单](https://github.com/luziyangz/codex-troubleshooting/issues/new/choose)。

## 问题索引

| 编号 | 问题 | 依据 | 适用范围 |
| --- | --- | --- | --- |
| [CT-001](issues/CT-001-projects-disappear.md) | 项目消失，旧聊天集中到最近 | 实测案例，状态解析失败有日志证据 | Windows 本地项目；其他环境需重新核对 |
| [CT-002](issues/CT-002-repair-stops-on-exit.md) | 已安排修复，重启后仍然没有恢复 | 实测案例，修复进程随应用退出而停止 | 修复进程依赖被关闭的宿主时 |
| [CT-003](issues/CT-003-sidebar-grouping.md) | 聊天平铺显示，项目分组不符合预期 | 实测设置检查；通用分诊 | 提供相应侧栏分组设置的版本 |
| [CT-004](issues/CT-004-hidden-or-archived-chats.md) | 只找不到部分聊天 | 官方排查流程整理 | 提供过滤与归档功能的版本 |
| [CT-005](issues/CT-005-permission-denied.md) | 读写文件或联网报权限错误 | 官方权限说明整理 | Windows Codex 沙箱，配置随版本变化 |

“实测案例”只证明记录中的条件下有效。“官方流程整理”并不表示维护者遇到过该故障。未知原因会明确标注，不把猜测当成根因。

## 只读诊断

需要 Python 3.10 或更高版本，仅使用标准库：

```sh
python tools/codex_doctor.py
python tools/codex_doctor.py --codex-home /path/to/.codex --output ./doctor-report.json
python -m unittest discover -s tests -v
```

目录选择顺序为 `--codex-home`、环境变量 `CODEX_HOME`、当前用户目录下的 `.codex`。工具检查 JSON 是否有效、项目及归属记录数量、可读的 SQLite 表结构；不修改 Codex 状态，不读取登录凭据或聊天正文，不发网络请求。

工具输出的是诊断线索，不能单凭一个报错确认根因。首版不提供通用自动写回：不同版本的数据结构不同，聊天工作目录也不足以证明项目归属。

## 通用方案的边界

通用的是**分诊 → 取证 → 备份 → 生成本次清单 → 副本验证 → 独立执行 → 重启验收 → 必要时回退**，不是把某台电脑的路径、项目数量和旧修复脚本复制给所有人。

本仓库不附带原事故配置、原始日志、个人路径或包含固定项目标识的恢复包。详细原则见 [数据与证据规范](docs/evidence-and-privacy.md)。

## 持续收录与内容分享

- [贡献指南](CONTRIBUTING.md)：统一的问题结构和验证要求。
- [通用问题模板](templates/problem.md)：新案例可直接填写。
- [发布流程](publishing/README.md)：以 GitHub 为维护源，向 CSDN、稀土掘金、知乎分享。
- 首篇分享稿：[CSDN](publishing/csdn-projects-disappear.md) · [掘金](publishing/juejin-projects-disappear.md) · [知乎](publishing/zhihu-projects-disappear.md)。这些是待审稿，尚未发布到对应平台。

最后核对日期：2026-10-21。后续更正以仓库提交记录为准。

## 许可

仓库原创代码与文字使用 [MIT License](LICENSE)。第三方链接内容归原作者所有，引用不改变其许可。
