# Test_Prompt

提示词调试平台，目前包含：

- 基础信息：模型服务器（原型 `list_server.html`、`server_add.html`）
  与模型（原型 `model_list.html`、`model_add.html`）；
- 提示词调试：按原型 `prompt_dis.html` 组织页面，点「开始调试」真实调用所选模型的接口。

技术栈：Python 3.14 + Django 6.1 + SQLite。

## 快速开始

```bash
pip install -r requirements.txt
python manage.py migrate          # 建表并写入原型列表中的初始数据
python manage.py runserver        # http://127.0.0.1:8000/
```

| 页面 | 地址 | 原型 |
| --- | --- | --- |
| 服务器列表 | `/server/list/`（`/` 会跳转到这里） | `list_server.html` |
| 添加服务器 | `/server/add/` | `server_add.html` |
| 编辑服务器 | `POST /server/update/` | 列表页新增的编辑弹窗 |
| 删除服务器 | `POST /server/delete/` | 原型中的删除确认弹窗 |
| 模型列表 | `/model/list/` | `model_list.html` |
| 添加模型 | `/model/add/` | `model_add.html` |
| 编辑模型 | `POST /model/update/` | 列表页新增的编辑弹窗 |
| 删除模型 | `POST /model/delete/` | 原型中的删除确认弹窗 |
| 提示词调试 | `/prompt/dis/` | `prompt_dis.html` |
| 调试调用 | `POST /prompt/run/` | 页面「开始调试」按下的每一次调用 |

后台管理：`python manage.py createsuperuser` 后访问 `/admin/`。

## 目录结构

```
manage.py
requirements.txt
Prompt_Test_DB.db                    # SQLite 库文件（库名 Prompt_Test_DB）
test_prompt/                         # 项目配置
  settings.py  urls.py  wsgi.py  asgi.py
basic/                               # 基础信息 + 提示词调试模块
  models.py                          # ai_server / ai_model
  views.py  urls.py  admin.py
  migrations/0001_initial.py         # 建表
  migrations/0002_seed_ai_server.py  # list_server.html 原型里的初始数据
  migrations/0003_seed_ai_model.py   # model_list.html 原型里的初始数据
  templates/basic/
    base.html                        # 页面骨架：左侧菜单 / 页头 / Toast / 公共脚本
    list_server.html                 # 服务器列表      （原型 list_server.html）
    server_add.html                  # 添加服务器      （原型 server_add.html）
    model_list.html                  # 模型列表        （原型 model_list.html）
    model_add.html                   # 添加模型        （原型 model_add.html）
    prompt_dis.html                  # 提示词调试      （原型 prompt_dis.html）
```

## 数据库

SQLite，库名 `Prompt_Test_DB`，库文件为项目根目录下的 `Prompt_Test_DB.db`。
两张表与给定的建表语句一致：

- `ai_server`：`id`、`plat_name`（唯一，约束名 `uk_plat_name`）、`base_url`、`comp_name`、
  `home_url`、`created_at`、`updated_at`。
- `ai_model`：`id`、`srv_id`（外键 → `ai_server.id`，`on_delete=RESTRICT`）、`model_name`、
  `in_price`、`out_price`、`bill_unit`、`model_type`、`doc_url`、`created_at`、`updated_at`。

与原 MySQL 建表语句的差异（SQLite 限制）：

- `created_at` / `updated_at` 没有数据库层 `DEFAULT CURRENT_TIMESTAMP` / `ON UPDATE`，
  由 Django 的 `auto_now_add` / `auto_now` 在写入时维护。
- 外键在 SQLite 上以 `REFERENCES` 形式存在，`ON DELETE RESTRICT` 由
  `on_delete=RESTRICT` 在 ORM 层保证。
- `DECIMAL(12,6)` 映射为 `DecimalField(max_digits=12, decimal_places=6)`。

## 按原型开发的约定

- 样式、字段、排版逐字取自原型：五个页面的 `<style>` 块、页头、Toast、删除弹窗、
  表单与表格骨架均直接取自 `list_server.html` / `server_add.html` /
  `model_list.html` / `model_add.html` / `prompt_dis.html`，控件与文案保持原样。
  列表页新增的编辑弹窗没有原型，按对应添加页的字段与控件补齐，样式沿用同一套变量
  （模板里的「编辑弹窗」一节）。
  左侧菜单与页头由 `base.html` 统一输出，按当前页面高亮 / 展开对应的二级菜单。
- 必填等校验沿用原型自带的前端校验，服务端不再重复校验，只负责落库。
- 服务端只处理数据库层面的错误：`plat_name` 唯一约束冲突、外键 `RESTRICT`
  导致无法删除，均以原型 Toast 的警示样式提示。
- 协议、列表、表格均按原型的属性输出（如行上的 `data-platform` / `data-model` /
  `data-type` / `data-in` / `data-out`），因此原型的筛选脚本无需改动即可作用于
  `ai_model` 表中的数据。列表行另外补了 `data-base-url` / `data-home-url`（服务器行）
  与 `data-unit` / `data-url`（模型行），供编辑弹窗回填。

## 已实现的交互

- 列表页：平台 / 官方名与公司名检索（`搜索` 提交到服务端按 `icontains` 查询，
  `重置` 回到全量列表，回车即搜索）、全选 / 单行选择、`已选 N 项` 计数、
  删除按钮随选择启用、删除确认弹窗、确认后从 `ai_server` 表删除并提示
  `已删除 N 个服务器`、无匹配时显示原型的空状态、聚合平台标记。
  平台 / 官方名与公司名都是指向该平台首页（`ai_server.home_url`）的新窗口链接，
  未登记首页时退化为普通文字；`编辑` 按钮随选择启用，弹出与「添加服务器」字段一致的
  编辑弹窗（平台 / 官方名、api 网址、公司名、首页），保存后 `POST /server/update/`
  落库并刷新列表。
- 添加页：可编辑下拉框（选项来自 `ai_server` 已登记的平台 / 官方名，支持输入过滤、
  高亮匹配、上下键选择、回车确认、无匹配时的自定义平台提示）、必填与 URL 格式校验、
  保存成功后 Toast 提示「已保存服务器「xxx」」并跳回列表页、取消返回列表页。
- 模型列表页：平台 / 官方名与类型（可编辑下拉框，选项取自当前表格中的去重值）、
  模型名、输入 / 输出 token 费用区间的筛选都在页面上完成（沿用原型脚本，作用在
  `ai_model` 的数据上）、`重置` 清空条件并提示、全选 / 单行选择、
  `共 N 条记录 · 已选 N 项` 计数、删除按钮随选择启用、删除确认弹窗、确认后从
  `ai_model` 表删除并提示 `已删除 N 个模型`、无匹配时显示原型的空状态。
  平台 / 官方名链接到该平台首页（`ai_server.home_url`），模型名链接到模型说明
  （`ai_model.doc_url`），未登记时退化为普通文字；右上角 `添加模型` 指向 `/model/add/`；
  `编辑` 按钮随选择启用，弹出与「添加模型」字段一致的编辑弹窗（服务器、模型名、类型、
  输入 / 输出 token 计费、单位、网址），保存后 `POST /model/update/` 落库并刷新列表。
- 添加模型页：服务器下拉选项来自 `ai_server` 已登记的平台 / 官方名；类型为可多选
  下拉框（全选 / 清空 / 完成，已选标签可点 × 移除，落库时以「,」拼接）；
  计费输入只保留数字与小数点；必填与 URL 格式校验；保存成功后 Toast 提示
  「已保存模型「xxx」」并跳回列表页；取消返回列表页。
- 提示词调试页：服务器下拉与 Base_url 读取 `ai_server`，模型下拉与单价读取
  `ai_model`（顺序都与列表页一致，选完服务器才可选模型）；`api_key` 可切换明文 /
  密文、系统提示词可一键复制、输出框可一键复制；「多轮会话」勾选后可增删轮次
  （最多 6 轮，留空轮次按原型规则忽略），系统提示词与各轮用户提示词都带实时字数 /
  token 估算；`开始调试`（或 `Ctrl/Cmd + Enter`）沿用原型的必填校验，通过后先禁用按钮、
  文案改为「调试中…」，再按轮次逐次调用远端 `chat/completions`。

  **调用与输出（原型第 7 条要求）**：「模型输出」文本框显示的是每次调用大模型的真实
  返回——单轮即模型原文，多轮按 `【第 N 轮】` 分段累加，每收到一次返回就立刻刷新该框；
  上一轮回复会作为 `assistant` 消息带入下一轮。调用完成后按钮恢复、输出框上方显示
  原型的「用时 N ms · 输出 N tokens」、四张指标卡按原型脚本做计数动画；任一次调用
  失败即停止，输出框保留已拿到的内容，`outMeta` 显示「调用失败」，Toast 以警示样式给出
  原因（HTTP 状态 + 远端 `error.message`、连接失败、返回非 JSON、缺少
  `choices[0].message.content`、服务器未登记）。

## 与原型的已知差异

1. 两个添加页的 `syncPreview()` 分别引用了 `pvName` / `pvCompany` / `pvApi` /
   `pvHome` 与 `pvName` / `pvServer` / `pvUrl` / `pvTypes` / `pvIn` / `pvOut`，
   但原型 HTML 中没有对应的预览区标记（只有 `.side` / `.preview` / `.tips` 样式与
   这部分脚本）。模板按原型原样保留标记，未新增预览区；预览逻辑加了空值保护，
   不会报错。若把预览区标记补进原型，脚本无需改动即可生效。
2. 原型中指向 `detail_server.html`、`detail_model.html`、`detail_company.html`
   的详情页因原型尚未提供，未新建页面；列表页里的平台 / 官方名、公司名与模型名改为
   外链到数据自身的地址——平台首页 `ai_server.home_url`、模型说明 `ai_model.doc_url`
   （`prompt_dis.html` 已实现，左侧菜单直接跳转 `/prompt/dis/`）。
3. 分页器保持原型的静态状态（上一页 / 1 / 2 / 3 / 下一页），未接后端分页。
4. 下拉框选项改为读表：`server_add.html` 的平台 / 官方名（原型里是固定的 4 个平台短名）
   与 `model_add.html` 的服务器下拉都读取 `ai_server` 表中已登记的记录（与列表页同一批
   数据）；「聚合平台」标记按原型规则判断（平台名以 硅基流动 / OpenRouter / 魔搭社区 开头）。
5. 删除为真实删除（原型只在页面上移除行）。
6. 计费单位：原型列表里的单位后缀不统一（`/K`、`/百万`、`/k`、部分为空），初始数据
   按原型原样落到 `bill_unit`；列表按 `单价 / 单位` 渲染，未填单位的行不显示后缀。
   计费为 0 时原型用 `—` 表示该维度不计费，只有输入与输出都为 0 的模型按原型显示
   `¥0.00`。
7. 「免费 / 限免」与「区域部署」标记在原型中按行手写，这里改为按数据判断：
   输入与输出计费都为 0 → `免费`（聚合平台上的免费模型按原型显示 `限免`）；
   平台为 Azure OpenAI → `区域部署`。
8. 类型可多选（原型添加页的控件如此），落库到 `ai_model.model_type` 时以「,」拼接，
   列表页按原型的 `.type` 标签逐个渲染。
9. `prompt_dis.html` 的脚本引用了 `sysCount` / `sysTok` / `estIn` 三个统计位，但原型
   HTML 里没有对应标记；模板保持原型标记原样、未新增节点，脚本改为判空后写入，
   不会因取不到节点而报错。
10. 调试页的指标卡（输入 / 输出 token 与费用）沿用原型脚本的估算口径
   （`estimateTokens` 按字符粗估）与 `ai_model` 表中的单价，不采用接口返回的 `usage`，
   因此与账单口径可能存在出入；调用失败时指标卡不刷新。
11. 「提示词调试」在 `prompt_dis.html` 上保持原型的
   `<div class="m1 current" id="m1-debug">`（原型该节点本身不带 `<a>` 包裹），其他页面
   才补上指向 `/prompt/dis/` 的链接，避免当前页自链。
12. 计费不做四舍五入：原型按两位小数渲染（`17.50`、`1.10`），本项目按库里的原值
   去掉尾部多余的 0 输出（`17.5`、`0.003`、`0`），行上的 `data-in` / `data-out`
   同样是原值，避免 `0.003` 这类小额单价被舍成 `0.00`。
