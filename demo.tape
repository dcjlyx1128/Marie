# 用 vhs 录制演示 GIF: vhs demo.tape  (生成 docs/demo.gif)
# 安装 vhs: brew install vhs
# ⚠️ 录制前必须先设置 key,否则 --ai 会失败:
#     export MARIE_API_KEY=sk-你的新密钥
Output docs/demo.gif

Set FontSize 16
Set Width 1200
Set Height 900
Set Theme "Dracula"
Set Padding 20

Type "python examples/make_demo.py"  Enter  Sleep 1.5s
Type "ls examples/messy"             Enter  Sleep 2.5s
Type "marie organize examples/messy --ai"  Enter  Sleep 10s
Sleep 4s
