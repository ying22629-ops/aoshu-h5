# 思维数学 H5

小学数学思维训练 H5:专题练习、分步提示、错题本、每日一题。纯前端,无后端,练习记录保存在浏览器 localStorage。

## 运行

```bash
npm install
npm run dev        # 开发,http://localhost:5173(局域网内手机也能访问)
npm run verify     # 校验题库(需要 Python 3)
npm run build      # 打包到 dist/
npm run preview    # 本地预览打包结果
```

## 部署

`dist/` 是纯静态文件,使用相对路径加 hash 路由,上传到任意静态托管(云服务器 Nginx、对象存储 + CDN 等)的任意目录即可,不需要服务端配置。国内服务器需要完成 ICP 备案。

**演示用 GitHub Pages**:仓库里已经有 `.github/workflows/deploy.yml`,每次推送到 `main` 都会先校验题库,再打包、发布。第一次使用时,在仓库的 Settings → Pages 里把 Source 选成 **GitHub Actions**。发布后的网址是 `https://<用户名>.github.io/<仓库名>/`。

## 添加到手机桌面(PWA)

页面带有 `manifest.webmanifest` 和 `sw.js`(离线缓存,只在打包后的版本里生效),必须通过 **HTTPS** 访问才能安装:

- iPhone:用 Safari 打开 → 分享 → 添加到主屏幕
- 安卓:用 Chrome 或 Edge 打开 → 菜单 → 添加到主屏幕 / 安装应用
- 微信里打不开安装选项,要先点右上角 ··· 选“在浏览器中打开”

App 内的“我的”页和首页横幅会按设备自动显示对应步骤。图标在 `public/icons/`。

## 题库

题目在 `src/data/questions.json`。每道题的结构:

| 字段 | 说明 |
|---|---|
| `id` | 唯一,如 `calc-09` |
| `topic` | 专题 id(见文件顶部 `topics`) |
| `grade` / `difficulty` | 年级 1–6 / 难度 1–3 |
| `type` | `input`(键盘输入)或 `choice`(需要 `options`) |
| `stem` / `hints` / `solution` | 题干、分步提示(≥2 条)、解析;公式用 `$...$`(KaTeX) |
| `answer` | 标准答案;判题时分数、小数等价(`9/10` = `0.9`),会忽略末尾单位 |
| `verify` | 一段独立算出答案的 Python 表达式,`npm run verify` 用它核对 `answer` |
| `figure` / `solutionFigure` | 可选,题目配图 / 解析配图,填 `src/figures/` 下的文件名(不带 `.svg`) |

配图是手写的 SVG(建议 `viewBox` 宽 280~320),颜色不要写死,用这些 class:`l` 线条、`d` 虚线、`a` 强调色线条、`s` 浅紫填充、`w` 浅黄填充、`fa` 强调色实心、`text.ta` 强调色文字、`text.sm` 小号文字。这样深色、浅色模式都能自动适配。注意配图不能直接透露答案。

新增题目后必须运行 `npm run verify`,通过后再打包。

## 用 AI 扩充题库

大模型做数学题会出错,所以 AI 出的题要经过“生成 → 独立重解 → 程序验证 → 人工审核”四关才能进题库。

```bash
pip install -r scripts/requirements.txt
export ANTHROPIC_API_KEY=...        # Windows PowerShell: $env:ANTHROPIC_API_KEY="..."
python scripts/generate_questions.py --topic travel --grade 5 --count 5
python scripts/generate_questions.py --topic count --grade 4 --count 3 --difficulty 2
```

`--topic` 取 `topics` 里的 id;`--grade` 为 1–6;`--count` 每次 1–10 道;默认模型 `claude-opus-5-5`(`--model` 可改)。

每道题的检查:

1. **生成**:模型按题库结构出题,包括 `verify` 表达式。提示词要求改编经典题型,不照搬杯赛真题。
2. **独立重解**:另开一次调用,只给题干(选择题加选项),不给答案、解析和 `verify`,让模型重新解题。
3. **程序验证**:用 `verify_questions.py` 同一套 `ENV` 和 `normalize` 执行 `verify`。执行前先做语法白名单检查(禁止 `__import__`、`open`、下划线属性等),再放进独立的 Python 子进程运行,超过 5 秒就算失败。
4. **分流**:出题答案、重解答案、`verify` 结果三方一致(分数和小数按前端判题规则视为相等),并且格式检查通过、题干不重复,就写入 `scripts/out/pending.json`;否则写入 `scripts/out/rejected.json`,`reasons` 字段写明原因。

人工审核:打开 `scripts/out/pending.json`,逐题检查题干是否通顺、有无歧义、是否符合年级、是否像某道真题,然后把 `review` 改成:

- `"approved"`:合并进题库
- `"rejected"`:移到 `rejected.json`,原因写在 `review_note`
- 保持 `"pending"`:下次再审

审核时可以直接修改题目内容,合并时会重新检查。AI 只出纯文字题,不生成 `figure` / `solutionFigure`;如果审核时决定配图,先把 SVG 放进 `src/figures/`,再在 pending.json 的题目里加上这两个字段,合并时会原样保留并检查文件是否存在。`_check` 里有重解答案和解题过程,可供参考。

```bash
python scripts/merge_pending.py
npm run build
```

`merge_pending.py` 会按专题接着编号分配 id(如 `travel-09`),把新题追加到 `questions.json` 末尾,不改动原有内容,再对合并结果跑一遍 `verify_questions.py`。任何一道题复查不通过,或者整体校验失败,题库都不会被修改。

**演示模式**:不调用 API、不需要 key,用内置假数据走完整个流程。5 道假题里 2 道通过,3 道分别因为 verify 不一致、重解不一致、verify 不安全被拒。结果写到 `scripts/out/dry-run/`,不会碰真题库:

```bash
python scripts/generate_questions.py --dry-run
python scripts/merge_pending.py --dry-run     # 把所有待审核题视为通过,合并到 scripts/out/dry-run/questions.json
```

`scripts/out/` 已在 `.gitignore` 中。

## 代码结构

- `src/bank.js`:读题库、每日一题、判题
- `src/store.js`:练习记录、错题本、打卡(localStorage)
- `src/views/`:首页 / 刷题 / 错题本 / 我的
- `scripts/verify_questions.py`:题库校验(可传入其他 json 路径)
- `scripts/generate_questions.py` / `scripts/merge_pending.py`:AI 出题流水线(见上),公共逻辑在 `scripts/qbank.py`
