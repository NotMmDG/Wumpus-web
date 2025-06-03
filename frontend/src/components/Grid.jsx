import React from 'react';
import './Grid.css';

const Grid = ({ visibleGrid = [], agentPos = [0, 0], boardLabels = { cols: [], rows: [] }, bestMove, percepts = [], cellPercepts = {} }) => {
  const { cols = [], rows = [] } = boardLabels;

  console.log("cellPercepts prop:", cellPercepts); // Debugging line

  const getCellStyle = (r, c) => {
    const cell = visibleGrid[r][c];
    const isCurrentCell = agentPos[0] === r && agentPos[1] === c;

    if (cell === 'unknown') {
      return { backgroundColor: '#777' };
    }

    // Always prioritize current cell percepts
    if (isCurrentCell) {
      if (percepts.includes("breeze")) return { backgroundColor: 'cyan' };
      if (percepts.includes("stench")) return { backgroundColor: 'lightgreen' };
      return { backgroundColor: 'white' };
    }

    // For any visited cell, use persistent percepts if available
    const persistent = cellPercepts[`${r},${c}`];
    if (persistent && persistent.includes("breeze")) return { backgroundColor: 'cyan' };
    if (persistent && persistent.includes("stench")) return { backgroundColor: 'lightgreen' };

    return { backgroundColor: 'white' };
  };

  return (
    <table className="wumpus-board">
      <thead>
        <tr>
          <th></th>
          {cols && cols.map(col => <th key={col}>{col}</th>)}
        </tr>
      </thead>
      <tbody>
        {visibleGrid.map((row, r) => (
          <tr key={r}>
            <td className="row-label">{rows[r]}</td>
            {row.map((cell, c) => {
              const isBestMove = bestMove && bestMove[0] === r && bestMove[1] === c;
              let content = '';

              if (agentPos[0] === r && agentPos[1] === c) {
                content = '🤖';
              } else if (cell.includes('gold')) {
                content = '🏆';
              } else if (cell.includes('wumpus')) {
                content = '🐉';
              } else if (cell === 'pit') {
                content = '🕳️';
              } else if (cell === 'unknown') {
                content = '';
              } else if (cell.includes("breeze") || cell.includes("stench")) {
                content = cell.split('+').map((p, i) => {
                  if (p === 'breeze') return <span key={i} role="img" aria-label="breeze">🌬️</span>;
                  if (p === 'stench') return <span key={i} role="img" aria-label="stench">👃</span>;
                  return p;
                });
              }

              const style = getCellStyle(r, c);
              if (isBestMove) style.border = '3px solid orange';

              return (
                <td key={c} style={style} className="cell">
                  {content}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default Grid;
