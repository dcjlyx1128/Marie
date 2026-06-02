# 用 vhs 录制演示 GIF: vhs demo.tape  (生成 docs/demo.gif)
# 安装 vhs: brew install vhs
# 演示 watch 自动整理,纯规则、无需 API key。
Output docs/demo.gif

Set FontSize 16
Set Width 1200
Set Height 800
Set Theme "Dracula"
Set Padding 20

Hide
Type "export PATH=/opt/miniconda3/bin:$PATH" Enter
Type "rm -rf /tmp/marie_demo /tmp/marie_src && mkdir -p /tmp/marie_demo /tmp/marie_src" Enter
Type "for f in song.mp3 movie.mp4 archive.zip; do printf x > /tmp/marie_src/$f; done" Enter
Type "clear" Enter
Show

Type "# Marie watch:监听文件夹,新文件到达自动归类(只移不删,可 undo)" Enter Sleep 1s
Type "marie watch /tmp/marie_demo &" Enter Sleep 2.5s
Type "cp /tmp/marie_src/song.mp3 /tmp/marie_demo/" Enter Sleep 3.5s
Type "cp /tmp/marie_src/movie.mp4 /tmp/marie_demo/" Enter Sleep 3.5s
Type "cp /tmp/marie_src/archive.zip /tmp/marie_demo/" Enter Sleep 3.5s
Type "ls /tmp/marie_demo" Enter Sleep 3s
Type "marie undo /tmp/marie_demo" Enter Sleep 3s
Type "kill %1" Enter Sleep 1.5s
