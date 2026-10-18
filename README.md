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

## 题库

题目在 `src/data/questions.json`。每道题的结构:

| 字段 | 说明 |
|---|---|
| `id` | 唯一,如 `calc-09` |
| `topic` | 专题 id(见文件顶部 `topics`) |
| `grade` / `difficulty` | 年级 3–6 / 难度 1–3 |
| `type` | `input`(键盘输入)或 `choice`(需要 `options`) |
| `stem` / `hints` / `solution` | 题干、分步提示(≥2 条)、解析;公式用 `$...$`(KaTeX) |
| `answer` | 标准答案;判题时分数、小数等价(`9/10` = `0.9`),会忽略末尾单位 |
| `verify` | 一段独立算出答案的 Python 表达式,`npm run verify` 用它核对 `answer` |

新增题目后必须运行 `npm run verify`,通过后再打包。AI 生成的题目也走同样的流程:生成后写 `verify`,校验通过,再由人工审读题干和解析。

## 代码结构

- `src/bank.js`:读题库、每日一题、判题
- `src/store.js`:练习记录、错题本、打卡(localStorage)
- `src/views/`:首页 / 刷题 / 错题本 / 我的
- `scripts/verify_questions.py`:题库校验
