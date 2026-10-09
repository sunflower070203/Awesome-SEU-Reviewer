%%% ---------------------------------------------------------------------------
%%% exampaper.cls —— 通用中文试卷 LaTeX 模板（A4 / 12pt）
%%%
%%% 版式取自「东南大学试卷（A卷）」样式，可按需改造成任意高校/课程的试卷：
%%%   正文宋体 12pt、栏目标题黑体、填写内容楷体、左侧竖排密封线、
%%%   自动中文大题序号（一、二、三…）、页脚「试卷名  共 X 页  第 Y 页」。
%%%
%%% 编译：xelatex（推荐）或 lualatex，请连续编译两遍
%%%       （页脚总页数由 lastpage 提供，第二遍才正确）。
%%% 许可：MIT
%%% ---------------------------------------------------------------------------
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{exampaper}[2026/10/07 v0.1 Generic Chinese exam paper template]

%% ===========================================================================
%% 1. 基类与选项
%% ===========================================================================
\LoadClass[12pt,a4paper]{ctexart}
%% 未识别的选项（如 fontset=mac）原样交给 ctexart
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{ctexart}}
\ProcessOptions\relax

%% ===========================================================================
%% 2. 依赖宏包
%% ===========================================================================
\RequirePackage{geometry}
\RequirePackage{amsmath}    % 数学环境（cases、align…）
\RequirePackage{graphicx}   % \rotatebox：竖排密封线文字
\RequirePackage{array}
\RequirePackage{tabularx}   % 评分表（按 \textwidth 等分列宽）
\RequirePackage{multirow}   % 评分表「总分」跨行
\RequirePackage{lastpage}   % 页脚「共 X 页」
\RequirePackage{eso-pic}    % 密封线背景层
\RequirePackage{fancyhdr}   % 页脚
\RequirePackage{iftex}      % 引擎检测：本模板必须用 XeLaTeX/LuaLaTeX
\ifPDFTeX
  \ClassError{exampaper}%
    {本模板包含中文，必须使用 XeLaTeX 或 LuaLaTeX 编译}%
    {请在编辑器里把编译器切换为 XeLaTeX 后重新编译：%
     Overleaf 为 Menu ---> Compiler ---> XeLaTeX；%
     命令行请执行 xelatex main.tex}
\fi

%% ===========================================================================
%% 3. 页面尺寸（A4 = 595.28pt × 841.89pt）
%%    top=4cm   标题首行基线距页顶约 4.6cm，与原卷一致
%%    left=3.7cm 留出左侧密封线位置；right=2.6cm
%%    headheight/headsep 置 0，使正文顶边正好落在 top 处
%% ===========================================================================
\geometry{a4paper,
  top=4cm, bottom=2.5cm,
  left=3.7cm, right=2.6cm,
  headheight=0pt, headsep=0pt,
  footskip=0.8cm}

%% ===========================================================================
%% 4. 可调版式参数（集中在此，方便按校情修改）
%% ===========================================================================
\setlength{\parindent}{0.8em}   % 段落首行缩进（原卷约 9.8pt）
\setlength{\parskip}{0pt}       % 段间距统一由环境/命令控制
\newlength{\examindent}
\setlength{\examindent}{0.8em}  % 题目整体左缩进（与首行缩进一致）
\newcommand*{\examziju}{0.46em} % 试卷标题字距（相对标题字号；原卷约 7.9pt）
\newlength{\examitemsep}
\setlength{\examitemsep}{13pt}  % 小题之间的默认间距（原卷约 13pt）
\newlength{\examsectionpreskip}
\setlength{\examsectionpreskip}{1.2em}
\newlength{\examsectionpostskip}
\setlength{\examsectionpostskip}{0.4em}

%% ===========================================================================
%% 5. 页脚：试卷名 + 共 X 页 + 第 Y 页
%% ===========================================================================
\newcommand*{\examname}[1]{\def\exam@name{#1}}
\examname{试卷}                 % 默认值，请在导言区用 \examname{...} 覆盖
\newcommand*{\exam@foot}{%
  \footnotesize\songti
  \exam@name\hspace{1em}共~\pageref{LastPage}~页\hspace{1em}第~\thepage~页}
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancyfoot[C]{\exam@foot}
%% plain 样式也装上同一个页脚：多页试卷里若某页被切成 plain（\thispagestyle{plain}、
%% 章节起始页等），页码与「共 X 页」不会丢。
\fancypagestyle{plain}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0pt}%
  \renewcommand{\footrulewidth}{0pt}%
  \fancyfoot[C]{\exam@foot}}

%% ===========================================================================
%% 6. 试卷标题：居中、\Large、自动加字距
%%    用法：\examtitle{东南大学试卷（A卷）}
%% ===========================================================================
\def\exam@stop{}
\def\exam@next{}
\def\examspread#1{{\kern-\examziju\exam@spreadloop#1\exam@stop}}
\def\exam@spreadloop#1{%
  \ifx#1\exam@stop
    \let\exam@next\relax
  \else
    \kern\examziju#1%
    \let\exam@next\exam@spreadloop
  \fi
  \exam@next}
\newcommand{\examtitle}[1]{{\centering\Large\songti\examspread{#1}\par}}

%% ===========================================================================
%% 7. 抬头信息栏
%%    用法：\examfield[<横线宽度>]{<项目名>}{<填写内容>}
%%    例：\examfield[3.5cm]{课程名称}{高等数学分析II}
%%        内容留空即得一条空白横线：\examfield[3.5cm]{课程名称}{}
%% ===========================================================================
\newcommand{\examfield}[3][3cm]{%
  {\heiti#2}\hspace{0.15em}\underline{\makebox[#1][c]{\kaishu#3}}}

%% ===========================================================================
%% 8. 评分表
%%    用法：\examscoretable[<大题数>]（默认 6，即 6 个评阅格）
%% ===========================================================================
\newcolumntype{C}{>{\centering\arraybackslash}X}
\newcounter{examsection}
\newcounter{examitem}
\newcount\exam@col

%% 中文数字（1–12），超出则回退为阿拉伯数字
\newcommand*{\exam@chnum}[1]{%
  \ifcase#1\or
    一\or 二\or 三\or 四\or 五\or 六\or
    七\or 八\or 九\or 十\or 十一\or 十二%
  \else #1\fi}
%% \newcounter 已自动定义 \theexamsection，此处改为 \renewcommand 覆盖为中文数字
\renewcommand*{\theexamsection}{\exam@chnum{\value{examsection}}}

%% 加高行高的支柱（「得分」「评阅人」行，文字在行内垂直居中）
\newcommand*{\exam@strut}{\rule[-0.7em]{0pt}{1.45em}}

%% 评分表的行体：必须在表格环境之外先把「&」串与表头串展开好。
%% LaTeX 的表格钩子（\__tbl_hook_use_protected:nVVn）不允许在单元格内使用
%% \loop 这类前瞻式循环（会报 Forbidden control sequence found while scanning
%% use of \loop）。
\newcommand*{\exam@ampstr}{}
\newcommand*{\exam@headstr}{}
\newcommand*{\exam@buildrows}[1]{%
  \def\exam@ampstr{}%
  \def\exam@headstr{}%
  \exam@col=\z@
  \loop\ifnum\exam@col<#1\relax
    \advance\exam@col\@ne
    \ifnum\exam@col>\@ne
      \xdef\exam@ampstr{\exam@ampstr &}%
      \xdef\exam@headstr{\exam@headstr & \exam@chnum{\exam@col}}%
    \else
      \xdef\exam@headstr{\exam@chnum{\exam@col}}%
    \fi
  \repeat}

\newcommand{\examscoretable}[1][6]{%
  \begingroup
  \exam@buildrows{#1}%                        行体在表格外生成
  \edef\exam@clinend{\the\numexpr#1+1\relax}%  横线只画到「总分」列之前
  \begin{center}
  \setlength{\tabcolsep}{4pt}%
  \begin{tabularx}{\textwidth}{|C|*{#1}{C|}C|}
    \hline
    \heiti 题号 & \exam@headstr & \multirow{3}{*}{\heiti 总分} \\
    \cline{1-\exam@clinend}
    \heiti 得分\exam@strut & \exam@ampstr & \\
    \cline{1-\exam@clinend}
    \heiti 评阅人\exam@strut & \exam@ampstr & \\
    \hline
  \end{tabularx}
  \end{center}
  \endgroup}

%% ===========================================================================
%% 9. 大题与小题
%%    \examsection{<栏目标题>}      自动加「一、」「二、」…
%%    \begin{examquestions}[<题间距>] \examquestion 题干 … \end{examquestions}
%%    \begin{examproblem} 题干 \end{examproblem}   （无编号的单个大题）
%% ===========================================================================
\newcommand{\examsection}[1]{%
  \par
  \stepcounter{examsection}%
  \setcounter{examitem}{0}%
  \addvspace{\examsectionpreskip}%
  \noindent\hspace*{\examindent}{\heiti\theexamsection、#1}%
  \par
  \addvspace{\examsectionpostskip}}

%% 题目块：整体左缩进、首行不再额外缩进（换行与原卷一样与首行左端对齐）
\newcommand*{\exam@blockstart}[1]{%
  \par
  \setlength{\leftskip}{\examindent}%
  \setlength{\parindent}{0pt}%
  \setlength{\parskip}{#1}}
\newcommand*{\exam@blockend}{\par}

\newenvironment{examquestions}[1][\examitemsep]{%
  \exam@blockstart{#1}%
}{%
  \exam@blockend}

\newenvironment{examproblem}{%
  \exam@blockstart{0pt}%
}{%
  \exam@blockend}

%% 小题编号：1. 2. 3. …（每道大题内重新计数）
\newcommand{\examquestion}{%
  \par\stepcounter{examitem}\arabic{examitem}.\hspace{0.35em}\ignorespaces}
%% 可选短别名（若文档中未定义 \question）
\providecommand*{\question}{\examquestion}

%% ===========================================================================
%% 9b. 插图：\examfigure[<宽度>]{<图题>}{<图片文件>}
%%     默认宽度 0.6\textwidth；图片建议放在 figures/ 目录下。
%%     需要图文混排、多子图等复杂排版时，直接使用标准的
%%     \begin{figure}...\end{figure} 环境即可（graphicx 已加载）。
%% ===========================================================================
\newcommand{\examfigure}[3][0.6\textwidth]{%
  \par\addvspace{0.3em}%
  \refstepcounter{figure}%
  \begin{center}
    \includegraphics[width=#1]{#3}\\[0.3em]
    {\small\songti 图~\thefigure\quad #2}
  \end{center}%
  \addvspace{0.3em}\par}

%% ===========================================================================
%% 10. 左侧密封线（背景层，每页都有；坐标单位为 pt，原点在页面左下角）
%%     不需要密封线时，在导言区写 \examsidebarfalse 即可。
%% ===========================================================================
\newif\ifexamsidebar
\examsidebartrue
%% 考场纪律提示（宋体，竖排）
\newcommand*{\exam@warn}{%
  \songti 自觉遵守考场纪律\hspace{1.5em}如考试作弊\hspace{1.5em}此答卷无效}
%% 学号 / 姓名
\newcommand*{\exam@id}{%
  {\heiti 学号}\underline{\hspace{3.4cm}}\hspace{0.7em}%
  {\heiti 姓名}\underline{\hspace{3.4cm}}}
%% 密封线（点线 + 密、封、线，楷体）
\newcommand*{\exam@seal}{%
  \kaishu\makebox[516pt]{\dotfill 密\dotfill 封\dotfill 线\dotfill}}
%% 三个竖排元素：x = 基线位置，y = 文字起点（自下而上阅读）
\newcommand*{\exam@side}{%
  \setlength{\unitlength}{1pt}%
  \normalsize
  \ifexamsidebar
    \put(27.9,286.0){\rotatebox[origin=lb]{90}{\exam@warn}}%
    \put(53.1,283.5){\rotatebox[origin=lb]{90}{\exam@id}}%
    \put(76.0,145.5){\rotatebox[origin=lb]{90}{\exam@seal}}%
  \fi}
\AddToShipoutPictureBG{\exam@side}

\endinput
