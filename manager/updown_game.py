from random import randint


class UpdownGame:
    """Updown 게임 객체입니다."""

    SAY_DOWN = 1
    SAY_UP = -1
    SAY_CORRECT = 0

    def __init__(self, range_: int):
        self.range = range_
        self.number = randint(1, self.range)
        self.tries = 0

    def guess(self, guessing_number: int) -> int:
        """
        숫자를 예상합니다.
        :param guessing_number: 예상할 숫자
        :return: 이 숫자가 게임의 숫자보다 큰지 작은지 같은지
        """
        self.tries += 1
        if guessing_number > self.number:
            return UpdownGame.SAY_DOWN
        elif guessing_number < self.number:
            return UpdownGame.SAY_UP
        else:
            return UpdownGame.SAY_CORRECT

    @staticmethod
    def get_receive(tries: int) -> float:
        return max((54 / tries - 4) / 5, 0)
