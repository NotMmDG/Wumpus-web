import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Grid from './components/Grid';
import Explanation from './components/Explanation';
import './App.css';

function App() {
  const [gameState, setGameState] = useState(null);
  const [manualMove, setManualMove] = useState('');
  const [bestMove, setBestMove] = useState(null);
  const [bestMoveReason, setBestMoveReason] = useState('');
  

  useEffect(() => {
    restartGame();
  }, []);

  const restartGame = () => {
    axios.get('http://localhost:5000/api/init')
      .then(res => {
        setGameState(res.data);
        setTimeout(() => {
          previewBestMove(res.data);
        }, 0);
      })
      .catch(console.error);
  };
  
  const previewBestMove = (state = gameState) => {
    if (!state) return;
  
    axios.post('http://localhost:5000/api/preview-best-move', {
      visibleGrid: state.visible_grid,
      agentPos: state.agent_pos
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    })  
    .then(res => {
      setBestMove(res.data.best_move);
      setBestMoveReason(res.data.reason);
    })
    .catch(() => {
      setBestMove(null);
      setBestMoveReason('');
    });
  };
  
  

  const handleNextMove = () => {
    axios.post('http://localhost:5000/api/next-move')
      .then(res => {
        setGameState(res.data);
        previewBestMove();
      })
      .catch(console.error);
  };

  const handleManualMove = () => {
    if (!manualMove.match(/^[A-E][1-5]$/i)) {
      alert("Invalid move format! Use format like A1, B3, etc.");
      return;
    }
    const col = manualMove[0].toUpperCase().charCodeAt(0) - 65;
    const row = parseInt(manualMove[1], 10) - 1;
    axios.post('http://localhost:5000/api/manual-move', { move: [row, col] })
      .then(res => {
        setGameState(res.data);
        previewBestMove();
      })
      .catch(console.error);
  };

  if (!gameState) return <div>Loading...</div>;

  return (
    <div className="App">
      <h1>Wumpus World 🌍</h1>

      <Grid
        visibleGrid={gameState.visible_grid}
        agentPos={gameState.agent_pos}
        boardLabels={gameState.board_labels}
        bestMove={bestMove}
        percepts={gameState.percepts}
        cellPercepts={gameState.cell_percepts}
      />

      <Explanation
        percepts={gameState.percepts}
        reason={
          gameState.move_reason +
          (bestMoveReason && !gameState.move_reason.includes(bestMoveReason)
            ? `\n\nBest move preview: ${bestMoveReason}`
            : '')
        }
      />

      <div style={{ margin: '10px 0' }}>
        <button onClick={handleNextMove} disabled={gameState.game_over}>Next Auto Move</button>
      </div>

      <div>
        <input
          type="text"
          placeholder="Enter manual move (e.g. B3)"
          value={manualMove}
          onChange={e => setManualMove(e.target.value)}
          disabled={gameState.game_over}
        />
        <button onClick={handleManualMove} disabled={gameState.game_over}>Make Manual Move</button>
      </div>

      <div style={{ marginTop: 10 }}>
        <button onClick={restartGame}>Restart Game</button>
      </div>
    </div>
  );
}

export default App;
