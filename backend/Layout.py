from enum import Enum

class H_align(Enum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'
    SPLIT = 'split'

    def __str__(self):
        return self.value


class V_align(Enum):
    TOP = 'top'
    BOTTOM = 'bottom'

    def __str__(self):
        return self.value