"""
Handle puzzle creation and utils.
"""

import copy
import math
import random

PUZZLE_LABEL_CORRECT = [1, 0]
PUZZLE_LABEL_INCORRECT = [0, 1]

PUZZLE_CORRUPTION_MAX = 10

PUZZLE_NOTE_CORRRECT = 'solved'

def generatePuzzle(dimension, x, y, labels, exampleChooser):
    """
    Generate a valid puzzle and return the visual (pixel) and label representation for it.
    """

    puzzleImages = None
    puzzleCellLabels = None

    while (puzzleImages is None):
        puzzleImages, puzzleCellLabels, corruptCellLabels = _generatePuzzle(dimension, x, y, labels, exampleChooser)

    return puzzleImages, puzzleCellLabels, corruptCellLabels

def _generatePuzzle(dimension, x, y, labels, exampleChooser):
    """
    Generate a puzzle, but return (None, None) on failure.
    Failure can be encountered because this does not backtrack.
    Instead, just call again until you get a valid puzzle.
    """

    puzzleImages = [[None] * dimension for i in range(dimension)]
    puzzleCellLabels = [[None] * dimension for i in range(dimension)]
    corruptCellLabels = [[None] * dimension for i in range(dimension)]

    labels = ['mnist_0', 'mnist_1', 'mnist_2', 'mnist_3', 'mnist_4']
    for row in range(dimension):
        for col in range(dimension):
            puzzleCellLabels[row][col] = labels[x[row * 4 + col]]
            corruptCellLabels[row][col] = labels[y[row * 4 + col]]

    # Once we have a complete puzzle, choose the examples.
    for row in range(dimension):
        for col in range(dimension):
            puzzleImages[row][col] = exampleChooser.takeExample(puzzleCellLabels[row][col])

    return puzzleImages, puzzleCellLabels, corruptCellLabels

def checkPuzzle(puzzleCellLabels):
    """
    Return true if the labels create a correct puzzle.
    Note that we are checking for duplicates, not deficiencies.
    """

    dimension = len(puzzleCellLabels)

    # {row/col: {value, ...}, ...}
    seenInRow = {}
    seenInCol = {}

    # {blockRowId: {blockColId: {value, ...}, ...}, ...}
    seenInBlock = {}

    size = dimension
    blockSize = int(math.sqrt(dimension))

    # Pre-load the seen data structures.
    for i in range(size):
        seenInRow[i] = set()
        seenInCol[i] = set()

    for blockRowID in range(blockSize):
        seenInBlock[blockRowID] = {}

        for blockColID in range(blockSize):
            seenInBlock[blockRowID][blockColID] = set()

    # Load the seen data structures.
    for row in range(size):
        for col in range(size):
            label = puzzleCellLabels[row][col]

            seenInRow[row].add(label)
            seenInCol[col].add(label)
            seenInBlock[row // blockSize][col // blockSize].add(label)

    # Check for valid rows/cols.
    for i in range(size):
        if (len(seenInRow[i]) != size):
            return False

        if (len(seenInCol[i]) != size):
            return False

    # Check for valid grids.
    for blockRowID in range(blockSize):
        for blockColID in range(blockSize):
            if (len(seenInBlock[blockRowID][blockColID]) != size):
                return False

    return True

def corruptPuzzle(dimension, labels, exampleChooser, originalImages, originalCellLabels, corruptionChance):
    """
    Take in a valid puzzle and return a copy that is corrupted.
    """

    corruptCellLabels = None
    while (corruptCellLabels is None or checkPuzzle(corruptCellLabels)):
        corruptImages = copy.deepcopy(originalImages)
        corruptCellLabels = copy.deepcopy(originalCellLabels)

        corruptImages, corruptCellLabels, corruptNote = removePuzzleByReplacement(dimension, labels, exampleChooser, corruptImages, corruptCellLabels, corruptionChance)

    return corruptImages, originalCellLabels, corruptNote, corruptCellLabels

def corruptPuzzleBySwap(dimension, labels, exampleChooser, corruptImages, corruptCellLabels, corruptionChance):
    """
    Corrupt a puzzle by swaping cells from the same puzzle.
    """

    count = 0
    seenLocations = set()
    maxSwaps = min(PUZZLE_CORRUPTION_MAX, dimension ** 2 // 2)

    while ((count < maxSwaps) and (count == 0 or random.random() < corruptionChance)):
        count += 1

        row1, col1 = randCell(dimension, seenLocations)
        seenLocations.add((row1, col1))

        row2, col2 = randCell(dimension, seenLocations)
        seenLocations.add((row2, col2))

        corruptImages[row1][col1], corruptImages[row2][col2] = corruptImages[row2][col2], corruptImages[row1][col1]
        corruptCellLabels[row1][col1], corruptCellLabels[row2][col2] = corruptCellLabels[row2][col2], corruptCellLabels[row1][col1]

    return corruptImages, corruptCellLabels, "swap(%d)" % (count)

def corruptPuzzleByReplacement(dimension, labels, exampleChooser, corruptImages, corruptCellLabels, corruptionChance):
    """
    Corrupt a puzzle by replacing single cells at a time.
    """

    count = 0
    seenLocations = set()
    maxReplacements = min(PUZZLE_CORRUPTION_MAX, dimension ** 2)

    while ((count < maxReplacements) and (count == 0 or random.random() < corruptionChance)):
        count += 1

        corruptRow, corruptCol = randCell(dimension, seenLocations)
        seenLocations.add((corruptRow, corruptCol))

        oldLabel = corruptCellLabels[corruptRow][corruptCol]
        newLabel = oldLabel
        while (oldLabel == newLabel):
            newLabel = random.choice(labels)

        corruptImages[corruptRow][corruptCol] = exampleChooser.getExample(newLabel)
        corruptCellLabels[corruptRow][corruptCol] = newLabel

    return corruptImages, corruptCellLabels, "replace(%d)" % (count)

def removePuzzleByReplacement(dimension, labels, exampleChooser, corruptImages, corruptCellLabels, corruptionChance):
    """
    Corrupt a puzzle by removing single cell at a time.
    """

    count = 0
    seenLocations = set()
    maxReplacements = min(PUZZLE_CORRUPTION_MAX, dimension ** 2)

    while ((count < maxReplacements) and (count == 0 or random.random() < corruptionChance)):
        count += 1

        corruptRow, corruptCol = randCell(dimension, seenLocations)
        seenLocations.add((corruptRow, corruptCol))

        oldLabel = corruptCellLabels[corruptRow][corruptCol]
        newLabel = 'mnist_4'
        # while (oldLabel == newLabel): newLabel = random.choice(labels)

        corruptImages[corruptRow][corruptCol] = exampleChooser.getExample(newLabel)
        corruptCellLabels[corruptRow][corruptCol] = newLabel

    return corruptImages, corruptCellLabels, "replace(%d)" % (count)

def randCell(dimension, skipLocations = set()):
    row = None
    col = None

    while (row is None or (row, col) in skipLocations):
        row = random.randrange(0, dimension)
        col = random.randrange(0, dimension)

    return row, col
