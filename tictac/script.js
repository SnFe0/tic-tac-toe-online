const cells = document.querySelectorAll('.cell');
const restartBtn = document.getElementById('restart');
const botCheckbox = document.getElementById('bot-checkbox');

let currentPlayer = 'X';
let board = Array(9).fill('');
let gameActive = true;
let vsBot = botCheckbox.checked; // mode from checkbox
let botPlayer = 'O'; // бот играет за O

const winningCombinations = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
];

botCheckbox.addEventListener('change', () => {
    vsBot = botCheckbox.checked;
    if (vsBot && botPlayer === 'X') {
        setTimeout(botMove, 200);
    }
});

function handleCellClick(e) {
    const index = e.target.dataset.index;
    if (!gameActive || board[index] !== '') return;
    makeMove(index, currentPlayer);
    if (checkWin()) {
        endGame(`${currentPlayer} wins`);
        return;
    }
    if (board.every(cell => cell !== '')) {
        endGame('draw');
        return;
    }
    currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
    if (vsBot && currentPlayer === botPlayer) {
        setTimeout(botMove, 200);
    }
}

function makeMove(index, player) {
    board[index] = player;
    const cell = cells[index];
    cell.textContent = player;
    cell.classList.add(player === 'X' ? 'x' : 'o');
}

function endGame(message) {
    gameActive = false;
    highlightWinningCells();
    if (message === 'draw') {
        setTimeout(() => alert('Ничья'), 10);
    } else {
        const winner = message.split(' ')[0];
        setTimeout(() => alert(`Победил ${winner}!`), 10);
    }
}

function checkWin() {
    return winningCombinations.some(combo => {
        const [a, b, c] = combo;
        return board[a] && board[a] === board[b] && board[a] === board[c];
    });
}

function highlightWinningCells() {
    winningCombinations.forEach(combo => {
        const [a, b, c] = combo;
        if (board[a] && board[a] === board[b] && board[a] === board[c]) {
            cells[a].classList.add('winner');
            cells[b].classList.add('winner');
            cells[c].classList.add('winner');
        }
    });
}

function restartGame() {
    board = Array(9).fill('');
    currentPlayer = 'X';
    gameActive = true;
    // vsBot keeps checkbox state
    cells.forEach(cell => {
        cell.textContent = '';
        cell.classList.remove('winner', 'x', 'o');
    });
}

restartBtn.addEventListener('click', restartGame);

cells.forEach(cell => cell.addEventListener('click', handleCellClick));

// ---------- Bot logic ----------
function botMove() {
    if (!gameActive) return;
    // 1. Попытка выиграть
    const winIdx = findBestMove(botPlayer);
    if (winIdx !== -1) { makeMove(winIdx, botPlayer); finishBotTurn(); return; }
    // 2. Блокировать opponent
    const opponent = botPlayer === 'X' ? 'O' : 'X';
    const blockIdx = findBestMove(opponent);
    if (blockIdx !== -1) { makeMove(blockIdx, botPlayer); finishBotTurn(); return; }
    // 3. Центр
    if (board[4] === '') { makeMove(4, botPlayer); finishBotTurn(); return; }
    // 4. Углы
    const corners = [0,2,6,8].filter(i=>board[i]==='');
    if (corners.length) { const idx = corners[Math.floor(Math.random()*corners.length)]; makeMove(idx, botPlayer); finishBotTurn(); return; }
    // 5. Любая свободная ячейка
    const empty = board.map((v,i)=>v===''?i:null).filter(i=>i!==null);
    const idx = empty[Math.floor(Math.random()*empty.length)];
    makeMove(idx, botPlayer); finishBotTurn();
}

function finishBotTurn() {
    if (checkWin()) {
        endGame(`${botPlayer} wins`);
        return;
    }
    if (board.every(cell=>cell!=='')) {
        endGame('draw');
        return;
    }
    currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
}

function findBestMove(player) {
    for (const combo of winningCombinations) {
        const [a,b,c] = combo;
        const line = [board[a], board[b], board[c]];
        const playerCount = line.filter(v=>v===player).length;
        const emptyCount = line.filter(v=>v==='').length;
        if (playerCount===2 && emptyCount===1) {
            const emptyIdx = [a,b,c].find(i=>board[i]==='');
            return emptyIdx;
        }
    }
    return -1;
}
