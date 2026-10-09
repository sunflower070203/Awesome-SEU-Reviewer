# Overleaf 集成（Skill D）— 能力盘点

> 状态：**Phase 5 待实现**。本文件记录对现有 `overleaf-webbridge-check` skill 的盘点结论，避免重复建设。

## 复用对象

`~/.workbuddy/skills/overleaf-webbridge-check/SKILL.md` —— 用本机 **Kimi WebBridge**（`127.0.0.1:10086`）驱动用户真实浏览器（含 Overleaf 登录态）。

## 依赖（前置检查）

```bash
curl -s http://127.0.0.1:10086/status     # 期望 extension_connected: true
```

未监听时启动（需关闭沙箱）：
```powershell
& "$env:USERPROFILE\.kimi-webbridge\bin\kimi-webbridge.exe" start
```

## 需求 vs 能力对照

| Skill D 需求 | 桥已具备的能力 | 满足 |
|---|---|---|
| 打开 Overleaf 项目 | `navigate` | ✓ |
| 上传 / 覆盖 `.tex` | `upload`（Uppy 面板 + 点 Overwrite） | ✓ |
| 切换编译器为 XeLaTeX | `evaluate` 设 `#compiler` select | ✓ |
| 切换主文档 | `evaluate` 设 `#rootDocId` select | ✓ |
| 触发编译 | `evaluate` 点 `Recompile` 按钮 | ✓ |
| 读取编译日志 | `evaluate` 读 `.log-entry-content-raw-container` | ✓ |
| 下载编译产物 PDF | in-page fetch → base64 分片 | ✓ |

**结论：能力完全满足，Skill D 不需要扩展桥，只需编排调用序列。**

## 调用序列（草案）

```
1. navigate 打开项目 URL
2. 若编译器非 XeLaTeX → evaluate 设 #compiler（原生 setter + change 事件）
3. upload 覆盖入口 .tex → JS 点 Overwrite → JS 点 OK
4. evaluate 点 Recompile
   （若刚改过设置/主文档 → 用下拉里的「Recompile from scratch」清缓存）
5. 等 15–35 秒 → 读日志：`!` 开头的行为 error，需为 0
6. in-page fetch 取 PDF → base64 分片 → 本地 Python 解码存盘
```

## 注意事项

- **Windows 请求体**：一律写成独立 JSON 文件 + `curl --data-binary @file`（PowerShell 内联回显会被截断）
- **路径分隔符**：`path` 参数用正斜杠（反斜杠被 JSON 转义破坏）
- **日志不可单独作为结论**：`.log-entry-content-raw-container` 可能是上一次构建的文本；以 **PDF 预览出现** + **截图实际渲染** 为准
- **编译器切换不可省**：Overleaf 项目设置优先于 `latexmkrc` 与 `% !TEX program` magic comment
- **收尾**：任务结束把浏览器交还用户，不主动关闭标签组

## 与 Skill C 的衔接

Skill C 产出的 `.tex` 直接作为本 Skill 的上传内容。模板固定为 `templates/exampaper.cls` 定义的命令集，编译必须 XeLaTeX。
