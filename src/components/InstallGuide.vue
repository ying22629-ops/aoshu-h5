<script setup>
import { canPromptInstall, isAndroid, isIOS, isStandalone, isWeChat, promptInstall } from '../install.js'
</script>

<template>
  <div class="guide">
    <p v-if="isStandalone" class="done">✓ 已经添加到桌面,正在以 App 模式使用。</p>

    <template v-else-if="isWeChat">
      <p class="lead">微信里不能直接添加到桌面,请先用浏览器打开:</p>
      <ol>
        <li>点右上角 <b>···</b></li>
        <li>选 <b>{{ isIOS ? '在 Safari 中打开' : '在浏览器中打开' }}</b></li>
        <li>在浏览器里按下面的方法添加到桌面</li>
      </ol>
    </template>

    <template v-else-if="isIOS">
      <ol>
        <li>用 <b>Safari</b> 打开本页面</li>
        <li>点底部的 <b>分享</b> 按钮(方框加向上箭头)</li>
        <li>往下找到 <b>添加到主屏幕</b>,点右上角“添加”</li>
      </ol>
    </template>

    <template v-else>
      <button v-if="canPromptInstall" class="btn primary install" @click="promptInstall">📲 一键添加到桌面</button>
      <ol>
        <li>点浏览器右上角(或底部)的 <b>菜单</b></li>
        <li>选 <b>添加到主屏幕</b> 或 <b>安装应用</b></li>
        <li v-if="isAndroid">部分国产浏览器可能要在“工具箱”里找;如果没有这个选项,建议换用 Chrome 或 Edge</li>
        <li v-else>在电脑上也可以安装:地址栏右侧会出现安装图标</li>
      </ol>
    </template>
  </div>
</template>

<style scoped>
.guide {
  font-size: 14px;
}
.lead,
.done {
  margin: 0 0 6px;
}
.done {
  color: var(--ok);
  font-weight: 600;
}
ol {
  margin: 0;
  padding-left: 1.4em;
}
li {
  margin: 4px 0;
}
.install {
  width: 100%;
  margin-bottom: 8px;
}
</style>
