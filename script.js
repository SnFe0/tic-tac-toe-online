// ------------------- Онлайн‑мультиплеер (WebSocket) -------------------
const cells = document.querySelectorAll('.cell');
const resultOverlay = document.getElementById('result-overlay');
function showWaiting(){
  resultOverlay.innerHTML = '<h2>Ожидаем соперника...</h2>';
  resultOverlay.classList.remove('hidden');
  resultOverlay.classList.add('show');
}
function hideWaiting(){
  setTimeout(()=>{
    resultOverlay.classList.remove('show');
    resultOverlay.classList.add('hidden');
  }, 300);
}

function showResult(text) {
  resultOverlay.innerHTML = `<h2>${text}</h2>`;
  resultOverlay.classList.remove('hidden');
  resultOverlay.classList.add('show');
  setTimeout(() => resultOverlay.classList.remove('show'), 2500);
}


const playerInfo = document.getElementById('player-info');
const turnInfo   = document.getElementById('turn-info');
const lobbyDiv   = document.getElementById('lobby');
const createBtn  = document.getElementById('create-room');
const restartBtn = document.getElementById('restart');
const roomListUl = document.getElementById('room-list');
const gameDiv    = document.getElementById('game');

// WebSocket подключение к текущему хосту
const socket = new WebSocket(`ws://${location.host}`);
let mySymbol = null;          // X или O, получаем от сервера
let roomId = null;            // текущая комната
let board = Array(9).fill('');
let gameActive = true;
let hasJoined = false;

const winningCombinations = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6]
];

// ---------- UI helpers ----------
function showLobby() {
  lobbyDiv.style.display = 'block';
  gameDiv.style.display = 'none';
  restartBtn.style.display = 'none';
  playerInfo.textContent = '';
  turnInfo.textContent = '';
}
function showGame() {
  // hide restart button during active game; it will be shown only when the game ends
  restartBtn.style.display = 'none';
  lobbyDiv.style.display = 'none';
  gameDiv.style.display = 'grid';

}

// ---------- Modal handling ----------
const modal = document.getElementById('room-modal');
const modalTitle = document.getElementById('modal-title');
const roomNameInput = document.getElementById('room-name');
const roomPassInput = document.getElementById('room-pass');
const modalCancel = document.getElementById('modal-cancel');
const modalSubmit = document.getElementById('modal-submit');
let modalMode = 'create'; // 'create' or 'join'
let pendingRoomId = null; // id of room we want to join (when mode='join')

function openModal(mode, roomId = null, locked = false) {
  console.log('openModal', mode, roomId, locked);
  modalMode = mode;
  modalMode = mode;
  pendingRoomId = roomId;
  modal.classList.add('show');
  if (mode === 'create') {
    modalTitle.textContent = 'Создать комнату';
    roomNameInput.disabled = false;
    roomNameInput.value = '';
    roomPassInput.value = '';
    roomPassInput.placeholder = 'Пароль (необязательно)';
  } else {
    modalTitle.textContent = 'Подключиться к комнате';
    roomNameInput.disabled = true;
    roomNameInput.value = roomId;
    roomPassInput.value = '';
    roomPassInput.placeholder = locked ? 'Введите пароль' : 'Пароль (необязательно)';
  }
}
function closeModal() { modal.classList.remove('show'); }
modalCancel.addEventListener('click', closeModal);
modalSubmit.addEventListener('click', () => {
  const name = roomNameInput.value.trim();
  const pwd = roomPassInput.value;
  if (modalMode === 'create') {
    const id = name || 'room-' + Math.random().toString(36).substr(2, 5);
    console.log('Создаём комнату', id, 'пароль:', pwd);
    joinRoomWithPassword(id, pwd);
  } else {
    joinRoomWithPassword(pendingRoomId, pwd);
  }
  closeModal();
});

// ---------- Room list rendering ----------
function renderRoomList(rooms) {
  // rooms – массив объектов {roomId, playersCount, locked}
  roomListUl.innerHTML = '';
  rooms.forEach(r => {
    const li = document.createElement('li');
    li.textContent = `${r.roomId} (${r.playersCount} игрок${r.playersCount===1?'':'а'})`;
    if (r.locked) {
      const lockSpan = document.createElement('span');
      lockSpan.textContent = ' 🔒';
      li.appendChild(lockSpan);
    }
    li.dataset.locked = r.locked; // храним статус
    li.style.cursor = 'pointer';
    li.addEventListener('click', () => {
      const locked = li.dataset.locked === 'true';
      if (locked) {
        openModal('join', r.roomId, true);
      } else {
        // без пароля сразу соединяемся
        joinRoomWithPassword(r.roomId, '');
      }
    });
    roomListUl.appendChild(li);
  });
}

// ---------- Room actions ----------
function createRoom() { console.log('createRoom called'); openModal('create'); }
function joinRoomWithPassword(id, pwd) {
  console.log('Пытаемся присоединиться к комнате', id);
  roomId = id;
  socket.send(JSON.stringify({type: 'join', roomId, password: pwd}));
}

// ---------- WebSocket handling ----------
socket.addEventListener('open', () => {
  console.log('WebSocket открыт');
  socket.send(JSON.stringify({type: 'roomList'}));
});

socket.addEventListener('message', e => {
  const data = JSON.parse(e.data);
  switch (data.type) {
    case 'joined':
      if (!hasJoined) {
        // first time we receive join info
        hasJoined = true;
        mySymbol = data.symbol;
        playerInfo.textContent = `Вы ходите ${mySymbol === 'X' ? 'крестиком' : 'ноликом'}`;
        showGame();
      } else {
        // second join notification – both players now know their symbols
        mySymbol = data.symbol;
        const msg = mySymbol === 'X' ? 'Вы ходите крестиком' : 'Вы ходите ноликом';
        showResult(msg);
        // ensure game view is visible
        showGame();
      }
      break;
    case 'state':
      board = data.board;
      renderBoard();
      restartBtn.style.display = 'none';
      turnInfo.textContent = `Сейчас ходит ${data.turn === 'X' ? 'крестик' : 'нолик'}`;
      break;
    case 'end':
      board = data.board;
      renderBoard();
      if (data.winner) showResult(`Победил ${data.winner}!`);
      else if (data.draw) showResult('Ничья');
      restartBtn.style.display = 'inline-block';
      break;
    case 'wait':
      showWaiting();
      break;
    case 'opponentJoined':
      hideWaiting();
      break;
    case 'roomList':
      renderRoomList(data.rooms);
      break;
    case 'error':
      alert('Ошибка: ' + data.msg);
      break;
    case 'info':
      console.log(data.msg);
      break;
  }
});

function renderBoard() {
  board.forEach((sym, i) => {
    const cell = cells[i];
    cell.textContent = sym || '';
    cell.className = 'cell';
    if (sym === 'X') cell.classList.add('x');
    if (sym === 'O') cell.classList.add('o');
  });
}

function handleCellClick(e) {
  const idx = Number(e.target.dataset.index);
  if (!gameActive || board[idx]) return;
  socket.send(JSON.stringify({type: 'move', roomId, index: idx}));
}

restartBtn.addEventListener('click', () => {
  socket.send(JSON.stringify({type: 'restart', roomId}));
  // hide button again until next game ends
  restartBtn.style.display = 'none';
});

createBtn.addEventListener('click', () => openModal('create'));

cells.forEach(cell => cell.addEventListener('click', handleCellClick));

// Placeholder helpers – not used
function checkWin() {}
function highlightWinningCells() {}
