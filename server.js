const http = require('http');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

const PORT = process.env.PORT || 8000;

// ---------- HTTP-сервер для отдачи статических файлов клиенту ----------
const server = http.createServer((req, res) => {
  // Отдаём файлы index.html, style.css и script.js из корневой папки проекта.
// Когда пользователь открывает сайт в браузере, именно этот код читает нужный файл
// с диска и отправляет его клиенту.
  let filePath = '.' + req.url;
  if (filePath === './') filePath = './index.html';
  const ext = path.extname(filePath).toLowerCase();
  const mime = {
    '.html': 'text/html',
    '.js':   'application/javascript',
    '.css':  'text/css',
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.svg':  'image/svg+xml'
  }[ext] || 'application/octet-stream';
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      return res.end('Not found');
    }
    res.writeHead(200, { 'Content-Type': mime });
    res.end(data);
  });
});

const wss = new WebSocket.Server({ server });

// ---------- Хранилище комнат в оперативной памяти ----------
const rooms = new Map();
// rooms — это Map, где:
//   ключ   = идентификатор комнаты (roomId),
//   значение = объект с состоянием комнаты:
//     board    — массив из 9 клеток игрового поля,
//     turn     — символ игрока, который должен ходить ('X' или 'O'),
//     players  — Set с WebSocket‑подключениями игроков,
//     password — пароль комнаты или null, если пароль не установлен.

// Сбрасывает состояние комнаты после окончания партии.
// Очищает игровое поле и устанавливает первый ход за символом X.
function resetRoom(room) {
  room.board = Array(9).fill('');
  room.turn = 'X';
}
// Проверяет, собрал ли указанный символ выигрышную комбинацию.
// Возвращает true, если игрок занял три клетки подряд.
function checkWin(board, sym) {
  const combos = [
    [0,1,2],[3,4,5],[6,7,8],
    [0,3,6],[1,4,7],[2,5,8],
    [0,4,8],[2,4,6]
  ];
  return combos.some(c => c.every(i => board[i] === sym));
}
// Отправляет одно и то же сообщение всем игрокам, находящимся в указанной комнате.
function broadcast(room, msg) {
  const data = JSON.stringify(msg);
  for (const p of room.players) p.send(data);
}
// Формирует и отправляет клиенту список доступных комнат.
function sendRoomList(ws) {
  const list = [];
  for (const [id, r] of rooms) {
    list.push({ roomId:id, playersCount:r.players.size, locked:!!r.password });
  }
  ws.send(JSON.stringify({ type:'roomList', rooms:list }));
}
// Формирует список комнат и рассылает его всем подключённым клиентам.
function broadcastRoomList() {
  const list = [];
  for (const [id, r] of rooms) {
    list.push({ roomId:id, playersCount:r.players.size, locked:!!r.password });
  }
  const payload = JSON.stringify({ type:'roomList', rooms:list });
  wss.clients.forEach(c => { if (c.readyState===WebSocket.OPEN) c.send(payload); });
}

function handlePlayerLeave(ws) {
  const room = rooms.get(ws.roomId);
  if (!room) return;

  room.players.delete(ws);
  if (ws.roomHandler) ws.off('message', ws.roomHandler);

  const oldId = ws.roomId;
  ws.roomId = null;
  ws.symbol = null;

  if (room.players.size === 0) {
    // Комната пустая — удаляем
    rooms.delete(oldId);
  } else {
    // Остался один игрок — сбрасываем доску и уведомляем
    resetRoom(room);
    const remaining = Array.from(room.players)[0];
    remaining.send(JSON.stringify({ type: 'opponentLeft' }));
  }

  broadcastRoomList();
}

wss.on('connection', ws => {
  // ---------- Обработка новых WebSocket-подключений ----------
// После подключения клиент должен первым сообщением либо запросить список комнат ('roomList'),
// либо сразу попытаться войти в комнату ('join').
  const initialHandler = raw => {
    let msg;
    try { msg = JSON.parse(raw); } catch (_) { return; }
    if (msg.type === 'roomList') {
      sendRoomList(ws);
      return;
    }
    if (msg.type === 'join' && typeof msg.roomId === 'string') {
      ws.removeListener('message', ws.initialHandler);
      attachRoomHandlers(ws, msg.roomId, msg.password);
      return;
    }
    ws.send(JSON.stringify({ type:'error', msg:'Invalid request' }));
  };
  ws.initialHandler = initialHandler;
  ws.on('message', ws.initialHandler);
});

function attachRoomHandlers(ws, roomId, password) {
  // Ищем комнату по её идентификатору.
// Если такой комнаты ещё нет, создаём новую.
  let room = rooms.get(roomId);
  if (!room) {
    room = { board:Array(9).fill(''), turn:'X', players:new Set(), password: password || null };
    rooms.set(roomId, room);
  }
  // Если для комнаты установлен пароль, проверяем, что клиент указал правильный пароль.
  if (room.password && password !== room.password) {
    ws.send(JSON.stringify({ type:'error', msg:'Invalid password' }));
    return ws.close();
  }
  if (room.players.size >= 2) {
    ws.send(JSON.stringify({ type:'error', msg:'Room full' }));
    return ws.close();
  }

  // Добавляем игрока в комнату и сохраняем его символ и идентификатор комнаты в объекте WebSocket.
  room.players.add(ws);
  ws.roomId = roomId;
  ws.symbol = room.players.size === 1 ? 'X' : 'O';

  // Сообщаем подключившемуся игроку, что он успешно вошёл в комнату.
  ws.send(JSON.stringify({ type:'joined', roomId, symbol: ws.symbol }));
  if (room.players.size === 1) ws.send(JSON.stringify({ type:'wait' }));
  broadcast(room, { type:'state', board:room.board, turn:room.turn });

  // Когда в комнате становится два игрока, случайным образом определяем, кто будет играть крестиками, а кто ноликами, и отправляем эту информацию обоим игрокам.
  if (room.players.size === 2) {
    const arr = Array.from(room.players);
    const first = arr[0], second = arr[1];
    const assignXtoFirst = Math.random() < 0.5;
    first.symbol = assignXtoFirst ? 'X' : 'O';
    second.symbol = assignXtoFirst ? 'O' : 'X';
    room.turn = 'X';
    first.send(JSON.stringify({ type:'joined', roomId, symbol:first.symbol }));
    second.send(JSON.stringify({ type:'joined', roomId, symbol:second.symbol }));
    
  }
  broadcastRoomList();

  // ---------- Обработчик сообщений внутри комнаты ----------
  const roomHandler = raw => {
    let data;
    try { data = JSON.parse(raw); } catch (_) { return; }
    // Обработка хода игрока.
    if (data.type === 'move') {
      if (ws.symbol !== room.turn) return;
      const idx = data.index;
      if (typeof idx !== 'number' || idx < 0 || idx > 8) return;
      if (room.board[idx]) return;
      room.board[idx] = ws.symbol;
      if (checkWin(room.board, ws.symbol)) {
        broadcast(room, { type:'end', board:room.board, winner:ws.symbol });
        resetRoom(room);
        broadcastRoomList();
        return;
      }
      if (room.board.every(c=>c)) {
        broadcast(room, { type:'end', board:room.board, draw:true });
        resetRoom(room);
        broadcastRoomList();
        return;
      }
      room.turn = room.turn === 'X' ? 'O' : 'X';
      broadcast(room, { type:'state', board:room.board, turn:room.turn });
    }
    // Перезапуск партии.
// Поле очищается, а символы X и O заново распределяются случайным образом.
    if (data.type === 'restart') {
      resetRoom(room);
      const arr = Array.from(room.players);
      if (arr.length === 2) {
        const [first, second] = arr;
        const assignXtoFirst = Math.random() < 0.5;
        first.symbol = assignXtoFirst ? 'X' : 'O';
        second.symbol = assignXtoFirst ? 'O' : 'X';
        first.send(JSON.stringify({ type:'joined', roomId, symbol:first.symbol }));
        second.send(JSON.stringify({ type:'joined', roomId, symbol:second.symbol }));
        
      }
      broadcast(room, { type:'state', board:room.board, turn:room.turn });
    }
    // Игрок покидает комнату.
// WebSocket‑соединение не закрывается, чтобы клиент мог сразу создать новую комнату или присоединиться к другой.
    if (data.type === 'leave') {
	  ws.send(JSON.stringify({type:'left'}));
	  if (ws.initialHandler) ws.on('message', ws.initialHandler);
	  handlePlayerLeave(ws);
    }
    // Клиент запросил актуальный список доступных комнат.
    if (data.type === 'roomList') sendRoomList(ws);
  };
  ws.roomHandler = roomHandler;
  ws.on('message', ws.roomHandler);

  // ---------- Очистка данных при полном закрытии соединения ----------
  ws.on('close', () => {
	handlePlayerLeave(ws);
  });
}

// ---------- Запуск HTTP- и WebSocket-сервера ----------
server.listen(PORT, () => {
  console.log(`🚀 Server listening on http://0.0.0.0:${PORT}`);
  console.log(`   WS endpoint: ws://0.0.0.0:${PORT}`);
});
