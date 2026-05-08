const http = require('http');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

const PORT = process.env.PORT || 8000;

// ---------- HTTP server to serve static files ----------
const server = http.createServer((req, res) => {
  // Serve index.html, style.css, script.js from the project root
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

// ---------- In‑memory rooms ----------
const rooms = new Map(); // roomId -> {board, turn, players:Set, password}

function resetRoom(room) {
  room.board = Array(9).fill('');
  room.turn = 'X';
}
function checkWin(board, sym) {
  const combos = [
    [0,1,2],[3,4,5],[6,7,8],
    [0,3,6],[1,4,7],[2,5,8],
    [0,4,8],[2,4,6]
  ];
  return combos.some(c => c.every(i => board[i] === sym));
}
function broadcast(room, msg) {
  const data = JSON.stringify(msg);
  for (const p of room.players) p.send(data);
}
function sendRoomList(ws) {
  const list = [];
  for (const [id, r] of rooms) {
    list.push({ roomId:id, playersCount:r.players.size, locked:!!r.password });
  }
  ws.send(JSON.stringify({ type:'roomList', rooms:list }));
}
function broadcastRoomList() {
  const list = [];
  for (const [id, r] of rooms) {
    list.push({ roomId:id, playersCount:r.players.size, locked:!!r.password });
  }
  const payload = JSON.stringify({ type:'roomList', rooms:list });
  wss.clients.forEach(c => { if (c.readyState===WebSocket.OPEN) c.send(payload); });
}

wss.on('connection', ws => {
  // ---------- Initial handler (roomList / join) ----------
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
  // Find or create room
  let room = rooms.get(roomId);
  if (!room) {
    room = { board:Array(9).fill(''), turn:'X', players:new Set(), password: password || null };
    rooms.set(roomId, room);
  }
  // Password check
  if (room.password && password !== room.password) {
    ws.send(JSON.stringify({ type:'error', msg:'Invalid password' }));
    return ws.close();
  }
  if (room.players.size >= 2) {
    ws.send(JSON.stringify({ type:'error', msg:'Room full' }));
    return ws.close();
  }

  // Register player
  room.players.add(ws);
  ws.roomId = roomId;
  ws.symbol = room.players.size === 1 ? 'X' : 'O';

  // Notify newcomer
  ws.send(JSON.stringify({ type:'joined', roomId, symbol: ws.symbol }));
  if (room.players.size === 1) ws.send(JSON.stringify({ type:'wait' }));
  broadcast(room, { type:'state', board:room.board, turn:room.turn });

  // If second player joins, randomise symbols & notify both
  if (room.players.size === 2) {
    const arr = Array.from(room.players);
    const first = arr[0], second = arr[1];
    const assignXtoFirst = Math.random() < 0.5;
    first.symbol = assignXtoFirst ? 'X' : 'O';
    second.symbol = assignXtoFirst ? 'O' : 'X';
    room.turn = 'X';
    first.send(JSON.stringify({ type:'joined', roomId, symbol:first.symbol }));
    second.send(JSON.stringify({ type:'joined', roomId, symbol:second.symbol }));
    broadcast(room, { type:'opponentJoined' });
  }
  broadcastRoomList();

  // ---------- Room‑specific message handler ----------
  const roomHandler = raw => {
    let data;
    try { data = JSON.parse(raw); } catch (_) { return; }
    // Move
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
    // Restart – fresh game with new random symbols
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
        broadcast(room, { type:'opponentJoined' });
      }
      broadcast(room, { type:'state', board:room.board, turn:room.turn });
    }
    // Leave – detach only room handler, keep socket usable
    if (data.type === 'leave') {
      const currentRoom = rooms.get(ws.roomId);
      if (currentRoom) {
        currentRoom.players.delete(ws);
        if (ws.roomHandler) ws.off('message', ws.roomHandler);
		if (ws.initialHandler) {
			ws.on('message', ws.initialHandler);
		}
        const oldId = ws.roomId;
        ws.roomId = null;
        ws.symbol = null;
        ws.send(JSON.stringify({ type:'left' }));
        if (currentRoom.players.size > 0) {
          broadcast(currentRoom, { type:'info', msg:'Соперник вышел' });
        } else {
          rooms.delete(oldId);
        }
        broadcastRoomList();
      }
    }
    // Request fresh room list
    if (data.type === 'roomList') sendRoomList(ws);
  };
  ws.roomHandler = roomHandler;
  ws.on('message', ws.roomHandler);

  // ---------- Cleanup on disconnect ----------
  ws.on('close', () => {
    const r = rooms.get(ws.roomId);
    if (!r) return;
    r.players.delete(ws);
    if (r.players.size === 0) {
      rooms.delete(ws.roomId);
    } else {
      broadcast(r, { type:'info', msg:'Соперник вышел' });
    }
    broadcastRoomList();
  });
}

// ---------- Start server ----------
server.listen(PORT, () => {
  console.log(`🚀 Server listening on http://0.0.0.0:${PORT}`);
  console.log(`   WS endpoint: ws://0.0.0.0:${PORT}`);
});
