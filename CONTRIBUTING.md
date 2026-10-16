# 如何贡献

欢迎补充文书类型、条文与范文。本仓库刻意做成「数据驱动」：大部分贡献不需要改代码，只加 YAML 或 Markdown 即可。

## 新增一类文书

1. 在 `lws/data/documents/` 下新建 `<type>.yaml`，字段见下。
2. 运行 `lws verify`，确认结构与条号校验通过。
3. 为该类型补一篇范文（见下），并跑 `pytest`。

```yaml
type: <唯一英文标识>
label: <中文名称>
category: <分类，如 民事诉讼文书 / 非诉法律文书>
usage: <一句话说明谁向谁提交、起什么作用>
party_notes:                       # 可选，按立场给提示
  原告: <提示>
  被告: <提示>
legal_basis:                       # 必须全部命中 laws.yaml 的 key
  - 民事诉讼法第122条
structure:                         # 结构顺序
  - 文书标题：xxx
elements:
  - id: xxx
    label: xxx
    required: true                 # 必备要素至少一项
    keywords: [命中关键词]         # 校验用，不可缺
    parties: [原告]                # 可选，立场侧重
    basis:
      - 民事诉讼法第122条
    note: <给使用者的说明>
tips:
  - <写作要点>
```

要点：`elements` 每项必须有 `id`、`label`、`keywords`；必备要素至少一项；`basis` 引用的 key 必须已在 `lws/data/laws.yaml` 中登记，否则 `validate_all` 报错。

## 新增一条法条

1. 先用法律数据库（如 `ailawcat-mcp` 的 `lookup_law_article`）按「法规名称 + 条号」调阅原文，确认现行有效，记录生效日期与制定机关。
2. 在 `lws/data/laws.yaml` 的对应分组下追加一条，`key` 形如 `民事诉讼法第225条`，`law` 写全称，`article` 写数字，`effective_from` 写施行日期。
3. **禁止凭记忆写条号**，尤其注意民事诉讼法 2023 年修正后条号整体位移。

## 新增一篇范文

1. 在 `lws/data/samples/` 下新建 `<序号>-<type>-<主题>.md`，序号从 01 起连续。
2. front matter 必须包含 `type`、`title`、`summary`、`reference`（含 `case_id`、`case_name`、`source`、`original_cause`、`original_forum`、`notes`）。基于真实公开案例的，写明案号与来源；脱敏示例的，在 `source` 与 `notes` 中明确标注「示例/脱敏，仅供格式参考」。
3. 正文以 `## 范文` 为标题展示完整文书，文末 `## 写作要点` 说明哪些主张被采纳、哪些没有。
4. **正文里以汉字写成的条号**（如「第二百二十五条」）必须紧跟在 `《法律名称》` 之后，且该条号必须已在法条库中登记；合同、协议等条款引用会被自动排除，不计入法条校验。
5. 该范文应能通过其所属类型的要素校验（`test_every_sample_passes_its_own_check`）。

## 本地校验

```bash
pip install -e ".[dev]"
python -m pytest -q
lws verify
```

## 代码风格

Python 部分保持无第三方依赖（仅 `PyYAML`）；新增能力优先做成数据驱动，避免写死逻辑。提交前确保 `pytest` 全绿。

## 许可

本项目以 MIT 许可发布，供学习与教学使用，不构成法律意见。
