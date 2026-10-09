# Overleaf 集成（Skill D）

> 状态：**已验证**（2026-10-09，用本仓库 examples 数据在真实 Overleaf 上完整跑通：新建项目 → 上传 → 切 XeLaTeX → 编译 → 读日志 → 下载 PDF → 渲染预览）。
>
> 本 Skill **不需要写新代码**——桥（`overleaf-webbridge-check` / `kimi-webbridge`）已提供全部原子能力。Skill D 的「实现」就是本文档描述的编排序列。

## 依赖

本机运行 Kimi Browser Extension daemon（默认 `127.0.0.1:10086`）+ 浏览器扩展已连接（含 Overleaf 登录态）。

```bash
curl.exe -s http://127.0.0.1:10086/status     # 期望 extension_connected: true
```

**daemon 与扩展版本必须一致**。不一致时 `status` 会给出 `version_mismatch`，先让用户执行 `kimi-webbridge upgrade <version>` 再继续（不要自动执行 stop/upgrade）。

## 调用格式（Windows 必须遵守）

- 端点：`POST http://127.0.0.1:10086/command`
- 请求体**必须**写成独立 JSON 文件，用 `curl.exe --data-binary @file` 发送；每个请求用唯一文件名
- `session` 是**顶层字段**（不在 `args` 内），整个任务用同一个名字
- 响应为 `{"ok":true,"data":…}` 或 `{"ok":false,"error":{…}}`
- `screenshot` / `save_as_pdf` 的 `path` 用正斜杠

## 已验证的操作序列

### 0. 打开 Overleaf

```json
{"action":"navigate","args":{"url":"https://www.overleaf.com/project","newTab":true,"group_title":"Awesome-SEU-Reviewer 编译验证"},"session":"seu-reviewer-phase5"}
```

### 1. 新建项目（导入 zip）

```
click「New project」按钮（snapshot 里 name="New project" 的 button）
→ click menuitem「Existing project (.zip)」
→ evaluate 确认存在 input.uppy-Dashboard-input（accept=".zip"）
→ upload: {"action":"upload","args":{"selector":"input.uppy-Dashboard-input","files":["<绝对路径>/upload.zip"]}}
→ 等待 8–12 秒，页面自动跳转到新项目
```

zip 内文件**平铺在根目录**（`main.tex` + `exampaper.cls` + `latexmkrc`），否则 Overleaf 会多套一层目录。

> 若复用已有项目，跳过本步，直接 navigate 到项目 URL。

### 2. 切换编译器为 XeLaTeX（**必须**）

项目设置优先于 `latexmkrc` 和 `% !TEX program` magic comment——**导入不会自动切**。

```
click「Settings」按钮
→ evaluate（原生 setter + change 事件，普通赋值不触发 React）：
   const s=document.querySelector('#compiler');
   const opt=[...s.options].find(o=>/XeLaTeX/.test(o.textContent));
   Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(s,opt.value);
   s.dispatchEvent(new Event('change',{bubbles:true}));
→ 隔 2 秒再读一次 s.value 确认（回读常滞后，第一次可能仍显示旧值）
```

### 3. 触发编译

```js
[...document.querySelectorAll('button')].filter(x=>/recompile/i.test(x.textContent||''))[0].click()
```

改过设置/主文档后建议用下拉里的 `Recompile from scratch`（清缓存）。

### 4. 等待并读日志

等 25–35 秒，然后：

```js
(() => { const el=document.querySelector('.log-entry-content-raw-container')||document.querySelector('.log-entry-content');
  const t=el?(el.innerText||''):''; return JSON.stringify({total:t.length,text:t.slice(0,9000)}); })()
```

日志可能长达 35–40 KB，**必须分片读**（每次 ≤13 K 字符）。

判据：
- `!` 开头的行 = error，**必须为 0**
- `Overfull \hbox` = 排版警告，可接受
- `Output written on output.xdv (N pages, …)` = 成功，N 为页数
- `**main.tex` = 实际编译的主文件（确认没编译错文件）

### 5. 下载编译产物 PDF

Overleaf 的 PDF 是同源直链，可在页内 fetch 转 base64：

```js
(async () => { const ls=[...document.querySelectorAll('a')].map(a=>a.href).filter(h=>h.indexOf('.pdf')>=0);
  if(!window.__pdfb64){ const r=await fetch(ls[0]); const b=await r.arrayBuffer(); const u8=new Uint8Array(b);
    let s=''; const CH=8192; for(let i=0;i<u8.length;i+=CH) s+=String.fromCharCode.apply(null,u8.subarray(i,i+CH));
    window.__pdfb64=btoa(s); }
  const t=window.__pdfb64; return JSON.stringify({total:t.length,start:0,data:t.slice(0,52000)}); })()
```

后续分片复用 `window.__pdfb64`（无需重新下载），按 `slice(52000,104000)`、`slice(104000,127000)` 取。本地用 `base64.b64decode(''.join(parts))` 还原成 `.pdf`。

典型 2 页试卷 ≈ 94 KB PDF → 126 KB base64 → 3 片。

### 6. 渲染预览图核验排版

```bash
python scripts/overleaf/render_pdf_preview.py examples/output/overleaf-compiled.pdf examples/output/overleaf-page
```

再用 Read 工具打开 PNG 肉眼核验（这是**最可靠的判据**，日志只证明编译通过，预览图证明排版正确）。

## 踩过的坑

| 坑 | 现象 | 处理 |
|---|---|---|
| Settings 面板关不掉 | `click` 面板 Close 按钮返回成功但面板仍在 | 改用坐标点击 `cdp` + `Input.dispatchMouseEvent`，或直接在预览图上核验、不依赖关闭面板 |
| 日志长度超限 | 一次取全文会导致传输截断 | 分片读，每次 ≤13 K |
| 编译器回读滞后 | 切完立刻读 `s.value` 仍是旧值 | 隔 2 秒再读一次确认 |
| 上传路径分隔符 | 反斜杠被 JSON 转义破坏 | `files` 里一律用正斜杠 |
| 中文字符损坏 | Windows shell 内联 JSON 把中文变 `?` | 一律用文件体 + `curl.exe`，绝不用 `echo`/heredoc 构造 JSON |

## 与 Skill C 的衔接

Skill C 产出的 `.tex` 直接作为上传内容。模板为 `templates/exampaper.cls` 的命令集，**编译必须 XeLaTeX**，页脚总页数需**连编两遍**（Overleaf 默认会跑两遍）。

## 收尾

任务结束把浏览器交还用户，**不主动**关闭标签组；仅当用户明确要求时调用 `close_session`。
