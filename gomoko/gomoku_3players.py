# -*- coding: utf-8 -*-
import pickle

maxx = 10
maxy = 10

# ============ 玩家类 ============
class Player():
    """玩家类：管理"该谁下子"这一状态。三方轮流：黑→白→红→黑……
    turn 为当前回合编号（0黑 1白 2红），chess 为对应的棋子编号（1/2/3）。
    """
    def __init__(self):
        self.turn = 0          # 0 黑方(先手)，1 白方，2 红方
        self.chess = 1         # 当前棋子编号：1 黑，2 白，3 红
    def switch(self):
        """切换到下一家，三家循环后回到黑方。返回切换后的棋子编号。"""
        self.turn = (self.turn + 1) % 3
        self.chess = self.turn + 1
        return self.chess
    def name(self):
        """返回当前玩家名称，供提示信息复用。"""
        return ['黑方', '白方', '红方'][self.turn]
    def color(self, value):
        """把棋盘上的数字翻译成中文颜色，供打印棋盘时统一调用。"""
        return {0: '空', 1: '黑', 2: '白', 3: '红'}.get(value, '空')
# ============ 玩家类 ============

# ============ 棋盘类 ============
class Board():
    """棋盘类：封装棋盘数据以及与棋盘有关的全部独立算法。
    三方对局判胜规则不变：某一方自己的颜色连续五子即获胜。
    """
    def __init__(self, maxx, maxy):
        self.maxx = maxx
        self.maxy = maxy
        # 用列表推导式生成棋盘，保证每个格子独立
        self.check_board = [[0 for _ in range(self.maxy)] for _ in range(self.maxx)]
    # 判断坐标是否在棋盘范围内
    def inrange(self, xPoint, yPoint):
        return 0 <= xPoint < self.maxx and 0 <= yPoint < self.maxy
    # 落子：内部先做越界和占用检查
    def place(self, xPoint, yPoint, chess):
        if not self.inrange(xPoint, yPoint):
            return False
        if self.check_board[xPoint][yPoint] == 0:
            self.check_board[xPoint][yPoint] = chess
            return True
        return False
    # 棋盘是否下满（下满无人获胜则判平局）
    def isFull(self):
        for i in range(self.maxx):
            for j in range(self.maxy):
                if self.check_board[i][j] == 0:
                    return False
        return True
    # 判断棋局：沿一个方向统计连续同色子是否达到五子
    def check_five_row(self, xPoint, yPoint, xDir, yDir):
        count = 0
        t = self.check_board[xPoint][yPoint]
        # 先向正方向延伸（含落子点本身）
        x, y = xPoint, yPoint
        while self.inrange(x, y) and t == self.check_board[x][y]:
            count += 1
            x += xDir
            y += yDir
        # 再从落子点的前一格向反方向延伸（落子点只计一次）
        x, y = xPoint - xDir, yPoint - yDir
        while self.inrange(x, y) and t == self.check_board[x][y]:
            count += 1
            x -= xDir
            y -= yDir
        return count >= 5
    # 判断棋局：四个方向任意一个成立即获胜
    def isWin(self, xPoint, yPoint):
        return (self.check_five_row(xPoint, yPoint, 1, 0) or
                self.check_five_row(xPoint, yPoint, 0, 1) or
                self.check_five_row(xPoint, yPoint, 1, 1) or
                self.check_five_row(xPoint, yPoint, -1, 1))
    # 显示棋盘
    def print_check_board(self, player):
        print('       三人五子棋     ')
        for i in range(self.maxx):
            cells = ''.join('  ' + player.color(self.check_board[i][j]) + '  '
                            for j in range(self.maxy))
            line = ''.join([str(i), ' ', cells])
            print(line)
            print()
# ============ 棋盘类 ============

# ============ 文件类 ============
class FileSaveLoad():
    """文件类：只负责棋局的持久化（保存/读取），与游戏逻辑解耦。"""
    def __init__(self, maxx, maxy):
        # 注意：这里不要再次 self.check_board = []，
        # 否则会覆盖掉 Board 类已经建好的棋盘（多继承父类初始化顺序陷阱）
        self.maxx = maxx; self.maxy = maxy
        self.turn = 0             # 保存的下子方回合编号
    def save(self, check_board, turn):
        fpath = input('请输入保存路径：')
        file = open(fpath, 'wb')
        self.turn = turn
        pickle.dump(self, file)   # 直接序列化整个游戏对象，棋盘随 Game 一并保存
        file.close()
    def load(self):
        fpath = input('请输入棋盘路径：')
        import os
        if os.access(fpath, os.F_OK):
            file = open(fpath, 'rb')
            status = pickle.load(file)
            file.close()
            return status
        else:
            print('文件不存在！')
            return None
# ============ 文件类 ============

# ============ 游戏类 ============
class Game(Player, Board, FileSaveLoad):
    """游戏类：同时继承玩家类、棋盘类、文件类。
    三方轮流落子（黑→白→红），同色五子连珠获胜，棋盘下满判平局。
    """
    def __init__(self, maxx, maxy):
        # 分别显式初始化三个父类，保证各模块独立就绪
        Player.__init__(self)
        Board.__init__(self, maxx, maxy)
        FileSaveLoad.__init__(self, maxx, maxy)
    # 记录棋局
    def record(self):
        end_chess = False
        while not end_chess:
            t = input('请下子（x,y），现在由%s下子（S保存/L读取）：' % self.name()).split(',')
            if len(t) == 2:
                try:
                    x = int(t[0])
                    y = int(t[1])
                except ValueError:
                    print('输入有误，请重新输入！')
                    continue
                if self.place(x, y, self.chess):
                    # 判断棋局
                    if self.isWin(x, y):
                        print('%s赢！' % self.name())
                        end_chess = True
                    elif self.isFull():
                        print('棋盘下满，平局！')
                        end_chess = True
                    else:
                        self.switch()
                        self.print_check_board(self)
                else:
                    print('该位置已经有子或超出棋盘，请重下！')
            elif len(t) == 1:
                if t[0] == 'S':
                    self.save(self.check_board, self.turn)
                elif t[0] == 'L':
                    status = self.load()
                    if status is not None:
                        # 同步棋盘尺寸与回合方，避免与当前状态不一致
                        self.maxx = status.maxx
                        self.maxy = status.maxy
                        self.check_board = status.check_board
                        self.turn = status.turn
                        self.chess = self.turn + 1
                        self.print_check_board(self)
                else:
                    print('输入有误，请重新输入！')
            else:
                print('输入有误，请重新输入！')
# ============ 游戏类 ============

# 主程序
if __name__ == '__main__':
    game = Game(maxx, maxy)
    game.record()
# 主程序
