from hashlib import md5

from flask import render_template, redirect

from manager import web_app
from manager.maze import maze
from util import singleton


@singleton
class MazeWeb:
    WIDTH, HEIGHT = 10, 10
    OBJECT = None

    def __init__(self):
        self.code, self.maze_board, self.maze_path = maze.create_maze(MazeWeb.WIDTH, MazeWeb.HEIGHT)
        self.success_code = ''

    @staticmethod
    @web_app.route('/maze')
    def index():
        return render_template('maze.html')

    @staticmethod
    @web_app.route('/maze/get')
    def get_maze():
        return {
            'width': MazeWeb.WIDTH, 'height': MazeWeb.HEIGHT,
            'board': MazeWeb.OBJECT.maze_board.listify(),
            'code': MazeWeb.OBJECT.code
        }

    @staticmethod
    @web_app.route('/maze/update')
    def update_maze():
        MazeWeb.OBJECT.code, MazeWeb.OBJECT.maze_board, MazeWeb.OBJECT.maze_path = maze.create_maze(MazeWeb.WIDTH, MazeWeb.HEIGHT)
        MazeWeb.OBJECT.success_code = md5((str(MazeWeb.OBJECT.code) + MazeWeb.OBJECT.maze_path.navigate()).encode()).hexdigest()
        return redirect('/maze')

    @staticmethod
    @web_app.route('/maze/get-code')
    def get_maze_code():
        return {'code': MazeWeb.OBJECT.code}


MazeWeb.OBJECT = MazeWeb()
MazeWeb.OBJECT.update_maze()
