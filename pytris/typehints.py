"""
    Useful type hints because I don't want to make objects
"""
from typing import List, Tuple


BoolGrid = List[List[bool]]
Cell = Tuple[int, int]
PiecePos = List[Cell]
