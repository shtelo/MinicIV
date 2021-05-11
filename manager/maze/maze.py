from random import choice
from time import time
from typing import Optional, Tuple

from PIL import Image, ImageDraw

PADDING = 20


class BoardLine(list):
    def __repr__(self):
        return '-'.join(map(repr, self))

    def listify(self):
        return [repr(index) for index in self]


class Board(list):
    def __repr__(self):
        return ' '.join(map(repr, self))

    def listify(self):
        return [line.listify() for line in self]


class History(list):
    def navigate(self):
        return ' - '.join(str(cell) for cell in self)

    def copy(self) -> 'History':
        result = History()
        for place in self:
            result.append(place)
        return result

    def listify(self):
        return [str(index) for index in self]


class Cell:
    SIZE = 40

    LEFT = 'LEFT'
    RIGHT = 'RIGHT'
    TOP = 'TOP'
    BOTTOM = 'BOTTOM'

    @staticmethod
    def get_neighbors(cell, board: Board) -> list:
        height, width = len(board), len(board[0])

        result = list()
        if (x := cell.x - 1) >= 0 and not (this := board[cell.y][x]).visited:
            result.append((this, Cell.LEFT))
        if (x := cell.x + 1) < width and not (this := board[cell.y][x]).visited:
            result.append((this, Cell.RIGHT))
        if (y := cell.y - 1) >= 0 and not (this := board[y][cell.x]).visited:
            result.append((this, Cell.TOP))
        if (y := cell.y + 1) < height and not (this := board[y][cell.x]).visited:
            result.append((this, Cell.BOTTOM))
        return result

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

        self.visited = False

        self.left_border = True
        self.right_border = True
        self.top_border = True
        self.bottom_border = True

    def visit(self):
        self.visited = True
        return self

    def draw(self, image):
        x = self.x * Cell.SIZE + PADDING
        y = self.y * Cell.SIZE + PADDING

        image_draw = ImageDraw.Draw(image)
        if self.left_border:
            image_draw.line((x, y, x, y + Cell.SIZE))
        if self.right_border:
            image_draw.line((x + Cell.SIZE, y, x + Cell.SIZE, y + Cell.SIZE))
        if self.top_border:
            image_draw.line((x, y, x + Cell.SIZE, y))
        if self.bottom_border:
            image_draw.line((x, y + Cell.SIZE, x + Cell.SIZE, y + Cell.SIZE))

    def __repr__(self):
        borders = ''
        borders += '1' if self.left_border else '0'
        borders += '1' if self.right_border else '0'
        borders += '1' if self.top_border else '0'
        borders += '1' if self.bottom_border else '0'
        return f'{str(self)}:{borders}'

    def __str__(self):
        return f'{self.x}.{self.y}'


def create_maze(width: int, height: int) -> Tuple[int, Board, History]:
    board = Board()

    history = History()
    path: Optional[History] = None

    for j in range(height):
        line = BoardLine()
        for i in range(width):
            line.append(Cell(i, j))
        board.append(line)
    current = board[0][0].visit()

    while True:
        if neighbors := Cell.get_neighbors(current, board):
            history.append(current)
            next_, direction = choice(neighbors)

            if next_.x == width - 1 and next_.y == height - 1:
                path = history.copy()

            if direction == Cell.LEFT:
                current.left_border = False
                next_.right_border = False
            elif direction == Cell.RIGHT:
                current.right_border = False
                next_.left_border = False
            elif direction == Cell.TOP:
                current.top_border = False
                next_.bottom_border = False
            elif direction == Cell.BOTTOM:
                current.bottom_border = False
                next_.top_border = False

            current = next_.visit()
        elif history:
            current = history.pop(-1)
        else:
            break

    # with Image.new('RGB', (width * Cell.SIZE + 2 * PADDING, height * Cell.SIZE + 2 * PADDING)) as image:
    #     for i in range(width):
    #         for j in range(height):
    #             board[j][i].draw(image)
    #     image.save('out.png')

    return int(time()), board, path


if __name__ == '__main__':
    code, board_, path_ = create_maze(4, 4)
    print(code, repr(board_), repr(path_), sep='\n')
