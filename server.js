// server.js – unified Express + WebSocket server for Tic‑Tac‑Toe lobby
// ---------------------------------------------------------------
// Run: npm i express ws   then   node server.js
// Serves static files (index.html, style.css, script.js) on the same port
// and hosts the WebSocket lobby/game logic.

const express = require('express');
const http = require('http');
const path = require('path');
const WebSocket = require('ws');

const PORT = 8000; // single port for HTTP + WS

// -------------------- Express static server --------------------
const app = express();
// Serve everything from the project root (where index.html lives)
app.use(express.static(__dirname));

// No explicit fallback needed – static middleware serves index.html for '/'

// Create the underlying HTTP server (needed for WS upgrade)
const server = http.createServer(app);

// -------------------- WebSocket lobby logic --------------------
const wss = new WebSocket.Server({ server }); // shares the same http server

// roomId -> { board: Array(9).fill(''), turn: 'X', players: Set<WebSocket> }
const rooms = new Map();

// Helper: broadcast payload to all sockets in a room
function broadcast(room, payload) {
  const msg = JSON.stringify(payload);
  for (const client of room.players) {
    if (client.readyState === WebSocket.OPEN) client.send(msg);
  }
}

// Helper: send current list of rooms (only those with a single player) to a socket
function sendRoomList(ws) {
  const list = [];
  for (const [id, r] of rooms.entries()) {
    if (r.players.size === 1) {
      list.push({ roomId: id, playersCount: 1, locked: !!r.password });
    }
  }
  ws.send(JSON.stringify({ type: 'roomList', rooms: list }));
}

// Broadcast the lobby list to **all** connected clients
function broadcastRoomList() {
  const list = [];
  for (const [id, r] of rooms.entries()) {
    if (r.players.size === 1) list.push({ roomId: id, playersCount: 1, locked: !!r.password });
  }
  const payload = JSON.stringify({ type: 'roomList', rooms: list });
  wss.clients.forEach(c => {
    if (c.readyState === WebSocket.OPEN) c.send(payload);
  });
}

// Reset a room after game end
function resetRoom(room) {
  room.board = Array(9).fill('');
  room.turn = 'X';
}

// Win detection – unchanged from original implementation
function checkWin(board, sym) {
  const combos = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6]
  ];
  return combos.some(c => c.every(i => board[i] === sym));
}

// -------------------- Connection handling --------------------
wss.on('connection', ws => {
  // First message must be either "roomList" or "join"
  const initialHandler = raw => {
    let msg;
    try { msg = JSON.parse(raw); } catch (_) { return; }

    if (msg.type === 'roomList') {
      sendRoomList(ws);
      return;
    }

    if (msg.type === 'join' && typeof msg.roomId === 'string') {
      ws.removeListener('message', initialHandler);
        attachRoomHandlers(ws, msg.roomId, msg.password);
      return;
    }

    ws.send(JSON.stringify({ type: 'error', msg: 'Invalid request' }));
  };

  ws.on('message', initialHandler);
});

function attachRoomHandlers(ws, roomId, password) {
  // Find or create the room
  let room = rooms.get(roomId);
    if (!room) {
      room = { board: Array(9).fill(''), turn: 'X', players: new Set(), password: password || null };
      rooms.set(roomId, room);
    }

    // If room has a password, verify it
    if (room.password) {
      if (!password || password !== room.password) {
        ws.send(JSON.stringify({ type: 'error', msg: 'Invalid password' }));
        return ws.close();
      }
    }
  if (room.players.size >= 2) {
    ws.send(JSON.stringify({ type: 'error', msg: 'Room full' }));
    return ws.close();
  }

  // Register player
  room.players.add(ws);
  const symbol = room.players.size === 1 ? 'X' : 'O';
  ws.roomId = roomId;
  ws.symbol = symbol;

   // Inform the newcomer and update lobby for everybody
   ws.send(JSON.stringify({ type: 'joined', roomId, symbol }));
   // Show waiting overlay for the first player (if no opponent yet)
   if (room.players.size === 1) {
     ws.send(JSON.stringify({ type: 'wait' }));
   }
   broadcast(room, { type: 'state', board: room.board, turn: room.turn });
    // If second player just joined, assign random symbols and notify both
    if (room.players.size === 2) {
      const playersArray = Array.from(room.players);
      const first = playersArray[0];
      const second = playersArray[1];
      const assignXtoFirst = Math.random() < 0.5;
      first.symbol = assignXtoFirst ? 'X' : 'O';
      second.symbol = assignXtoFirst ? 'O' : 'X';
      // Ensure turn starts with X
      room.turn = 'X';
      // Notify both players of their symbols
      first.send(JSON.stringify({ type: 'joined', roomId, symbol: first.symbol }));
      second.send(JSON.stringify({ type: 'joined', roomId, symbol: second.symbol }));
      // Notify both that opponent has joined (overlay hide)
      broadcast(room, { type: 'opponentJoined' });
    }
    broadcastRoomList();

  // ------- Game messages -------
  ws.on('message', raw => {
    let data;
    try { data = JSON.parse(raw); } catch (_) { return; }

    // 1. Move
    if (data.type === 'move') {
      if (ws.symbol !== room.turn) return; // not this player's turn
      const idx = data.index;
      if (typeof idx !== 'number' || idx < 0 || idx > 8) return;
      if (room.board[idx]) return; // occupied

      room.board[idx] = ws.symbol;
      if (checkWin(room.board, ws.symbol)) {
        broadcast(room, { type: 'end', board: room.board, winner: ws.symbol });
        resetRoom(room);
        broadcastRoomList();
        return;
      }
      if (room.board.every(c => c)) {
        broadcast(room, { type: 'end', board: room.board, draw: true });
        resetRoom(room);
        broadcastRoomList();
        return;
      }
      room.turn = room.turn === 'X' ? 'O' : 'X';
      broadcast(room, { type: 'state', board: room.board, turn: room.turn });
    }

    // 4. Leave request – player exits the room
    if (data.type === 'leave') {
      // Remove player from room
      room.players.delete(ws);
      // If other player remains, notify them
      if (room.players.size > 0) {
        broadcast(room, { type: 'info', msg: 'Opponent left' });
        // Optionally close the room for remaining player – here we keep room alive so they can create new game
      } else {
        // No players left – delete room
        rooms.delete(ws.roomId);
      }
      // Reset UI for leaving player will be handled client‑side when socket closes or on receiving 'info'
      broadcastRoomList();
      return;
    }

    // 3. Explicit lobby refresh request
    if (data.type === 'roomList') {
      sendRoomList(ws);
    }
  });

  // ------- Cleanup on disconnect -------
  ws.on('close', () => {
    const r = rooms.get(ws.roomId);
    if (!r) return;
    r.players.delete(ws);
    if (r.players.size === 0) {
      rooms.delete(ws.roomId);
    } else {
      // Notify remaining player that opponent left
      broadcast(r, { type: 'info', msg: 'Opponent left' });
    }
    broadcastRoomList();
  });
}

// Start listening
server.listen(PORT, () => {
  console.log(`🚀 Server listening on http://0.0.0.0:${PORT}`);
  console.log(`   WS endpoint: ws://0.0.0.0:${PORT}`);
});
