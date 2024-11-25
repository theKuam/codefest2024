import logging

class MapMatrix:
    def __init__(self, matrix):
        self.matrix = matrix
        self.rows = len(matrix) if matrix else 0
        self.cols = len(matrix[0]) if matrix and matrix[0] else 0

    def get(self, row: int, col: int) -> int:
        """Get the value at the specified position.
        
        Args:
            row (int): Row index
            col (int): Column index
            
        Returns:
            int: Value at the position, or -1 if position is invalid
        """
        if self.is_valid_position(row, col):
            return self.matrix[row][col]
        return -1

    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if the position is valid within the matrix bounds.
        
        Args:
            row (int): Row index
            col (int): Column index
            
        Returns:
            bool: True if position is valid, False otherwise
        """
        return 0 <= row < self.rows and 0 <= col < self.cols

    def __getitem__(self, position: tuple) -> int:
        """Allow accessing values using array notation: matrix[row, col]
        
        Args:
            position (tuple): (row, col) tuple
            
        Returns:
            int: Value at the position
        """
        row, col = position
        return self.get(row, col)
